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
from fastapi.middleware.cors import CORSMiddleware
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

TEST_IMAGES_DIR = os.path.join(CONFIG.user_data_dir, "test_images")
os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

def _resolve_photo_path(p: str) -> str:
    """Resolve a relative photo path (e.g. test_images/photo.jpg) to the absolute user_data_dir location."""
    if not p:
        return ""
    if os.path.isabs(p):
        return p
    return os.path.join(CONFIG.user_data_dir, p)

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
        ai_pool = AIEnginePool(pool_size=CONFIG.ai_engine_pool_size)
        try:
            search_engine = SearchEngine()
        except Exception:
            logger.exception('Failed to load SearchEngine')
            search_engine = None

        try:
            storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)
        except Exception as exc:
            logger.warning('Unable to initialize face storage: %s', exc)
            storage = None

        try:
            search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)
        except Exception as exc:
            logger.warning('Unable to initialize semantic storage: %s', exc)
            search_storage = None

        # Reconcile all indices with actual files on disk at startup
        try:
            _reconcile_storage_with_disk()
        except Exception as exc:
            logger.warning('Startup storage reconciliation error: %s', exc)
    else:
        logger.warning('Skipping model load per configuration')

    yield

    logger.info('Shutting down VisionArchive server')
    ai_pool = None
    search_engine = None
    storage = None
    search_storage = None


