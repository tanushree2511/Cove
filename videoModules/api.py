from fastapi import FastAPI, UploadFile, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil, os, sqlite3, json, time, threading, traceback, subprocess
import numpy as np

from core.video_processor import extract_frames
from core.face_processor import process_and_link_faces, cluster_all_faces, remove_duplicate_faces
from core.embedder import generate_video_embedding, encode_text
from core.vector_store import add_vector, search_vector
from core.classifier import classify_video
from core.database import init_db, add_video, get_video_by_index, DB_PATH, link_face_to_person

app = FastAPI()

job_progress = {
    "bulk_index": {"status": "idle", "current": 0, "total": 0, "eta": 0, "message": ""},
    "clustering": {"status": "idle", "current": 0, "total": 0, "message": ""},
}
stop_flags = {"bulk_index": False, "clustering": False}

init_db()

UPLOAD_DIR = "uploaded_videos"
THUMB_DIR = "static/face_thumbnails"
AUDIO_DIR = "static/audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

app.mount("/stream", StaticFiles(directory=UPLOAD_DIR), name="stream")
app.mount("/faces", StaticFiles(directory=THUMB_DIR), name="faces")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

def process_single_video(file_path):
    print(f"DEBUG: Processing {file_path}")
    frames = extract_frames(file_path)
    if not frames:
        print(f"DEBUG: No frames extracted from {file_path}")
        return "unknown"
    v_emb = generate_video_embedding(frames)
    label = classify_video(v_emb)
    add_vector(v_emb)
    video_id = add_video(file_path, label, v_emb)
    process_and_link_faces(frames, video_id)
    return label

