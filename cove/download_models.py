import os
import requests

from vision_config import CONFIG

# Define the files we need (Using Xenova's optimized ONNX models)
# These are standard, lightweight, and don't require PyTorch.
FILES = {
    "clip_image.onnx": "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/onnx/vision_model.onnx",
    "clip_text.onnx":  "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/onnx/text_model.onnx",
    "tokenizer.json":  "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/tokenizer.json"
}

OUTPUT_DIR = CONFIG.assets_dir

def download_file(url, filename):
    path = os.path.join(OUTPUT_DIR, filename)
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
    # 1. Create models folder if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured models directory exists: {OUTPUT_DIR}")

    # 2. Download all files
    for filename, url in FILES.items():
        download_file(url, filename)

    print("\n🎉 All CLIP models are ready!")
    print(f"   - Image Model: {os.path.join(OUTPUT_DIR, 'clip_image.onnx')}")
    print(f"   - Text Model:  {os.path.join(OUTPUT_DIR, 'clip_text.onnx')}")
    print(f"   - Tokenizer:   {os.path.join(OUTPUT_DIR, 'tokenizer.json')}")

if __name__ == "__main__":
    main()