# Cove

A local-first AI photo & video manager: CLIP semantic search, InsightFace-based
face detection/clustering, and FAISS vector search for photos (`cove/`), plus
a face/video indexing and search pipeline for video libraries (`videoModules/`). One React frontend
(`frontend/`) covers both, and it also ships as a Tauri desktop app (Windows installer built in CI).

**Docs:** [Architecture](docs/ARCHITECTURE.md) · [API reference](docs/API.md) · [Configuration](docs/CONFIGURATION.md) ·
[Development](docs/DEVELOPMENT.md) · [Technical report](TECHNICAL_REPORT.md)

---

## ⚡ Quick Start

### Requirements

| Method | Requirements |
|---|---|
| **Docker** (recommended) | [Docker Desktop 4.x](https://www.docker.com/products/docker-desktop/) or Docker Engine + Compose v2 |
| **Native** | Python 3.10+, Node.js 18+, [ffmpeg](https://ffmpeg.org/download.html) |

> [!NOTE]
> The ML model weights are ~700 MB in total (see "First-time model & data setup" below). Subsequent
> starts reuse the cached `cove_models` volume and are much faster.

---

### 🐳 Docker — any platform (recommended)

```bash
git clone <this-repo-url>
cd cove
docker compose up
```

Open **<http://localhost:8080>**.

#### With an NVIDIA GPU

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up
```

---

### 🐧 Linux / macOS — native

```bash
chmod +x start.sh
./start.sh
```

`start.sh` will:
- Create and populate `.venv` automatically if it doesn't exist
- Auto-detect an NVIDIA GPU and set `COVE_FORCE_CPU` accordingly
- Start **cove-api** (port 8000), **video-api** (port 8001), and the **React frontend** (port 8080)
- Wait until cove-api is healthy, then print a success banner
- Capture all service logs to `.logs/`
- Shut everything down cleanly on **Ctrl+C**

---

### 🪟 Windows — native

Double-click **`start.bat`** or run it in Command Prompt:

```bat
start.bat
```

`start.bat` will create `.venv`, start all three services, and automatically open **<http://localhost:8080>** in your browser after a 5-second delay. Logs are written to `.logs\`. Close the Command Prompt window (or press **Ctrl+C**) to stop all services.

---

This guide gets a fresh clone running end-to-end with Docker Compose — no
manual Python/Node environment setup required.

## Architecture

| Service      | What it is                                   | Port (host) | Container name               |
|--------------|-----------------------------------------------|:-----------:|-------------------------------|
| `frontend`   | React SPA + nginx (reverse-proxies `/api/cove` to `cove-api`) | **8080** | `cove-frontend-1` |
| `cove-api`   | FastAPI backend — face detection, CLIP search, indexing jobs | 8000 | `cove-cove-api-1` |
| `video-api`  | FastAPI backend for video indexing/search                    | 8001 | `cove-video-api-1`|

**The app you use day-to-day is `http://localhost:8080`** (Library, People, Search, Videos, Indexing and
Settings are all in the React app).

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose version` should work)
- ~5 GB free disk (Python/ML base images + model weights)
- Internet access on first run (to download CLIP/InsightFace model weights)

## 1. Clone and build

```bash
git clone <this-repo-url>
cd cove
docker compose build
```

This builds two images: `backend` (shared by `cove-api`/`video-api`)
and `frontend` (the React SPA behind nginx). First build takes a while — it
installs face-recognition/ML dependencies (torch, onnxruntime, insightface, etc.).

## 2. Start everything

```bash
docker compose up -d
```

Check everything came up:

```bash
docker compose ps
curl http://localhost:8000/health   # cove-api
curl http://localhost:8080          # frontend
```

`cove-api`'s `/health` should report `"status": "ok"` (or `"degraded"` if
`COVE_SKIP_MODEL_LOAD` is set, or if the face/CLIP models below haven't been
downloaded yet).

## 3. First-time model & data setup

Model weights are **not** baked into the image (they're large binaries — see
`.gitignore`) and live in the persistent `cove_models` Docker volume, so they
only need downloading once, the first time you stand the stack up.

```bash
docker compose exec cove-api sh -c "cd /app/cove && python3 pipeline/download_models.py"
```

This fetches the CLIP ViT-B/16 ONNX models (~590 MB, full precision) into the
shared `cove_models` volume; interrupted downloads resume when you re-run it.
The InsightFace face-detection model (`buffalo_s`, ~130 MB) downloads
automatically into the same volume at `cove-api` startup.

> [!NOTE]
> ViT-B/16 replaced the earlier int8 ViT-B/32 because it is markedly more accurate
> (COCO text→image Recall@1 39% → 51%, UCF101 video tagging top-1 58% → 70%) at the
> cost of slower indexing on CPU. Embeddings from different CLIP models aren't
> comparable, so when the model changes the app automatically rebuilds the photo
> search index and re-analyses stored videos. To keep an existing legacy
> `clip_image.onnx` / `clip_text.onnx` pair, set `COVE_CLIP_MODEL=b32`.

`video-api` downloads its own models (InsightFace `buffalo_l` + a CLIP model
via HuggingFace `transformers`) automatically on first use — no manual step,
but expect the *first* video indexing request to be slow while it fetches
them. They're cached in the `video_hf_cache`/`video_insightface_cache`
volumes, so recreating the container won't force a re-download.

### Add photos to the library

Photos live in `cove/test_images/` (bind-mounted into `cove-api`, so
you can drop files there directly from the host, or use the app's own upload):

- **Easiest — via the UI**: open `http://localhost:8080`, use the **Import**
  button (top bar, or inside the Library view) to upload photos. This
  automatically kicks off indexing.
- **Bulk / scripted**: copy files straight into `cove/test_images/` on the
  host, then trigger indexing via the UI's **Indexing** tab → **Start
  Indexing** button, or:
  ```bash
  curl -X POST http://localhost:8000/index/start
  curl http://localhost:8000/index/status   # poll progress
  ```
- **No photos of your own?** Seed the library with the public LFW face
  dataset for a quick demo:
  ```bash
  docker compose exec cove-api sh -c "cd /app/cove && python3 pipeline/prepare_lfw.py"
  curl -X POST http://localhost:8000/index/start
  ```

Indexing runs face detection, CLIP embedding, and face clustering in the
background; watch progress in the **Indexing** tab or via `/index/status`.

## 4. Use the app

Open **http://localhost:8080**:

| View | What it does |
|---|---|
| **Library** | Browse all photos; grid view, person filter, import/delete |
| **People** | Face clusters detected across your library; click to filter Library by person |
| **Search** | CLIP-powered natural-language photo search ("a man in a suit") |
| **Indexing** | Real-time status of the background indexing job; manual "Start Indexing" trigger |
| **Videos** | Index, search and browse videos; video people and label corrections |
| **Settings** | Real system stats (GPU/CPU, photos indexed, people detected), theme |

## Hardware: automatic detection and tuning

The app adapts itself to the machine it runs on — nothing to configure.

* **Detection** (`cove/config/hardware.py`): physical/logical CPU cores (respecting container CPU quotas and
  affinity), RAM, and GPUs/NPUs of any vendor — NVIDIA (CUDA), AMD (ROCm / DirectML), Intel (OpenVINO /
  DirectML), Apple Silicon (Core ML), Qualcomm (QNN) — plus which ONNX Runtime providers are installed.
* **Benchmark & choose** (`cove/config/runtime.py`): on first start every candidate (each accelerator, the CPU at
  physical-core and all-thread counts) is timed on the real CLIP model in an isolated subprocess and the fastest
  wins; the result is cached per machine. A weak integrated GPU that is slower than the CPU is never picked, a
  broken GPU driver can't crash the app, and if an accelerator fails to start the CPU is used.
* **Live adaptation**: real throughput is tracked while the app works, and the number of video frames sent through
  CLIP is scaled to it (about one frame per 3 s of video, capped by a ~2 s compute budget). Accuracy is flat from 16
  down to ~4 frames per clip, so slow CPUs do less work for the same results and fast GPUs use more frames.
* **Pipelining**: images are decoded in parallel threads and embedded in batches; for videos, face detection runs
  alongside CLIP; face-model replicas each get a thread budget instead of every one grabbing every core.

See what was chosen at `GET /api/cove/hardware` and `GET /api/video/hardware` (hardware found, the chosen
configuration and the benchmark numbers). On the dev laptop used for testing (4-core i5-8250U) this made video
analysis ~2.4x faster (3.9 → 1.6 s per video) and photo embedding 1.35x faster with unchanged accuracy.
More threads do not help once the CPU's maths units are saturated (CLIP ViT-B/16 measured 3.7 img/s at 2 threads and
4.0 at 8), which is why "CPU usage %" is not the goal — throughput is.

