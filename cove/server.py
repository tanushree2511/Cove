import os

import cv2
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ai_engine import AIEnginePool
from search_engine import SearchEngine
from vector_storage import VectorStorage
from vision_config import CONFIG, get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
ai_pool = None
search_engine = None
storage = None
search_storage = None


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


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=8000, workers=1)
