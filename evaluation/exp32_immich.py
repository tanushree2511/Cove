"""Experiment 32 - what does Immich (self-hosted photo manager, default face grouping) score on the same LFW test libraries?

Three of our 30 identity-disjoint test libraries (the smallest: indices 12, 6, 1; 543, 585, 642 photos, clean condition) are uploaded to a
local Immich server (one user per library, so each is clustered separately, as in our protocol). After Immich's face detection, recognition and
clustering jobs finish, every photo is mapped to the Immich "person" of its faces. A photo may hold several faces (LFW crops have background
faces); we score the photo-level assignment of the face that sits at the image centre (largest bounding box nearest the centre), which is
the labelled LFW face. Photos without a detected face are counted as misses and excluded from F1 (their number is reported).
We report B-Cubed F1 against the identity labels, next to our clusterer (EdgeFace-S, shipped setting) on exactly the same photos.
Nothing is tuned; Immich runs with its default settings (no rename, no merges, no corrections).
Run: python evaluation/exp32_immich.py  (Immich on http://localhost:2283, see D:/wincode/immich_run)
"""
import json
import mimetypes
import os
import sys
import time
import urllib.request
import uuid

os.environ["COVE_FACE_MODEL"] = "edgeface_s"
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import exp14_disjoint as D  # noqa: E402
import exp24_cavg_timing as T  # noqa: E402
from common import save_json  # noqa: E402
from exp20_exact_read import build  # noqa: E402

BASE = "http://localhost:2283/api"
LFW = os.path.join(os.path.dirname(__file__), "..", "datasets", "lfw", "lfw_funneled")
LIBS = [12, 6, 1]


def call(method, path, body=None, key=None, raw=None, ctype=None):
    h = {"Accept": "application/json"}
    if key:
        h["x-api-key"] = key
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if ctype:
        h["Content-Type"] = ctype
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        t = r.read()
        return json.loads(t) if t else {}


def multipart(fields, fname, content):
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{b}\r\nContent-Disposition: form-data; name="assetData"; filename="{fname}"\r\n'
            f'Content-Type: application/octet-stream\r\n\r\n').encode() + content + f"\r\n--{b}--\r\n".encode()
    return out, f"multipart/form-data; boundary={b}"


def bcubed(pred, true):
    pred, true = np.asarray(pred), np.asarray(true)
    P, R = [], []
    for i in range(len(pred)):
        same_c = pred == pred[i]
        same_t = true == true[i]
        both = (same_c & same_t).sum()
        P.append(both / same_c.sum())
        R.append(both / same_t.sum())
    p, r = float(np.mean(P)), float(np.mean(R))
    return 2 * p * r / (p + r), p, r


def make_user(i, admin_key):
    email = f"lib{i}@example.test"
    try:
        call("POST", "/admin/users", {"email": email, "password": "pass12345", "name": f"lib{i}"}, key=admin_key)
    except Exception as e:
        print("user exists:", e)
    tok = call("POST", "/auth/login", {"email": email, "password": "pass12345"})["accessToken"]
    r = urllib.request.Request(BASE + "/api-keys", data=json.dumps({"name": "x", "permissions": ["all"]}).encode(),
                               headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(r, timeout=60).read())["secret"]


