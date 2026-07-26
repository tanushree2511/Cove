import numpy as np
import json
import os
import time
from cluster_engine import ClusterEngine
from person_manager import PersonManager
from vision_config import CONFIG

def main():
    print("⚡ VISION ARCHIVE: INSTANT TUNER (Threshold Mode) ⚡")
    
    # Load Vectors from the CONFIG paths (Fixed by fix_data.py)
    if os.path.exists(CONFIG.embeddings_file):
        embeddings = np.load(CONFIG.embeddings_file)
    else:
        print("❌ No embeddings found.")
        return

    # Load Paths
    paths_file = f"{CONFIG.faiss_index_path}.paths"
    if os.path.exists(paths_file):
        with open(paths_file, "r") as f:
            paths = json.load(f)
    else:
        print("❌ No paths file found.")
        return

    print(f"Loaded {len(embeddings)} faces.")
    
    # Defaults
    current_thresh = 0.35
    min_size = 1  # Changed from 3 to 1 to include people with single photos (LFW has many)

    while True:
        print(f"\n--- CONFIGURATION ---")
        print(f"1. Threshold: {current_thresh} (Higher = Stricter)")
        print(f"2. Min Cluster Size: {min_size} (Minimum photos to be a 'person')")
        
        val = input("Enter new Threshold or 'size <N>' or 'exit': ")
        if val == 'exit': break
        
        if val.startswith("size "):
            try:
                min_size = int(val.split(" ")[1])
                continue
            except:
                print("Invalid size.")
                continue
                
        try:
            current_thresh = float(val)
        except: continue

        start = time.time()
        clusterer = ClusterEngine(min_cluster_size=min_size, threshold=current_thresh)
        labels = clusterer.fit_predict(embeddings)
        
        unique = len(set(labels)) - (1 if -1 in labels else 0)
        print(f"✅ Found {unique} unique people in {time.time()-start:.2f}s")
        
        if input("Save? (y/n): ") == 'y':
            PersonManager().save_people(labels, paths, overwrite=True)
            print("💾 Saved.")

if __name__ == "__main__":
    main()