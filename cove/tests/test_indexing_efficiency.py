import contextlib
import types

import cv2
import numpy as np
import pytest

from api import server


class _Pool:
    def __init__(self):
        self.calls = 0

    @contextlib.contextmanager
    def borrow(self):
        pool = self

        class _Engine:
            def get_faces(self, img):
                pool.calls += 1
                return []   # every photo is faceless

        yield _Engine()


@pytest.fixture
def library(tmp_path, monkeypatch):
    photos = tmp_path / "test_images"
    photos.mkdir()
    for name in ("a.jpg", "b.jpg"):
        cv2.imwrite(str(photos / name), np.zeros((8, 8, 3), dtype="uint8"))
    pool = _Pool()
    monkeypatch.setattr(server, "TEST_IMAGES_DIR", str(photos))
    monkeypatch.setattr(server, "NO_FACE_CACHE_FILE", str(tmp_path / "no_face_cache.json"))
    monkeypatch.setattr(server, "_resolve_photo_path", lambda p: str(photos / p.split("/", 1)[1]))
    monkeypatch.setattr(server, "ai_pool", pool)
    monkeypatch.setattr(server, "storage", types.SimpleNamespace(paths=[]))
    monkeypatch.setattr(server, "search_storage", types.SimpleNamespace(paths=[]))
    return photos, pool


def test_faceless_photos_are_detected_once(library):
    _, pool = library
    assert server._run_face_detection_stage() == 0
    assert pool.calls == 2
    assert server._run_face_detection_stage() == 0
    assert pool.calls == 2   # second pass skipped both cached faceless photos


def test_replaced_faceless_photo_is_rescanned(library):
    photos, pool = library
    server._run_face_detection_stage()
    cv2.imwrite(str(photos / "a.jpg"), np.random.default_rng(0).integers(0, 255, (96, 96, 3), dtype="uint8"))   # clearly different size
    server._run_face_detection_stage()
    assert pool.calls == 3


def test_upgrade_seeds_cache_from_semantic_index(library):
    photos, pool = library
    # an install that predates the cache: both photos are already semantically indexed, neither has a face entry
    server.search_storage.paths = ["test_images/a.jpg", "test_images/b.jpg"]
    assert server._run_face_detection_stage() == 0
    assert pool.calls == 0   # nothing re-scanned on the first run after upgrading
