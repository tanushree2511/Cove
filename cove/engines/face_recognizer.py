"""Pluggable face-recognition (embedding) models.

InsightFace's FaceAnalysis runs `model.get(img, face)` for every non-detection model, so any object with the same
small interface can replace the bundled recogniser (buffalo_s MobileFaceNet, w600k_mbf). The detector (SCRFD) and the
standard 5-point ArcFace alignment to 112x112 stay exactly the same.

EdgeFace-S (gamma 0.5) - George, Ecabert, Otroshi Shahreza, Kotwal, Marcel, "EdgeFace: Efficient Face Recognition Model
for Edge Devices", IEEE T-BIOM 2024. Weights: Idiap Research Institute, CC BY-NC-SA 4.0 (non-commercial use).
Measured in this project (evaluation/exp13_*): about 2x faster than w600k_mbf on CPU, equal or better accuracy on
cross-age (CALFW, AgeDB-30) and cross-pose (CPLFW, CFP-FP) face pairs.
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

import numpy as np

# name -> (file name, download URL). The ONNX export is identical (cosine 0.9999998) to exporting the official
# PyTorch checkpoint ourselves (evaluation/convert_face_models.py).
FACE_MODELS = {
    "edgeface_s": ("edgeface_s_gamma_05.onnx",
                   "https://github.com/yakhyo/edgeface-onnx/releases/download/weights/edgeface_s_gamma_05.onnx"),
}
EDGEFACE_DIR = "edgeface"


def model_path(assets_dir: str, name: str) -> Optional[str]:
    if name not in FACE_MODELS:
        return None
    return os.path.join(assets_dir, EDGEFACE_DIR, FACE_MODELS[name][0])


class OnnxFaceRecognizer:
    """Drop-in replacement for insightface.model_zoo.ArcFaceONNX (RGB, (x - 127.5) / 127.5, NCHW, 112x112)."""

    taskname = "recognition"

    def __init__(self, model_file: str, providers: Optional[Iterable[str]] = None, session=None):
        import onnxruntime as ort

        self.model_file = model_file
        self.input_size = (112, 112)
        self.input_mean = 127.5
        self.input_std = 127.5
        self.session = session or ort.InferenceSession(model_file, providers=list(providers or ["CPUExecutionProvider"]))

    @property
    def input_name(self) -> str:
        return self.session.get_inputs()[0].name

    def prepare(self, ctx_id: int = 0, **kwargs) -> None:   # FaceAnalysis.prepare() calls this on every model
        return None

    def _blob(self, crops_bgr: np.ndarray) -> np.ndarray:
        x = (crops_bgr[..., ::-1].astype(np.float32) - self.input_mean) / self.input_std
        return np.ascontiguousarray(x.transpose(0, 3, 1, 2))

    def get_feat(self, crops_bgr) -> np.ndarray:
        """Embeddings for aligned 112x112 BGR face crops (one image or a batch)."""
        crops = np.asarray(crops_bgr)
        if crops.ndim == 3:
            crops = crops[None]
        return self.session.run(None, {self.input_name: self._blob(crops)})[0].reshape(len(crops), -1)

    def get(self, img: np.ndarray, face) -> np.ndarray:
        from insightface.utils import face_align

        crop = face_align.norm_crop(img, landmark=face.kps, image_size=self.input_size[0])
        face.embedding = self.get_feat(crop).flatten()
        return face.embedding


def install_recognizer(face_app, assets_dir: str, name: str, providers=None, logger=None) -> str:
    """Swap FaceAnalysis' recogniser for `name` if its model file exists. Returns the model actually in use
    ('buffalo_s' when falling back), so the caller can keep embeddings from different models apart."""
    if not name or name == "buffalo_s":
        return "buffalo_s"
    path = model_path(assets_dir, name)
    if not path or not os.path.isfile(path):
        if logger:
            logger.warning("Face model %s not found at %s - using buffalo_s (run pipeline/download_models.py)", name, path)
        return "buffalo_s"
    try:
        face_app.models["recognition"] = OnnxFaceRecognizer(path, providers)
        return name
    except Exception as exc:                                   # broken file / unsupported runtime -> keep working
        if logger:
            logger.warning("Could not load face model %s (%s) - using buffalo_s", name, exc)
        return "buffalo_s"
