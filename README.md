# VisionArchive AI — Major Project

A local-first AI photo & video manager: CLIP semantic search, InsightFace-based
face detection/clustering, and FAISS vector search for photos (`cove/`), plus
a separate face/video indexing pipeline for video libraries (`videoModules/`).
A single React frontend (`frontend/`) ties the photo features together; the
video features currently live in their own Streamlit screen.

---

## ⚡ Quick Start

### Requirements

| Method | Requirements |
|---|---|
| **Docker** (recommended) | [Docker Desktop 4.x](https://www.docker.com/products/docker-desktop/) or Docker Engine + Compose v2 |
| **Native** | Python 3.10+, Node.js 18+, [ffmpeg](https://ffmpeg.org/download.html) |

> [!NOTE]
> On first run the Docker build downloads ~600 MB of ML model weights. Subsequent
> starts reuse the cached `cove_models` volume and are much faster.

---

### 🐳 Docker — any platform (recommended)

```bash
git clone <this-repo-url>
cd Major-Project
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
- Auto-detect an NVIDIA GPU and set `VISION_FORCE_CPU` accordingly
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
| `frontend`   | React SPA + nginx (reverse-proxies `/api/cove` to `cove-api`) | **8080** | `major-project-frontend-1` |
| `cove-api`   | FastAPI backend — face detection, CLIP search, indexing jobs | 8000 | `major-project-cove-api-1` |
| `cove-ui`    | Streamlit UI for the same photo backend (alternate/dev UI)    | 8501 | `major-project-cove-ui-1`  |
| `video-api`  | FastAPI backend for video indexing/search                    | 8001 | `major-project-video-api-1`|
| `video-ui`   | Streamlit UI for video features                               | **8502** | `major-project-video-ui-1` |

**The app you actually use day-to-day is `http://localhost:8080`.** Clicking
"Videos" in its sidebar opens the `video-ui` Streamlit screen (port 8502) in a
new tab — video features aren't (yet) embedded in the React app itself.

## Prerequisites

- Docker Engine + Docker Compose v2 (`docker compose version` should work)
- ~5 GB free disk (Python/ML base images + model weights)
- Internet access on first run (to download CLIP/InsightFace model weights)

## 1. Clone and build

```bash
git clone <this-repo-url>
cd Major-Project
docker compose build
```

This builds three images: `backend` (shared by `cove-api`/`cove-ui`/`video-api`/`video-ui`)
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
`VISION_SKIP_MODEL_LOAD` is set, or if the face/CLIP models below haven't been
downloaded yet).

## 3. First-time model & data setup

Model weights are **not** baked into the image (they're large binaries — see
`.gitignore`) and live in the persistent `cove_models` Docker volume, so they
only need downloading once, the first time you stand the stack up.

```bash
docker compose exec cove-api sh -c "cd /app/cove && python3 pipeline/download_models.py"
```

This fetches the CLIP ONNX models (~600 MB) into the shared `cove_models`
volume. The InsightFace face-detection model (`buffalo_s`, ~130 MB) downloads
automatically into the same volume at `cove-api` startup.

`video-api` downloads its own models (InsightFace `buffalo_l` + a CLIP model
via HuggingFace `transformers`) automatically on first use — no manual step,
but expect the *first* video indexing request to be slow while it fetches
them. They're cached in the `video_hf_cache`/`video_insightface_cache`
volumes, so recreating the container won't force a re-download.

### Add photos to the library

Photos live in `cove/test_images/` (bind-mounted into `cove-api`/`cove-ui`, so
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
| **Videos** | Opens the separate `video-ui` screen (port 8502) in a new tab |
| **Settings** | Real system stats (GPU/CPU, photos indexed, people detected), theme |

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
docker compose build cove-api cove-ui video-api video-ui
docker compose up -d cove-api cove-ui video-api video-ui

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
  (still downloading) or `VISION_SKIP_MODEL_LOAD` is set — see step 3.
- **Permission denied writing into `cove/test_images/`**: the directory can
  end up root-owned since it's created by the container; fix from the host
  with `docker compose exec -u root cove-api chown -R $(id -u):$(id -g) /app/cove/test_images`.
- **Search/People return empty after adding photos**: indexing hasn't run yet
  — check the **Indexing** tab or `GET /index/status`.
- **Port already in use**: another process is bound to 8000/8080/8501/8502/8001
  on the host; stop it or edit the `ports:` mappings in `docker-compose.yml`.

## Project structure

```
cove/            Photo backend — FastAPI API, engines (face/CLIP/cluster),
                  pipeline scripts, Streamlit UI, tests. See cove/RUNNING.md.
videoModules/     Video backend — FastAPI API + Streamlit UI, own SQLite DB.
frontend/         React (Vite) SPA — Library/People/Search/Indexing/Settings.
nginx.conf        Reverse proxy config baked into the frontend image.
docker-compose.yml Orchestrates all five services + persistent volumes.
Dockerfile        Multi-stage build: frontend (nginx) + backend (Python/ML).
```
