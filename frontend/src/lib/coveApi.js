/**
 * Cove API — real client for the VisionArchive FastAPI backend.
 * Reached via the nginx (or Vite dev) reverse proxy at /api/cove, so no
 * base-URL env var or CORS setup is needed.
 */
const isTauri = typeof window !== 'undefined' && Boolean(
  window.__TAURI__ ||
  window.__TAURI_INTERNALS__ ||
  window.location.protocol === 'tauri:' ||
  window.location.hostname === 'tauri.localhost' ||
  window.location.origin.includes('tauri') ||
  (window.location.protocol === 'http:' && !window.location.port) ||
  (window.location.protocol === 'https:' && !window.location.port)
);
const BASE = isTauri ? 'http://127.0.0.1:8005/api/cove' : '/api/cove';

function mediaUrl(path) {
  return `${BASE}/media/${path}`;
}

function mtimeToDate(mtime) {
  if (!mtime) return undefined;
  return new Date(mtime * 1000).toISOString().split('T')[0];
}

/** Fetch paginated images from the library */
export async function fetchImages(page = 0, pageSize = 1000) {
  const res = await fetch(`${BASE}/images?offset=${page * pageSize}&limit=${pageSize}`);
  if (!res.ok) throw new Error('Failed to fetch images');
  const data = await res.json();
  return data.images.map((img) => ({
    id: img.path,
    path: img.path,
    src: mediaUrl(img.path),
    thumbnail: mediaUrl(img.path),
    date: mtimeToDate(img.mtime),
    tags: [],
  }));
}

/** Fetch face clusters (people) */
export async function fetchClusters(offset = 0, limit = 200) {
  const res = await fetch(`${BASE}/people?offset=${offset}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch people');
  const data = await res.json();
  const rawPeople = data.people ?? [];
  const people = rawPeople.map((p) => {
    const thumbPath = p.preview_photo || (p.photos && p.photos[0]);
    const thumbUrl = thumbPath ? mediaUrl(thumbPath) : undefined;
    return {
      id: p.id,
      name: p.name,
      thumbnail: thumbUrl,
      previewUrl: thumbUrl,
      count: p.photo_count ?? (p.photos ? p.photos.length : 0),
      imageCount: p.photo_count ?? (p.photos ? p.photos.length : 0),
      confidence: 1,
    };
  });
  return {
    total: data.total ?? people.length,
    people,
  };
}

/** Fetch live photo paths for a specific person cluster */
export async function fetchPersonPhotos(personId, offset = 0, limit = 1000) {
  const res = await fetch(`${BASE}/people/${personId}/photos?offset=${offset}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch person photos');
  const data = await res.json();
  return {
    total: data.total ?? 0,
    photos: data.photos ?? [],
  };
}

/** Rename a person in the backend database */
export async function renamePerson(personId, newName) {
  const res = await fetch(`${BASE}/people/${personId}/rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
  });
  if (!res.ok) throw new Error('Failed to rename person');
  return res.json();
}

/** Perform semantic search using CLIP embeddings */
export async function searchImages(query, limit = 40) {
  if (!query?.trim()) return [];
  const res = await fetch(`${BASE}/search/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: query, limit, threshold: 0.01 }),
  });
  if (!res.ok) throw new Error('Search failed');
  const data = await res.json();
  return data.results.map((r) => ({
    id: r.path,
    path: r.path,
    src: mediaUrl(r.path),
    thumbnail: mediaUrl(r.path),
    tags: [],
    score: r.score,
  }));
}

/** Get current indexing job status */
export async function getIndexingStatus() {
  const res = await fetch(`${BASE}/index/status`);
  if (!res.ok) throw new Error('Failed to fetch indexing status');
  const data = await res.json();
  return {
    isIndexing: data.status === 'running',
    status: data.status,
    stage: data.stage,
    progress: data.progress,
    processed: data.processed,
    total: data.total,
    message: data.message,
  };
}

/** Trigger a full indexing run (scan -> detect -> embed -> cluster) */
export async function startIndexing() {
  const res = await fetch(`${BASE}/index/start`, { method: 'POST' });
  return res.json();
}

/** Permanently delete images (removes the file, embeddings, and people-DB references) */
export async function deleteImages(paths) {
  const res = await fetch(`${BASE}/images/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paths }),
  });
  if (!res.ok) throw new Error('Delete failed');
  return res.json();
}

/** Upload new images into the library with real-time per-file progress */
export async function uploadImages(fileList, onProgress) {
  const files = Array.from(fileList);
  const totalFiles = files.length;
  const totalBytes = files.reduce((acc, f) => acc + f.size, 0);

  const BATCH_SIZE = 50; // Keep batches under Starlette max_files limit
  let processedFiles = 0;
  let loadedBytesSoFar = 0;
  let totalSaved = [];
  let indexingStarted = false;

  for (let i = 0; i < files.length; i += BATCH_SIZE) {
    const chunk = files.slice(i, i + BATCH_SIZE);
    const chunkBytes = chunk.reduce((acc, f) => acc + f.size, 0);
    const form = new FormData();
    chunk.forEach((file) => form.append('files', file));

    await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BASE}/upload`);

      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const currentTotalLoaded = loadedBytesSoFar + e.loaded;
            const percent = totalBytes > 0 ? (currentTotalLoaded / totalBytes) * 100 : 50;
            const currentFileIdx = Math.min(
              totalFiles,
              Math.max(1, Math.round((currentTotalLoaded / totalBytes) * totalFiles))
            );
            onProgress({
              percent: Math.min(99, percent),
              loaded: currentTotalLoaded,
              total: totalBytes,
              fileIndex: currentFileIdx,
              totalFiles,
              fileName: chunk[0]?.name || '',
            });
          }
        });
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            if (data.saved) totalSaved.push(...data.saved);
            if (data.indexing_started) indexingStarted = true;
          } catch {
            // fallback
          }
          loadedBytesSoFar += chunkBytes;
          processedFiles += chunk.length;
          resolve();
        } else {
          reject(new Error(`Upload failed (${xhr.status}): ${xhr.responseText || 'Server error'}`));
        }
      };

      xhr.onerror = () => reject(new Error('Network connection to backend failed (check 127.0.0.1:8000)'));
      xhr.send(form);
    });
  }

  if (onProgress) {
    onProgress({
      percent: 100,
      loaded: totalBytes,
      total: totalBytes,
      fileIndex: totalFiles,
      totalFiles,
      fileName: files[files.length - 1]?.name || '',
    });
  }

  return { saved: totalSaved, count: totalSaved.length, indexing_started: indexingStarted };
}

/** Real system stats (GPU availability, worker pool, library size) — no fabricated metrics */
export async function getSystemStats() {
  const [health, imagesPage, people] = await Promise.all([
    fetch(`${BASE}/health`).then((r) => r.json()),
    fetch(`${BASE}/images?limit=1`).then((r) => r.json()),
    fetchClusters(0, 1),   // just fetch 1 person to get total count cheaply
  ]);
  return {
    gpuAvailable: !!health?.models?.gpu_enabled,
    poolSize: health?.models?.pool_size ?? 0,
    totalImages: imagesPage?.total ?? 0,
    totalPeople: people.total ?? 0,
  };
}
