import sqlite3
import os

DB_PATH = "data/videos.db"

def fix_timestamps():
    if not os.path.exists(DB_PATH): return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Update all NULL timestamps to current time
        cursor.execute("UPDATE videos SET created_at = datetime('now') WHERE created_at IS NULL")
        updated = cursor.rowcount
        conn.commit()
        print(f"Successfully fixed {updated} missing timestamps.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_timestamps()
