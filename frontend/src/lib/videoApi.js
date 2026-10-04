/**
 * Video API — real client for the Cove video FastAPI backend
 * (videoModules/api.py). Reached via the nginx (or Vite dev) reverse proxy
 * at /api/video, so no base-URL env var or CORS setup is needed.
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
const BASE = isTauri ? 'http://127.0.0.1:8001' : '/api/video';

function streamUrl(path) {
  return `${BASE}/stream/${encodeURIComponent(path.split(/[\\/]/).pop())}`;
}

export function faceThumbnailUrl(thumb) {
  if (!thumb) return null;
  if (thumb.startsWith('http') || thumb.startsWith('/')) return thumb;
  return `${BASE}/faces/${encodeURIComponent(thumb)}`;
}

function videoThumbnailUrl(filename) {
  const baseName = filename.substring(0, filename.lastIndexOf('.')) || filename;
  return `${BASE}/thumbnails/${encodeURIComponent(baseName)}.jpg`;
}

function mapVideo(v) {
  const filename = v.path.split(/[\\/]/).pop();
  const thumbUrl = videoThumbnailUrl(filename);
  const sUrl = streamUrl(v.path);
  return {
    id: v.id ?? v.path,
    type: 'video',
    mediaType: 'video',
    path: v.path,
    src: sUrl,
    thumb: thumbUrl,
    thumbnail: thumbUrl,
    title: filename,
    label: v.label,
    tags: v.label ? v.label.split(',').map((s) => s.trim()).filter(Boolean) : [],
    date: v.created_at ? v.created_at.split(' ')[0] : 'Recent',
    score: v.score ?? v.similarity,
    similarity: v.score ?? v.similarity,
  };
}

/** Fetch all indexed videos */
export async function fetchVideos() {
  const res = await fetch(`${BASE}/videos`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  const data = await res.json();
  const rawList = (data.videos || []).map(mapVideo);
  
  const seen = new Set();
  const unique = [];
  for (const v of rawList) {
    const key = v.title || v.path;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(v);
    }
  }
  return unique;
}

/** Upload and index new videos (with real-time progress tracking) */
export async function uploadVideos(fileList, onProgress) {
  const files = Array.from(fileList);
  const totalBytes = files.reduce((acc, f) => acc + f.size, 0);
  const loadedPerFile = new Array(files.length).fill(0);
  let succeeded = 0;

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (onProgress) {
      onProgress({
        fileIndex: i + 1,
        totalFiles: files.length,
        fileName: file.name,
        percent: totalBytes > 0 ? (loadedPerFile.reduce((a, b) => a + b, 0) / totalBytes) * 100 : ((i) / files.length) * 100,
        loaded: loadedPerFile.reduce((a, b) => a + b, 0),
        total: totalBytes,
      });
    }

    await new Promise((resolve) => {
      const form = new FormData();
      form.append('file', file);
      form.append('batch_total', String(files.length));
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BASE}/index-video`);

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          loadedPerFile[i] = e.loaded;
          const currentTotalLoaded = loadedPerFile.reduce((a, b) => a + b, 0);
          if (onProgress) {
            onProgress({
              fileIndex: i + 1,
              totalFiles: files.length,
              fileName: file.name,
              percent: totalBytes > 0 ? (currentTotalLoaded / totalBytes) * 100 : 50,
              loaded: currentTotalLoaded,
              total: totalBytes,
            });
          }
        }
      });

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          succeeded++;
        }
        loadedPerFile[i] = file.size;
        resolve();
      };
      xhr.onerror = () => {
        loadedPerFile[i] = file.size;
        resolve();
      };
      xhr.send(form);
    });
  }

  if (onProgress) {
    onProgress({
      fileIndex: files.length,
      totalFiles: files.length,
      fileName: 'Complete',
      percent: 100,
      loaded: totalBytes,
      total: totalBytes,
    });
  }

  return { count: succeeded, total: files.length };
}

/** Fetch all recognized persons across videos */
export async function fetchAllVideoPersons() {
  const res = await fetch(`${BASE}/all-persons`);
  if (!res.ok) throw new Error('Failed to fetch video persons');
  const data = await res.json();
  return (data.persons || []).map((p) => ({
    id: `video_${p.id}`,
    sourceId: p.id,
    sourceType: 'video',
    name: p.name || `Person #${p.id}`,
    count: p.count || 1,
    thumbnail: faceThumbnailUrl(p.thumbnail),
  }));
}

/** Fetch all video paths linked to a given person ID */
export async function fetchPersonVideos(personId) {
  const cleanId = String(personId).replace(/^video_/, '');
  const res = await fetch(`${BASE}/person-videos/${cleanId}`);
  if (!res.ok) throw new Error('Failed to fetch person videos');
  const data = await res.json();
  return (data.videos || []).map((v) => v.path);
}

/** Rename a video person */
export async function renameVideoPerson(personId, newName) {
  const cleanId = String(personId).replace(/^video_/, '');
  const res = await fetch(`${BASE}/name-person/${cleanId}?name=${encodeURIComponent(newName)}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to rename person');
  return res.json();
}

/** Perform semantic search over indexed videos */
export async function searchVideos(query, threshold = 0.20) {
  if (!query?.trim()) return [];
  const res = await fetch(`${BASE}/search?query=${encodeURIComponent(query)}&threshold=${threshold}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Search failed');
  const data = await res.json();
  return (data.results || []).map(mapVideo);
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

/** Delete selected videos by IDs or paths */
export async function deleteVideos(videoIdsOrPaths) {
  if (!videoIdsOrPaths) return { deleted: 0 };
  
  let videoIds = [];
  let paths = [];

  if (Array.isArray(videoIdsOrPaths)) {
    for (const item of videoIdsOrPaths) {
      if (typeof item === 'number' || /^\d+$/.test(String(item))) {
        videoIds.push(Number(item));
      } else {
        paths.push(String(item));
      }
    }
  } else if (typeof videoIdsOrPaths === 'object') {
    if (Array.isArray(videoIdsOrPaths.videoIds || videoIdsOrPaths.video_ids)) {
      videoIds = (videoIdsOrPaths.videoIds || videoIdsOrPaths.video_ids).map(Number);
    }
    if (Array.isArray(videoIdsOrPaths.paths)) {
      paths = videoIdsOrPaths.paths.map(String);
    }
  } else if (typeof videoIdsOrPaths === 'number' || /^\d+$/.test(String(videoIdsOrPaths))) {
    videoIds.push(Number(videoIdsOrPaths));
  } else {
    paths.push(String(videoIdsOrPaths));
  }

  const res = await fetch(`${BASE}/videos/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_ids: videoIds, paths }),
  });
  if (!res.ok) throw new Error('Failed to delete videos');
  return res.json();
}

/** Delete a single video by ID or path */
export async function deleteSingleVideo(videoIdOrPath) {
  return deleteVideos([videoIdOrPath]);
}

/** Trigger video re-indexing across all videos in uploaded_videos */
export async function startVideoIndexing() {
  const res = await fetch(`${BASE}/reindex-all`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to start video indexing');
  return res.json();
}

/** Trigger face clustering for videos */
export async function startVideoClustering() {
  const res = await fetch(`${BASE}/cluster-faces`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to start video face clustering');
  return res.json();
}

/** Get video job progress */
export async function getVideoJobStatus() {
  const res = await fetch(`${BASE}/job-status`);
  if (!res.ok) throw new Error('Failed to fetch video job status');
  return res.json();
}