For native (non-Docker) runs, `scripts/install_runtime.py` (run automatically by `start.sh` / `start.bat` when the
venv is created) installs the matching ONNX Runtime build: `onnxruntime-gpu` (NVIDIA), `onnxruntime-directml`
(any DirectX 12 GPU on Windows), `onnxruntime-openvino` (Intel on Linux), `onnxruntime-qnn` (Snapdragon), or the
plain build (macOS has Core ML built in). Docker on Linux/WSL2 can only use NVIDIA GPUs (`docker-compose.gpu.yml`);
AMD ROCm needs AMD's own wheel. Overrides: `COVE_FORCE_CPU=1`, `COVE_AUTOTUNE=0`, `COVE_ORT_THREADS=N`,
`COVE_BATCH_SIZE=N`, `COVE_VIDEO_BUDGET_S=S`, `COVE_ORT_PACKAGE=<pip package>`.

> [!NOTE]
> Hardware paths other than CPU were verified by simulation (unit tests for NVIDIA, AMD, Apple, Intel, Qualcomm,
> DirectML and container limits) and, on real hardware, the CPU and DirectML-on-Intel-UHD paths only.

## Local development (without full Docker)

Useful for frontend UI iteration without rebuilding the image each time.

```bash
# Keep the backend running in Docker
docker compose up -d cove-api

# Run the frontend dev server on the host
cd frontend
npm install
npm run dev
```

