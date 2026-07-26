import sqlite3
import os

DB_PATH = "data/videos.db"

def migrate():
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(videos)")
        columns = [c[1] for c in cursor.fetchall()]
        
        if "embedding" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN embedding TEXT")
            print("Added 'embedding' column.")
        
        if "created_at" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("Added 'created_at' column.")
            
        conn.commit()
        print("Migration check complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
