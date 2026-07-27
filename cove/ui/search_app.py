import os
import numpy as np
import sys
import os
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from engines.search_engine import SearchEngine
from engines.vector_storage import VectorStorage

def main():
    # 1. Initialize
    searcher = SearchEngine()
    storage = VectorStorage()

    if storage.index.ntotal == 0:
        print("❌ No images indexed. Run 'python pipeline/reindex_search.py' first.")
        return

    print(f"✅ Loaded {storage.index.ntotal} image vectors.")

    # 2. Interactive Search Loop
    while True:
        query = input("\n🔎 Enter search query (or 'exit'): ")
        if query.lower() == 'exit':
            break

        text_vec = searcher.get_text_embedding(query)
        results = storage.search(text_vec, k=5)

        print(f"\nTop results for '{query}':")
        for res in results:
            print(f" [{res['score']:.4f}] {res['path']}")

if __name__ == "__main__":
    main()