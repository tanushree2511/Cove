import os

import cv2
import numpy as np
import json
import shutil
import threading
import time
import concurrent.futures
from contextlib import asynccontextmanager
from typing import List
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys
import os
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from engines.ai_engine import AIEnginePool
from engines.cluster_engine import ClusterEngine
from engines.person_manager import PersonManager
from engines.search_engine import SearchEngine
from engines.vector_storage import VectorStorage
from config.vision_config import CONFIG, get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
ai_pool = None
search_engine = None
storage = None
search_storage = None

TEST_IMAGES_DIR = os.path.join(os.getcwd(), "test_images")
os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

indexing_job = {
    "status": "idle",
    "stage": "idle",
    "progress": 0,
    "processed": 0,
    "total": 0,
    "message": "",
    "error": None,
}
indexing_job_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_pool, search_engine, storage, search_storage
    logger.info('Starting VisionArchive server (skip_model_load=%s)', CONFIG.skip_model_load)
    if not CONFIG.skip_model_load:
        ai_pool = AIEnginePool(pool_size=CONFIG.effective_workers)
        try:
            search_engine = SearchEngine()
        except Exception:
            logger.exception('Failed to load SearchEngine')
            search_engine = None

        try:
            storage = VectorStorage(index_path=CONFIG.faiss_index_path)
        except Exception as exc:
            logger.warning('Unable to initialize face storage: %s', exc)
            storage = None

        try:
            search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)
        except Exception as exc:
            logger.warning('Unable to initialize semantic storage: %s', exc)
            search_storage = None
    else:
        logger.warning('Skipping model load per configuration')

    yield

    logger.info('Shutting down VisionArchive server')
    ai_pool = None
    search_engine = None
    storage = None
    search_storage = None


app = FastAPI(title='VisionArchive Sidecar', lifespan=lifespan)
app.mount('/media/test_images', StaticFiles(directory=TEST_IMAGES_DIR), name='media')

API_KEY_HEADER = 'x-api-key'

if CONFIG.api_key:
    @app.middleware('http')
    async def enforce_api_key(request: Request, call_next):
        incoming_key = request.headers.get(API_KEY_HEADER)
        if incoming_key != CONFIG.api_key:
            return JSONResponse(status_code=401, content={'detail': 'Unauthorized'})
        return await call_next(request)


class SearchQuery(BaseModel):
    text: str
    limit: int = 20


class ImageIndexRequest(BaseModel):
    file_path: str


class RenameRequest(BaseModel):
    name: str


class DeleteImagesRequest(BaseModel):
    paths: List[str]


@app.get('/health')
async def health():
    ready = not CONFIG.skip_model_load and ai_pool is not None and search_engine is not None
    data = {
        'status': 'ok' if ready else 'degraded',
        'models': {
            'gpu_enabled': CONFIG.use_gpu,
            'pool_size': CONFIG.effective_workers,
        },
        'indexes': {
            'faces': storage.index.ntotal if storage else 0,
            'semantic': search_storage.index.ntotal if search_storage else 0,
        },
        'vector_cache': bool(search_storage and search_storage.vector_matrix is not None),
    }
    return data


@app.post('/search/text')
async def search_by_text(query: SearchQuery):
    if search_engine is None or search_storage is None:
        raise HTTPException(status_code=503, detail='Semantic search is not available')

    vector = search_engine.get_text_embedding(query.text)
    if vector is None:
        raise HTTPException(status_code=422, detail='Unable to encode query')

    results = search_storage.search(vector, k=query.limit)
    return {'results': results}


