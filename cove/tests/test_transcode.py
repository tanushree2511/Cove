import importlib.util
import os

import cv2
import numpy as np
import pytest

_SPEC = importlib.util.spec_from_file_location(
    "cove_transcode", os.path.join(os.path.dirname(__file__), "..", "..", "videoModules", "core", "transcode.py"))
transcode = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(transcode)

pytestmark = pytest.mark.skipif(transcode.ffmpeg_exe() is None, reason="ffmpeg not available")


def _write_avi(path, fourcc="MJPG"):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*fourcc), 10, (64, 48))
    if not writer.isOpened():
        pytest.skip(f"OpenCV cannot write {fourcc} here")
    for i in range(20):
        writer.write(np.full((48, 64, 3), i * 10, dtype="uint8"))
    writer.release()


def test_avi_is_not_playable_and_gets_converted(tmp_path):
    src = tmp_path / "clip.avi"
    _write_avi(src)
    assert not transcode.is_browser_playable(str(src))

    out = transcode.ensure_playable(str(src))

    assert out.endswith(".mp4") and os.path.exists(out)
    assert not src.exists()                       # converted in place: the unplayable original is gone
    assert transcode.is_browser_playable(out)
    info = transcode.probe(out)
    assert info["video"] == "h264" and info["pix_fmt"] in ("yuv420p", "yuvj420p")


def test_already_playable_file_is_left_alone(tmp_path):
    src = tmp_path / "clip.avi"
    _write_avi(src)
    mp4 = transcode.ensure_playable(str(src))
    before = os.stat(mp4).st_mtime_ns
    assert transcode.ensure_playable(mp4) == mp4
    assert os.stat(mp4).st_mtime_ns == before


def test_conversion_does_not_overwrite_an_unrelated_mp4(tmp_path):
    other = tmp_path / "clip.avi"
    _write_avi(other)
    existing = transcode.ensure_playable(str(other))          # -> clip.mp4
    clash = tmp_path / "clip.avi"
    _write_avi(clash)                                         # a different file with the same base name
    size_before = os.path.getsize(existing)

    out = transcode.ensure_playable(str(clash))

    assert out.endswith("clip_converted.mp4")
    assert os.path.getsize(existing) == size_before


def test_failed_conversion_keeps_the_original(tmp_path):
    bad = tmp_path / "broken.avi"
    bad.write_bytes(b"not a video")
    assert transcode.ensure_playable(str(bad)) == str(bad)
    assert bad.exists()
    assert not list(tmp_path.glob(".convert_*"))              # no temp files left behind
