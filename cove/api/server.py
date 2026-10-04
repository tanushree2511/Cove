import os

import cv2
import numpy as np
import json
import re
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
from engines.search_engine import SearchEngine, LEGACY_MODEL_ID
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
NO_FACE_CACHE_FILE = os.path.join(CONFIG.user_data_dir, "no_face_cache.json")   # photos already scanned with no face

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


def _ensure_search_index_matches_model() -> bool:
    """CLIP embeddings from different models aren't comparable. If the semantic index was built with another
    model (an index with no record predates model tracking, i.e. the legacy int8 ViT-B/32), discard it so it is
    rebuilt. Returns True when the index was reset and needs re-embedding."""
    global search_storage
    if search_engine is None or search_storage is None:
        return False

    current = getattr(search_engine, 'model_id', None)
    if not isinstance(current, str):  # not a real engine (e.g. mocked in tests) -> never touch stored data
        return False

    marker = f"{CONFIG.search_index_path}.model"
    stored = None
    if os.path.exists(marker):
        with open(marker, 'r') as f:
            stored = f.read().strip()
    elif search_storage.paths:
        stored = LEGACY_MODEL_ID

    if stored is None or stored == current:
        with open(marker, 'w') as f:
            f.write(current)
        return False

    logger.warning('CLIP model changed (%s -> %s): resetting semantic index for re-embedding', stored, current)
    for stale in (CONFIG.search_index_path, f"{CONFIG.search_index_path}.paths", CONFIG.vector_path):
        if stale and os.path.exists(stale):
            os.remove(stale)
    search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)
    with open(marker, 'w') as f:
        f.write(current)
    return True


def _start_background_reindex(message: str):
    with indexing_job_lock:
        if indexing_job['status'] == 'running':
            return
        indexing_job.update(status='running', stage='scanning', progress=0, processed=0, total=1, message=message, error=None)
    threading.Thread(target=run_indexing_job, daemon=True).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ai_pool, search_engine, storage, search_storage
    logger.info('Starting Cove server (skip_model_load=%s)', CONFIG.skip_model_load)

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

        # A different CLIP model invalidates every stored embedding -> rebuild the semantic index
        try:
            if _ensure_search_index_matches_model():
                _start_background_reindex('CLIP model changed - rebuilding the search index…')
        except Exception as exc:
            logger.warning('Search index model check failed: %s', exc)
    else:
        logger.warning('Skipping model load per configuration')

    yield

    logger.info('Shutting down Cove server')
    ai_pool = None
    search_engine = None
    storage = None
    search_storage = None


app = FastAPI(title='Cove Sidecar', lifespan=lifespan)

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


RELATIVE_CUTOFF = 0.88   # keep results scoring within 12% of the best match...
MIN_RESULTS = 8          # ...but always return at least this many (when above the similarity floor)


class SearchQuery(BaseModel):
    text: str
    limit: int = 40
    threshold: float = 0.20


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


@app.get('/hardware')
async def hardware_info():
    """What hardware was detected, which runtime configuration was chosen, and the benchmark behind that choice."""
    profile = CONFIG.runtime_profile
    if profile is None:
        return {'available': False}
    return {
        'available': True,
        'summary': profile.describe(),
        'source': profile.source,
        'hardware': profile.hardware.to_dict(),
        'runtime': profile.config.to_dict(),
        'benchmark_images_per_second': profile.results,
        'clip_batch_size': profile.clip_batch_size,
        'face_engine_replicas': profile.face_pool_size,
        'worker_threads': profile.workers,
    }


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
    # The similarity floor used to be hard-coded at 0.245 (tuned for the old int8 ViT-B/32). ViT-B/16 scores
    # real matches around 0.20-0.34, so the floor is now just the client's `threshold`.
    if top_score < query.threshold:
        return {'results': []}

    # Everything close to the best match, but always at least MIN_RESULTS alternatives when above the floor.
    cutoff = max(query.threshold, top_score * RELATIVE_CUTOFF)
    filtered_results = [r for i, r in enumerate(results)
                        if r['score'] >= cutoff or (i < MIN_RESULTS and r['score'] >= query.threshold)][:query.limit]
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
    survivor_vectors = None
    if existing.vector_matrix is not None:
        keep = [i for i, path in enumerate(existing.paths[:len(existing.vector_matrix)]) if path not in paths_to_remove]
        survivor_paths = [existing.paths[i] for i in keep]
        survivor_vectors = existing.vector_matrix[keep]   # one fancy-index copy instead of a per-row Python loop

    for path in (index_path, f'{index_path}.paths', vector_path):
        if os.path.exists(path):
            os.remove(path)

    rebuilt = VectorStorage(index_path=index_path, vector_path=vector_path)
    if survivor_vectors is not None and len(survivor_vectors):
        rebuilt.add(np.ascontiguousarray(survivor_vectors, dtype='float32'), survivor_paths)
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


