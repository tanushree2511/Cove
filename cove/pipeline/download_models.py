import os
import requests
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.vision_config import CONFIG

FILES = {
    "clip_image.onnx": "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/onnx/vision_model_quantized.onnx",
    "clip_text.onnx":  "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/onnx/text_model_quantized.onnx",
    "tokenizer.json":  "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/tokenizer.json"
}

OUTPUT_DIR = CONFIG.assets_dir

def download_file(url, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print(f"✅ {filename} already exists. Skipping.")
        return

    print(f"⬇️ Downloading {filename}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Saved {filename}")
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured models directory exists: {OUTPUT_DIR}")

    for filename, url in FILES.items():
        download_file(url, filename)
        
    print("\n🎉 All models are ready!")

if __name__ == "__main__":
    main()
