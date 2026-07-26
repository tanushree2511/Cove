/**
 * Mock API — Simulates a local AI photo backend.
 * Uses seeded deterministic data for reproducible renders.
 */

const TAGS      = ['nature', 'portrait', 'city', 'beach', 'mountain', 'sunset', 'food', 'travel', 'architecture', 'animal'];
const DATES     = ['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-18', '2024-06-22', '2024-07-30', '2024-08-14', '2024-09-03', '2024-10-25', '2024-11-11', '2024-12-01'];
const CAMERAS   = ['Sony α7 IV', 'Canon EOS R5', 'Fujifilm X-T5', 'Nikon Z8', 'iPhone 15 Pro Max'];
const LENSES    = ['24-70mm f/2.8 GM II', '50mm f/1.2 L USM', '35mm f/1.4 WR', '85mm f/1.4 DG DN', '24mm f/1.8 G'];
const LOCATIONS = ['Kyoto, Japan', 'Swiss Alps', 'Big Sur, California', 'Santorini, Greece', 'Reykjavik, Iceland', 'New York City, USA'];
const NAMES     = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry', 'Iris', 'Jack', 'Karen', 'Leo'];

function generateMockImages(count) {
  return Array.from({ length: count }, (_, i) => {
    const seed = i + 1;
    const w    = 300 + (i % 5) * 50;
    const h    = 200 + (i % 4) * 50;
    return {
      id:          `img-${seed}`,
      src:         `https://picsum.photos/seed/${seed}/${w * 4}/${h * 4}`,
      thumbnail:   `https://picsum.photos/seed/${seed}/${w}/${h}`,
      width:       w * 4,
      height:      h * 4,
      date:        DATES[i % DATES.length],
      tags:        [TAGS[i % TAGS.length], TAGS[(i + 3) % TAGS.length]],
      camera:      CAMERAS[i % CAMERAS.length],
      lens:        LENSES[i % LENSES.length],
      location:    LOCATIONS[i % LOCATIONS.length],
      iso:         [100, 200, 400, 800, 1600][i % 5],
      aperture:    `f/${(1.4 + (i % 4) * 0.7).toFixed(1)}`,
      shutter:     `1/${125 * (i % 8 + 1)}s`,
      focalLength: `${24 + (i % 5) * 20}mm`,
    };
  });
}

function generateMockClusters(count) {
  return Array.from({ length: count }, (_, i) => ({
    id:          `cluster-${i + 1}`,
    name:        NAMES[i % NAMES.length],
    previewUrl:  `https://i.pravatar.cc/150?img=${(i % 70) + 1}`,
    // Deterministic count & confidence — no Math.random() to avoid hydration issues
    imageCount:  50 + (i * 37) % 450,
    confidence:  Math.round((0.7 + (i * 0.03) % 0.3) * 100) / 100,
    faces:       Array.from({ length: 5 + (i % 15) }, (_, j) => `img-${i * 20 + j + 1}`),
  }));
}

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Fetch paginated images */
export async function fetchImages(page = 0, pageSize = 200) {
  await delay(200);
  const all = generateMockImages(1000);
  return all.slice(page * pageSize, (page + 1) * pageSize);
}

/** Fetch face clusters */
export async function fetchClusters() {
  await delay(250);
  return generateMockClusters(12);
}

/** Perform semantic search using CLIP embeddings (simulated) */
export async function searchImages(query) {
  await delay(350);
  if (!query?.trim()) return [];

  const all     = generateMockImages(1000);
  const qLower  = query.toLowerCase();
  const filtered = all.filter(
    (img) =>
      img.tags.some((t) => t.includes(qLower)) ||
      img.location.toLowerCase().includes(qLower) ||
      img.camera.toLowerCase().includes(qLower)
  );

  // If no exact match, return a deterministic semantic subset
  if (filtered.length > 0) return filtered;

  // Fallback: return 24 items deterministically (no random sort)
  return all.slice(0, 24);
}

/** Get current indexing status */
export async function getIndexingStatus() {
  await delay(100);
  return {
    isIndexing: true,
    stage:      'embedding',
    progress:   67,
    processed:  67432,
    total:      100000,
  };
}
