"""Experiment 3 (efficiency half): real per-video processing time and peak RAM of every frame-sampling strategy.

Uses the app's own code paths: video_processor.extract_frames (seek-based reader + histogram filter), embedder.encode_images_batch
(CLIP ViT-B/16), face_processor.get_face_app().get (the face stage runs on every kept frame). Each strategy runs in a FRESH process
(so peak RAM is that strategy's own), on the same fixed random sample of videos, after one untimed warm-up video.

   python exp3_timing.py driver [n_videos]      run all strategies, write results/exp3_timing.json
   python exp3_timing.py child <strategy> <n>   (internal)
"""
import json
import os
import subprocess
import sys
import threading
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, RESULTS, save_json  # noqa: E402

STRATEGIES = ["Uniform 4 frames", "Uniform 8 frames", "Uniform 14 frames", "Uniform 20 frames", "Dense reference (25 frames)",
              "Middle frame only (1)", "Ours: 14 pos + redundancy filter", "Ours deployed (filter + adaptive CLIP frames)"]
VDIR = os.path.join(DS, "ucf101", "videos1k")


def sample_videos(n):
    meta = json.load(open(os.path.join(DS, "ucf101", "ucf101_1000.json")))
    rng = np.random.RandomState(7)
    pick = rng.permutation(len(meta))[:n + 1]                      # +1: the warm-up video
    return [os.path.join(VDIR, meta[i]["video"]) for i in pick]


def child(strategy, n):
    os.environ["COVE_AUTOTUNE"] = "0"          # deterministic: the heuristic choice (cpu-4t) = the profile measured on an idle machine
    os.environ["COVE_USER_DATA"] = os.path.join(CACHE, "userdata_timing")
    os.makedirs(os.environ["COVE_USER_DATA"], exist_ok=True)
    hp = os.path.join(os.environ.get("APPDATA", ""), "Cove", "hardware_profile.json")
    if os.path.exists(hp):
        import shutil
        shutil.copy2(hp, os.environ["COVE_USER_DATA"])
    import cv2
    import psutil
    from core.video_processor import extract_frames, pick_evenly, video_duration
    from core.embedder import encode_images_batch, _get_engine
    from core.face_processor import get_face_app
    from config.vision_config import CONFIG

    profile = CONFIG.runtime_profile
    _get_engine(); face_app = get_face_app()
    proc = psutil.Process()
    base_rss = proc.memory_info().rss
    peak = {"v": base_rss}
    stop = threading.Event()

    def sampler():
        while not stop.is_set():
            r = proc.memory_info().rss
            peak["v"] = max(peak["v"], r)
            time.sleep(0.02)

    th = threading.Thread(target=sampler, daemon=True); th.start()

    def uniform_frames(path, count):
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
        out = []
        for i in np.linspace(0, total - 1, count).astype(int):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
            ok, fr = cap.read()
            if ok:
                h, w = fr.shape[:2]
                if max(h, w) > 1280:
                    s = 1280.0 / max(h, w); fr = cv2.resize(fr, (int(w * s), int(h * s)))
                out.append(fr)
        cap.release()
        return out

    def middle_frame(path):
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
        cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
        ok, fr = cap.read(); cap.release()
        return [fr] if ok else []

    def run(path):
        t0 = time.perf_counter()
        if strategy.startswith("Uniform"):
            frames = uniform_frames(path, int(strategy.split()[1])); clip_frames = frames
        elif strategy.startswith("Dense"):
            frames = uniform_frames(path, 25); clip_frames = frames
        elif strategy.startswith("Middle"):
            frames = middle_frame(path); clip_frames = frames
        elif strategy.startswith("Ours deployed"):
            frames = extract_frames(path)                                   # 14 positions + redundancy filter
            n_clip = profile.frames_for_video(video_duration(path)) if profile else len(frames)
            clip_frames = pick_evenly(frames, n_clip)
        else:                                                              # Ours: all kept frames to CLIP
            frames = extract_frames(path); clip_frames = frames
        t1 = time.perf_counter()
        emb = encode_images_batch(clip_frames)
        t2 = time.perf_counter()
        for fr in frames:                                                   # the face stage looks at every kept frame
            face_app.get(fr)
        t3 = time.perf_counter()
        return {"extract_s": t1 - t0, "clip_s": t2 - t1, "face_s": t3 - t2, "total_s": t3 - t0,
                "frames_extracted": len(frames), "frames_clip": len(clip_frames)}

    paths = sample_videos(n)
    run(paths[0])                                                           # warm-up (kernel init, caches)
    peak["v"] = proc.memory_info().rss
    rows = [run(p) for p in paths[1:]]
    stop.set()
    agg = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
    agg.update({"strategy": strategy, "videos": len(rows), "peak_rss_mb": peak["v"] / 2**20, "baseline_rss_mb_after_model_load": base_rss / 2**20,
                "total_s_median": float(np.median([r["total_s"] for r in rows])), "total_s_std": float(np.std([r["total_s"] for r in rows]))})
    print("RESULT " + json.dumps(agg), flush=True)


def driver(n):
    results = []
    for s in STRATEGIES:
        print("running", s, flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "child", s, str(n)], capture_output=True, text=True)
        line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
        if not line:
            print("FAILED", s, p.stderr[-600:], flush=True); continue
        r = json.loads(line[0][7:]); results.append(r)
        print(f"  {s:<48} total={r['total_s']:.2f}s (extract {r['extract_s']:.2f} clip {r['clip_s']:.2f} face {r['face_s']:.2f}) "
              f"peakRAM={r['peak_rss_mb']:.0f}MB frames={r['frames_extracted']:.1f}/{r['frames_clip']:.1f}", flush=True)
    save_json("exp3_timing.json", {"videos_per_strategy": n, "results": results})
    print("DONE", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "child":
        child(sys.argv[2], int(sys.argv[3]))
    else:
        driver(int(sys.argv[2]) if len(sys.argv) > 2 else 30)
