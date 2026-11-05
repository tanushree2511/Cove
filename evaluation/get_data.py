"""Fetch the evaluation data that is not already on disk (idempotent, resumable).

  * MS COCO val2017: all 5,000 images (the fixed 5,000-image evaluation set) -> datasets/coco/images5k
  * UCF101: a fixed 1,000-video stratified subset of official test split 1 -> datasets/ucf101/videos1k
"""
import json, os, random, shutil, sys, time, urllib.request, concurrent.futures as cf

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DS = os.path.join(ROOT, "datasets")


def coco():
    caps = json.load(open(os.path.join(DS, "coco", "annotations", "captions_val2017.json"), encoding="utf8"))
    imgs = sorted(caps["images"], key=lambda i: i["id"])
    assert len(imgs) == 5000, len(imgs)
    out = os.path.join(DS, "coco", "images5k"); os.makedirs(out, exist_ok=True)
    have1k = os.path.join(DS, "coco", "images1k")

    def get(i):
        dst = os.path.join(out, i["file_name"])
        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
            return 1
        src = os.path.join(have1k, i["file_name"])
        if os.path.exists(src) and os.path.getsize(src) > 1000:
            shutil.copy2(src, dst); return 1
        for _ in range(6):
            try:
                urllib.request.urlretrieve("http://images.cocodataset.org/val2017/" + i["file_name"], dst)
                if os.path.getsize(dst) > 1000:
                    return 1
            except Exception:
                time.sleep(1)
        return 0

    n = 0
    with cf.ThreadPoolExecutor(8) as ex:
        for ok in ex.map(get, imgs):
            n += ok
            if n % 250 == 0: print("coco", n, flush=True)
    print("COCO DONE", n, "of", len(imgs), flush=True)


def ucf():
    from remotezip import RemoteZip
    out = os.path.join(DS, "ucf101", "videos1k"); os.makedirs(out, exist_ok=True)
    meta_path = os.path.join(DS, "ucf101", "ucf101_1000.json")
    B = "https://huggingface.co/datasets/quchenyuan/UCF101-ZIP/resolve/main/"
    test_list = [l.strip().split()[0] for l in open(os.path.join(DS, "ucf101", "splits", "ucfTrainTestlist", "testlist01.txt")) if l.strip()]
    by_class = {}
    for rel in test_list:                       # e.g. ApplyEyeMakeup/v_ApplyEyeMakeup_g01_c01.avi
        by_class.setdefault(rel.split("/")[0], []).append(rel)
    classes = sorted(by_class)
    assert len(classes) == 101
    rng = random.Random(0)
    order = classes[:]; rng.shuffle(order)
    take = {c: 10 for c in order[:99]}; take.update({c: 5 for c in order[99:]})     # 99*10 + 2*5 = 1,000
    chosen = []
    for c in classes:
        vids = sorted(by_class[c]); rng.shuffle(vids)
        chosen += [{"video": os.path.basename(v).replace("\\", "/"), "label": c, "zip_rel": v} for v in sorted(vids[:take[c]])]
    assert len(chosen) == 1000, len(chosen)
    json.dump([{"video": m["video"], "label": m["label"]} for m in chosen], open(meta_path, "w"), indent=1)
    todo = [m for m in chosen if not (os.path.exists(os.path.join(out, m["video"])) and os.path.getsize(os.path.join(out, m["video"])) > 1000)]
    print("ucf to fetch:", len(todo), flush=True)
    def worker(chunk):
        for attempt in range(30):
            try:
                with RemoteZip(B + "UCF-101.zip") as z:
                    bybase = {os.path.basename(n): n for n in z.namelist() if n.lower().endswith(".avi")}
                    for m in chunk:
                        dst = os.path.join(out, m["video"])
                        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
                            continue
                        with z.open(bybase[m["video"]]) as s_, open(dst + ".part", "wb") as o:
                            shutil.copyfileobj(s_, o)
                        os.replace(dst + ".part", dst)
                return
            except Exception as e:
                print("retry", attempt, repr(e)[:120], flush=True); time.sleep(5)

    workers = 8
    chunks = [todo[i::workers] for i in range(workers)]
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(worker, c) for c in chunks]
        while not all(f.done() for f in futs):
            time.sleep(15)
            print("ucf", sum(1 for m in chosen if os.path.exists(os.path.join(out, m["video"]))), flush=True)
    n = sum(1 for m in chosen if os.path.exists(os.path.join(out, m["video"])))
    print("UCF DONE", n, "of 1000", flush=True)


if __name__ == "__main__":
    what = sys.argv[1:] or ["coco", "ucf"]
    if "coco" in what: coco()
    if "ucf" in what: ucf()
