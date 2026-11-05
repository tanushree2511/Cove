"""Experiment 5 - system efficiency / scalability, measured on the REAL app (cove-api, uvicorn, the production indexing job).

For N in {1,000, 5,000, 10,000} photos (nested random mixes of COCO val2017 + LFW; fixed seed) in a fresh, isolated data folder:
  initial indexing time (faces + CLIP + clustering, the app's own job), peak RAM of the server process, index/disk storage,
  average end-to-end search latency (HTTP POST /search/text), FAISS throughput on the stored vectors, and the incremental-indexing
  time after adding 100 new photos.  For N=1,000 the ablation 'no incremental indexing' (wipe the indexes and re-index everything,
  which is what a non-incremental system must do) is measured too.

   python exp5_scale.py 1000 [5000 10000]          (run on an otherwise idle machine - it measures time and RAM)
"""
import glob
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

import numpy as np
import psutil

sys.path.insert(0, os.path.dirname(__file__))
from common import DS, ROOT, RESULTS, save_json  # noqa: E402

PORT = 18000
BASE = f"http://127.0.0.1:{PORT}"
PY = sys.executable


def http(path, body=None, timeout=120):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST" if body is not None or path == "/index/start" else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def library_order():
    coco = sorted(glob.glob(os.path.join(DS, "coco", "images5k", "*.jpg")))
    lfw = sorted(glob.glob(os.path.join(DS, "lfw", "lfw_funneled", "*", "*.jpg")))
    rng = random.Random(0)
    lfw = rng.sample(lfw, 5000)
    allp = coco + lfw
    rng.shuffle(allp)
    return allp


class Server:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.proc = None
        self.peak = 0
        self._stop = threading.Event()

    def start(self):
        env = dict(os.environ, COVE_AUTOTUNE="0", COVE_USER_DATA=self.data_dir, COVE_MODEL_DIR=os.path.join(ROOT, "models"), COVE_PORT=str(PORT))
        hp = os.path.join(os.environ["APPDATA"], "Cove", "hardware_profile.json")
        if os.path.exists(hp):
            shutil.copy2(hp, self.data_dir)                      # same measured hardware profile as the app (no first-run benchmark)
        t0 = time.time()
        self.proc = subprocess.Popen([PY, "-m", "uvicorn", "api.server:app", "--host", "127.0.0.1", "--port", str(PORT)],
                                     cwd=os.path.join(ROOT, "cove"), env=env, stdout=open(os.path.join(self.data_dir, "server.out"), "w"),
                                     stderr=subprocess.STDOUT)
        for _ in range(600):
            try:
                if http("/health", timeout=3).get("status") == "ok":
                    break
            except Exception:
                time.sleep(1)
        self.startup_s = time.time() - t0
        self._stop.clear()
        self.peak = 0
        self.ps = psutil.Process(self.proc.pid)
        threading.Thread(target=self._sample, daemon=True).start()

    def _sample(self):
        while not self._stop.is_set():
            try:
                rss = self.ps.memory_info().rss + sum(c.memory_info().rss for c in self.ps.children(recursive=True))
                self.peak = max(self.peak, rss)
            except Exception:
                pass
            time.sleep(0.1)

    def reset_peak(self):
        self.peak = 0

    def stop(self):
        self._stop.set()
        try:
            for c in self.ps.children(recursive=True):
                c.kill()
            self.proc.kill()
        except Exception:
            pass
        time.sleep(2)


def index_and_wait(poll=2.0, limit=4 * 3600):
    http("/index/start", body={})
    t0 = time.time()
    time.sleep(1.0)
    while time.time() - t0 < limit:
        st = http("/index/status")
        if st["status"] in ("completed", "error"):
            return time.time() - t0, st
        time.sleep(poll)
    raise TimeoutError


def dir_size(path, skip=()):
    total = 0
    for dp, dn, fn in os.walk(path):
        dn[:] = [d for d in dn if os.path.join(dp, d) not in skip]
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total


def faiss_bench(data_dir):
    import faiss
    v = np.load(os.path.join(data_dir, "image_vectors.npy")).astype("float32")
    idx = faiss.IndexFlatIP(v.shape[1]); idx.add(v)
    rng = np.random.RandomState(0)
    q = v[rng.randint(0, len(v), 2000)]
    t = time.perf_counter()
    for i in range(1000):
        idx.search(q[i:i + 1], 10)
    single = 1000 / (time.perf_counter() - t)
    t = time.perf_counter(); idx.search(q[:1024], 10); batch = 1024 / (time.perf_counter() - t)
    t = time.perf_counter(); idx.search(q[:1], 10); one_ms = (time.perf_counter() - t) * 1000
    return {"vectors": int(len(v)), "single_query_qps": single, "batch1024_qps": batch, "single_query_ms": 1000.0 / single}


