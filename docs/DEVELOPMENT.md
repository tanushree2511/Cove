# Development guide

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt            # requirements-gpu.txt for NVIDIA
python scripts/install_runtime.py          # installs the right onnxruntime build for this machine
cd cove && python pipeline/download_models.py   # CLIP ViT-B/16 ONNX (~590 MB); buffalo_s downloads on first start
cd ../frontend && npm install
```

Requires Python 3.10+ (CI uses 3.11), Node 18+ (CI uses 20), and ffmpeg.

## Run

| Goal | Command |
|---|---|
| Everything (native) | `./start.sh` or `start.bat` → <http://localhost:8080> |
| Everything (Docker) | `docker compose up` (add `-f docker-compose.gpu.yml` for NVIDIA) |
| Photo API only | `cd cove && python backend_main.py` (port 8000) |
| Video API only | `cd videoModules && python video_main.py` (port 8001) |
| Frontend dev | `cd frontend && npm run dev` (proxies `/api/cove`→8000, `/api/video`→8001) |
| Desktop app dev | `cd frontend && npm run tauri dev` (needs Rust + built sidecars) |

Docker bakes `cove/`, `videoModules/` and `nginx.conf` into the image: rebuild after backend changes
(`docker compose build cove-api video-api && docker compose up -d`).

## Tests

```bash
cd cove && python -m pytest tests -q     # backend (also run in CI before every release build)
cd frontend && npm test                  # vitest
cd frontend && npm run lint
```

Notable suites: `test_hardware.py` and `test_cpu_parallelism.py` (hardware detection and thread budgeting,
simulated for NVIDIA/AMD/Apple/Intel/Qualcomm/DirectML/containers), `test_cluster_engine.py`,
`test_vector_storage.py`, `test_server*.py` (API), `test_transcode.py`, `test_indexing_efficiency.py`,
`test_frozen_benchmark.py`. `integration_live.py` / `test_live_server.py` need a running server and real models.

## Building the desktop installer

```bash
python scripts/build_backends.py     # downloads models into ./models and freezes both backends with PyInstaller
cd frontend && npm ci && npm run tauri build
```

`scripts/build_sidecars.py` produces `frontend/src-tauri/bin/{cove,video}-backend-<target-triple>[.exe]`.
The GitHub Actions workflow `.github/workflows/build-releases.yml` does this on `v*` tags (or manually) — currently
**Windows only**, using `onnxruntime-directml` so one build works on any DirectX 12 GPU, with CPU fallback.

## Evaluation and benchmarks

- `benchmarks/run_model_benchmarks.py` – compares CLIP/face model candidates.
- `evaluation/`, `datasets/` (COCO, LFW, MSR-VTT, UCF101) – local accuracy experiments; large and not committed.
- Reference results (see `TECHNICAL_REPORT.md` and README): COCO text→image Recall@1 51%, UCF101 tagging top-1 70%,
  MSR-VTT Recall@1 72% (50-video gallery), face clustering pairwise F1 0.993 on LFW.

## Conventions

- Backend modules use package-qualified imports (`from config.vision_config import CONFIG`); entry points add
  `cove/` to `sys.path`.
- Embeddings from different CLIP models are not comparable — anything that changes the model, prompts or
  preprocessing must invalidate stored vectors (see `PROMPT_VERSION` in `classifier.py`).
- Check the **licence** of any new model or dependency before adding it; the project is intended for open-source
  release (Apple MobileCLIP2 was rejected for this reason).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/api/cove/*` 502 | `cove-api` not up – `docker compose logs cove-api` or `.logs/`. |
| Health `degraded` | Models missing – run `download_models.py`. |
| Search/People empty | Indexing hasn't run – Indexing tab or `GET /index/status`. |
| Port 8000/8001/8080 busy | Stop the other process (the desktop app force-frees 8000/8001 on launch). |
| Slow indexing on CPU | Expected for ViT-B/16 (~4 img/s on a 4-core laptop); more threads don't help past core saturation. |
| Windows build prints garbled/crashes on emoji | Set `PYTHONUTF8=1`. |
