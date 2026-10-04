import faiss
import numpy as np
import os
import sys

_cove_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../cove'))
if _cove_dir not in sys.path:
    sys.path.insert(0, _cove_dir)

try:
    from config.vision_config import CONFIG
    BASE_DATA_DIR = CONFIG.user_data_dir
except Exception:
    try:
        from cove.config.vision_config import CONFIG
        BASE_DATA_DIR = CONFIG.user_data_dir
    except Exception:
        BASE_DATA_DIR = os.getcwd()

INDEX_DIR = os.path.join(BASE_DATA_DIR, "data")
INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")
DIM = 512

os.makedirs(INDEX_DIR, exist_ok=True)

if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
else:
    index = faiss.IndexFlatIP(DIM)


def add_vector(vector):
    vector = np.array([vector]).astype("float32")
    index.add(vector)
    faiss.write_index(index, INDEX_PATH)


def search_vector(query_vector, top_k=5):
    query_vector = np.array([query_vector]).astype("float32")
    scores, indices = index.search(query_vector, top_k)
    return scores[0], indices[0]