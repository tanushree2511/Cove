import os
from vision_config import CONFIG

def main():
    print("🧹 Cleaning up all generated data...")
    
    files_to_delete = [
        CONFIG.vector_path,
        CONFIG.faiss_index_path,
        f"{CONFIG.faiss_index_path}.paths",
        CONFIG.search_index_path,
        f"{CONFIG.search_index_path}.paths",
        CONFIG.people_db_path,
        CONFIG.paths_file,
        CONFIG.embeddings_file,
        CONFIG.image_cache,
        # Temporary files
        f"{CONFIG.vector_path}.tmp",
        f"{CONFIG.embeddings_file}.tmp",
        f"{CONFIG.faiss_index_path}.tmp",
        f"{CONFIG.search_index_path}.tmp",
        f"{CONFIG.vector_path}.tmp.npy",
        f"{CONFIG.embeddings_file}.tmp.npy",
    ]

    # Also clean up the local models/ directory just in case there are leftovers
    local_models = "models"
    if os.path.exists(local_models):
        for f in os.listdir(local_models):
            if f.endswith(".npy") or f.endswith(".bin") or f.endswith(".paths") or f in ["paths.json", "people_db.json", "image_cache.json"]:
                files_to_delete.append(os.path.join(local_models, f))

    deleted = 0
    for f in set(files_to_delete):
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"🗑️ Deleted: {f}")
                deleted += 1
            except Exception as e:
                print(f"❌ Failed to delete {f}: {e}")

    print(f"\n✅ Total files deleted: {deleted}")
    print("Ready for a fresh start!")

if __name__ == "__main__":
    main()