def main():
    paths, X, N = D.load_set("lfw_clean")
    by, half = D.split_identities(paths)
    libs = D.make_libs(by, *half["test"], seed=0)
    pos = {p: i for i, p in enumerate(paths)}
    # admin
    try:
        call("POST", "/auth/admin-sign-up", {"email": "admin@example.test", "password": "pass12345", "name": "admin"})
    except Exception as e:  # already exists
        print("admin sign-up:", e)
    tok = call("POST", "/auth/login", {"email": "admin@example.test", "password": "pass12345"})["accessToken"]
    r = urllib.request.Request(BASE + "/api-keys", data=json.dumps({"name": "adm", "permissions": ["all"]}).encode(),
                               headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, method="POST")
    admin_key = json.loads(urllib.request.urlopen(r, timeout=60).read())["secret"]
    rows = []
    for n, li in enumerate(LIBS):
        files = [str(f) for f in libs[li]]
        key = make_user(n, admin_key)
        ids = {}
        for k, f in enumerate(files):
            with open(os.path.join(LFW, f), "rb") as fh:
                content = fh.read()
            mt = str(int(os.path.getmtime(os.path.join(LFW, f))))
            body, ct = multipart({"deviceAssetId": f"{li}-{k}", "deviceId": "exp32", "fileCreatedAt": "2020-01-01T00:00:00.000Z",
                                  "fileModifiedAt": "2020-01-01T00:00:00.000Z"}, f.replace("/", "_"), content)
            res = call("POST", "/assets", key=key, raw=body, ctype=ct)
            ids[res["id"]] = f
        print(f"library {li}: uploaded {len(ids)}", flush=True)
        try:
            call("PUT", "/jobs/faceDetection", {"command": "start", "force": False}, key=admin_key)
        except Exception as e:
            print("job start skipped:", e)
        time.sleep(5)
        # wait for queues
        t0 = time.time()
        while True:
            q = call("GET", "/jobs", key=admin_key)
            busy = sum(v["jobCounts"]["active"] + v["jobCounts"]["waiting"] for v in q.values())
            if busy == 0:
                break
            if int(time.time() - t0) % 60 == 0:
                print("  jobs busy", busy, flush=True)
            time.sleep(5)
        time.sleep(10)
        # collect people per asset
        pred, true, missed, scored_files = [], [], 0, []
        for aid, f in ids.items():
            fcs = call("GET", f"/faces?id={aid}", key=key)
            best = None
            for fc in fcs:   # the labelled LFW face is the one nearest the centre, whether or not Immich gave it a person
                w = fc["boundingBoxX2"] - fc["boundingBoxX1"]
                h = fc["boundingBoxY2"] - fc["boundingBoxY1"]
                cx = (fc["boundingBoxX1"] + fc["boundingBoxX2"]) / 2 / max(fc["imageWidth"], 1)
                cy = (fc["boundingBoxY1"] + fc["boundingBoxY2"]) / 2 / max(fc["imageHeight"], 1)
                score = (w * h) / max(fc["imageWidth"] * fc["imageHeight"], 1) - 2 * ((cx - .5) ** 2 + (cy - .5) ** 2)
                if best is None or score > best[0]:
                    best = (score, fc["person"]["id"] if fc.get("person") else None)
            if best is not None and best[1] is None:
                best = None
            if best is None:
                missed += 1
                continue
            pred.append(best[1])
            scored_files.append(f)
            true.append(f.split("/")[0])
        from collections import Counter
        cnt = Counter(f.split('/')[0] for f in files)
        unassigned = [f for f in files if f not in set(scored_files)]
        singleton_unassigned = sum(1 for f in unassigned if cnt[f.split('/')[0]] == 1)
        f1, pr, rc = bcubed(pred, true)
        # ours on the same photos
        keep = [pos[f] for f in files if f in pos]
        c = build(X[keep], N[keep], T.P, True)
        lab = c.labels()
        yy = [files[j].split("/")[0] for j in range(len(files))]
        o_f1, o_p, o_r = bcubed(lab, yy)
        idx = [files.index(f) for f in scored_files]
        s_f1, s_p, s_r = bcubed(np.asarray(lab)[idx], [yy[j] for j in idx])
        rows.append({"library": li, "photos": len(files), "scored": len(pred), "no_person_assigned": missed, "unassigned_one_photo_identities": singleton_unassigned, "immich_version": call("GET", "/server/version", key=key),
                     "immich_people": len(set(pred)), "true_people": len(set(true)),
                     "immich": {"F1": f1, "P": pr, "R": rc}, "ours_all_photos": {"F1": o_f1, "P": o_p, "R": o_r}, "ours_same_photos_as_immich": {"F1": s_f1, "P": s_p, "R": s_r}})
        print(rows[-1], flush=True)
    save_json("exp32_immich_edgeface_s.json", {"protocol": __doc__, "rows": rows,
              "mean_immich_F1": float(np.mean([r["immich"]["F1"] for r in rows])),
              "mean_ours_F1": float(np.mean([r["ours_all_photos"]["F1"] for r in rows])), "mean_ours_same_photos_F1": float(np.mean([r["ours_same_photos_as_immich"]["F1"] for r in rows]))})


if __name__ == "__main__":
    main()
