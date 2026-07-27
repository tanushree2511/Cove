/**
 * Cove API — real client for the VisionArchive FastAPI backend.
 * Reached via the nginx (or Vite dev) reverse proxy at /api/cove, so no
 * base-URL env var or CORS setup is needed.
 */
const BASE = '/api/cove';

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
export async function fetchClusters() {
  const res = await fetch(`${BASE}/people`);
  if (!res.ok) throw new Error('Failed to fetch people');
  const data = await res.json();
  return data.people.map((p) => ({
    id: p.id,
    name: p.name,
    previewUrl: p.photos[0] ? mediaUrl(p.photos[0]) : undefined,
    imageCount: p.photo_count,
    confidence: 1,
    photos: p.photos,
  }));
}

/** Perform semantic search using CLIP embeddings */
export async function searchImages(query, limit = 40) {
  if (!query?.trim()) return [];
  const res = await fetch(`${BASE}/search/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: query, limit }),
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

/** Rename a clustered person */
export async function renamePerson(personId, name) {
  const res = await fetch(`${BASE}/people/${personId}/rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
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

/** Upload new images into the library (auto-triggers indexing) */
export async function uploadImages(fileList) {
  const form = new FormData();
  Array.from(fileList).forEach((file) => form.append('files', file));
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

/** Real system stats (GPU availability, worker pool, library size) — no fabricated metrics */
export async function getSystemStats() {
  const [health, imagesPage, people] = await Promise.all([
    fetch(`${BASE}/health`).then((r) => r.json()),
    fetch(`${BASE}/images?limit=1`).then((r) => r.json()),
    fetchClusters(),
  ]);
  return {
    gpuAvailable: !!health?.models?.gpu_enabled,
    poolSize: health?.models?.pool_size ?? 0,
    totalImages: imagesPage?.total ?? 0,
    totalPeople: people.length,
  };
}
