# Architecture

Cove is a local-first photo and video manager. Nothing leaves the machine: all models are open-weight and run
through ONNX Runtime (photos) or PyTorch/transformers (video).

## System overview

```
                      ┌─────────────────────────────────────────────┐
                      │ Frontend  (React 18 + Vite + Tailwind/shadcn) │
                      │ Library · People · Search · Videos · Indexing │
                      └───────────┬───────────────────┬─────────────┘
          web / Docker: /api/cove │                   │ /api/video
          desktop: 127.0.0.1:8000 │                   │ 127.0.0.1:8001
                      ┌───────────▼─────────┐ ┌───────▼───────────┐
                      │ cove-api  (FastAPI) │ │ video-api (FastAPI)│
                      │ photos: CLIP+faces  │ │ video: CLIP+faces  │
                      └───────────┬─────────┘ └───────┬───────────┘
                  FAISS + .npy + JSON files      FAISS + SQLite (videos.db)
```

Three deployment shapes share the same code:

| Shape | How it runs |
|---|---|
| **Desktop app** (Tauri 2) | Tauri shell launches two PyInstaller-frozen sidecars (`cove-backend` on :8000, `video-backend` on :8001) and loads the React build. Models are bundled as a Tauri resource. |
| **Docker** | `cove-api`, `video-api` and an nginx `frontend` container (:8080) that reverse-proxies `/api/cove` and `/api/video`. Models live in the `cove_models` volume. |
| **Native dev** | `start.sh` / `start.bat` create `.venv`, start both APIs and the Vite dev server (:8080 proxy → :8000/:8001). |

## Repository layout

| Path | Purpose |
|---|---|
| `cove/` | Photo backend (`api/server.py`, `engines/`, `config/`, `pipeline/` scripts, `tests/`) |
| `videoModules/` | Video backend (`api.py`, `core/`, `pipeline/` sample-video downloaders) |
| `frontend/` | React SPA; `src-tauri/` holds the Rust desktop shell |
| `scripts/` | `install_runtime.py`, `build_backends.py`, `build_sidecars.py` |
| `benchmarks/` | Model benchmark runner |
| `evaluation/`, `datasets/`, `scratch/` | Local accuracy experiments and datasets (not part of the product) |
| `TECHNICAL_REPORT.md` | Research-style audit of methods and measured results |

## Photo pipeline (`cove/`)

**Engines** (`cove/engines/`)

- `ai_engine.py` – InsightFace (`buffalo_s`) face detection + 512-d face embeddings.
- `search_engine.py` – CLIP ViT-B/16 (ONNX) image and text encoders. Images are decoded in parallel threads and
  embedded in batches; text uses a bundled `tokenizer.json`.
- `vector_storage.py` – FAISS inner-product indexes plus the path manifest. Two indexes: faces
  (`faiss_index.bin`) and CLIP search (`faiss_search_index.bin`).
- `cluster_engine.py` – two-stage face clustering: a strict greedy "first-leader" pass (threshold 0.45) followed by
  an average-linkage merge of cluster centroids (0.40). Clusters smaller than `min_cluster_size` stay unassigned.
  Measured pairwise F1 on 900 LFW faces: 0.993.
- `person_manager.py` – persistent person records (names, thumbnails) in `people_db.json`.

**Indexing** (`POST /index/start`, background job): scan the image folder → skip paths already in the manifest
(incremental) → detect faces → CLIP-embed → cluster → persist. Progress is exposed at `GET /index/status`.

**Search** (`POST /search/text`): encode the query with CLIP, take the top 40+ FAISS candidates, drop everything
below the client `threshold` (default 0.20), then keep results within 12% of the best score (always at least 8).
If the CLIP model changes, embeddings are incompatible and the search index is rebuilt automatically.

## Video pipeline (`videoModules/`)

1. **Frame sampling** (`core/video_processor.py`) – 14 frames evenly across the clip, near-duplicate frames removed
   by colour histogram (≥4 kept). The number actually sent through CLIP adapts to measured hardware speed.
