import sqlite3
import json
import os

DB_PATH = "data/videos.db"
os.makedirs("data", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Videos Table
    cursor.execute("CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT, label TEXT, embedding TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
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
    # Migration: add pose_yaw column if it doesn't exist yet
    try:
        cursor.execute("ALTER TABLE faces ADD COLUMN pose_yaw REAL DEFAULT NULL")
    except Exception:
        pass  # Column already exists

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
    conn.commit()
    conn.close()

def add_video(path, label, embedding=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (path, label, embedding) VALUES (?, ?, ?)", (path, label, json.dumps(embedding.tolist()) if embedding is not None else None))
    v_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return v_id

# --- THE MISSING FUNCTION ---
def get_video_by_index(index_id):
    """Retrieves video details based on the vector index (FAISS index).
    Uses OFFSET to match the sequential nature of the FAISS index.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # OFFSET matches the 0-indexed FAISS position perfectly
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
    """
    Saves a user label correction to database.
    Updates the main video label and stores the embedding as a training exemplar.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Retrieve the video's embedding
    cursor.execute("SELECT embedding FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()

    if row and row[0]:
        embedding_str = row[0]
        # 2. Insert feedback record
        cursor.execute("INSERT INTO user_feedback (video_id, corrected_label, embedding) VALUES (?, ?, ?)",
                       (video_id, corrected_label, embedding_str))

    # 3. Update the primary video label
    cursor.execute("UPDATE videos SET label = ? WHERE id = ?", (corrected_label, video_id))

    conn.commit()
    conn.close()

def get_all_feedback():
    """
    Retrieves all user correction exemplars for active adaptation.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT corrected_label, embedding FROM user_feedback WHERE embedding IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return rows