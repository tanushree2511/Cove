import sqlite3
import json
import numpy as np
from core.classifier import classify_video

DB_PATH = "data/videos.db"

def fix_labels():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, embedding FROM videos")
    rows = cursor.fetchall()
    
    updated = 0
    for vid_id, emb_str in rows:
        if emb_str:
            emb = np.array(json.loads(emb_str)).astype("float32")
            new_label = classify_video(emb)
            cursor.execute("UPDATE videos SET label = ? WHERE id = ?", (new_label, vid_id))
            updated += 1
            print(f"Video {vid_id} relabeled to: {new_label}")
            
    conn.commit()
    conn.close()
    print(f"\nDone! Successfully updated {updated} video labels.")

if __name__ == "__main__":
    fix_labels()