`frontend/vite.config.js` proxies `/api/cove/*` to `http://localhost:8000`
(the Dockerized `cove-api`, whose port is published to the host), so
`http://localhost:8080` in dev mode behaves the same as the full Docker build
— no CORS setup or `VITE_API_URL` env var needed either way.

For running `cove/`'s Python code directly on the host (outside Docker) —
e.g. the pipeline CLI scripts or `pytest` — see **[cove/RUNNING.md](cove/RUNNING.md)**.

## Running tests

`cove/tests/` is intentionally excluded from the Docker build context
(`.dockerignore`), so tests only run from the host, not inside a container.
Set up a virtualenv with the root `requirements.txt` installed, then:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd cove && python3 -m pytest tests/ -q
```

## Rebuilding after code changes

`cove/`, `videoModules/`, and `nginx.conf` are **copied into the image at
build time**, not volume-mounted — so backend/nginx code changes need a
rebuild + recreate, not just a container restart:

```bash
# Backend (cove/ or videoModules/) changes:
docker compose build cove-api video-api
docker compose up -d cove-api video-api

# Frontend or nginx.conf changes:
docker compose build frontend
docker compose up -d frontend
```

(`nginx.conf` dynamically re-resolves `cove-api`'s address at request time, so
recreating `cove-api` alone — without touching `frontend` — no longer breaks
the proxy; you only need to rebuild `frontend` when `nginx.conf` itself or the
React source changes.)

## Troubleshooting

- **`/api/cove/*` returns 502 through the frontend**: `cove-api` isn't up yet,
  or crashed — check `docker compose logs cove-api`.
- **Health check shows `"status": "degraded"`**: models haven't loaded yet
  (still downloading) or `COVE_SKIP_MODEL_LOAD` is set — see step 3.
- **Permission denied writing into `cove/test_images/`**: the directory can
  end up root-owned since it's created by the container; fix from the host
  with `docker compose exec -u root cove-api chown -R $(id -u):$(id -g) /app/cove/test_images`.
- **Search/People return empty after adding photos**: indexing hasn't run yet
  — check the **Indexing** tab or `GET /index/status`.
- **Port already in use**: another process is bound to 8000/8001/8080
  on the host; stop it or edit the `ports:` mappings in `docker-compose.yml`.

## Project structure

```
cove/             Photo backend - FastAPI API, engines (face/CLIP/cluster), hardware tuning, pipeline scripts, tests
videoModules/     Video backend - FastAPI API, frame sampling, zero-shot labelling, faces, SQLite store
frontend/         React (Vite) SPA - Library/People/Search/Videos/Indexing/Settings; src-tauri/ = desktop shell
scripts/          Runtime installer, backend/sidecar packaging
docs/             Architecture, API, configuration, development guides
nginx.conf        Reverse proxy baked into the frontend image
docker-compose.yml  cove-api, video-api and frontend services + persistent volumes
```
