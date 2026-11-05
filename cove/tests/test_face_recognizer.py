import os
import types

import numpy as np
import pytest

from config.face_clustering import FACE_CLUSTERING, clustering_config
from config.vision_config import CONFIG, _resolve_face_model
from engines.face_recognizer import OnnxFaceRecognizer, install_recognizer, model_path
from engines.stable_cluster import StableIncrementalClusterer

EDGE = model_path(CONFIG.assets_dir, "edgeface_s")
needs_model = pytest.mark.skipif(not (EDGE and os.path.isfile(EDGE)), reason="EdgeFace-S model not downloaded")


def test_missing_model_falls_back_to_buffalo(tmp_path):
    assert _resolve_face_model(str(tmp_path), "edgeface_s") == "buffalo_s"
    assert _resolve_face_model(str(tmp_path), "buffalo_s") == "buffalo_s"
    assert _resolve_face_model(str(tmp_path), "no_such_model") == "buffalo_s"
    app = types.SimpleNamespace(models={"recognition": "original"})
    assert install_recognizer(app, str(tmp_path), "edgeface_s") == "buffalo_s"
    assert app.models["recognition"] == "original"


def test_clustering_config_valid_for_every_model():
    for name in FACE_CLUSTERING:
        StableIncrementalClusterer(dim=512, **clustering_config(name))
    assert clustering_config("unknown") == clustering_config("buffalo_s")


@needs_model
def test_edgeface_embeds_and_is_stable_under_flip():
    rec = OnnxFaceRecognizer(EDGE)
    rng = np.random.RandomState(0)
    crops = (rng.rand(3, 112, 112, 3) * 255).astype(np.uint8)
    E = rec.get_feat(crops)
    assert E.shape == (3, 512) and np.isfinite(E).all()
    a = rec.get_feat(crops[0])[0]
    b = rec.get_feat(crops[0][:, ::-1])[0]
    cos = a @ b / np.linalg.norm(a) / np.linalg.norm(b)
    assert cos > 0.3


@needs_model
def test_install_replaces_recognizer():
    app = types.SimpleNamespace(models={"recognition": "original"})
    assert install_recognizer(app, CONFIG.assets_dir, "edgeface_s") == "edgeface_s"
    assert isinstance(app.models["recognition"], OnnxFaceRecognizer)
