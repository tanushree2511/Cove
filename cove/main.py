"""
Vision Archive AI - Main Entry Point
Run this file to show the CLI guidance and check component readiness.
"""
from __future__ import annotations

import argparse
import os
from typing import Iterable

from vision_config import CONFIG


def _print_section(title: str, lines: Iterable[str]) -> None:
    print(title)
    for line in lines:
        print(line)
    print()


def show_commands() -> None:
    print("=" * 50)
    print("  👁️  VISION ARCHIVE AI")
    print("=" * 50)
    print()

    _print_section("SETUP:", [
        "    python download_models.py      Download CLIP models (~500MB)",
        "    python prepare_lfw.py          Copy LFW dataset to test_images/",
    ])

    _print_section("PROCESSING:", [
        "    python production_pipeline.py  Extract face embeddings (fast)",
        "    python tune_clustering.py      Cluster faces & tune parameters",
        "    python reindex_search.py       Build semantic search index",
    ])

    _print_section("INTERFACES:", [
        "    streamlit run app.py           Launch Streamlit Web UI",
        "    python gallery.py              Generate & serve HTML gallery",
        "    python search_app.py           CLI text-to-image search",
        "    python server.py               Start FastAPI server",
    ])

    _print_section("UTILITIES:", [
        "    python rename_person.py ID Name  Rename a person in DB",
        "    python watcher.py [dir]        Watch folder for new images",
        "    python align_database.py       Repair vector database",
    ])


def show_status() -> None:
    face_models_dir = os.path.join(CONFIG.assets_dir, "buffalo_s")
    face_model_ready = os.path.exists(os.path.join(face_models_dir, "det_500m.onnx"))
    clip_ready = all(os.path.exists(os.path.join(CONFIG.assets_dir, f)) for f in [
        "clip_image.onnx",
        "clip_text.onnx",
        "tokenizer.json",
    ])
    db_ready = os.path.exists(CONFIG.people_db_path)
    search_index_ready = os.path.exists(CONFIG.search_index_path)

    print("-" * 50)
    print("System Status:")
    print(f"  Face Models:   {'✅ Ready' if face_model_ready else '❌ Missing (run download_models.py)'}")
    print(f"  CLIP Models:   {'✅ Ready' if clip_ready else '❌ Missing (run download_models.py)'}")
    print(f"  People DB:     {'✅ Ready' if db_ready else '⚠️  Not built yet'}")
    print(f"  Search Index:  {'✅ Ready' if search_index_ready else '⚠️  Not built yet'}")
    print(f"  Vectors Cache: {'✅ Ready' if os.path.exists(CONFIG.vector_path) else '⚠️  Not built yet'}")
    print(f"  User Data Dir: {CONFIG.user_data_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Vision Archive CLI entry point')
    parser.add_argument('command', nargs='?', choices=['help', 'status'], default='help')
    args = parser.parse_args()

    if args.command == 'status':
        show_status()
    else:
        show_commands()


if __name__ == '__main__':
    main()