def search_latency(queries):
    http("/search/text", body={"text": "warm up", "limit": 40})
    ts = []
    for q in queries:
        t = time.perf_counter(); r = http("/search/text", body={"text": q, "limit": 40}); ts.append((time.perf_counter() - t) * 1000)
    return {"n": len(ts), "mean_ms": statistics.mean(ts), "median_ms": statistics.median(ts), "p95_ms": float(np.percentile(ts, 95))}


def captions(n=100):
    d = json.load(open(os.path.join(DS, "coco", "annotations", "captions_val2017.json"), encoding="utf8"))
    rng = random.Random(3)
    a = rng.sample(d["annotations"], n)
    return [x["caption"].strip() for x in a]


def run_size(n, order, ablation_full_reindex=False):
    work = tempfile.mkdtemp(prefix=f"cove_scale_{n}_")
    photos = os.path.join(work, "test_images"); os.makedirs(photos)
    print(f"\n=== N={n}  data dir {work}", flush=True)
    t0 = time.time()
    for p in order[:n]:
        shutil.copy2(p, os.path.join(photos, os.path.basename(p) if not os.path.exists(os.path.join(photos, os.path.basename(p))) else
                                     os.path.basename(os.path.dirname(p)) + "_" + os.path.basename(p)))
    print(f"copied {n} photos in {time.time() - t0:.0f}s", flush=True)
    photo_bytes = dir_size(photos)
    s = Server(work); s.start()
    res = {"items": n, "server_startup_s": s.startup_s, "photo_bytes": photo_bytes}
    try:
        base_rss = s.peak
        s.reset_peak()
        sec, st = index_and_wait()
        h = http("/health")
        res.update({"initial_index_s": sec, "initial_index_status": st["status"], "faces_indexed": h["indexes"]["faces"],
                    "clip_indexed": h["indexes"]["semantic"], "peak_rss_mb_initial_indexing": s.peak / 2**20,
                    "idle_rss_mb_after_startup": base_rss / 2**20, "items_per_second": n / sec})
        print(f"initial indexing {sec:.0f}s ({n / sec:.2f} items/s) faces={h['indexes']['faces']} clip={h['indexes']['semantic']} peakRAM={s.peak / 2**20:.0f}MB", flush=True)
        res["index_storage_bytes"] = dir_size(work, skip=(photos,)) - os.path.getsize(os.path.join(work, "server.out")) if os.path.exists(os.path.join(work, "server.out")) else 0
        s.reset_peak()
        res["search"] = search_latency(captions(100))
        res["search_peak_rss_mb"] = s.peak / 2**20
        print("search:", res["search"], flush=True)
        res["faiss"] = faiss_bench(work); print("faiss:", res["faiss"], flush=True)
        # no-op pass (nothing new) - what an idle "Start Indexing" costs
        noop, _ = index_and_wait(poll=0.2); res["noop_pass_s"] = noop
        # incremental: 100 NEW photos
        extra = order[n:n + 100]
        for p in extra:
            shutil.copy2(p, os.path.join(photos, os.path.basename(p) if not os.path.exists(os.path.join(photos, os.path.basename(p))) else
                                         os.path.basename(os.path.dirname(p)) + "_" + os.path.basename(p)))
        s.reset_peak()
        inc, st2 = index_and_wait()
        h2 = http("/health")
        res.update({"incremental_100_s": inc, "incremental_peak_rss_mb": s.peak / 2**20, "after_incremental_clip": h2["indexes"]["semantic"]})
        print(f"incremental +100: {inc:.1f}s  (clip index {h['indexes']['semantic']} -> {h2['indexes']['semantic']})", flush=True)
        if ablation_full_reindex:
            s.stop()
            for f in ("faiss_index.bin", "faiss_index.bin.paths", "faiss_search_index.bin", "faiss_search_index.bin.paths", "faiss_search_index.bin.model",
                      "image_vectors.npy", "embeddings.npy", "paths.json", "people_db.json", "no_face_cache.json"):
                fp = os.path.join(work, f)
                if os.path.exists(fp):
                    os.remove(fp)
            s.start(); s.reset_peak()
            full, st3 = index_and_wait()
            res.update({"full_reindex_n_plus_100_s": full, "full_reindex_peak_rss_mb": s.peak / 2**20})
            print(f"WITHOUT incremental (wipe + re-index {n + 100}): {full:.0f}s", flush=True)
    finally:
        s.stop()
        try:
            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
    return res


if __name__ == "__main__":
    sizes = [int(x) for x in sys.argv[1:]] or [1000]
    order = library_order()
    print("candidate pool:", len(order), flush=True)
    out_path = os.path.join(RESULTS, "exp5_scale.json")
    out = json.load(open(out_path)) if os.path.exists(out_path) else {"runs": {}}
    for n in sizes:
        out["runs"][str(n)] = run_size(n, order, ablation_full_reindex=(n == 1000))
        save_json("exp5_scale.json", out)
    print("DONE", flush=True)
