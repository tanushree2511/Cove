/**
 * Video API — real client for the VisionArchive video FastAPI backend
 * (videoModules/api.py). Reached via the nginx (or Vite dev) reverse proxy
 * at /api/video, so no base-URL env var or CORS setup is needed.
 */
const BASE = '/api/video';

function streamUrl(path) {
  return `${BASE}/stream/${encodeURIComponent(path.split(/[\\/]/).pop())}`;
}

function mapVideo(v) {
  const filename = v.path.split(/[\\/]/).pop();
  return {
    id: v.id ?? v.path,
    path: v.path,
    src: streamUrl(v.path),
    thumb: `${streamUrl(v.path)}#t=0.5`,
    title: filename,
    label: v.label,
    tags: v.label ? [v.label] : [],
    date: v.created_at ? v.created_at.split(' ')[0] : undefined,
  };
}

/** Fetch all indexed videos */
export async function fetchVideos() {
  const res = await fetch(`${BASE}/videos`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  const data = await res.json();
  return data.videos.map(mapVideo);
}

/** Upload and index new videos (backend indexes one file per request) */
export async function uploadVideos(fileList) {
  const files = Array.from(fileList);
  const results = await Promise.allSettled(
    files.map((file) => {
      const form = new FormData();
      form.append('file', file);
      return fetch(`${BASE}/index-video`, { method: 'POST', body: form }).then((res) => {
        if (!res.ok) throw new Error('Upload failed');
        return res.json();
      });
    })
  );
  const succeeded = results.filter((r) => r.status === 'fulfilled').length;
  return { count: succeeded, total: files.length };
}

/** Perform semantic search over indexed videos */
export async function searchVideos(query, threshold = 0.23) {
  if (!query?.trim()) return [];
  const res = await fetch(
    `${BASE}/search?${new URLSearchParams({ query, threshold })}`,
    { method: 'POST' }
  );
  if (!res.ok) throw new Error('Search failed');
  const data = await res.json();
  return data.results.map(mapVideo);
}

/** Extract the audio track for a video, returns a playable URL */
export async function extractAudio(videoPath) {
  const res = await fetch(
    `${BASE}/extract-audio?${new URLSearchParams({ video_path: videoPath })}`,
    { method: 'POST' }
  );
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return `${BASE}${data.audio_url}`;
}
