"""Before/after benchmark for CPU utilisation: embed N COCO images with the project's SearchEngine and record
throughput, whole-CPU utilisation and RAM, for a given copy of the code.

    python cpu_util_bench.py <path-to-cove-dir> <label> [n_images]

Run it once for the old tree (a `git worktree` of the previous commit) and once for the current one, each in a FRESH user-data
folder so each runs its own start-up benchmark on the idle machine. Also writes the embeddings so the two can be compared.
"""
import glob
import json
import os
import shutil
import sys
import tempfile
import threading
import time

import numpy as np

cove_dir, label = os.path.abspath(sys.argv[1]), sys.argv[2]
n_images = int(sys.argv[3]) if len(sys.argv) > 3 else 160
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
work = tempfile.mkdtemp(prefix=f"cove_cpubench_{label}_")
os.environ["COVE_USER_DATA"] = work
os.environ["COVE_MODEL_DIR"] = os.path.join(ROOT, "models")
sys.path.insert(0, cove_dir)

import psutil  # noqa: E402

t0 = time.time()
from engines.search_engine import SearchEngine  # noqa: E402
from config.vision_config import CONFIG  # noqa: E402

eng = SearchEngine()
profile = CONFIG.runtime_profile
startup_s = time.time() - t0
files = sorted(glob.glob(os.path.join(ROOT, "datasets", "coco", "images5k", "*.jpg")))[:n_images]
eng.get_image_embeddings(files[:16])                              # warm-up (not timed)

proc = psutil.Process()
series, rss_peak, stop = [], [0], threading.Event()


def sampler():
    psutil.cpu_percent(interval=None)
    while not stop.is_set():
        series.append(psutil.cpu_percent(interval=0.5))
        rss_peak[0] = max(rss_peak[0], proc.memory_info().rss)


th = threading.Thread(target=sampler, daemon=True); th.start()
t = time.perf_counter()
embs = eng.get_image_embeddings(files)
elapsed = time.perf_counter() - t
stop.set(); th.join()
ok = [e for e in embs if e is not None]
np.save(os.path.join(ROOT, "evaluation", "cache", f"cpubench_{label}.npy"), np.stack(ok))
res = {"label": label, "images": len(ok), "seconds": elapsed, "images_per_second": len(ok) / elapsed,
       "cpu_percent_mean": float(np.mean(series)) if series else None, "cpu_percent_max": float(np.max(series)) if series else None,
       "peak_rss_mb": rss_peak[0] / 2**20, "profile": profile.describe() if profile else None,
       "profile_table": getattr(profile, "results", None), "startup_incl_benchmark_s": startup_s}
print("RESULT " + json.dumps(res), flush=True)
shutil.rmtree(work, ignore_errors=True)
