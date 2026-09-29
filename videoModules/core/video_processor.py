import cv2
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor

def extract_frames(video_path, fast_mode=True):
    """
    Extracts representative frames from a video maintaining temporal story flow.
    fast_mode=True: Samples 14 frames evenly across timeline, downscales for speed, and filters out static duplicates using color histograms.
    """
    cap = cv2.VideoCapture(video_path)
    frames = []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0: total_frames = 60

    if fast_mode:
        # Sample 14 frames uniformly across video duration to preserve full story flow
        num_samples = 14
        indices = np.linspace(0, total_frames - 1, num_samples).astype(int)
        raw_frames = []

        for i in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                # Downscale while preserving aspect ratio for fast CLIP embedding and face detection
                h, w = frame.shape[:2]
                max_dim = max(w, h)
                if max_dim > 1280:
                    scale = 1280.0 / max_dim
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                raw_frames.append(frame)

        # Fallback to sequential read if seeking yielded too few frames (e.g. truncated file or bad container index)
        if len(raw_frames) < 4:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            seq_frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                h, w = frame.shape[:2]
                max_dim = max(w, h)
                if max_dim > 1280:
                    scale = 1280.0 / max_dim
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                seq_frames.append(frame)
            if len(seq_frames) > 0:
                if len(seq_frames) > num_samples:
                    sub_idx = np.linspace(0, len(seq_frames) - 1, num_samples).astype(int)
                    raw_frames = [seq_frames[idx] for idx in sub_idx]
                else:
                    raw_frames = seq_frames

        # Filter near-duplicate consecutive frames to speed up while keeping narrative progression
        if len(raw_frames) > 4:
            hists = []
            for f in raw_frames:
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                hists.append(hist)

            selected_indices = [0]  # Start anchor frame
            for i in range(1, len(raw_frames)):
                # Compare histogram with the previous selected frame to avoid repetitive static shots
                last_selected = selected_indices[-1]
                corr = cv2.compareHist(hists[i], hists[last_selected], cv2.HISTCMP_CORREL)
                if corr < 0.95:  # Distinct scene/motion threshold
                    selected_indices.append(i)

            # Ensure at least 4 keyframes are retained across story timeline
            if len(selected_indices) < 4:
                remaining = [x for x in range(len(raw_frames)) if x not in selected_indices]
                remaining.sort(key=lambda x: min([cv2.compareHist(hists[x], hists[s], cv2.HISTCMP_CORREL) for s in selected_indices]))
                while len(selected_indices) < 4 and remaining:
                    selected_indices.append(remaining.pop(0))

            # Keep chronological story order
            frames = [raw_frames[s] for s in sorted(selected_indices)]
        else:
            frames = raw_frames
    else:
        # Scene detection fallback
        from scenedetect import detect, ContentDetector
        scene_list = detect(video_path, ContentDetector(threshold=27.0))
        if scene_list:
            for scene in scene_list:
                cap.set(cv2.CAP_PROP_POS_MSEC, scene[0].get_seconds() * 1000)
                ret, frame = cap.read()
                if ret:
                    h, w = frame.shape[:2]
                    new_w = 1280
                    frame = cv2.resize(frame, (new_w, int(h * new_w / w)))
                    frames.append(frame)

    cap.release()
    return frames

def batch_extract_frames(video_paths):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda x: extract_frames(x, fast_mode=True), video_paths))
    return results