app = FastAPI(title='VisionArchive Sidecar', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    limit: int = 40
    threshold: float = 0.24


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
            'pool_size': ai_pool.pool_size if ai_pool else CONFIG.ai_engine_pool_size,
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

    k_candidates = max(query.limit, 40)
    results = search_storage.search(vector, k=k_candidates)
    if not results:
        return {'results': []}

    top_score = results[0]['score']
    min_floor = max(query.threshold, 0.245)
    if top_score < min_floor:
        return {'results': []}

    adaptive_cutoff = max(min_floor, top_score * 0.90)
    filtered_results = [r for r in results if r['score'] >= adaptive_cutoff][:query.limit]
    return {'results': filtered_results}


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
async def list_people(offset: int = 0, limit: int = 200):
    pm = PersonManager()
    people = []
    for person_id, data in pm.people.items():
        photos = data.get('photos', [])
        # Filter out photos that no longer exist on disk
        live_photos = [p for p in photos if os.path.exists(_resolve_photo_path(p))]
        if not live_photos:
            continue

        name = data.get('name')
        if not name or name == 'Unknown':
            try:
                num = int(person_id.split('_')[-1]) + 1
                name = f"Person {num}"
            except Exception:
                name = person_id.replace('_', ' ')

        people.append({
            'id': person_id,
            'name': name,
            'photo_count': len(live_photos),
            'preview_photo': live_photos[0],  # Only send the first photo for avatar, not the full list
        })

    # Sort by photo count descending (most-seen people first)
    people.sort(key=lambda x: x['photo_count'], reverse=True)
    total = len(people)
    page = people[offset:offset + limit]
    return {'total': total, 'offset': offset, 'limit': limit, 'people': page}

@app.get('/people/{person_id}/photos')
async def list_person_photos(person_id: str, offset: int = 0, limit: int = 200):
    """Return the live photos for a specific person, paginated."""
    pm = PersonManager()
    if person_id not in pm.people:
        raise HTTPException(status_code=404, detail='Person not found')
    all_photos = pm.people[person_id].get('photos', [])
    live = [p for p in all_photos if os.path.exists(_resolve_photo_path(p))]
    page = live[offset:offset + limit]
    return {'total': len(live), 'offset': offset, 'limit': limit, 'photos': page}


@app.post('/people/cleanup')
async def cleanup_stale_people():
    """Remove people whose photos no longer exist on disk. Returns counts."""
    pm = PersonManager()
    stale = [pid for pid, data in pm.people.items()
             if not any(os.path.exists(_resolve_photo_path(p)) for p in data.get('photos', []))]
    for pid in stale:
        del pm.people[pid]
    if stale:
        import json as _json
        if pm.people:
            with open(pm.db_path, 'w') as f:
                _json.dump(pm.people, f, indent=2)
        else:
            if os.path.exists(pm.db_path):
                os.remove(pm.db_path)
    return {'removed': len(stale), 'remaining': len(pm.people)}


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


def _reconcile_storage_with_disk():
    """
    Synchronize VectorStorage indices, paths.json, and PersonManager with the actual
    files present in TEST_IMAGES_DIR on disk. Removes any dead/phantom entries.
    """
    global storage, search_storage
    if not os.path.isdir(TEST_IMAGES_DIR):
        os.makedirs(TEST_IMAGES_DIR, exist_ok=True)

    # 0. Deduplicate timestamped files on disk (e.g. name_1787487347990.jpg)
    import re
    dup_pattern = re.compile(r"^(.*)_\d{10,14}(\.[^.]+)$")
    for f in list(os.listdir(TEST_IMAGES_DIR)):
        m = dup_pattern.match(f)
        if m:
            orig_name = m.group(1) + m.group(2)
            orig_path = os.path.join(TEST_IMAGES_DIR, orig_name)
            dup_path = os.path.join(TEST_IMAGES_DIR, f)
            if os.path.exists(orig_path):
                try:
                    os.remove(dup_path)
                    logger.info("Removed duplicate file from disk: %s", f)
                except Exception:
                    pass
            else:
                try:
                    os.rename(dup_path, orig_path)
                    logger.info("Renamed %s back to %s", f, orig_name)
                except Exception:
                    pass

    disk_filenames = set(
        f for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )
    disk_paths = set(f'test_images/{f}' for f in disk_filenames)

    # 1. Clean paths.json
    if os.path.exists(CONFIG.paths_file):
        try:
            with open(CONFIG.paths_file, 'r') as f:
                tracked = json.load(f)
            clean_tracked = [p for p in tracked if p in disk_paths or os.path.exists(_resolve_photo_path(p))]
            # Deduplicate tracked paths while preserving order
            seen_tracked = set()
            dedup_tracked = []
            for p in clean_tracked:
                if p not in seen_tracked:
                    seen_tracked.add(p)
                    dedup_tracked.append(p)
            if len(dedup_tracked) != len(tracked):
                logger.info("Pruned %d dead/duplicate paths from %s", len(tracked) - len(dedup_tracked), CONFIG.paths_file)
                with open(CONFIG.paths_file, 'w') as f:
                    json.dump(dedup_tracked, f, indent=2)
        except Exception as exc:
            logger.warning("Error cleaning paths.json: %s", exc)

    # 2. Clean Face Vector Storage
    if storage is not None and storage.paths:
        dead_face_paths = set(p for p in storage.paths if p not in disk_paths and not os.path.exists(_resolve_photo_path(p)))
        if dead_face_paths:
            logger.info("Pruning %d dead entries from face storage", len(dead_face_paths))
            storage = _rebuild_storage_without(storage, CONFIG.faiss_index_path, CONFIG.embeddings_file, dead_face_paths)

    # 3. Clean Semantic Vector Storage
    if search_storage is not None and search_storage.paths:
        dead_search_paths = set(p for p in search_storage.paths if p not in disk_paths and not os.path.exists(_resolve_photo_path(p)))
        if dead_search_paths:
            logger.info("Pruning %d dead entries from search storage", len(dead_search_paths))
            search_storage = _rebuild_storage_without(search_storage, CONFIG.search_index_path, CONFIG.vector_path, dead_search_paths)

    # 4. Clean PersonManager (people_db.json)
    try:
        pm = PersonManager()
        changed = False
        for pid in list(pm.people.keys()):
            photos = pm.people[pid].get('photos', [])
            seen_p = set()
            live = []
            for p in photos:
                if (p in disk_paths or os.path.exists(_resolve_photo_path(p))) and p not in seen_p:
                    seen_p.add(p)
                    live.append(p)
            if live:
                if len(live) != len(photos):
                    pm.people[pid]['photos'] = live
                    changed = True
            else:
                del pm.people[pid]
                changed = True
        if changed:
            os.makedirs(os.path.dirname(pm.db_path), exist_ok=True)
            with open(pm.db_path, 'w') as f:
                json.dump(pm.people, f, indent=2)
    except Exception as exc:
        logger.warning("Error cleaning people_db.json: %s", exc)


def _run_face_detection_stage():
    """Detect faces + extract embeddings for files not yet in face storage."""
    global storage
    if storage is None:
        storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)

    indexed_paths = set(storage.paths)
    all_files = sorted(
        f'test_images/{f}' for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )
    new_files = [p for p in all_files if p not in indexed_paths]

    indexing_job.update(
        stage='detecting', progress=0, processed=0, total=max(1, len(new_files)),
        message=f'Detecting faces in {len(new_files)} new images…',
    )

    if not new_files:
        indexing_job.update(progress=100, processed=0, total=0)
        return storage.paths

    results = []
    results_lock = threading.Lock()
    progress_lock = threading.Lock()

    def _detect(path):
        full_path = _resolve_photo_path(path)
        img = cv2.imread(full_path)
        if img is None or ai_pool is None:
            return
        try:
            with ai_pool.borrow() as engine:
                faces = engine.get_faces(img)
            if not faces:
                return
            faces.sort(key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
            with results_lock:
                results.append((path, faces[0].embedding))
        except Exception as exc:
            logger.warning("Face detection failed on %s: %s", path, exc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG.effective_workers) as executor:
        futures = [executor.submit(_detect, path) for path in new_files]
        for i, _ in enumerate(concurrent.futures.as_completed(futures)):
            with progress_lock:
                indexing_job['processed'] = i + 1
                indexing_job['progress'] = round(100 * (i + 1) / max(1, len(new_files)))
                indexing_job['message'] = f'Detecting faces ({i + 1}/{len(new_files)})…'

    if results:
        paths, embeddings = zip(*results)
        storage.add(np.array(embeddings, dtype='float32'), list(paths))
        storage.save()
        with open(CONFIG.paths_file, 'w') as f:
            json.dump(storage.paths, f, indent=2)

    return storage.paths


def _run_semantic_reindex_stage(all_paths=None):
    """Incrementally add CLIP embeddings for images not yet in the semantic index."""
    global search_storage, search_engine
    if search_storage is None:
        search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)

    all_files = sorted(
        f'test_images/{f}' for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )
    already_indexed = set(search_storage.paths)
    new_paths = [p for p in all_files if p not in already_indexed]

    indexing_job.update(
        stage='embedding', progress=0, processed=0, total=max(1, len(new_paths)),
        message=f'Building semantic embeddings for {len(new_paths)} new images…',
    )

    if not new_paths:
        indexing_job.update(progress=100, processed=0, total=0)
        return

    if search_engine is None:
        try:
            search_engine = SearchEngine()
        except Exception as exc:
            logger.warning('SearchEngine unavailable for CLIP embeddings: %s', exc)
            indexing_job.update(progress=100, message='SearchEngine skipped (models not ready)')
            return

    clip_vectors = []
    valid_paths = []
    progress_lock = threading.Lock()
    results_lock = threading.Lock()

    def _embed(path):
        full_path = _resolve_photo_path(path)
        try:
            emb = search_engine.get_image_embedding(full_path)
            return (path, emb) if emb is not None else None
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG.effective_workers) as executor:
        futures = [executor.submit(_embed, path) for path in new_paths]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            if result:
                with results_lock:
                    valid_paths.append(result[0])
                    clip_vectors.append(result[1])
            with progress_lock:
                indexing_job['processed'] = i + 1
                indexing_job['progress'] = round(100 * (i + 1) / max(1, len(new_paths)))
                indexing_job['message'] = f'Building semantic embeddings ({i + 1}/{len(new_paths)})…'

    if clip_vectors:
        search_storage.add(np.array(clip_vectors, dtype='float32'), valid_paths)
        search_storage.save()

    indexing_job.update(processed=len(new_paths), progress=100)