2. **Embedding** (`core/embedder.py`) – per-frame CLIP embeddings stored as float16 in SQLite.
3. **Classification** (`core/classifier.py`, `label_taxonomy.py`) – zero-shot: frame embeddings vs. text embeddings
   of the label taxonomy, softmax with logit scale 50, up to 3 labels within 40% of the best probability; below
   cosine 0.18 the label is the generic `video`. Label text embeddings are cached on disk per (model, prompt version).
4. **Faces** (`core/face_processor.py`) – InsightFace `buffalo_l` on sampled frames, clustered into persons;
   blurry faces can be pruned.
5. **Search** (`POST /search`) – frame-level scoring: a smooth maximum (log-mean-exp, temperature `POOL_TAU`) over a
   video's frame similarities, so a clip matches if *any* part shows the query.
6. **Transcoding** (`core/transcode.py`) – incompatible codecs are converted with ffmpeg so videos play in the
   browser/webview; files are served from `/stream`.

**SQLite schema** (`videos.db`): `videos` (path, label, embedding, per-frame embeddings), `persons`, `faces`
(video, person, embedding, thumbnail), `user_feedback` (label corrections), `meta`.

## Hardware detection and tuning (`cove/config/`)

- `hardware.py` – detects physical/logical cores (respecting container quotas), RAM, and GPUs/NPUs
  (NVIDIA CUDA, AMD ROCm/DirectML, Intel OpenVINO/DirectML, Apple Core ML, Qualcomm QNN) and installed ORT providers.
- `runtime.py` – on first start, benchmarks each candidate (every accelerator; CPU at physical-core and all-thread
  counts) on the real CLIP model in an isolated subprocess, picks the fastest, and caches the result per machine.
  A slower-than-CPU GPU is never chosen and a driver failure falls back to CPU. Live throughput then scales the
  number of video frames processed.
- `vision_config.py` – the single config object: paths, model resolution, data-dir selection, env overrides.
- `envcompat.py` – accepts legacy `VISION_*` variables as aliases for `COVE_*`.

Inspect decisions at `GET /hardware` on each API.

## Data locations

User data (indexes, manifests, `people_db.json`, `videos.db`, logs) lives in the OS user-data directory
(`%APPDATA%\Cove`, `~/Library/Application Support/Cove`, `~/.config/Cove`) unless `COVE_USER_DATA` is set.
Models are resolved from, in order: PyInstaller bundle, repo `models/`, package `models/`, user-data `models/`,
`COVE_MODEL_DIR`. Required: a CLIP ONNX pair (`clip_b16_*.onnx` or legacy `clip_*.onnx`) and `buffalo_s/`.

## Frontend (`frontend/src`)

- `pages/Index.jsx` + `layouts/DesktopLayout.jsx` – shell and view routing.
- `components/features/` – `GalleryView`, `PeopleView`, `SearchView`, `VideoView`, `IndexingPanel`,
  `SettingsView`, modals and cards.
- `lib/coveApi.js`, `lib/videoApi.js` – API clients; detect Tauri and talk to `127.0.0.1:8000/8001` directly,
  otherwise use the `/api/cove` and `/api/video` proxies.
- `store/useAppStore.js` – global state.

## Desktop shell (`frontend/src-tauri`)

`lib.rs` frees ports 8000/8001, spawns the two sidecars with `COVE_PORT`, `COVE_USER_DATA`, `COVE_MODEL_DIR`, a
private temp dir (to clean stale PyInstaller `_MEI*` folders), and kills them on exit. `tauri.conf.json` declares
`bin/cove-backend` and `bin/video-backend` as `externalBin` and bundles `models/` as a resource.

## Security model

Backends bind to `127.0.0.1` by default (`COVE_HOST`). CORS is open because the frontend origin varies
(Vite, nginx, `tauri://`). If `COVE_API_KEY` is set, photo-API requests must send it in `x-api-key`. There is no
user authentication; do not expose the ports to an untrusted network.
