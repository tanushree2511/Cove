"""Face association in video (UCF101, 1,000 videos): how many usable faces does the face stage find, and does the redundancy filter lose any?

For every video the app's frame reader takes 14 uniform positions; the app's histogram filter keeps a subset; the face stage looks at
every KEPT frame. The faces counted are exactly the ones the app would store: detector score >= 0.35, |yaw| <= 75 degrees,
box >= 24x24 px, Laplacian blur variance >= 10 (videoModules/core/face_processor.py). Detection runs once on all 14 frames and the
two views (uniform 14, filtered) are read from the same results. UCF101 has no identity labels, so this measures coverage, not
identity accuracy.
"""
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import CACHE, DS, save_json  # noqa: E402

os.environ["COVE_USER_DATA"] = os.path.join(CACHE, "userdata")
from core.face_processor import get_face_app  # noqa: E402
from exp34_analyze import redundancy_filter  # noqa: E402

VDIR = os.path.join(DS, "ucf101", "videos1k")


def read14(path):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
    frames = []
    for i in np.linspace(0, total - 1, 14).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if ok:
            h, w = fr.shape[:2]
            if max(h, w) > 1280:
                s = 1280.0 / max(h, w); fr = cv2.resize(fr, (int(w * s), int(h * s)))
            frames.append(fr)
    cap.release()
    return frames


def usable_faces(face_app, frame):
    n = 0
    for face in face_app.get(frame) or []:
        if hasattr(face, "det_score") and face.det_score < 0.35:
            continue
        yaw = float(face.pose[1]) if getattr(face, "pose", None) is not None else None
        if yaw is not None and abs(yaw) > 75.0:
            continue
        x1, y1, x2, y2 = [max(0, int(v)) for v in face.bbox]
        if (x2 - x1) * (y2 - y1) < 576:
            continue
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        if cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var() < 10.0:
            continue
        n += 1
    return n


def main():
    meta = json.load(open(os.path.join(DS, "ucf101", "ucf101_1000.json")))
    face_app = get_face_app()
    rows = []
    t0 = time.time()
    for k, m in enumerate(meta):
        frames = read14(os.path.join(VDIR, m["video"]))
        if len(frames) < 4:
            continue
        hists = []
        for f in frames:
            h = cv2.calcHist([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)], [0], None, [256], [0, 256])
            hists.append(cv2.normalize(h, h).flatten())
        keep = redundancy_filter(np.array(hists, dtype="float32"))
        per = [usable_faces(face_app, f) for f in frames]
        rows.append({"video": m["video"], "label": m["label"], "frames": len(frames), "kept": len(keep),
                     "faces_uniform14": int(sum(per)), "faces_kept": int(sum(per[i] for i in keep)),
                     "frames_with_face_uniform14": int(sum(1 for v in per if v > 0)),
                     "frames_with_face_kept": int(sum(1 for i in keep if per[i] > 0))})
        if (k + 1) % 100 == 0:
            rate = (k + 1) / (time.time() - t0)
            print(f"{k + 1}/{len(meta)}  {rate * 60:.0f} videos/min  eta {(len(meta) - k - 1) / rate / 60:.1f} min", flush=True)
    a = np.array([[r["faces_uniform14"], r["faces_kept"], r["frames"], r["kept"], r["frames_with_face_uniform14"], r["frames_with_face_kept"]] for r in rows])
    has14, hask = a[:, 0] > 0, a[:, 1] > 0
    out = {"videos": len(rows),
           "videos_with_a_usable_face_uniform14": int(has14.sum()), "videos_with_a_usable_face_kept_frames": int(hask.sum()),
           "videos_lost_by_the_filter": int((has14 & ~hask).sum()),
           "face_detections_uniform14": int(a[:, 0].sum()), "face_detections_kept": int(a[:, 1].sum()),
           "share_of_face_detections_kept": float(a[:, 1].sum() / max(a[:, 0].sum(), 1)),
           "frames_scanned_uniform14": int(a[:, 2].sum()), "frames_scanned_kept": int(a[:, 3].sum()),
           "frames_with_face_uniform14": int(a[:, 4].sum()), "frames_with_face_kept": int(a[:, 5].sum()),
           "mean_faces_per_video_uniform14": float(a[:, 0].mean()), "mean_faces_per_video_kept": float(a[:, 1].mean()),
           "per_video": rows}
    save_json("exp34_faces.json", out)
    print({k: v for k, v in out.items() if k != "per_video"}, flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
