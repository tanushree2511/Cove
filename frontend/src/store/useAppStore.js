/**
 * Global application state managed with Zustand.
 * Sliced state structure with optimized setters to prevent unnecessary rerenders.
 */
import { create } from 'zustand';

export const useAppStore = create((set, get) => ({
  images: [],
  clusters: [],
  searchResults: [],
  searchQuery: '',
  sidebarCollapsed: false,
  selectedImages: new Set(),
  activeView: 'library',
  activeMediaModal: null, // { type: 'photo' | 'video', item: Object } | null
  selectedPersonFilter: null, // { id: string, name: string } | null
  theme: 'dark',

  indexingStatus: {
    isIndexing: false,
    stage: 'idle',
    progress: 0,
    processed: 0,
    total: 0,
  },
  hardwareInfo: {
    cpuUsage: 34,
    gpuUsage: 67,
    gpuAvailable: true,
  },

  // --- Core Actions ---
  setImages: (images) => set({ images }),
  setClusters: (clusters) => set({ clusters }),
  setSearchResults: (results) => set({ searchResults: results }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setActiveView: (view) => set({ activeView: view }),

  // --- Selection Management ---
  selectImage: (id) => set({ selectedImages: new Set([id]) }),
  toggleImageSelection: (id) => {
    const selected = new Set(get().selectedImages);
    if (selected.has(id)) {
      selected.delete(id);
    } else {
      selected.add(id);
    }
    set({ selectedImages: selected });
  },
  selectRange: (startId, endId) => {
    const { images } = get();
    const startIdx = images.findIndex((img) => img.id === startId);
    const endIdx = images.findIndex((img) => img.id === endId);
    if (startIdx === -1 || endIdx === -1) return;
    const [lo, hi] = [Math.min(startIdx, endIdx), Math.max(startIdx, endIdx)];
    const selected = new Set(images.slice(lo, hi + 1).map((img) => img.id));
    set({ selectedImages: selected });
  },
  selectAllImages: () => {
    const { images } = get();
    set({ selectedImages: new Set(images.map((img) => img.id)) });
  },
  clearSelection: () => set({ selectedImages: new Set() }),

  deleteSelectedImages: () => {
    const { images, selectedImages } = get();
    const remaining = images.filter((img) => !selectedImages.has(img.id));
    set({ images: remaining, selectedImages: new Set() });
  },

  // --- Media Lightbox Modal ---
  openMediaModal: (type, item) => set({ activeMediaModal: { type, item } }),
  closeMediaModal: () => set({ activeMediaModal: null }),

  // --- Person Filter ---
  setPersonFilter: (person) => set({ selectedPersonFilter: person, activeView: 'library' }),

  // --- File Import ---
  importFiles: (fileList) => {
    const newImages = Array.from(fileList).map((file, idx) => {
      const seed = Date.now() + idx;
      return {
        id: `imported-${seed}`,
        src: URL.createObjectURL(file),
        thumbnail: URL.createObjectURL(file),
        width: 1920,
        height: 1080,
        date: new Date().toISOString().split('T')[0],
        tags: ['imported', file.type.startsWith('video') ? 'video' : 'photo'],
        title: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      };
    });
    set((s) => ({ images: [...newImages, ...s.images] }));
    return newImages.length;
  },

  // --- Theme Management ---
  setTheme: (theme) => {
    set({ theme });
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme');
    } else {
      document.documentElement.classList.remove('light-theme');
    }
  },
  toggleTheme: () => {
    const nextTheme = get().theme === 'dark' ? 'light' : 'dark';
    get().setTheme(nextTheme);
  },

  // --- Indexing & Hardware Status ---
  // Accepts a plain object (partial update). Do NOT pass a function here.
  setIndexingStatus: (partialStatus) =>
    set((s) => ({ indexingStatus: { ...s.indexingStatus, ...partialStatus } })),
  setHardwareInfo: (partialInfo) =>
    set((s) => ({ hardwareInfo: { ...s.hardwareInfo, ...partialInfo } })),
}));
