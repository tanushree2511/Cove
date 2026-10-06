# API reference

Two FastAPI services. Interactive OpenAPI docs are at `/docs` on each (`http://localhost:8000/docs`,
`http://localhost:8001/docs`). Through nginx or the Vite proxy they are prefixed `/api/cove` and `/api/video`.

## Photo API — port 8000

If `COVE_API_KEY` is set, every request needs the header `x-api-key: <key>` (401 otherwise).

| Method & path | Description |
|---|---|
| `GET /health` | `status` is `ok` or `degraded` (models not loaded / `COVE_SKIP_MODEL_LOAD`). |
| `GET /hardware` | Detected hardware, chosen ORT configuration, benchmark numbers. |
| `POST /upload` | Multipart upload of images into the library; starts indexing. |
| `POST /index/start` | Start the background indexing job (incremental). |
| `GET /index/status` | Progress of the current/last indexing job. |
| `POST /index/image` | Index one file. Body: `{"file_path": "..."}`. |
| `GET /images` | List indexed images (path, mtime, people). |
| `POST /images/delete` | Delete images. Body: `{"paths": ["..."]}`. |
| `POST /search/text` | Semantic search. Body: `{"text": "a man in a suit", "limit": 40, "threshold": 0.20}` → `{"results": [{path, score, ...}]}`. 503 if search is unavailable, 422 if the query can't be encoded. |
| `GET /people` | Face clusters with thumbnails and counts. |
| `GET /people/{person_id}/photos` | Photos containing that person. |
| `POST /people/{person_id}/rename` | Body: `{"name": "..."}`. |
| `POST /people/cleanup` | Remove empty/stale person records. |
| `GET /media/test_images/{file}` | Static image files. |

Example:

```bash
curl -X POST http://localhost:8000/search/text \
  -H "Content-Type: application/json" \
  -d '{"text":"dog on a beach","limit":20}'
```

## Video API — port 8001

| Method & path | Description |
|---|---|
| `GET /health`, `GET /hardware` | Status and hardware report. |
| `POST /index-video` | Upload and index one video (frames → CLIP → labels → faces). |
| `POST /index-bulk` | Index many videos / a folder. |
| `POST /reindex-all` | Re-analyse stored videos (e.g. after a model change). |
| `POST /rebuild-index` | Rebuild the vector index from the database. |
| `POST /cluster-faces` | Re-cluster faces into persons. |
| `GET /job-status` | State of running jobs. |
| `POST /cancel-job/{job_type}` · `POST /clear-jobs` | Cancel / reset jobs. |
| `POST /search?query=...&threshold=...` | Text → video search (frame-level smooth-max scoring). Query parameters, not a JSON body. |
| `GET /videos` | List videos with labels. |
| `POST /videos/{video_id}/correct-label` | Record a user label correction. |
| `POST /videos/delete` · `DELETE /videos/{video_id}` · `DELETE /videos/delete-by-time` · `DELETE /videos/delete-all` | Deletion. |
| `POST /extract-audio` | Extract an audio track (ffmpeg). |
| `GET /all-persons` · `GET /face-gallery` · `GET /face-stats` | Face/person data. |
| `POST /name-person/{p_id}` · `GET /person-videos/{p_id}` | Name a person; videos they appear in. |
| `DELETE /remove-duplicates` · `DELETE /remove-blurred-faces` | Maintenance. |
| `GET /stream/{filename}` | Static video files. |

> Request/response bodies for the video API are defined in `videoModules/api.py`; consult `/docs` for exact schemas.
