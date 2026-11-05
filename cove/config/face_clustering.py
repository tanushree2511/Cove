"""Clustering thresholds for the order-stable clusterer (engines/stable_cluster.py), per face-recognition model.

Cosine-similarity scales differ between embedding models, so each model has its own thresholds. All values were
chosen on TUNING data only (30 synthetic personal libraries built from LFW under 7 image conditions; the
'library-ARI' selection rule of evaluation/exp10 / exp11) and then tested on held-out data (evaluation/exp9,
results/exp9_hard*.json). Never tuned on the test sets.
"""

FACE_CLUSTERING = {
    # buffalo_s MobileFaceNet (w600k_mbf) - evaluation/results/exp10_tuned_config.json ("v2")
    "buffalo_s": dict(link_threshold=0.50, min_neighbors=1, attach_threshold=0.35, merge_threshold=0.45),
    # EdgeFace-S (gamma 0.5) - its cosine scale is ~0.10 higher, so it was tuned on the same grid shifted by +0.10
    # (COVE_GRID_SHIFT=0.10, evaluation/results/exp11_tuned_config_edgeface_s.json), library-ARI rule ("v5").
    # Held-out: CPLFW F1 0.854 vs 0.783 for buffalo_s, CALFW 0.949 vs 0.934, degraded photos within +-0.4 points.
    "edgeface_s": dict(link_threshold=0.60, min_neighbors=1, attach_threshold=0.50, merge_threshold=0.55),
}


def clustering_config(face_model: str) -> dict:
    return dict(FACE_CLUSTERING.get(face_model, FACE_CLUSTERING["buffalo_s"]))
