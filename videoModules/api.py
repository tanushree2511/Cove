import logging
logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, Query, BackgroundTasks, HTTPException, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional, Union
import shutil, os, sqlite3, json, time, threading, traceback, subprocess
import numpy as np

from core.video_processor import extract_frames, video_duration, pick_evenly
from concurrent.futures import ThreadPoolExecutor
from core.face_processor import process_and_link_faces, cluster_all_faces, remove_duplicate_faces
from core.embedder import generate_video_embedding, encode_text, encode_images_batch, encode_query
from core.vector_store import add_vector, search_vector
from core.classifier import classify_video
from core.transcode import ensure_playable, is_browser_playable, transcode_to_mp4
from core.database import init_db, add_video, update_video_vectors, get_video_by_index, DB_PATH, link_face_to_person

from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

try:
    from config.vision_config import CONFIG
    BASE_DATA_DIR = CONFIG.user_data_dir
except Exception:
    try:
        from cove.config.vision_config import CONFIG
        BASE_DATA_DIR = CONFIG.user_data_dir
    except Exception:
        BASE_DATA_DIR = os.getcwd()

UPLOAD_DIR = os.path.join(BASE_DATA_DIR, "uploaded_videos")
THUMB_DIR = os.path.join(BASE_DATA_DIR, "static", "face_thumbnails")
AUDIO_DIR = os.path.join(BASE_DATA_DIR, "static", "audio")
import cv2