@app.post('/index/image')
async def index_image(request: ImageIndexRequest):
    if ai_pool is None or storage is None:
        raise HTTPException(status_code=503, detail='Indexer is not ready')

    file_path = os.path.abspath(request.file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail='File not found')

    img = cv2.imread(file_path)
    if img is None:
        raise HTTPException(status_code=400, detail='Invalid image file')

    with ai_pool.borrow() as engine:
        faces = engine.get_faces(img)

    if not faces:
        return {'status': 'ignored', 'reason': 'no_faces_found'}

    faces.sort(key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
    vector = np.array([faces[0].embedding], dtype='float32')
    storage.add(vector, [file_path])
    storage.save()

    return {'status': 'indexed', 'path': file_path}


@app.get('/images')
async def list_images(offset: int = 0, limit: int = 1000):
    if not os.path.isdir(TEST_IMAGES_DIR):
        return {'total': 0, 'offset': offset, 'limit': limit, 'images': []}

    filenames = sorted(
        f for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )
    total = len(filenames)
    page = filenames[offset:offset + limit]

    images = []
    for fname in page:
        full_path = os.path.join(TEST_IMAGES_DIR, fname)
        try:
            mtime = os.stat(full_path).st_mtime
        except OSError:
            mtime = 0
        images.append({'path': f'test_images/{fname}', 'mtime': mtime})

    return {'total': total, 'offset': offset, 'limit': limit, 'images': images}


@app.get('/people')
async def list_people():
    pm = PersonManager()
    people = [
        {
            'id': person_id,
            'name': data.get('name', 'Unknown'),
            'photo_count': len(data.get('photos', [])),
            'photos': data.get('photos', []),
        }
        for person_id, data in pm.people.items()
    ]
    return {'people': people}


@app.post('/people/{person_id}/rename')
async def rename_person_endpoint(person_id: str, body: RenameRequest):
    pm = PersonManager()
    if person_id not in pm.people:
        raise HTTPException(status_code=404, detail='Person not found')
    pm.rename_person(person_id, body.name)
    return {'status': 'ok', 'id': person_id, 'name': body.name}


def _rebuild_storage_without(existing: VectorStorage, index_path: str, vector_path: str, paths_to_remove: set):
    """Return a fresh VectorStorage containing every entry of `existing` except paths_to_remove."""
    survivor_paths = []
    survivor_vectors = []
    if existing.vector_matrix is not None:
        for i, path in enumerate(existing.paths):
            if path not in paths_to_remove:
                survivor_paths.append(path)
                survivor_vectors.append(existing.vector_matrix[i])

    for path in (index_path, f'{index_path}.paths', vector_path):
        if os.path.exists(path):
            os.remove(path)

    rebuilt = VectorStorage(index_path=index_path, vector_path=vector_path)
    if survivor_vectors:
        rebuilt.add(np.array(survivor_vectors, dtype='float32'), survivor_paths)
    rebuilt.save()
    return rebuilt


@app.post('/images/delete')
async def delete_images(request: DeleteImagesRequest):
    if indexing_job['status'] == 'running':
        raise HTTPException(status_code=409, detail='Indexing is in progress, try again shortly')

    paths_to_remove = set(request.paths)
    if not paths_to_remove:
        return {'deleted': [], 'count': 0}

    deleted = []
    for rel_path in paths_to_remove:
        filename = os.path.basename(rel_path)
        full_path = os.path.join(TEST_IMAGES_DIR, filename)
        if os.path.commonpath([TEST_IMAGES_DIR, os.path.abspath(full_path)]) == TEST_IMAGES_DIR and os.path.exists(full_path):
            os.remove(full_path)
            deleted.append(rel_path)

    if os.path.exists(CONFIG.paths_file):
        with open(CONFIG.paths_file, 'r') as f:
            stored_paths = json.load(f)
        stored_paths = [p for p in stored_paths if p not in paths_to_remove]
        with open(CONFIG.paths_file, 'w') as f:
            json.dump(stored_paths, f, indent=2)

    global storage, search_storage
    if storage is not None:
        storage = _rebuild_storage_without(storage, CONFIG.faiss_index_path, CONFIG.embeddings_file, paths_to_remove)
    if search_storage is not None:
        search_storage = _rebuild_storage_without(search_storage, CONFIG.search_index_path, CONFIG.vector_path, paths_to_remove)

    PersonManager().remove_photos(paths_to_remove)

    return {'deleted': deleted, 'count': len(deleted)}


def _run_face_detection_stage():
    """Detect faces + extract embeddings for new files, mirroring pipeline/production_pipeline.py."""
    stored_paths = []
    if os.path.exists(CONFIG.paths_file):
        try:
            with open(CONFIG.paths_file, 'r') as f:
                stored_paths = json.load(f)
        except (json.JSONDecodeError, OSError):
            stored_paths = []

    existing = set(stored_paths)
    all_files = sorted(
        f'test_images/{f}' for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )
    new_files = [p for p in all_files if p not in existing]

    indexing_job.update(
        stage='detecting', progress=0, processed=0, total=len(new_files),
        message=f'Detecting faces in {len(new_files)} new images…',
    )

    results = []
    results_lock = threading.Lock()
    progress_lock = threading.Lock()

    def _detect(path):
        img = cv2.imread(path)
        if img is None:
            return
        with ai_pool.borrow() as engine:
            faces = engine.get_faces(img)
        if not faces:
            return
        faces.sort(key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
        with results_lock:
            results.append((path, faces[0].embedding))

    if new_files:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG.effective_workers) as executor:
            futures = [executor.submit(_detect, path) for path in new_files]
            for i, _ in enumerate(concurrent.futures.as_completed(futures)):
                with progress_lock:
                    indexing_job['processed'] = i + 1
                    indexing_job['progress'] = round(100 * (i + 1) / max(1, len(new_files)))

    global storage
    if results:
        face_storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)
        paths, embeddings = zip(*results)
        face_storage.add(np.array(embeddings, dtype='float32'), list(paths))
        face_storage.save()
        stored_paths.extend(paths)
        with open(CONFIG.paths_file, 'w') as f:
            json.dump(stored_paths, f, indent=2)

    storage = VectorStorage(index_path=CONFIG.faiss_index_path)
    return stored_paths


