import sqlite3
import os

DB_PATH = "data/videos.db"

def migrate():
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Add column without default to bypass SQLite limitation on ALTER
        cursor.execute("ALTER TABLE videos ADD COLUMN created_at DATETIME")
        # Set a default value for existing rows
        cursor.execute("UPDATE videos SET created_at = datetime('now') WHERE created_at IS NULL")
        conn.commit()
        print("Successfully added created_at column and updated existing rows.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