def _run_clustering_stage():
    """Cluster face embeddings and rebuild the people DB."""
    global storage
    if storage is None:
        storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)

    if storage.vector_matrix is None or len(storage.vector_matrix) == 0:
        logger.info('No face embeddings found — skipping clustering stage')
        indexing_job.update(stage='clustering', progress=100, processed=0, total=0, message='No faces to cluster')
        return

    embeddings = storage.vector_matrix
    face_paths = storage.paths
    total_faces = len(face_paths)

    indexing_job.update(
        stage='clustering', progress=20, processed=0, total=total_faces,
        message=f'Clustering {total_faces} face embeddings…',
    )

    try:
        labels = ClusterEngine(min_cluster_size=1, threshold=0.35).fit_predict(embeddings)
        indexing_job.update(progress=75, message='Saving people database…')
        PersonManager().save_people(labels, face_paths, overwrite=True)
        unique_clusters = len(set(l for l in labels if l != -1))
        indexing_job.update(progress=100, processed=total_faces, message=f'Discovered {unique_clusters} people')
    except Exception as exc:
        logger.exception('Face clustering failed: %s', exc)
        indexing_job.update(progress=100, message=f'Clustering failed: {exc}')


def run_indexing_job():
    try:
        indexing_job.update(
            status='running', stage='scanning', progress=0, processed=0, total=1,
            message='Reconciling library files…', error=None,
        )

        _reconcile_storage_with_disk()
        _run_face_detection_stage()
        _run_semantic_reindex_stage()
        _run_clustering_stage()

        indexing_job.update(status='completed', stage='completed', progress=100, message='Indexing complete')
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
        with open(dest, 'wb') as out:
            shutil.copyfileobj(f.file, out)
        saved.append(safe_name)

    started = False
    with indexing_job_lock:
        if indexing_job['status'] != 'running':
            # Set status to running synchronously before returning HTTP response
            indexing_job.update(
                status='running',
                stage='scanning',
                progress=0,
                processed=0,
                total=len(saved),
                message=f'Received {len(saved)} images, starting indexing…',
                error=None
            )
            background_tasks.add_task(run_indexing_job)
            started = True

    return {'saved': saved, 'count': len(saved), 'indexing_started': started}


@app.post('/index/start')
async def start_indexing(background_tasks: BackgroundTasks):
    with indexing_job_lock:
        if indexing_job['status'] == 'running':
            return {'message': 'Already running', 'status': indexing_job}
        indexing_job.update(
            status='running',
            stage='scanning',
            progress=0,
            processed=0,
            total=1,
            message='Starting indexing…',
            error=None
        )
        background_tasks.add_task(run_indexing_job)
    return {'message': 'Started'}


@app.get('/index/status')
async def get_indexing_status():
    return indexing_job


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8000, workers=1)
