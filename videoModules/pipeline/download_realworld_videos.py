import os
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bulk_import")
os.makedirs(DATA_DIR, exist_ok=True)

VIDEOS = {
    "chromecast_blazes.mp4": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "chromecast_escapes.mp4": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "chromecast_joyrides.mp4": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
    "tears_of_steel_sci_fi.mp4": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"
}

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
            for chunk in response.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        print(f"✅ Saved to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False

def main():
    print("🎬 Setting up Real-World Video Dataset...")
    success_count = 0
    for filename, url in VIDEOS.items():
        filepath = os.path.join(DATA_DIR, filename)
        if download_file(url, filepath):
            success_count += 1
            
    print(f"\n🚀 {success_count} real-world videos ready in {DATA_DIR}")
    print("⏳ Triggering Video API Bulk Import...")
    
    API_URL = "http://localhost:8001"
    try:
        response = requests.post(
            f"{API_URL}/index-bulk", 
            params={"directory_path": "/app/videoModules/bulk_import"}
        )
        if response.status_code == 200:
            print("✅ Bulk Import Job Started!")
        else:
            print(f"❌ Failed to start bulk import: {response.text}")
    except Exception as e:
        print("❌ Could not connect to Video API.")

if __name__ == "__main__":
    main()
