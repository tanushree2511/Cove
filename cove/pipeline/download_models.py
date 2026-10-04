import os
import requests
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.vision_config import CONFIG

# The progress lines use emoji; a piped Windows console (CI, redirected output) defaults to cp1252 and would crash on them.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# CLIP ViT-B/16, full precision (~570 MB). Compared with the previous int8 ViT-B/32 it raised COCO-1k
# text->image Recall@1 from 39% to 51% and UCF101 video-tagging top-1 from 58% to 70%.
# (Set COVE_CLIP_MODEL=b32 to keep using a legacy clip_image.onnx / clip_text.onnx pair.)
_REPO = "https://huggingface.co/Xenova/clip-vit-base-patch16/resolve/main"
FILES = {
    "clip_b16_image.onnx": f"{_REPO}/onnx/vision_model.onnx",
    "clip_b16_text.onnx":  f"{_REPO}/onnx/text_model.onnx",
    "tokenizer.json":      f"{_REPO}/tokenizer.json",
}

OUTPUT_DIR = CONFIG.assets_dir
CHUNK = 1 << 20
MAX_ATTEMPTS = 20


def download_file(url, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print(f"✅ {filename} already exists. Skipping.")
        return True

    # Download to <name>.part and only rename once the byte count matches the server's, so a dropped
    # connection can never leave a truncated model that later looks "complete". Interrupted downloads resume.
    part = path + ".part"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        print(f"⬇️ Downloading {filename}" + (f" (resuming at {have / 1e6:.0f} MB)" if have else "") + "...")
        try:
            headers = {"Range": f"bytes={have}-"} if have else {}
            with requests.get(url, stream=True, headers=headers, timeout=60) as response:
                if response.status_code == 416:  # range past EOF -> already complete
                    total = have
                else:
                    response.raise_for_status()
                    if have and response.status_code != 206:  # server ignored Range -> start over
                        have = 0
                    total = have + int(response.headers.get("Content-Length", 0))
                    with open(part, "ab" if have else "wb") as f:
                        for chunk in response.iter_content(chunk_size=CHUNK):
                            f.write(chunk)
            size = os.path.getsize(part)
            if total and size != total:
                raise IOError(f"incomplete download: got {size} of {total} bytes")
            os.replace(part, path)
            print(f"✅ Saved {filename}")
            return True
        except Exception as e:
            print(f"⚠️ {filename}: attempt {attempt}/{MAX_ATTEMPTS} failed: {e}")
    print(f"❌ Failed to download {filename}")
    return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured models directory exists: {OUTPUT_DIR}")

    ok = all([download_file(url, filename) for filename, url in FILES.items()])

    if ok:
        print("\n🎉 All models are ready!")
    else:
        print("\n❌ Some models failed to download - re-run this script to resume.")
        sys.exit(1)


if __name__ == "__main__":
    main()
