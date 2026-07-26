import sqlite3
import os

DB_PATH = "data/videos.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found, skip migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE faces ADD COLUMN confidence REAL DEFAULT 0.0")
        conn.commit()
        print("Successfully added confidence column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'confidence' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
