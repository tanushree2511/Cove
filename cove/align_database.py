import numpy as np
import json
import os

from vision_config import CONFIG

def fix_database():
    print("🔧 VISION ARCHIVE: Database Repair Tool")
    
    # 1. Look for vectors (Try both names)
    vector_candidates = [CONFIG.embeddings_file, CONFIG.vector_path]
    vectors = None
    for candidate in vector_candidates:
        if os.path.exists(candidate):
            print(f"   -> Found vector file: {candidate}")
            vectors = np.load(candidate)
            break

    if vectors is None:
        print("❌ CRITICAL: No vector file found! You must run the pipeline first.")
        return

    if os.path.exists(CONFIG.paths_file):
        print(f"   -> Found paths file: {CONFIG.paths_file}")
        with open(CONFIG.paths_file, "r") as f:
            paths = json.load(f)
    else:
        print(f"❌ CRITICAL: '{CONFIG.paths_file}' is missing.")
        print("   The app cannot know which photo belongs to which vector.")
        return

    # 3. Validation
    if len(vectors) != len(paths):
        print(f"❌ DATA CORRUPTION: Found {len(vectors)} vectors but {len(paths)} file paths.")
        print("   You must re-run 'python test_pipeline_queue.py' to fix this.")
        return

    print(f"✅ Data Validated: {len(vectors)} images.")

    # 4. Convert List to Dictionary Map (Required for VectorStorage)
    # The App needs {"path/to/image.jpg": 0, "path/to/other.jpg": 1}
    data_map = {path: i for i, path in enumerate(paths)}

    # 5. Save in the Standard Format
    print("💾 Saving standardized database...")
    os.makedirs(os.path.dirname(CONFIG.vector_path), exist_ok=True)
    np.save(CONFIG.vector_path, vectors)
    cache_dir = os.path.dirname(CONFIG.image_cache)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
    with open(CONFIG.image_cache, "w") as f:
        json.dump(data_map, f)

    print("✅ DONE! You can now run 'streamlit run app.py'")

if __name__ == "__main__":
    fix_database()
    