@app.post("/index-video")
async def index_video(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    label = process_single_video(file_path)
    return {"message": "Success", "label": label}

def run_bulk_index_task(directory_path: str):
    global job_progress, stop_flags
    try:
        stop_flags["bulk_index"] = False
        directory_path = os.path.normpath(directory_path.strip().replace('"', '').replace("'", ""))
        extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
        
        if not os.path.isdir(directory_path):
            job_progress["bulk_index"] = {"status": "error", "message": f"Not a directory: {directory_path}"}
            return

        files_to_process = []
        for root, dirs, filenames in os.walk(directory_path):
            for f in filenames:
                if f.lower().endswith(extensions):
                    files_to_process.append(os.path.join(root, f))
                    
        print(f"DEBUG: Found {len(files_to_process)} files in {directory_path} and subdirectories")
        
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
        cursor.execute("SELECT path FROM videos")
        indexed_paths = {os.path.normpath(r[0]) for r in cursor.fetchall()}
        conn.close()

        for i, file_path in enumerate(files_to_process):
            if stop_flags["bulk_index"]:
                job_progress["bulk_index"]["status"] = "cancelled"
                job_progress["bulk_index"]["message"] = "Cancelled by user."
                return

            filename = os.path.basename(file_path)
            dest_path = os.path.normpath(os.path.join(UPLOAD_DIR, filename))
            
            if dest_path in indexed_paths or file_path in indexed_paths:
                print(f"DEBUG: Skipping {filename}, already indexed.")
            else:
                try:
                    if not filename.lower().endswith(".mp4"):
                        new_filename = os.path.splitext(filename)[0] + ".mp4"
                        dest_path = os.path.normpath(os.path.join(UPLOAD_DIR, new_filename))
                        if not os.path.exists(dest_path):
                            print(f"DEBUG: Fast converting {filename} to MP4...")
                            import imageio_ffmpeg
                            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                            subprocess.run([
                                ffmpeg_exe, "-y", "-i", file_path, 
                                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", 
                                "-c:a", "aac", dest_path
                            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        if not os.path.exists(dest_path):
                            shutil.copy(file_path, dest_path)
                            
                    process_single_video(dest_path)
                except Exception as e:
                    print(f"DEBUG: Error processing {filename}: {str(e)}")
                    print(traceback.format_exc())
                
            job_progress["bulk_index"]["current"] = i + 1
            job_progress["bulk_index"]["message"] = f"Indexing: {filename} ({i+1}/{len(files_to_process)})"
            elapsed = time.time() - job_progress["bulk_index"]["start_time"]
            avg_time = elapsed / (i + 1)
            job_progress["bulk_index"]["eta"] = avg_time * (len(files_to_process) - (i + 1))
            
        total_time = time.time() - job_progress["bulk_index"]["start_time"]
        mins, secs = divmod(int(total_time), 60)
        job_progress["bulk_index"]["status"] = "completed"
        job_progress["bulk_index"]["message"] = f"Finished indexing {len(files_to_process)} videos in {mins}m {secs}s."
    except Exception as e:
        print(f"DEBUG: Bulk task failed: {str(e)}")
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

# --- OTHER ENDPOINTS ---
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

@app.post("/search")
async def search(query: str, threshold: float = 0.23):
    # Base generic prompts
    prompts = [f"a video of {query}", f"a scene showing {query}", query]
    
    # Add human-specific prompts only if it seems like a human activity
    if any(x in query.lower() for x in ["person", "someone", "people", "man", "woman", "boy", "girl"]):
        prompts.append(f"a person {query}")
        prompts.append(f"someone {query}")
        
    if any(x in query.lower() for x in ["sign", "gesture", "hand"]):
        prompts.append(f"a person using their hands to {query}")
        prompts.append(f"manual communication or {query}")
        
    embs = [encode_text(p) for p in prompts]
    q_emb = np.mean(embs, axis=0)
    q_emb = q_emb / np.linalg.norm(q_emb)
    scores, indices = search_vector(q_emb, top_k=20); results = []
    
    # Keyword extraction for smarter filtering
    query_words = set(query.lower().replace("a ", "").replace("the ", "").split())
    
    for score, idx in zip(scores, indices):
        if float(score) >= threshold:
            video = get_video_by_index(idx)
            if video:
                v_path, v_label = video[0], video[1]
                v_label_lower = v_label.lower()
                
                # SENSOR: Check if the AI label contradicts the search
                # If they search for 'dog' and the label is 'biking', we should be skeptical
                label_words = set(v_label_lower.replace("playing ", "").replace("with a ", "").split())
                has_keyword_match = any(word in v_label_lower for word in query_words if len(word) > 2)
                
                final_score = float(score)
                # Boost if the label matches the query keywords
                if has_keyword_match:
                    final_score += 0.1
                else:
                    # Penalize if the AI thinks it's something totally different (like biking vs dog)
                    final_score -= 0.1
                
                if final_score >= threshold:
                    results.append({"path": v_path, "label": v_label, "score": final_score})
    
    # Sort by the new Hybrid Score
    results.sort(key=lambda x: x['score'], reverse=True)
    return {"results": results}

@app.get("/videos")
async def get_all_videos():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT path, label, created_at FROM videos"); res = [{"path": r[0], "label": r[1], "created_at": r[2]} for r in cursor.fetchall()]
    conn.close(); return {"videos": res}

@app.post("/extract-audio")
async def extract_audio_task(video_path: str):
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip
        filename = os.path.basename(video_path); audio_filename = f"{os.path.splitext(filename)[0]}.mp3"; audio_path = os.path.join(AUDIO_DIR, audio_filename)
        if not os.path.exists(audio_path):
            video = VideoFileClip(video_path)
            if video.audio: video.audio.write_audiofile(audio_path, logger=None); video.close()
            else: video.close(); return {"error": "No audio"}
        return {"audio_url": f"/audio/{audio_filename}"}
    except Exception as e: return {"error": str(e)}

@app.get("/all-persons")
async def get_all_persons():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT p.id, p.name, p.thumbnail, COUNT(f.id) FROM persons p LEFT JOIN faces f ON p.id = f.person_id GROUP BY p.id")
    res = [{"id": r[0], "name": r[1], "thumbnail": r[2], "count": r[3]} for r in cursor.fetchall()]
    conn.close(); return {"persons": res}

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
    print(f"DEBUG: Deleting videos newer than {cutoff_str}")
    cursor.execute(
        "SELECT id, path FROM videos WHERE datetime(created_at) >= ?",
        (cutoff_str,)
    )
    rows = cursor.fetchall()
    print(f"DEBUG: Found {len(rows)} videos to delete")
    deleted = 0
    for vid_id, path in rows:
        # Remove video file if it exists
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        # Remove related faces
        cursor.execute("DELETE FROM faces WHERE video_id=?", (vid_id,))
        # Remove video record
        cursor.execute("DELETE FROM videos WHERE id=?", (vid_id,))
        deleted += 1
    conn.commit()
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
    cursor.execute("SELECT id, thumbnail_path, confidence FROM faces")
    rows = cursor.fetchall()
    deleted = 0
    for f_id, f_path, conf in rows:
        # If the model was not confident it's a real face, delete it
        if conf is not None and conf < 0.85:
            cursor.execute("DELETE FROM faces WHERE id=?", (f_id,))
            full_path = os.path.join(THUMB_DIR, f_path)
            try:
                if os.path.exists(full_path): os.remove(full_path)
            except: pass
            deleted += 1
            continue

        full_path = os.path.join(THUMB_DIR, f_path)
        if os.path.exists(full_path):
            img = cv2.imread(full_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                variance = cv2.Laplacian(gray, cv2.CV_64F).var()
                # Increased threshold to 300 to aggressively catch blur
                if variance < 300:
                    cursor.execute("DELETE FROM faces WHERE id=?", (f_id,))
                    try:
                        os.remove(full_path)
                    except:
                        pass
                    deleted += 1
        else:
            cursor.execute("DELETE FROM faces WHERE id=?", (f_id,))
            deleted += 1
            
    # Cleanup: Delete any identities (persons) that have no faces left
    cursor.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")
            
    conn.commit()
    conn.close()
    return {"removed": deleted}