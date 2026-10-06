# Configuration

All settings are environment variables; the defaults need no configuration. Legacy `VISION_*` names are accepted
as aliases for `COVE_*`.

## Runtime and hardware

| Variable | Default | Effect |
|---|---|---|
| `COVE_FORCE_CPU` | off | Ignore all accelerators. |
| `COVE_AUTOTUNE` | on | `0` skips the start-up benchmark and uses defaults. |
| `COVE_CPU_MODE` | auto | CPU threading strategy override. |
| `COVE_USE_GPU` / `COVE_USE_IGPU` | auto | Force/forbid discrete / integrated GPU use. |
| `COVE_ENABLE_TRT` | off | Allow the TensorRT execution provider. |
| `COVE_ORT_THREADS` | auto | ONNX Runtime intra-op threads. |
| `COVE_AI_WORKERS` | auto | Parallel face-model replicas. |
| `COVE_BATCH_SIZE` | auto | CLIP image batch size. |
| `COVE_VIDEO_BUDGET_S` | ~2 | Compute budget (s) per video for CLIP frames. |
| `COVE_BENCH_ROUNDS`, `COVE_BENCH_BUDGET_S` | internal | Start-up benchmark length. |
| `COVE_ORT_PACKAGE` | auto | pip package `scripts/install_runtime.py` installs (`onnxruntime-gpu`, `-directml`, `-openvino`, `-qnn`, or plain). |
| `COVE_SKIP_RUNTIME_INSTALL` | off | Don't swap the ORT package at install. |
| `OMP_NUM_THREADS`, `OMP_WAIT_POLICY` | physical cores, `PASSIVE` | Set by default for numpy/FAISS/OpenCV. |

## Models

| Variable | Default | Effect |
|---|---|---|
| `COVE_CLIP_MODEL` | `b16` | `b32` keeps a legacy `clip_image.onnx` / `clip_text.onnx` pair. Changing models triggers an automatic index rebuild. |
| `COVE_MODEL_DIR` | auto | Model directory. |
| `COVE_DET_SIZE` | default | Face detector input size. |
| `COVE_SKIP_MODEL_LOAD` | off | Start without loading models (health = `degraded`; for tests). |

## Server and paths

| Variable | Default | Effect |
|---|---|---|
| `COVE_HOST` / `COVE_PORT` | `127.0.0.1` / `8000` | Bind address and port (the video backend uses its own port). |
| `COVE_API_KEY` | unset | Require `x-api-key` on photo-API requests. |
| `COVE_USER_DATA` | OS user-data dir | Where indexes, DBs and logs live. |
| `COVE_ROOT` | repo root | Project root. |
| `COVE_LOG_LEVEL`, `COVE_LOG_FILE` | `INFO`, `cove.log` | Logging. |
| `COVE_IMAGE_VECTOR_PATH`, `COVE_FAISS_INDEX`, `COVE_FAISS_SEARCH_INDEX`, `COVE_PEOPLE_DB_PATH`, `COVE_PATHS_FILE`, `COVE_EMBEDDINGS_FILE`, `COVE_IMAGE_CACHE` | file names in the data dir | Override individual storage files. |
| `VIDEO_CODECS` | browser-safe set | Codecs treated as playable without transcoding. |
| `COVE_LFW_SOURCE`, `COVE_LFW_FORCE_REFRESH` | – | Control `prepare_lfw.py` dataset download. |

## Where to look

`cove/config/vision_config.py` (paths/models), `cove/config/hardware.py` and `runtime.py` (hardware),
`GET /hardware` (what was actually chosen).
