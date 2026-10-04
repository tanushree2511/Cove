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

def _bgr_to_pil(frame):
    """Frames come from OpenCV, which is BGR. CLIP expects RGB: feeding BGR swaps the red and blue channels
    of every frame and measurably hurts video search and tagging accuracy."""
    return Image.fromarray(np.ascontiguousarray(frame[:, :, ::-1]))


def encode_image(frame):
    engine = _get_engine()
    image = _bgr_to_pil(frame)
    emb = engine.get_image_embedding(image)
    if emb is None:
        raise ValueError("Failed to encode image")
    return emb

def encode_images_batch(frames, batch_size=None):
    """Encodes OpenCV (BGR) frames with the shared engine, in hardware-sized batches."""
    engine = _get_engine()
    embeddings = engine.get_image_embeddings([_bgr_to_pil(f) for f in frames], batch_size=batch_size)
    all_embeddings = [e for e in embeddings if e is not None]

    if not all_embeddings:
        raise ValueError("Failed to encode any frames")

    return np.array(all_embeddings)

def encode_text(text):
    engine = _get_engine()
    emb = engine.get_text_embedding(text)
    if emb is None:
        raise ValueError("Failed to encode text")
    return emb

def encode_prompt(text):
    """Single text-encoder pass for a fixed label prompt (no prompt-ensembling).
    Matches the 6-pass ensemble's UCF101 accuracy exactly while being ~6x cheaper."""
    return _get_engine()._encode_single_text(text.strip())


def get_model_id():
    return _get_engine().model_id


def encode_query(text):
    """
    Text embedding used for free-text *video search*.
    The plain caption blended with its "a photo of ..." form scored best on MSR-VTT; wrapping the query
    in "a video of ..." prompts (the previous approach) scored lower because CLIP's image-text
    pretraining saw photos+captions, and our video embeddings are built from still frames.
    """
    engine = _get_engine()
    q = text.strip()
    a = engine._encode_single_text(q)
    b = engine._encode_single_text("a photo of " + q)
    v = a + b
    return v / (np.linalg.norm(v) + 1e-9)


def generate_video_embedding(frames, frame_embeddings=None):
    """Mean-pooled, L2-normalised video embedding. Pass `frame_embeddings` to avoid re-encoding frames."""
    if len(frames) == 0:
        raise ValueError("No frames extracted from video")

    embeddings = frame_embeddings if frame_embeddings is not None else encode_images_batch(frames)
    video_embedding = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(video_embedding)
    if norm > 0:
        video_embedding = video_embedding / norm
    return video_embedding