UPLOAD_DIR = os.path.join(BASE_DATA_DIR, "uploaded_videos")
THUMB_DIR = os.path.join(BASE_DATA_DIR, "static", "face_thumbnails")
VID_THUMB_DIR = os.path.join(BASE_DATA_DIR, "static", "video_thumbnails")
AUDIO_DIR = os.path.join(BASE_DATA_DIR, "static", "audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(VID_THUMB_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

job_progress = {
    "bulk_index": {"status": "idle", "current": 0, "total": 0, "eta": 0, "message": ""},
    "clustering": {"status": "idle", "current": 0, "total": 0, "message": ""},
}
stop_flags = {"bulk_index": False, "clustering": False}

init_db()

def rebuild_vector_index():
    try:
        from core.vector_store import INDEX_PATH, DIM
        import faiss
        new_index = faiss.IndexFlatIP(DIM)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT embedding FROM videos ORDER BY id ASC")
        for (emb_json,) in cur.fetchall():
            if emb_json:
                emb = np.array(json.loads(emb_json)).astype("float32")
                new_index.add(np.array([emb]))
        conn.close()
        faiss.write_index(new_index, INDEX_PATH)
        import core.vector_store
        core.vector_store.index = new_index
    except Exception as e:
        logger.warning("Error syncing vector index: %s", e)

def process_single_video(file_path):
    logger.info(f"DEBUG: Processing {file_path}")
    frames = extract_frames(file_path)
    if not frames:
        logger.info(f"DEBUG: No frames extracted from {file_path}")
        return "unknown"

    # Save a video cover thumbnail image
    try:
        vid_thumb_name = f"{os.path.splitext(os.path.basename(file_path))[0]}.jpg"
        vid_thumb_path = os.path.join(VID_THUMB_DIR, vid_thumb_name)
        if not os.path.exists(vid_thumb_path):
            cv2.imwrite(vid_thumb_path, frames[0])
    except Exception as e:
        logger.warning(f"Failed to write video thumbnail: {e}")

    # Register the row first (resets any old faces) so face detection can run *alongside* CLIP: both are
    # independent models, and overlapping them keeps the CPU/GPU fed instead of idling during the other stage.
    video_id = add_video(file_path, "Processing AI tags...")
    with ThreadPoolExecutor(max_workers=1) as pool:
        face_job = pool.submit(process_and_link_faces, frames, video_id)

        # CLIP only needs a few frames: accuracy is flat from 16 down to ~4 per clip, so use as many as the
        # hardware can afford within its time budget (more on a GPU, fewer on a slow CPU).
        profile = CONFIG.runtime_profile
        n_clip = profile.frames_for_video(video_duration(file_path)) if profile else len(frames)
        clip_frames = pick_evenly(frames, n_clip)
        frame_embs = encode_images_batch(clip_frames)  # [n_frames, 512], kept for frame-level search
        v_emb = generate_video_embedding(clip_frames, frame_embeddings=frame_embs)
        label = classify_video(v_emb)
        update_video_vectors(video_id, label, v_emb, frame_embs)

        try:
            face_job.result()
        except Exception:
            logger.exception("Face analysis failed for %s", file_path)
    rebuild_vector_index()
    return label

video_queue = []
video_queue_lock = threading.Lock()
is_queue_worker_running = False
total_batch_count = 0
completed_batch_count = 0

def video_queue_worker():
    global job_progress, is_queue_worker_running, total_batch_count, completed_batch_count
    while True:
        with video_queue_lock:
            if not video_queue:
                is_queue_worker_running = False
                job_progress["bulk_index"]["status"] = "completed"
                job_progress["bulk_index"]["message"] = f"Finished analyzing {completed_batch_count} video(s)."
                try:
                    cluster_res = cluster_all_faces()
                    logger.info(f"Auto-clustering completed: {cluster_res}")
                except Exception as e:
                    logger.warning(f"Auto-clustering error: {e}")
                break
            file_path = video_queue.pop(0)

        filename = os.path.basename(file_path)
        current_num = completed_batch_count + 1
        job_progress["bulk_index"] = {
            "status": "processing",
            "current": current_num,
            "total": total_batch_count,
            "eta": 0,
            "start_time": time.time(),
            "message": f"AI analyzing {filename} ({current_num}/{total_batch_count})",
        }
        try:
            label = process_single_video(file_path)
            completed_batch_count += 1
            job_progress["bulk_index"]["current"] = completed_batch_count
            job_progress["bulk_index"]["message"] = f"Indexed {filename} -> {label}"
        except Exception as err:
            logger.exception(f"Error processing video {filename}: {err}")
            completed_batch_count += 1

def enqueue_video_processing(file_path: str, batch_total: int = None):
    global is_queue_worker_running, total_batch_count, completed_batch_count
    with video_queue_lock:
        if not is_queue_worker_running:
            total_batch_count = 0
            completed_batch_count = 0
        if batch_total is not None and batch_total > total_batch_count:
            total_batch_count = batch_total
        elif batch_total is None:
            total_batch_count += 1
        video_queue.append(file_path)
        if not is_queue_worker_running:
            is_queue_worker_running = True
            t = threading.Thread(target=video_queue_worker, daemon=True)
            t.start()

def reconcile_video_storage_with_disk():
    """
    Scans UPLOAD_DIR on startup.
    1. Removes database records whose video files are missing on disk.
    2. Registers any unindexed video files found in UPLOAD_DIR and enqueues them for background AI processing.
    3. Resumes processing for any videos with incomplete labels, missing faces, or missing thumbnails.
    4. Rebuilds the FAISS vector index.
    """
    logger.info("Reconciling video database with disk...")
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        return

    valid_exts = ('.mp4', '.mkv', '.avi', '.mov', '.webm')
    disk_files = [
        os.path.join(UPLOAD_DIR, f)
        for f in os.listdir(UPLOAD_DIR)
        if f.lower().endswith(valid_exts) and os.path.isfile(os.path.join(UPLOAD_DIR, f))
    ]
    disk_names = {os.path.basename(p): p for p in disk_files}

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, path, label, embedding FROM videos")
    db_videos = cur.fetchall()

    db_paths = set()
    to_enqueue = []

    for vid_id, v_path, v_label, v_emb in db_videos:
        fn = os.path.basename(v_path)
        actual_path = disk_names.get(fn)
        if not actual_path or not os.path.exists(actual_path):
            logger.info(f"Removing missing video record from DB: {v_path}")
            cur.execute("DELETE FROM faces WHERE video_id = ?", (vid_id,))
            cur.execute("DELETE FROM videos WHERE id = ?", (vid_id,))
        else:
            db_paths.add(fn)
            if v_path != actual_path:
                cur.execute("UPDATE videos SET path = ? WHERE id = ?", (actual_path, vid_id))
            
            cur.execute("SELECT COUNT(*) FROM faces WHERE video_id = ?", (vid_id,))
            face_cnt = cur.fetchone()[0]

            vid_thumb_name = f"{os.path.splitext(fn)[0]}.jpg"
            vid_thumb_path = os.path.join(VID_THUMB_DIR, vid_thumb_name)

            if not v_emb or v_label == "Processing AI tags..." or v_label == "unknown" or not os.path.exists(vid_thumb_path):
                to_enqueue.append(actual_path)

    cur.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")
    conn.commit()
    conn.close()

    for fn, f_path in disk_names.items():
        if fn not in db_paths:
            logger.info(f"Discovered unindexed video on disk: {fn}")
            add_video(f_path, "Processing AI tags...")
            to_enqueue.append(f_path)

    rebuild_vector_index()

    if to_enqueue:
        logger.info(f"Enqueuing {len(to_enqueue)} video(s) for background processing...")
        for vp in to_enqueue:
            enqueue_video_processing(vp, batch_total=len(to_enqueue))
    else:
        try:
            cluster_all_faces()
        except Exception as e:
            logger.warning(f"Startup face clustering error: {e}")

def convert_unplayable_videos_on_disk():
    """Re-encode stored videos a browser can't play (AVI/Xvid, MPEG-4 Part 2, HEVC, MKV...) to H.264 MP4 and point
    their database rows at the new file. Needs no work once every file is playable."""
    if not os.path.isdir(UPLOAD_DIR):
        return
    valid_exts = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.wmv', '.m4v')
    for fn in sorted(os.listdir(UPLOAD_DIR)):
        old_path = os.path.join(UPLOAD_DIR, fn)
        if not fn.lower().endswith(valid_exts) or not os.path.isfile(old_path) or is_browser_playable(old_path):
            continue
        new_path = ensure_playable(old_path)
        if new_path == old_path:
            continue
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute("SELECT id, path FROM videos").fetchall()
            for vid_id, v_path in rows:
                if os.path.basename(v_path) == fn:
                    conn.execute("UPDATE videos SET path = ? WHERE id = ?", (new_path, vid_id))
            conn.commit()
        finally:
            conn.close()


@asynccontextmanager
async def video_lifespan(app: FastAPI):
    try:
        convert_unplayable_videos_on_disk()
    except Exception as e:
        logger.warning(f"Video conversion error: {e}")
    try:
        reconcile_video_storage_with_disk()
    except Exception as e:
        logger.warning(f"Video startup reconciliation error: {e}")
    yield

app = FastAPI(lifespan=video_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/stream", StaticFiles(directory=UPLOAD_DIR), name="stream")
app.mount("/faces", StaticFiles(directory=THUMB_DIR), name="faces")
app.mount("/thumbnails", StaticFiles(directory=VID_THUMB_DIR), name="thumbnails")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

@app.post("/index-video")
async def index_video(file: UploadFile = File(...), batch_total: Optional[int] = Form(None)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Browsers can't play AVI/Xvid, HEVC, MKV...: store an H.264 MP4 instead (no-op for files that already play)
    file_path = await run_in_threadpool(ensure_playable, file_path)
    # Register video immediately so it is playable in the Library right away
    video_id = add_video(file_path, "Processing AI tags...")
    enqueue_video_processing(file_path, batch_total=batch_total)
    return {"message": "Success", "video_id": video_id, "path": file_path, "label": "Processing AI tags..."}

def run_bulk_index_task(directory_path: str):
    global job_progress, stop_flags
    try:
        stop_flags["bulk_index"] = False
        directory_path = os.path.normpath(directory_path.strip().replace('"', '').replace("'", ""))
        extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
        
        files_to_process = []
        if os.path.isfile(directory_path):
            if directory_path.lower().endswith(extensions):
                files_to_process.append(directory_path)
            else:
                job_progress["bulk_index"] = {"status": "error", "message": f"Unsupported video format: {directory_path}"}
                return
        elif os.path.isdir(directory_path):
            for root, dirs, filenames in os.walk(directory_path):
                for f in filenames:
                    if f.lower().endswith(extensions):
                        files_to_process.append(os.path.join(root, f))
        else:
            job_progress["bulk_index"] = {"status": "error", "message": f"Path does not exist: {directory_path}"}
            return
                    
        logger.info(f"DEBUG: Found {len(files_to_process)} video file(s) at {directory_path}")
        
        if not files_to_process:
            job_progress["bulk_index"] = {"status": "error", "message": "No matching video files found."}
            return

        job_progress["bulk_index"] = {
            "status": "processing", 
            "current": 0, 
            "total": len(files_to_process), 
            "eta": 0, 
            "start_time": time.time(), 
            "message": f"Indexing {len(files_to_process)} videos..."
        }
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT path, label FROM videos")
        db_records = cursor.fetchall()
        conn.close()

        indexed_paths = {}
        for r_path, r_label in db_records:
            indexed_paths[os.path.normpath(r_path)] = r_label

        for i, file_path in enumerate(files_to_process):
            if stop_flags["bulk_index"]:
                job_progress["bulk_index"]["status"] = "cancelled"
                job_progress["bulk_index"]["message"] = "Cancelled by user."
                return

            filename = os.path.basename(file_path)
            dest_path = os.path.normpath(os.path.join(UPLOAD_DIR, filename))
            
            mp4_twin = os.path.normpath(os.path.join(UPLOAD_DIR, os.path.splitext(filename)[0] + ".mp4"))
            if dest_path in indexed_paths or mp4_twin in indexed_paths:
                label = indexed_paths.get(dest_path) or indexed_paths[mp4_twin]
                logger.info(f"DEBUG: Skipping {filename}, already indexed as '{label}'.")
            elif file_path in indexed_paths:
                label = indexed_paths[file_path]
                logger.info(f"DEBUG: Skipping {filename}, already indexed as '{label}'.")
            else:
                try:
                    if is_browser_playable(file_path):
                        if not os.path.exists(dest_path):
                            shutil.copy(file_path, dest_path)
                    else:
                        dest_path = os.path.normpath(os.path.join(UPLOAD_DIR, os.path.splitext(filename)[0] + ".mp4"))
                        if not os.path.exists(dest_path) and not transcode_to_mp4(file_path, dest_path):
                            raise RuntimeError(f"could not convert {filename} to a playable MP4")

                    label = process_single_video(dest_path)
                except Exception as e:
                    logger.info(f"DEBUG: Error processing {filename}: {str(e)}")
                    print(traceback.format_exc())
                    label = "error"
                
            job_progress["bulk_index"]["current"] = i + 1
            job_progress["bulk_index"]["message"] = f"Indexed: {filename} -> {label} ({i+1}/{len(files_to_process)})"
            elapsed = time.time() - job_progress["bulk_index"]["start_time"]
            avg_time = elapsed / (i + 1)
            job_progress["bulk_index"]["eta"] = avg_time * (len(files_to_process) - (i + 1))
            
        total_time = time.time() - job_progress["bulk_index"]["start_time"]
        mins, secs = divmod(int(total_time), 60)
        job_progress["bulk_index"]["status"] = "completed"
        job_progress["bulk_index"]["message"] = f"Finished indexing {len(files_to_process)} videos in {mins}m {secs}s."
    except Exception as e:
        logger.info(f"DEBUG: Bulk task failed: {str(e)}")
        print(traceback.format_exc())
        job_progress["bulk_index"]["status"] = "error"
        job_progress["bulk_index"]["message"] = str(e)

@app.post("/index-bulk")
async def index_bulk(directory_path: str, background_tasks: BackgroundTasks):
    normalized_path = os.path.normpath(directory_path.strip().replace('"', '').replace("'", ""))
    if not os.path.exists(normalized_path): 
        return {"error": f"Directory not found: {normalized_path}"}
    background_tasks.add_task(run_bulk_index_task, normalized_path)
    return {"message": "Started"}

def reindex_library():
    """Re-run the full analysis (frames, embeddings, labels, faces) over every stored video."""
    global job_progress, stop_flags
    try:
        stop_flags["bulk_index"] = False
        extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
        files_to_process = []
        if os.path.exists(UPLOAD_DIR):
            for f in os.listdir(UPLOAD_DIR):
                if f.lower().endswith(extensions):
                    files_to_process.append(os.path.join(UPLOAD_DIR, f))
        if not files_to_process:
            job_progress["bulk_index"] = {"status": "completed", "current": 0, "total": 0, "message": "No videos in library."}
            return

        job_progress["bulk_index"] = {
            "status": "processing",
            "current": 0,
            "total": len(files_to_process),
            "eta": 0,
            "start_time": time.time(),
            "message": f"Indexing {len(files_to_process)} video(s)..."
        }

        for i, dest_path in enumerate(files_to_process):
            if stop_flags.get("bulk_index"):
                job_progress["bulk_index"]["status"] = "cancelled"
                return
            filename = os.path.basename(dest_path)
            try:
                label = process_single_video(dest_path)
                job_progress["bulk_index"]["message"] = f"Processed: {filename} -> {label}"
            except Exception as err:
                logger.exception(f"Error processing video {filename}: {err}")
            job_progress["bulk_index"]["current"] = i + 1

        job_progress["bulk_index"]["status"] = "completed"
        job_progress["bulk_index"]["message"] = f"Indexed {len(files_to_process)} videos."
    except Exception as e:
        logger.exception(f"Reindex all failed: {e}")
        job_progress["bulk_index"]["status"] = "error"
        job_progress["bulk_index"]["message"] = str(e)


@app.post("/reindex-all")
async def reindex_all(background_tasks: BackgroundTasks):
    background_tasks.add_task(reindex_library)
    return {"message": "Started"}


def _reindex_if_clip_model_changed():
    """Stored video embeddings are only meaningful for the CLIP model that made them. If the model changed
    (a library with no record predates tracking, i.e. the legacy int8 ViT-B/32), re-analyse everything."""
    try:
        from core.embedder import _get_engine
        from core.database import get_meta, set_meta, count_videos
        from engines.search_engine import LEGACY_MODEL_ID
        # Load the models and build the label embeddings now (cached on disk afterwards), so the first video
        # a user adds doesn't pay for ~700 text-encoder passes.
        from core.classifier import get_cached_text_features
        get_cached_text_features()
        # The suffix is the frame-preprocessing version: "|rgb" marks embeddings made after the BGR->RGB fix,
        # so libraries embedded with swapped colour channels are re-analysed once.
        current = f"{_get_engine().model_id}|rgb"
        stored = get_meta("clip_model") or (LEGACY_MODEL_ID if count_videos() else current)
        set_meta("clip_model", current)
        if stored != current:
            logger.warning("CLIP model changed (%s -> %s): re-indexing the video library", stored, current)
            reindex_library()
    except Exception:
        logger.exception("CLIP model consistency check failed")


threading.Thread(target=_reindex_if_clip_model_changed, daemon=True).start()

@app.post("/cluster-faces")
async def run_clustering(background_tasks: BackgroundTasks):
    global job_progress
    
    def task():
        global job_progress
        job_progress["clustering"] = {"status": "processing", "current": 0, "total": 100, "message": "Clustering started..."}
        try:
            from core.face_processor import cluster_all_faces, clustering_progress
            
            # Start background thread to sync progress periodically
            def progress_sync():
                from core.face_processor import clustering_progress
                while job_progress["clustering"]["status"] == "processing":
                    job_progress["clustering"]["current"] = clustering_progress["current"]
                    job_progress["clustering"]["total"] = clustering_progress["total"]
                    job_progress["clustering"]["message"] = clustering_progress["message"]
                    time.sleep(0.5)
            
            sync_thread = threading.Thread(target=progress_sync, daemon=True)
            sync_thread.start()
            
            res = cluster_all_faces()
            
            job_progress["clustering"] = {
                "status": "completed",
                "current": 100,
                "total": 100,
                "message": f"Clustering complete! Grouped into {res.get('clusters', 0)} distinct identities."
            }
        except Exception as e:
            logger.info(f"DEBUG: Clustering failed: {str(e)}")
            job_progress["clustering"] = {
                "status": "error",
                "current": 0,
                "total": 100,
                "message": f"Clustering failed: {str(e)}"
            }
            
    background_tasks.add_task(task)
    return {"message": "Started"}

# --- OTHER ENDPOINTS ---
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/job-status")
async def get_job_status(): return job_progress

@app.post("/cancel-job/{job_type}")
async def cancel_job(job_type: str):
    if job_type in stop_flags: stop_flags[job_type] = True; return {"message": "Cancelled"}
    return {"error": "Invalid"}

@app.post("/clear-jobs")
async def clear_jobs():
    global job_progress
    for job in job_progress: job_progress[job] = {"status": "idle", "current": 0, "total": 0, "message": ""}
    return {"message": "Cleared"}

POOL_TAU = 0.02          # temperature of the log-mean-exp pooling over frame similarities
MIN_SEARCH_SCORE = 0.20  # below this similarity nothing plausibly matches the query
RELATIVE_CUTOFF = 0.88   # also keep every result scoring within 12% of the best one
MIN_RESULTS = 8          # ...but always show at least this many (when above the minimum score)
_vector_cache = {"key": None, "entries": []}


def _load_video_vectors():
    """[(id, path, label, frame_matrix[n,512])] for every video, cached until the table changes.
    Videos indexed before frame embeddings existed fall back to their single mean embedding."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COALESCE(MAX(id),0), COALESCE(SUM(LENGTH(frames)),0), COALESCE(SUM(LENGTH(label)),0) FROM videos")
    key = cur.fetchone()
    if key == _vector_cache["key"]:
        conn.close()
        return _vector_cache["entries"]

    cur.execute("SELECT id, path, label, embedding, frames FROM videos ORDER BY id ASC")
    entries = []
    for v_id, path, label, emb_json, frames in cur.fetchall():
        mat = None
        if frames:
            mat = np.frombuffer(frames, dtype=np.float16).reshape(-1, 512).astype("float32")
        elif emb_json:
            mat = np.array(json.loads(emb_json), dtype="float32").reshape(1, -1)
        if mat is None or mat.size == 0:
            continue
        mat = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9)
        entries.append((v_id, path, label, mat))
    conn.close()
    _vector_cache["key"], _vector_cache["entries"] = key, entries
    return entries


@app.post("/search")
async def search(query: str, threshold: float = MIN_SEARCH_SCORE):
    q_clean = query.strip().lower()
    if not q_clean:
        return {"results": []}

    q_emb = encode_query(q_clean)

    entries = _load_video_vectors()
    candidates = []
    seen_vids = set()

    for v_id, v_path, v_label, mat in entries:
        # Frame-level scoring: a smooth maximum over the video's frames, so a clip matches if *any*
        # part of it shows the query (mean-pooling washes out short events). On MSR-VTT this raised
        # Recall@1 from 60% to 72% on the 50-video gallery.
        sims = mat @ q_emb
        raw_score = float(POOL_TAU * np.log(np.mean(np.exp((sims - sims.max()) / POOL_TAU))) + sims.max())
        if v_id in seen_vids:
            continue
        seen_vids.add(v_id)

        # No label-word score boost: auto-generated labels are often wrong or vague, and boosting on them
        # pushed wrong clips above correctly-scored ones (Recall@1 52% with the boost vs 66% without).
        candidates.append({"id": v_id, "path": v_path, "label": v_label, "score": raw_score})

    if not candidates:
        return {"results": []}

    candidates.sort(key=lambda x: x['score'], reverse=True)
    top_score = candidates[0]['score']
    # ViT-B/16 similarities for real matches sit around 0.20-0.34 (median best hit 0.29), so the old 0.26
    # floor wrongly returned nothing for ~8% of queries and hid the correct clip in ~22%.
    if top_score < threshold:
        return {"results": []}

    # Keep everything close to the best match, but always show at least the MIN_RESULTS best as alternatives.
    cutoff = max(threshold, top_score * RELATIVE_CUTOFF)
    results = [c for i, c in enumerate(candidates)
               if c['score'] >= cutoff or (i < MIN_RESULTS and c['score'] >= threshold)]
    return {"results": results}

@app.get("/hardware")
async def hardware_info():
    """Detected hardware, chosen runtime configuration and the benchmark behind it."""
    profile = CONFIG.runtime_profile
    if profile is None:
        return {"available": False}
    return {
        "available": True,
        "summary": profile.describe(),
        "source": profile.source,
        "hardware": profile.hardware.to_dict(),
        "runtime": profile.config.to_dict(),
        "benchmark_images_per_second": profile.results,
        "clip_batch_size": profile.clip_batch_size,
        "frames_per_10s_video": profile.frames_for_video(10.0),
        "frames_per_long_video": profile.frames_for_video(600.0),
    }

@app.get("/videos")
async def get_all_videos():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, path, label, created_at FROM videos"); res = [{"id": r[0], "path": r[1], "label": r[2], "created_at": r[3]} for r in cursor.fetchall()]
    conn.close(); return {"videos": res}
    
@app.post("/videos/{video_id}/correct-label")
async def correct_label(video_id: int, corrected_label: str = Query(...)):
    from core.database import save_user_feedback
    save_user_feedback(video_id, corrected_label)
    return {"status": "success", "message": f"Updated video {video_id} to {corrected_label}"}

@app.post("/extract-audio")
async def extract_audio_task(video_path: str):
    try:
        import imageio_ffmpeg
        import subprocess
        
        filename = os.path.basename(video_path)
        audio_filename = f"{os.path.splitext(filename)[0]}.mp3"
        audio_path = os.path.normpath(os.path.join(AUDIO_DIR, audio_filename))
        video_path = os.path.normpath(video_path)
        
        if not os.path.exists(audio_path):
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            # Extract audio to MP3 using ffmpeg
            # -y overwrites, -vn excludes video, -q:a 2 high quality VBR
            result = subprocess.run([
                ffmpeg_exe, "-y", "-i", video_path,
                "-q:a", "2", "-vn", audio_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            
            if result.returncode != 0:
                err_msg = result.stderr.decode(errors='ignore') if result.stderr else "Unknown ffmpeg error"
                if "does not contain any stream" in err_msg or "Invalid argument" in err_msg:
                    return {"error": "This video does not contain an audio track."}
                logger.info(f"DEBUG: Audio extraction failed: {err_msg}")
                return {"error": f"Extraction failed: {err_msg}"}
                
        return {"audio_url": f"/audio/{audio_filename}"}
    except Exception as e:
        logger.info(f"DEBUG: Audio task error: {str(e)}")
        return {"error": str(e)}

@app.get("/all-persons")
async def get_all_persons():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, p.thumbnail, COUNT(f.id) 
        FROM persons p 
        JOIN faces f ON p.id = f.person_id 
        GROUP BY p.id 
        HAVING COUNT(f.id) > 0 
        ORDER BY p.id ASC
    """)
    res = [{"id": r[0], "name": r[1], "thumbnail": r[2], "count": r[3]} for r in cursor.fetchall()]
    conn.close()
    return {"persons": res}

@app.post("/rebuild-index")
async def rebuild_index():
    from core.vector_store import INDEX_PATH, DIM; import faiss
    if os.path.exists(INDEX_PATH): os.remove(INDEX_PATH)
    new_index = faiss.IndexFlatIP(DIM); conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT embedding FROM videos ORDER BY id ASC")
    for r in cursor.fetchall():
        if r[0]: emb = np.array(json.loads(r[0])).astype("float32"); new_index.add(np.array([emb]))
    faiss.write_index(new_index, INDEX_PATH); import core.vector_store; core.vector_store.index = new_index
    conn.close(); return {"message": "Rebuilt"}

@app.delete("/remove-duplicates")
async def cleanup_duplicates(): return {"removed_count": remove_duplicate_faces()}

class DeleteVideosRequest(BaseModel):
    video_ids: Optional[List[Union[int, str]]] = None
    paths: Optional[List[str]] = None


def _perform_video_deletion(cursor, conn, target_ids=None, target_paths=None):
    """Clean up files, thumbnails, faces, and SQLite rows for video IDs and/or paths."""
    video_rows = []
    
    # Resolve any numeric IDs or string IDs from target_ids
    valid_numeric_ids = []
    extra_paths = list(target_paths or [])
    
    if target_ids:
        for tid in target_ids:
            if isinstance(tid, int) or (isinstance(tid, str) and tid.isdigit()):
                valid_numeric_ids.append(int(tid))
            elif isinstance(tid, str):
                extra_paths.append(tid)

    if valid_numeric_ids:
        placeholders = ",".join("?" for _ in valid_numeric_ids)
        cursor.execute(f"SELECT id, path FROM videos WHERE id IN ({placeholders})", valid_numeric_ids)
        video_rows.extend(cursor.fetchall())
    
    if extra_paths:
        for p in extra_paths:
            fn = os.path.basename(p)
            cursor.execute("SELECT id, path FROM videos WHERE path = ? OR path = ? OR path LIKE ?", (p, f"uploaded_videos/{fn}", f"%{fn}"))
            video_rows.extend(cursor.fetchall())

    # Build unique mapping of id -> path
    unique_videos = {r[0]: r[1] for r in video_rows}
    
    # Also clean unindexed physical files from disk if given in paths
    for p in extra_paths:
        fn = os.path.basename(p)
        for candidate in [p, os.path.join(UPLOAD_DIR, fn), os.path.join("/app/videoModules/uploaded_videos", fn)]:
            if os.path.exists(candidate):
                try:
                    os.remove(candidate)
                except Exception:
                    pass

    if not unique_videos:
        conn.commit()
        return len(extra_paths) if extra_paths else 0

    all_ids = list(unique_videos.keys())
    id_placeholders = ",".join("?" for _ in all_ids)

    # 1. Fetch face thumbnails to remove from disk
    cursor.execute(f"SELECT thumbnail_path FROM faces WHERE video_id IN ({id_placeholders})", all_ids)
    for (thumb_name,) in cursor.fetchall():
        if thumb_name:
            for candidate in [os.path.join(THUMB_DIR, thumb_name), os.path.join("static/face_thumbnails", thumb_name)]:
                if os.path.exists(candidate):
                    try:
                        os.remove(candidate)
                    except Exception:
                        pass

    # 2. Delete physical video files
    for vid_id, path in unique_videos.items():
        fn = os.path.basename(path)
        for candidate in [path, os.path.join(UPLOAD_DIR, fn), os.path.join("/app/videoModules/uploaded_videos", fn)]:
            if candidate and os.path.exists(candidate):
                try:
                    os.remove(candidate)
                except Exception:
                    pass

    # 3. Clean database tables
    cursor.execute(f"DELETE FROM faces WHERE video_id IN ({id_placeholders})", all_ids)
    cursor.execute(f"DELETE FROM videos WHERE id IN ({id_placeholders})", all_ids)

    # 4. Clean up orphaned persons (people with 0 remaining faces)
    cursor.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")

    conn.commit()

    # 5. Rebuild FAISS index
    try:
        from core.vector_store import INDEX_PATH, DIM
        import faiss
        if os.path.exists(INDEX_PATH):
            os.remove(INDEX_PATH)
        new_index = faiss.IndexFlatIP(DIM)
        cursor.execute("SELECT embedding FROM videos ORDER BY id ASC")
        for (emb_json,) in cursor.fetchall():
            if emb_json:
                emb = np.array(json.loads(emb_json)).astype("float32")
                new_index.add(np.array([emb]))
        faiss.write_index(new_index, INDEX_PATH)
        import core.vector_store
        core.vector_store.index = new_index
    except Exception as exc:
        logger.warning("Error rebuilding FAISS index after deletion: %s", exc)

    return len(unique_videos)


@app.post("/videos/delete")
async def delete_videos_endpoint(payload: DeleteVideosRequest):
    """Delete selected videos by ID or path."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    deleted = _perform_video_deletion(cursor, conn, payload.video_ids, payload.paths)
    conn.close()
    return {"deleted": deleted, "count": deleted}


@app.delete("/videos/{video_id}")
async def delete_single_video_endpoint(video_id: str):
    """Delete a single video by its database ID or path."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if video_id.isdigit():
        deleted = _perform_video_deletion(cursor, conn, [int(video_id)], None)
    else:
        deleted = _perform_video_deletion(cursor, conn, None, [video_id])
    conn.close()
    return {"deleted": deleted, "video_id": video_id}


# --- DELETE VIDEOS BY TIME ---
@app.delete("/videos/delete-by-time")
async def delete_videos_by_time(hours: float = Query(...)):
    """Delete videos uploaded within the last <hours> hours.
    Also removes associated faces and video files from disk.
    Returns the number of videos deleted.
    """
    from datetime import datetime, timedelta
    import os, sqlite3
    # Use UTC time to match SQLite's default CURRENT_TIMESTAMP
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Select videos newer than cutoff (stored as TEXT timestamps)
    logger.info(f"DEBUG: Deleting videos newer than {cutoff_str}")
    cursor.execute(
        "SELECT id, path FROM videos WHERE datetime(created_at) >= ?",
        (cutoff_str,)
    )
    rows = cursor.fetchall()
    logger.info(f"DEBUG: Found {len(rows)} videos to delete")
    target_ids = [r[0] for r in rows]
    deleted = _perform_video_deletion(cursor, conn, target_ids)
    conn.close()
    return {"deleted": deleted}

@app.delete("/videos/delete-all")
async def delete_all_videos():
    """Delete all videos, faces, and files from the system."""
    import os, sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM videos")
    rows = cursor.fetchall()
    deleted = 0
    for vid_id, path in rows:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        deleted += 1
        
    cursor.execute("DELETE FROM faces")
    cursor.execute("DELETE FROM videos")
    cursor.execute("DELETE FROM persons")
    # Reset ID counters so new imports start at ID 1
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('videos', 'persons', 'faces')")
    
    # Also clear out the physical thumbnail and audio files
    for d in [THUMB_DIR, AUDIO_DIR]:
        if os.path.exists(d):
            for f in os.listdir(d):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass
    
    # Also delete the vector index file so it's fresh
    from core.vector_store import INDEX_PATH
    if os.path.exists(INDEX_PATH):
        try:
            os.remove(INDEX_PATH)
        except Exception:
            pass
            
    conn.commit()
    conn.close()
    return {"deleted": deleted}

@app.get("/face-stats")
async def get_face_stats():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM persons"); p = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM faces"); f = cursor.fetchone()[0]
    cursor.execute("SELECT p.id, COUNT(f.id) FROM persons p LEFT JOIN faces f ON p.id = f.person_id GROUP BY p.id")
    dist = {str(r[0]): r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT confidence FROM faces"); confs = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT video_id, COUNT(*) FROM faces GROUP BY video_id")
    v_dist = {str(r[0]): r[1] for r in cursor.fetchall()}
    conn.close(); return {"total_people": p, "total_faces": f, "distribution": dist, "confidences": confs, "video_distribution": v_dist}

@app.get("/face-gallery")
async def get_face_gallery():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT f.person_id, f.thumbnail_path, f.confidence, v.path FROM faces f JOIN videos v ON f.video_id = v.id ORDER BY f.person_id")
    gallery = {}
    for r in cursor.fetchall():
        p_id = str(r[0]); gallery.setdefault(p_id, []).append({"thumbnail": r[1], "confidence": r[2], "video": os.path.basename(r[3])})
    conn.close(); return {"gallery": gallery}

@app.post("/name-person/{p_id}")
async def name_person(p_id: int, name: str = Query(...)):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor(); cursor.execute("UPDATE persons SET name = ? WHERE id = ?", (name, p_id))
    conn.commit(); conn.close(); return {"status": "success"}

@app.get("/person-videos/{p_id}")
async def get_person_videos(p_id: int):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT v.path, v.label FROM videos v JOIN faces f ON v.id = f.video_id WHERE f.person_id = ?", (p_id,))
    res = [{"path": r[0], "label": r[1]} for r in cursor.fetchall()]
    conn.close(); return {"videos": res}

@app.delete("/remove-blurred-faces")
async def remove_blurred_faces():
    import cv2, os, sqlite3
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, thumbnail_path, confidence, pose_yaw FROM faces")
    rows = cursor.fetchall()
    deleted = 0
    
    for f_id, f_path, conf, pose_yaw in rows:
        should_delete = False
        reason = ""

        # Rule 1: Very low offline AI detection confidence → confirmed false positive
        if conf is not None and conf < 0.35:
            should_delete = True
            reason = f"low confidence ({conf:.2f})"

        # Rule 2: Extreme yaw angle → side-view or back-of-head, not a usable face
        # InsightFace yaw: 0° = front-facing, +/-90° = pure profile/back
        elif pose_yaw is not None and abs(pose_yaw) > 70:
            should_delete = True
            reason = f"extreme side-view angle ({pose_yaw:.1f}°)"

        # Rule 3: Missing file on disk → stale DB record
        else:
            full_path = os.path.join(THUMB_DIR, f_path)
            if not os.path.exists(full_path):
                should_delete = True
                reason = "file missing on disk"
            else:
                img = cv2.imread(full_path)
                if img is None:
                    should_delete = True
                    reason = "corrupt image file"

        if should_delete:
            logger.info(f"DEBUG: Removing face {f_path} — {reason}")
            cursor.execute("DELETE FROM faces WHERE id=?", (f_id,))
            full_path = os.path.join(THUMB_DIR, f_path)
            try:
                if os.path.exists(full_path): os.remove(full_path)
            except: pass
            deleted += 1
            
    # Cleanup: Delete any identities (persons) that have no faces left
    cursor.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")
            
    conn.commit()
    conn.close()
    return {"removed": deleted}