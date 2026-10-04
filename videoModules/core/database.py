import sqlite3
import json
import os
import sys
import numpy as np

_cove_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../cove'))
if _cove_dir not in sys.path:
    sys.path.insert(0, _cove_dir)

try:
    from config.vision_config import CONFIG
    BASE_DATA_DIR = CONFIG.user_data_dir
except Exception:
    try:
        from cove.config.vision_config import CONFIG
        BASE_DATA_DIR = CONFIG.user_data_dir
    except Exception:
        BASE_DATA_DIR = os.getcwd()

DB_PATH = os.path.join(BASE_DATA_DIR, "data", "videos.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Videos Table
    cursor.execute("CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT UNIQUE, label TEXT, embedding TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
    # Persons Table
    cursor.execute("CREATE TABLE IF NOT EXISTS persons (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, thumbnail TEXT)")
    
    # Faces Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            person_id INTEGER,
            embedding TEXT,
            thumbnail_path TEXT,
            confidence REAL DEFAULT 0.0,
            pose_yaw REAL DEFAULT NULL,
            FOREIGN KEY(video_id) REFERENCES videos(id),
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
    """)
    
    # User Feedback Table for few-shot exemplar learning
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            corrected_label TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
    """)
    # Key/value settings, e.g. which CLIP model produced the stored embeddings (they differ between models)
    cursor.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")

    # Per-frame CLIP embeddings (float16 bytes, shape [n_frames, 512]) for frame-level text->video search.
    # Older databases lack the column, so add it in place; existing rows simply have NULL until re-indexed.
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN frames BLOB")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Automatically clean up any orphan persons
    cursor.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")
    conn.commit()
    conn.close()
    deduplicate_videos()

def get_meta(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default

def set_meta(key, value):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    conn.commit()
    conn.close()

def count_videos():
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    conn.close()
    return n

def deduplicate_videos():
    """Removes any duplicate video rows in SQLite and cleans orphan faces/persons."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path FROM videos ORDER BY id ASC")
    rows = cursor.fetchall()
    seen = {}
    dups_to_remove = []
    for vid_id, path in rows:
        fn = os.path.basename(path)
        if fn in seen:
            dups_to_remove.append(vid_id)
        else:
            seen[fn] = vid_id
    if dups_to_remove:
        placeholders = ",".join("?" for _ in dups_to_remove)
        cursor.execute(f"DELETE FROM faces WHERE video_id IN ({placeholders})", dups_to_remove)
        cursor.execute(f"DELETE FROM videos WHERE id IN ({placeholders})", dups_to_remove)
    cursor.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")
    conn.commit()
    conn.close()

def add_video(path, label, embedding=None, frame_embeddings=None):
    """
    Inserts a new video or updates an existing video record by filename.
    Prevents duplicate database entries.
    `frame_embeddings` ([n_frames, 512] array) is kept so search can score individual frames.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    fn = os.path.basename(path)
    cursor.execute("SELECT id FROM videos WHERE path = ? OR path = ? OR path LIKE ?", (path, f"uploaded_videos/{fn}", f"%{fn}"))
    row = cursor.fetchone()

    emb_json = json.dumps(embedding.tolist()) if embedding is not None else None
    frames_blob = None
    if frame_embeddings is not None and len(frame_embeddings) > 0:
        frames_blob = np.asarray(frame_embeddings, dtype=np.float16).tobytes()

    if row:
        v_id = row[0]
        if frames_blob is not None:
            cursor.execute("UPDATE videos SET path = ?, label = ?, embedding = ?, frames = ? WHERE id = ?", (path, label, emb_json, frames_blob, v_id))
        else:
            # placeholder/label-only update: keep any frame embeddings already stored
            cursor.execute("UPDATE videos SET path = ?, label = ?, embedding = ? WHERE id = ?", (path, label, emb_json, v_id))
        # Clear previous faces for this video before re-populating to prevent duplicates
        cursor.execute("DELETE FROM faces WHERE video_id = ?", (v_id,))
        cursor.execute("DELETE FROM persons WHERE id NOT IN (SELECT DISTINCT person_id FROM faces WHERE person_id IS NOT NULL)")
    else:
        cursor.execute("INSERT INTO videos (path, label, embedding, frames) VALUES (?, ?, ?, ?)", (path, label, emb_json, frames_blob))
        v_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return v_id

def update_video_vectors(video_id, label, embedding, frame_embeddings=None):
    """Store a finished analysis (label + embeddings) for an existing video WITHOUT touching its faces -
    unlike add_video(), which resets them. Lets face detection run concurrently with CLIP."""
    conn = sqlite3.connect(DB_PATH)
    emb_json = json.dumps(embedding.tolist()) if embedding is not None else None
    frames_blob = np.asarray(frame_embeddings, dtype=np.float16).tobytes() if frame_embeddings is not None and len(frame_embeddings) else None
    conn.execute("UPDATE videos SET label = ?, embedding = ?, frames = COALESCE(?, frames) WHERE id = ?", (label, emb_json, frames_blob, video_id))
    conn.commit()
    conn.close()

def get_video_by_index(index_id):
    """Retrieves video details based on the vector index (FAISS index)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, path, label FROM videos ORDER BY id ASC LIMIT 1 OFFSET ?", (int(index_id),))
    result = cursor.fetchone()
    conn.close()
    return result

def link_face_to_person(video_id, person_id, embedding, thumb, confidence=0.0, pose_yaw=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO faces (video_id, person_id, embedding, thumbnail_path, confidence, pose_yaw) VALUES (?, ?, ?, ?, ?, ?)",
        (video_id, person_id, json.dumps(embedding), thumb, confidence, pose_yaw)
    )
    conn.commit()
    conn.close()

def save_user_feedback(video_id, corrected_label):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT embedding FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()

    if row and row[0]:
        embedding_str = row[0]
        cursor.execute("INSERT INTO user_feedback (video_id, corrected_label, embedding) VALUES (?, ?, ?)",
                       (video_id, corrected_label, embedding_str))

    cursor.execute("UPDATE videos SET label = ? WHERE id = ?", (corrected_label, video_id))
    conn.commit()
    conn.close()

def get_all_feedback():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT corrected_label, embedding FROM user_feedback WHERE embedding IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return rows
