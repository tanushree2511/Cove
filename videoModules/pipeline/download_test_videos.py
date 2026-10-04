import os
import requests
import json
import time

# List of varied test videos to download
VIDEOS = {
    "nature_jellyfish.mp4": "https://test-videos.co.uk/vids/jellyfish/mp4/h264/360/Jellyfish_360_10s_1MB.mp4",
    "animation_sintel.mp4": "https://test-videos.co.uk/vids/sintel/mp4/h264/360/Sintel_360_10s_1MB.mp4",
    "cartoon_bunny.mp4": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"
}

# The host machine maps ./videoModules/bulk_import to /app/videoModules/bulk_import in docker
BULK_IMPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bulk_import")
API_URL = "http://localhost:8001"

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"✅ {os.path.basename(filepath)} already exists.")
        return True
        
    print(f"⬇️ Downloading {os.path.basename(filepath)}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False

def main():
    print("🎬 Setting up Video Module Test Dataset...\n")
    os.makedirs(BULK_IMPORT_DIR, exist_ok=True)
    
    success_count = 0
    for filename, url in VIDEOS.items():
        filepath = os.path.join(BULK_IMPORT_DIR, filename)
        if download_file(url, filepath):
            success_count += 1
            
    if success_count == 0:
        print("\n❌ Failed to download any test videos.")
        return
        
    print(f"\n🚀 {success_count} videos ready in {BULK_IMPORT_DIR}")
    print("⏳ Triggering Video API Bulk Import...")
    
    # We trigger the bulk index API endpoint
    # The API runs inside Docker where the path is /app/videoModules/bulk_import
    try:
        response = requests.post(
            f"{API_URL}/index-bulk", 
            params={"directory_path": "/app/videoModules/bulk_import"}
        )
        if response.status_code == 200:
            print("✅ Bulk Import Job Started!")
            print("You can view the progress in the Video UI 'System Stats' or watch the terminal.")
        else:
            print(f"❌ Failed to start bulk import: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Video API at localhost:8001. Is it running?")

if __name__ == "__main__":
    main()
