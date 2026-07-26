import json
import os
import queue
import threading
import time

import cv2
import numpy as np
from tqdm import tqdm

from ai_engine import AIEnginePool
from prepare_lfw import ensure_test_images
from vector_storage import VectorStorage
from vision_config import CONFIG, get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

IMG_FOLDER = "test_images"
PATHS_FILE = CONFIG.paths_file


def _has_images(folder: str) -> bool:
    return os.path.isdir(folder) and any(
        file_name.lower().endswith((".jpg", ".jpeg", ".png"))
        for file_name in os.listdir(folder)
    )


def scan_worker(worker_id, file_queue, result_list, lock, pool, progress=None, progress_lock=None):
    while True:
        try:
            path = file_queue.get_nowait()
        except queue.Empty:
            break

        try:
            img = cv2.imread(path)
            if img is None:
                logger.warning("%s: Unable to read image", path)
                continue

            # Borrow engine only when needed for inference
            with pool.borrow() as engine:
                faces = engine.get_faces(img)
                
            if not faces:
                continue

            faces.sort(
                key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]),
                reverse=True,
            )

            with lock:
                result_list.append((path, faces[0].embedding))

        except Exception as exc:
            logger.exception("Worker %s failed to process %s: %s", worker_id, path, exc)
        finally:
            file_queue.task_done()
            if progress is not None and progress_lock is not None:
                with progress_lock:
                    progress.update(1)


def main():
    logger.info("🚀 Vision Archive: Auto-scaling pipeline")

    if not _has_images(IMG_FOLDER):
        logger.info("Image folder missing or empty (%s); preparing test images.", IMG_FOLDER)
        prepared_count = ensure_test_images(dest_dir=IMG_FOLDER)
        if prepared_count == 0:
            logger.error("No images available in %s", IMG_FOLDER)
            return

    if not _has_images(IMG_FOLDER):
        logger.error("Missing image folder (%s)", IMG_FOLDER)
        return

    stored_paths = []
    if os.path.exists(PATHS_FILE):
        try:
            with open(PATHS_FILE, "r") as f:
                stored_paths = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Unable to read paths file (%s): %s", PATHS_FILE, exc)
            stored_paths = []

    existing_paths = set(stored_paths)
    all_files = sorted(
        [os.path.join(IMG_FOLDER, f) for f in os.listdir(IMG_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    )
    new_files = [path for path in all_files if path not in existing_paths]

    if not new_files:
        logger.info("Database is already up to date (%d files)", len(all_files))
        return

    logger.info("Discovered %d new images", len(new_files))
    pool = AIEnginePool()

    file_queue = queue.Queue()
    for path in new_files:
        file_queue.put(path)

    results = []
    lock = threading.Lock()
    threads = []
    start_time = time.time()

    progress = tqdm(total=len(new_files), desc="Processing images", unit="img")
    progress_lock = threading.Lock()

    for worker_id in range(CONFIG.effective_workers):
        thread = threading.Thread(
            target=scan_worker,
            args=(worker_id, file_queue, results, lock, pool, progress, progress_lock),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    last_report = 0.0
    total = len(new_files)
    while any(thread.is_alive() for thread in threads):
        done = total - file_queue.qsize()
        elapsed = time.time() - start_time
        if elapsed > 0 and time.time() - last_report > 2:
            fps = done / elapsed
            logger.info("Progress %d/%d (%.1f FPS)", done, total, fps)
            last_report = time.time()
        time.sleep(0.5)

    file_queue.join()
    for thread in threads:
        thread.join()
    progress.close()

    if results:
        # Fix: Save to embeddings.npy (Face Embeddings) instead of image_vectors.npy
        storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)
        paths, embeddings = zip(*results)
        vectors = np.array(embeddings, dtype="float32")
        storage.add(vectors, list(paths))
        storage.save()
        logger.info("Saved %d embeddings to %s", len(vectors), CONFIG.faiss_index_path)

        processed_paths = [path for path, _ in results]
        stored_paths.extend(processed_paths)
        try:
            with open(PATHS_FILE, "w") as f:
                json.dump(stored_paths, f, indent=2)
        except OSError as exc:
            logger.warning("Failed to write paths file: %s", exc)

    logger.info("Pipeline complete. Added %d new images.", len(results))


if __name__ == "__main__":
    main()
