import numpy as np
from PIL import Image
import os
import sys

# Ensure cove modules can be imported for shared ONNX models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../cove')))
from engines.search_engine import SearchEngine

_search_engine = None

def _get_engine():
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine()
    return _search_engine

def encode_image(frame):
    engine = _get_engine()
    image = Image.fromarray(frame)
    emb = engine.get_image_embedding(image)
    if emb is None:
        raise ValueError("Failed to encode image")
    return emb

def encode_images_batch(frames, batch_size=32):
    """Encodes a batch of frames using the shared ONNX engine."""
    engine = _get_engine()
    all_embeddings = []
    
    # We process them sequentially through the ONNX engine.
    for f in frames:
        emb = engine.get_image_embedding(Image.fromarray(f))
        if emb is not None:
            all_embeddings.append(emb)
    
    if not all_embeddings:
        raise ValueError("Failed to encode any frames")
        
    return np.array(all_embeddings)

def encode_text(text):
    engine = _get_engine()
    emb = engine.get_text_embedding(text)
    if emb is None:
        raise ValueError("Failed to encode text")
    return emb

def generate_video_embedding(frames):
    if len(frames) == 0:
        raise ValueError("No frames extracted from video")
    
    embeddings = encode_images_batch(frames)
    video_embedding = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(video_embedding)
    if norm > 0:
        video_embedding = video_embedding / norm
    return video_embedding
