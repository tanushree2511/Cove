import os
import subprocess
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bulk_import")
os.makedirs(DATA_DIR, exist_ok=True)

FACES = {
    "einstein1.jpg": "https://upload.wikimedia.org/wikipedia/commons/d/d3/Albert_Einstein_Head.jpg",
    "einstein2.jpg": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Einstein_1921_by_F_Schmutzer_-_restoration.jpg",
    "obama1.jpg": "https://upload.wikimedia.org/wikipedia/commons/8/8d/President_Barack_Obama.jpg",
    "obama2.jpg": "https://upload.wikimedia.org/wikipedia/commons/a/a4/Barack_Obama_speech_at_UIT.jpg"
}

def download_file(url, path):
    if not os.path.exists(path):
        print(f"Downloading {url}...")
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=10)
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        except Exception as e:
            print(f"Failed: {e}")

def make_video(img_path, vid_path):
    print(f"Generating video {vid_path}...")
    # Scale and pad to standard size to avoid ffmpeg errors on odd resolutions
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path, 
        "-vf", "scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2", 
        "-c:v", "libx264", "-t", "3", "-pix_fmt", "yuv420p", vid_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print("📸 Downloading face images...")
    for filename, url in FACES.items():
        img_path = os.path.join(DATA_DIR, filename)
        download_file(url, img_path)
        vid_path = os.path.join(DATA_DIR, f"face_test_{filename.split('.')[0]}.mp4")
        make_video(img_path, vid_path)
        os.remove(img_path)  # Cleanup image, leave only video

    print("✅ Generated 4 face test videos in bulk_import/")
    print("⏳ Triggering Video API Bulk Import...")
    
    API_URL = "http://localhost:8001"
    try:
        response = requests.post(f"{API_URL}/index-bulk", params={"directory_path": "/app/videoModules/bulk_import"})
        if response.status_code == 200:
            print("✅ Bulk Import Started! Wait for it to finish, then hit /cluster-faces")
        else:
            print("❌ API Error:", response.text)
    except Exception as e:
        print("❌ Could not connect to API.")

if __name__ == "__main__":
    main()
