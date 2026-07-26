import sqlite3
import faiss
import os

def check():
    db_count = 0
    if os.path.exists('data/videos.db'):
        conn = sqlite3.connect('data/videos.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM videos')
        db_count = cursor.fetchone()[0]
        conn.close()
    
    index_count = 0
    if os.path.exists('data/faiss.index'):
        index = faiss.read_index('data/faiss.index')
        index_count = index.ntotal
        
    print(f"Videos in DB: {db_count}")
    print(f"Vectors in FAISS: {index_count}")

if __name__ == "__main__":
    check()
