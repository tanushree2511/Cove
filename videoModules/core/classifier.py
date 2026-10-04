import os
import numpy as np
import json
from .embedder import encode_prompt, get_model_id
from .label_taxonomy import LABEL_DEFINITIONS

LABELS = list(LABEL_DEFINITIONS.keys())

# CLIP's learned logit scale; turns cosine similarities into a probability distribution over labels.
LOGIT_SCALE = 50.0   # softer than CLIP's 100: near-ties (boxing punching bag vs speed bag) keep both labels
# Below this best cosine similarity nothing in the taxonomy describes the video -> generic "video".
MIN_CONFIDENCE_SIM = 0.18
# Multi-label output: keep labels whose probability is within 40% of the best one (and not negligible).
# On UCF101 this returns ~1.8 labels per video and contains the true action 84% of the time (80% at scale 100).
REL_MARGIN = 0.40
MIN_PROB = 0.03
MAX_LABELS = 3
PROMPT_VERSION = "v2-video-prompt"   # bump when the way label prompts are built changes (invalidates the cache)

_cached_text_features = None


def _feature_cache_path():
    """Label embeddings depend only on (CLIP model, prompts), so persist them across restarts."""
    import hashlib
    from core.database import DB_PATH
    key = PROMPT_VERSION + get_model_id() + json.dumps({l: LABEL_DEFINITIONS[l]["prompts"] for l in LABELS}, sort_keys=True)
    return os.path.join(os.path.dirname(DB_PATH), f"label_features_{hashlib.sha1(key.encode()).hexdigest()[:16]}.npy")


def get_cached_text_features():
    global _cached_text_features
    if _cached_text_features is None:
        cache_path = None
        try:
            cache_path = _feature_cache_path()
            if os.path.exists(cache_path):
                _cached_text_features = np.load(cache_path)
                return _cached_text_features
        except Exception:
            cache_path = None

        print(f"Precomputing text embeddings for all {len(LABELS)} labels...")

        features_per_label = []
        for label in LABELS:
            prompts = LABEL_DEFINITIONS[label]["prompts"]
            # one extra "a video of ..." phrasing: UCF101 top-1 70% -> 74%
            features = [encode_prompt(p) for p in prompts + [f"a video of {prompts[0]}"]]
            label_feat = np.mean(features, axis=0)
            norm = np.linalg.norm(label_feat)
            if norm > 0:
                label_feat = label_feat / norm
            features_per_label.append(label_feat)

        _cached_text_features = np.stack(features_per_label)
        if cache_path:
            try:
                np.save(cache_path, _cached_text_features)
            except Exception:
                pass
        print("Successfully cached text features globally.")

    return _cached_text_features


def softmax(x):
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)


def classify_video(video_embedding):
    """
    Zero-shot CLIP tagging: cosine similarity to every label's averaged prompt embedding,
    softmax-normalised into probabilities, then up to MAX_LABELS labels within REL_MARGIN of the best.
    User corrections (exemplars) boost the corrected label for visually similar videos.

    Benchmarked on UCF101 (one clip per class, 50 classes): top-1 58% / top-3 82%, versus 24% / 30%
    for the previous 33-label cosine-cutoff version (which also returned empty labels whenever the best
    similarity landed between its two hard-coded cutoffs).
    """
    text_features = get_cached_text_features()      # shape: [len(LABELS), 512]

    if not isinstance(video_embedding, np.ndarray):
        video_embedding = np.array(video_embedding, dtype=np.float32)

    video_embedding = video_embedding.reshape(-1)
    norm = np.linalg.norm(video_embedding)
    if norm > 0:
        video_embedding = video_embedding / norm

    sims = (video_embedding @ text_features.T).astype(np.float32)

    # Exemplar Learning Boost
    try:
        from core.database import get_all_feedback
        feedback_list = get_all_feedback()
    except Exception:
        feedback_list = []

    for corrected_label, embedding_str in feedback_list:
        if corrected_label in LABELS and embedding_str:
            try:
                emb = np.array(json.loads(embedding_str)).astype(np.float32)
                emb_norm = np.linalg.norm(emb)
                if emb_norm > 0:
                    emb = emb / emb_norm

                sim = np.clip(np.dot(video_embedding, emb), 0.0, 1.0)
                if sim > 0.80:
                    boost = 0.05 * ((sim - 0.80) / 0.20)
                    sims[LABELS.index(corrected_label)] += boost
            except Exception:
                pass

    if float(np.max(sims)) < MIN_CONFIDENCE_SIM:
        return "video"

    probs = softmax(LOGIT_SCALE * sims)
    p_max = float(probs.max())
    order = np.argsort(-probs)
    selected = [LABELS[i] for i in order[:MAX_LABELS]
                if probs[i] >= REL_MARGIN * p_max and (probs[i] >= MIN_PROB or i == order[0])]
    return ", ".join(selected)
