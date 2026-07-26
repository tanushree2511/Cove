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
            FOREIGN KEY(video_id) REFERENCES videos(id),
            FOREIGN KEY(person_id) REFERENCES persons(id)
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
    cursor.execute("SELECT path, label FROM videos ORDER BY id ASC LIMIT 1 OFFSET ?", (int(index_id),))
    result = cursor.fetchone()
    conn.close()
    return result

def link_face_to_person(video_id, person_id, embedding, thumb, confidence=0.0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO faces (video_id, person_id, embedding, thumbnail_path, confidence) VALUES (?, ?, ?, ?, ?)",
        (video_id, person_id, json.dumps(embedding), thumb, confidence)
    )
    conn.commit()
    conn.close()