_DUP_NAME_PATTERN = re.compile(r"^(.*)_\d{10,14}(\.[^.]+)$")   # timestamped duplicates, e.g. name_1787487347990.jpg


def _reconcile_storage_with_disk() -> bool:
    """
    Synchronize VectorStorage indices, paths.json, and PersonManager with the actual
    files present in TEST_IMAGES_DIR on disk. Removes any dead/phantom entries.
    """
    global storage, search_storage
    if not os.path.isdir(TEST_IMAGES_DIR):
        os.makedirs(TEST_IMAGES_DIR, exist_ok=True)

    # 0. Deduplicate timestamped files on disk (e.g. name_1787487347990.jpg)
    faces_changed = False
    listing = os.listdir(TEST_IMAGES_DIR)
    touched_disk = False
    for f in listing:
        m = _DUP_NAME_PATTERN.match(f)
        if m:
            touched_disk = True
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

    if touched_disk:   # only re-list when the de-dup pass actually renamed or removed something
        listing = os.listdir(TEST_IMAGES_DIR)
    disk_filenames = set(f for f in listing if f.lower().endswith(IMAGE_EXTENSIONS))
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
            faces_changed = True

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

    return faces_changed


def _library_files() -> List[str]:
    """Sorted `test_images/<name>` paths of every image on disk (one directory scan, shared by a pass's stages)."""
    return sorted(
        f'test_images/{f}' for f in os.listdir(TEST_IMAGES_DIR)
        if f.lower().endswith(IMAGE_EXTENSIONS)
    )


def _file_signature(path: str):
    """(mtime_ns, size) of a library photo, or None if it can't be stat'ed."""
    try:
        st = os.stat(_resolve_photo_path(path))
        return [st.st_mtime_ns, st.st_size]
    except OSError:
        return None


def _load_no_face_cache() -> dict:
    try:
        with open(NO_FACE_CACHE_FILE, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_no_face_cache(cache: dict) -> None:
    tmp = f'{NO_FACE_CACHE_FILE}.tmp'
    try:
        os.makedirs(os.path.dirname(NO_FACE_CACHE_FILE), exist_ok=True)
        with open(tmp, 'w') as f:
            json.dump(cache, f)
        os.replace(tmp, NO_FACE_CACHE_FILE)
    except OSError as exc:
        logger.warning('Could not save the no-face cache: %s', exc)


def _seed_no_face_cache(indexed_face_paths: set) -> dict:
    """First run after upgrading from a build without the cache: nothing is cached yet, but the old job ran face
    detection *before* semantic embedding, so any photo already in the semantic index yet absent from face storage
    was scanned and had no face. Seed from that so the upgrade needs no re-scan."""
    global search_storage
    seeded = {}
    try:
        if search_storage is None:
            search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)
        for path in search_storage.paths:
            if path not in indexed_face_paths:
                sig = _file_signature(path)
                if sig is not None:
                    seeded[path] = sig
    except Exception as exc:
        logger.warning('Could not seed the no-face cache: %s', exc)
        return {}
    _save_no_face_cache(seeded)
    return seeded


def _run_face_detection_stage(all_files=None) -> int:
    """Detect faces + extract embeddings for files not yet in face storage. Returns how many faces were added.

    Photos that were scanned and had no face are remembered (keyed by mtime/size) so later passes skip them
    instead of re-running detection on the same faceless photos every time.
    """
    global storage
    if storage is None:
        storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)

    if all_files is None:
        all_files = _library_files()
    indexed_paths = set(storage.paths)
    if os.path.exists(NO_FACE_CACHE_FILE):
        no_face = _load_no_face_cache()
    else:
        no_face = _seed_no_face_cache(indexed_paths)
    live = set(all_files)
    pruned = {p: sig for p, sig in no_face.items() if p in live and p not in indexed_paths}   # drop deleted/now-indexed
    new_files = [p for p in all_files if p not in indexed_paths and pruned.get(p) != _file_signature(p)]

    indexing_job.update(
        stage='detecting', progress=0, processed=0, total=max(1, len(new_files)),
        message=f'Detecting faces in {len(new_files)} new images…',
    )

    if not new_files:
        if len(pruned) != len(no_face):
            _save_no_face_cache(pruned)
        indexing_job.update(progress=100, processed=0, total=0)
        return 0

    results = []
    faceless = {}
    results_lock = threading.Lock()
    progress_lock = threading.Lock()

    def _detect(path):
        full_path = _resolve_photo_path(path)
        img = cv2.imread(full_path)
        if img is None or ai_pool is None:
            return   # unreadable right now: don't cache, retry next pass
        try:
            with ai_pool.borrow() as engine:
                faces = engine.get_faces(img)
            if not faces:
                sig = _file_signature(path)
                if sig is not None:
                    with results_lock:
                        faceless[path] = sig
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

    pruned.update(faceless)
    _save_no_face_cache(pruned)

    if results:
        paths, embeddings = zip(*results)
        storage.add(np.array(embeddings, dtype='float32'), list(paths))
        storage.save()
        with open(CONFIG.paths_file, 'w') as f:
            json.dump(storage.paths, f, indent=2)

    return len(results)


