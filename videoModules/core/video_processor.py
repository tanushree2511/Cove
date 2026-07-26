import cv2
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor

def extract_frames(video_path, fast_mode=True):
    """
    Extracts frames from a video. 
    fast_mode=True: Samples frames at fixed intervals (MUCH faster).
    fast_mode=False: Uses scene detection (more accurate but slower).
    """
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    if fast_mode:
        # Optimized for speed: Fixed count of 4 frames per video
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0: total_frames = 60
        
        # Target exactly 4 frames to keep CPU load low
        num_frames = 4
        indices = np.linspace(0, total_frames - 1, num_frames).astype(int)
        
        for i in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                # Downscale for faster processing
                h, w = frame.shape[:2]
                new_w = 640
                frame = cv2.resize(frame, (new_w, int(h * new_w / w)))
                frames.append(frame)
    else:
        # Scene detection fallback (slow)
        from scenedetect import detect, ContentDetector
        scene_list = detect(video_path, ContentDetector(threshold=27.0))
        if scene_list:
            for scene in scene_list:
                cap.set(cv2.CAP_PROP_POS_MSEC, scene[0].get_seconds() * 1000)
                ret, frame = cap.read()
                if ret: frames.append(frame)
    
    cap.release()
    return frames

def batch_extract_frames(video_paths):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda x: extract_frames(x, fast_mode=True), video_paths))
    return results