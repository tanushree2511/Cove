import os
import shutil

import numpy as np
from PIL import Image


DEFAULT_SOURCE_ROOT = "image_dataset/archive/lfw-deepfunneled/lfw-deepfunneled"
DEFAULT_CACHE_ROOT = os.path.expanduser("~/scikit_learn_data/lfw_home/lfw_funneled")
DEFAULT_DEST_DIR = "test_images"


def _count_images(directory: str) -> int:
    if not os.path.isdir(directory):
        return 0
    return sum(
        1
        for file_name in os.listdir(directory)
        if file_name.lower().endswith((".jpg", ".jpeg", ".png"))
    )


def _copy_local_dataset(source_root: str, dest_dir: str) -> int:
    count = 0
    print(f"Scanning {source_root}...")

    for root, dirs, files in os.walk(source_root):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                src_path = os.path.join(root, file)
                dst_path = os.path.join(dest_dir, file)

                if os.path.exists(dst_path):
                    base, ext = os.path.splitext(file)
                    dst_path = os.path.join(dest_dir, f"{base}_dup{ext}")

                shutil.copy2(src_path, dst_path)
                count += 1
                if count % 100 == 0:
                    print(f"Copied {count} images...", end='\r')

    return count


def _download_lfw_people(dest_dir: str) -> int:
    try:
        from sklearn.datasets import fetch_lfw_people
    except Exception as exc:
        print(f"❌ Unable to import the LFW fallback downloader: {exc}")
        return 0

    print("No local LFW archive found. Downloading the public LFW People dataset...")
    try:
        dataset = fetch_lfw_people(color=True, resize=1.0, download_if_missing=True)
    except Exception as exc:
        print(f"❌ Failed to download the public LFW dataset: {exc}")
        return 0

    count = 0
    for index, image in enumerate(dataset.images):
        label = dataset.target_names[dataset.target[index]].replace(" ", "_")
        dst_path = os.path.join(dest_dir, f"{label}_{index:05d}.jpg")
        if os.path.exists(dst_path):
            continue

        image_array = np.asarray(image)
        if image_array.dtype != np.uint8:
            image_array = np.clip(image_array, 0, 255).astype(np.uint8)

        Image.fromarray(image_array).save(dst_path, format="JPEG", quality=95)
        count += 1
        if count % 100 == 0:
            print(f"Saved {count} images...", end='\r')

    return count


def ensure_test_images(
    source_root: str = DEFAULT_SOURCE_ROOT,
    dest_dir: str = DEFAULT_DEST_DIR,
    force: bool = False,
) -> int:
    if force and os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)

    os.makedirs(dest_dir, exist_ok=True)

    existing_images = _count_images(dest_dir)
    if existing_images > 0:
        return existing_images

    for candidate in (source_root, DEFAULT_CACHE_ROOT):
        if candidate and os.path.exists(candidate):
            copied = _copy_local_dataset(candidate, dest_dir)
            if copied > 0:
                return copied

    return _download_lfw_people(dest_dir)

def main():
    source_root = os.getenv("VISION_LFW_SOURCE", DEFAULT_SOURCE_ROOT)
    dest_dir = DEFAULT_DEST_DIR
    force_refresh = os.getenv("VISION_LFW_FORCE_REFRESH", "0").strip().lower() in {"1", "true", "yes", "on"}

    os.makedirs(dest_dir, exist_ok=True)
    count = ensure_test_images(source_root, dest_dir, force=force_refresh)

    if count == 0:
        print(f"❌ No images were copied or downloaded into '{dest_dir}'.")
        return

    print(f"\n✅ Done! {count} images are available in '{dest_dir}'.")
    print("You can now run 'python production_pipeline.py' to build the embeddings.")

if __name__ == "__main__":
    main()