def _run_semantic_reindex_stage(all_files=None):
    """Incrementally add CLIP embeddings for images not yet in the semantic index."""
    global search_storage, search_engine
    if search_storage is None:
        search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)

    if all_files is None:
        all_files = _library_files()
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

    # Embed in hardware-sized batches (decode/resize of each batch is parallelised inside the engine) rather
    # than one image per thread: bigger matrix products keep the CPU/GPU busy. A few batches per chunk keeps
    # the progress bar moving smoothly.
    chunk = max(8, getattr(search_engine, 'batch_size', 8) * 2)
    for start in range(0, len(new_paths), chunk):
        part = new_paths[start:start + chunk]
        embeddings = search_engine.get_image_embeddings([_resolve_photo_path(p) for p in part])
        for path, emb in zip(part, embeddings):
            if emb is not None:
                valid_paths.append(path)
                clip_vectors.append(emb)
        done = min(start + chunk, len(new_paths))
        indexing_job['processed'] = done
        indexing_job['progress'] = round(100 * done / max(1, len(new_paths)))
        indexing_job['message'] = f'Building semantic embeddings ({done}/{len(new_paths)})…'

    if clip_vectors:
        search_storage.add(np.array(clip_vectors, dtype='float32'), valid_paths)
        search_storage.save()

    indexing_job.update(processed=len(new_paths), progress=100)


def _people_db_exists() -> bool:
    try:
        return os.path.getsize(CONFIG.people_db_path) > 2
    except OSError:
        return False


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
        labels = ClusterEngine(min_cluster_size=1).fit_predict(embeddings)
        indexing_job.update(progress=75, message='Saving people database…')
        PersonManager().save_people(labels, face_paths, overwrite=True)
        unique_clusters = len(set(l for l in labels if l != -1))
        indexing_job.update(progress=100, processed=total_faces, message=f'Discovered {unique_clusters} people')
    except Exception as exc:
        logger.exception('Face clustering failed: %s', exc)
        indexing_job.update(progress=100, message=f'Clustering failed: {exc}')


def _count_library_photos() -> int:
    try:
        return sum(1 for f in os.listdir(TEST_IMAGES_DIR) if f.lower().endswith(IMAGE_EXTENSIONS))
    except OSError:
        return 0


MAX_INDEXING_PASSES = 20   # safety cap; each pass handles everything that arrived during the previous one


def run_indexing_job():
    try:
        # The UI uploads in batches of 50, and the first batch starts this job - so most photos arrive *after* the
        # job has scanned the folder. Run another pass until nothing new landed during a pass, instead of leaving
        # those photos un-indexed until the user presses "Start Indexing" again.
        for pass_number in range(1, MAX_INDEXING_PASSES + 1):
            indexing_job.update(
                status='running', stage='scanning', progress=0, processed=0, total=1,
                message='Reconciling library files…' if pass_number == 1 else f'New photos arrived - indexing pass {pass_number}…',
                error=None,
            )

            faces_changed = _reconcile_storage_with_disk()
            files = _library_files()            # one directory scan, shared by both stages and the end-of-pass check
            faces_added = _run_face_detection_stage(files)
            _run_semantic_reindex_stage(files)
            # Re-clustering is the expensive step and only changes the result when the face set changed.
            if faces_added or faces_changed or not _people_db_exists():
                _run_clustering_stage()
            else:
                indexing_job.update(stage='clustering', progress=100, processed=0, total=0, message='No new faces - people unchanged')

            if _count_library_photos() == len(files):
                break

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
