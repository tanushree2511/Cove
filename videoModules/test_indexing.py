import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from core.video_processor import extract_frames
from core.embedder import generate_video_embedding
from core.classifier import classify_video
from core.database import init_db, add_video
import cv2

def test_index():
    init_db()
    # Find a video to test with
    test_video = None
    for f in os.listdir("uploaded_videos"):
        if f.endswith(".mp4"):
            test_video = os.path.join("uploaded_videos", f)
            break
            
    if not test_video:
        print("No test video found in uploaded_videos/")
        return

    print(f"Testing indexing for: {test_video}")
    try:
        frames = extract_frames(test_video)
        print(f"Extracted {len(frames)} frames")
        v_emb = generate_video_embedding(frames)
        print("Generated embedding")
        label = classify_video(v_emb)
        print(f"Classified as: {label}")
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_index()