def _run_semantic_reindex_stage(all_paths):
    """Incrementally add CLIP embeddings for images not yet in the semantic index."""
    existing_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)
    already_indexed = set(existing_storage.paths)
    new_paths = [p for p in all_paths if p not in already_indexed]

    indexing_job.update(
        stage='embedding', progress=0, processed=0, total=len(new_paths),
        message=f'Building semantic embeddings for {len(new_paths)} new images…',
    )

    clip_vectors = []
    valid_paths = []
    progress_lock = threading.Lock()

    def _embed(path):
        try:
            emb = search_engine.get_image_embedding(path)
            return (path, emb) if emb is not None else None
        except Exception:
            return None

    if new_paths:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG.effective_workers) as executor:
            futures = [executor.submit(_embed, path) for path in new_paths]
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
                if result:
                    valid_paths.append(result[0])
                    clip_vectors.append(result[1])
                with progress_lock:
                    indexing_job['processed'] = i + 1
                    indexing_job['progress'] = round(100 * (i + 1) / max(1, len(new_paths)))

    if clip_vectors:
        existing_storage.add(np.array(clip_vectors, dtype='float32'), valid_paths)
        existing_storage.save()

    indexing_job.update(processed=len(new_paths), progress=100)

    global search_storage
    search_storage = existing_storage


def _run_clustering_stage():
    """Cluster face embeddings and rebuild the people DB, mirroring pipeline/tune_clustering.py."""
    indexing_job.update(stage='clustering', progress=0, processed=0, total=1, message='Clustering faces…')

    if os.path.exists(CONFIG.embeddings_file) and os.path.exists(f'{CONFIG.faiss_index_path}.paths'):
        embeddings = np.load(CONFIG.embeddings_file)
        with open(f'{CONFIG.faiss_index_path}.paths', 'r') as f:
            face_paths = json.load(f)
        labels = ClusterEngine(min_cluster_size=1, threshold=0.35).fit_predict(embeddings)
        PersonManager().save_people(labels, face_paths, overwrite=True)

    indexing_job.update(processed=1, progress=100)


def run_indexing_job():
    try:
        indexing_job.update(
            status='running', stage='scanning', progress=0, processed=0, total=1,
            message='Preparing test_images…', error=None,
        )

        from pipeline.prepare_lfw import ensure_test_images

        if not any(f.lower().endswith(IMAGE_EXTENSIONS) for f in os.listdir(TEST_IMAGES_DIR)):
            ensure_test_images(dest_dir=TEST_IMAGES_DIR)
        indexing_job.update(processed=1, progress=100)

        stored_paths = _run_face_detection_stage()
        _run_semantic_reindex_stage(stored_paths)
        _run_clustering_stage()

        indexing_job.update(status='completed', message='Indexing complete')
    except Exception as exc:
        logger.exception('Indexing job failed: %s', exc)
        indexing_job.update(status='error', error=str(exc), message=f'Failed: {exc}')


@app.post('/upload')
async def upload_images(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    saved = []
    for f in files:
        if not f.filename.lower().endswith(IMAGE_EXTENSIONS):
            continue
        safe_name = os.path.basename(f.filename)
        dest = os.path.join(TEST_IMAGES_DIR, safe_name)
        if os.path.exists(dest):
            base, ext = os.path.splitext(safe_name)
            dest = os.path.join(TEST_IMAGES_DIR, f'{base}_{int(time.time() * 1000)}{ext}')
        with open(dest, 'wb') as out:
            shutil.copyfileobj(f.file, out)
        saved.append(os.path.basename(dest))

    started = False
    with indexing_job_lock:
        if indexing_job['status'] != 'running':
            background_tasks.add_task(run_indexing_job)
            started = True

    return {'saved': saved, 'count': len(saved), 'indexing_started': started}


@app.post('/index/start')
async def start_indexing(background_tasks: BackgroundTasks):
    with indexing_job_lock:
        if indexing_job['status'] == 'running':
            return {'message': 'Already running', 'status': indexing_job}
        background_tasks.add_task(run_indexing_job)
    return {'message': 'Started'}


@app.get('/index/status')
async def get_indexing_status():
    return indexing_job


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8000, workers=1)
