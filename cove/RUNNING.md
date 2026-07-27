# Running Vision Archive AI

This project has two runtime surfaces:

- Streamlit UI: `ui/app.py`
- FastAPI backend: `api/server.py`

The codebase also includes helper scripts (under `pipeline/`) to download models and build the local image indexes used by the UI.

## Folder structure

```
cove/
  config/    vision_config.py            - environment/paths configuration
  engines/   ai_engine.py, search_engine.py, cluster_engine.py,
             vector_storage.py, person_manager.py   - core AI/data engines
  api/       server.py                   - FastAPI sidecar
  ui/        app.py, gallery.py, search_app.py       - Streamlit / CLI interfaces
  pipeline/  download_models.py, prepare_lfw.py, production_pipeline.py,
             reindex_search.py, tune_clustering.py, align_database.py,
             reset_data.py, rename_person.py, watcher.py   - one-off/batch scripts
  main.py    - CLI entry point (help + status)
  models/    - downloaded model assets (clip_*.onnx, buffalo_s/)
  test_images/ - local image set used by the pipeline
  tests/     - pytest suite
```

Modules across folders use package-qualified imports (e.g. `from config.vision_config import CONFIG`, `from engines.ai_engine import AIEngine`), so the `cove/` repository root itself must be on `PYTHONPATH` — see step 1 below. `main.py`, each entry-point script (`api/server.py`, `ui/*.py`, `pipeline/*.py`), and the test suite (`tests/conftest.py`) already bootstrap this themselves.

## Prerequisites

- Python 3.11+ (a slim Docker image based on 3.11 is used in production; anything 3.11+ locally works)
- A virtual environment in the repository root
- Network access for the first model and dataset download

## 1. Create and activate a virtual environment

```bash
cd /path/to/Major-Project/cove
python3 -m venv .venv
source .venv/bin/activate
export PYTHONPATH="$PWD"
```

Add the `export PYTHONPATH` line to your shell profile or re-run it in every new shell before invoking scripts directly (not needed if you're using `main.py`, `pytest`, or Docker — all three already set this up for you).

## 2. Install dependencies

```bash
pip install -r ../requirements.txt
```

## 3. Download the model assets

The project needs CLIP models plus the InsightFace `buffalo_s` bundle.

```bash
python pipeline/download_models.py
python - <<'PY'
from insightface.app import FaceAnalysis
from config.vision_config import CONFIG

app = FaceAnalysis(
    name="buffalo_s",
    root=CONFIG.assets_base,
    allowed_modules=["detection", "recognition"],
    providers=["CPUExecutionProvider"],
)
app.prepare(ctx_id=-1, det_size=(320, 320))
print("face model ready")
PY
```

After that, `python main.py status` should report both Face Models and CLIP Models as ready.

## 4. Prepare the image set

The pipeline expects `test_images/` to exist and contain images.

If you have the original LFW archive on disk, the project can copy from it automatically. If not, the helper falls back to the cached LFW dataset on the machine or downloads the public LFW people dataset.

```bash
python pipeline/prepare_lfw.py
```

If you want to force a refresh of `test_images/`, run:

```bash
VISION_LFW_FORCE_REFRESH=1 python pipeline/prepare_lfw.py
```

## 5. Build the face embeddings

```bash
python pipeline/production_pipeline.py
```

This populates the face embedding index and the people database under the VisionArchive data directory.

## 6. Build the semantic search index

```bash
python pipeline/reindex_search.py
```

This creates the CLIP-based FAISS search index and vector cache.

## 7. Start the application

### Streamlit UI

```bash
streamlit run ui/app.py
```

The UI is usually available at `http://localhost:8501`.

### FastAPI backend

```bash
python api/server.py
```

The API listens on `http://127.0.0.1:8000`.

## 8. Verify readiness

Run the built-in status command at any time:

```bash
python main.py status
```

Expected output when everything is ready:

- Face Models: Ready
- CLIP Models: Ready
- People DB: Ready
- Search Index: Ready
- Vectors Cache: Ready

## Common issues

- If `pipeline/production_pipeline.py` reports a missing `test_images` folder, run `pipeline/prepare_lfw.py` first.
- If `ui/app.py` starts but semantic search is unavailable, run `pipeline/reindex_search.py`.
- If the UI starts without people data, run `pipeline/tune_clustering.py` after embeddings are built.
- If you need a fresh rebuild, remove generated data with `pipeline/reset_data.py` and then run the setup steps again.
- `ModuleNotFoundError` on a package import like `config.vision_config` or `engines.ai_engine` usually means `PYTHONPATH` isn't set to the `cove/` root — see step 1.

## Running with Docker

`docker compose up -d` from the repository root builds and runs everything (`cove-api`, `cove-ui`, `video-api`, `video-ui`, `frontend`) with `PYTHONPATH` already configured in the image — no manual setup needed.
