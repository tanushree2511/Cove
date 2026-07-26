# Running Vision Archive AI

This project has two runtime surfaces:

- Streamlit UI: `app.py`
- FastAPI backend: `server.py`

The codebase also includes helper scripts to download models and build the local image indexes used by the UI.

## Prerequisites

- Python 3.14 or later
- A virtual environment in the repository root
- Network access for the first model and dataset download

## 1. Create and activate a virtual environment

```bash
cd /home/shubham-singh/code/cove
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Download the model assets

The project needs CLIP models plus the InsightFace `buffalo_s` bundle.

```bash
python download_models.py
python - <<'PY'
from insightface.app import FaceAnalysis
from vision_config import CONFIG

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
python prepare_lfw.py
```

If you want to force a refresh of `test_images/`, run:

```bash
VISION_LFW_FORCE_REFRESH=1 python prepare_lfw.py
```

## 5. Build the face embeddings

```bash
python production_pipeline.py
```

This populates the face embedding index and the people database under the VisionArchive data directory.

## 6. Build the semantic search index

```bash
python reindex_search.py
```

This creates the CLIP-based FAISS search index and vector cache.

## 7. Start the application

### Streamlit UI

```bash
streamlit run app.py
```

The UI is usually available at `http://localhost:8501`.

### FastAPI backend

```bash
python server.py
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

- If `production_pipeline.py` reports a missing `test_images` folder, run `python prepare_lfw.py` first.
- If `app.py` starts but semantic search is unavailable, run `python reindex_search.py`.
- If the UI starts without people data, run `python tune_clustering.py` after embeddings are built.
- If you need a fresh rebuild, remove generated data with `python reset_data.py` and then run the setup steps again.
