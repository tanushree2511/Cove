import os
import numpy as np
import json
import time
import concurrent.futures
from tqdm import tqdm
from search_engine import SearchEngine
from vector_storage import VectorStorage
from vision_config import CONFIG

def main():
    print("🧠 SEMANTIC RE-INDEXING (Teaching AI to 'Read' your photos)...")
    
    # 1. Load the file list we already found
    if not os.path.exists(CONFIG.paths_file):
        print(f"❌ '{CONFIG.paths_file}' missing. Run production_pipeline.py first.")
        return
        
    with open(CONFIG.paths_file, "r") as f:
        paths = json.load(f)
        
    print(f"   -> Found {len(paths)} images to index.")
    
    # 2. Initialize CLIP (The Semantic Brain)
    searcher = SearchEngine()
    
    # 3. Build a SEPARATE FAISS index for CLIP semantic search
    #    This is distinct from faiss_index.bin which holds face embeddings.
    if os.path.exists(CONFIG.search_index_path):
        print(f"   Note: Overwriting existing search index at {CONFIG.search_index_path}")
        # Delete old index to prevent duplication during re-indexing
        try:
            os.remove(CONFIG.search_index_path)
            os.remove(f"{CONFIG.search_index_path}.paths")
            if os.path.exists(CONFIG.vector_path):
                 os.remove(CONFIG.vector_path)
        except OSError:
            pass

    search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)
    
    clip_vectors = []
    valid_paths = []
    
    print("   Starting multi-threaded indexing for max GPU usage...")
    
    # Helper function for parallel execution
    def process_image(path):
        try:
            # This handles file read + preprocessing + GPU inference
            # The GPU inference is thread-safe in ONNXRuntime
            emb = searcher.get_image_embedding(path)
            if emb is not None:
                return (path, emb)
        except Exception:
            pass
        return None

    # Use more workers because CLIP preprocessing (loading/resizing) is CPU bound
    # and we want to keep the GPU queue full.
    max_workers = CONFIG.effective_workers
    
    # Using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {executor.submit(process_image, p): p for p in paths}
        
        # Process as they complete
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(paths), unit="img"):
            result = future.result()
            if result:
                valid_paths.append(result[0])
                clip_vectors.append(result[1])

    print(f"\n✅ Re-indexing Complete! ({len(clip_vectors)} valid images)")
    
    # 4. Save to FAISS search index
    if clip_vectors:
        vectors = np.array(clip_vectors, dtype="float32")
        search_storage.add(vectors, valid_paths)
        search_storage.save()
        print(f"💾 Saved semantic search index to '{CONFIG.search_index_path}'.")
    
    print("🚀 Semantic Search is now ready. Restart Streamlit to test.")

if __name__ == "__main__":
    main()