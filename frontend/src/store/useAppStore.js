/**
 * Global application state managed with Zustand.
 * Sliced state structure with optimized setters to prevent unnecessary rerenders.
 */
import { create } from 'zustand';

export const useAppStore = create((set, get) => ({
  images: [],
  videos: [],
  clusters: [],
  searchResults: [],
  searchQuery: '',
  sidebarCollapsed: false,
  selectedImages: new Set(),
  activeView: 'library',
  activeMediaModal: null, // { type: 'photo' | 'video', item: Object } | null
  selectedPersonFilter: null, // { id: string, name: string } | null
  libraryFilter: 'all', // 'all' | 'photos' | 'videos'
  theme: 'dark',

  indexingStatus: {
    isIndexing: false,
    stage: 'idle',
    progress: 0,
    processed: 0,
    total: 0,
  },
  videoIndexingStatus: {
    status: 'idle',
    current: 0,
    total: 0,
    message: '',
  },
  uploadState: {
    isUploading: false,
    isCompleted: false,
    totalFiles: 0,
    currentFileIndex: 0,
    fileName: '',
    mediaType: 'photo', // 'photo' | 'video'
    progress: 0,
    bytesUploaded: 0,
    totalBytes: 0,
    error: null,
  },
  systemStats: {
    gpuAvailable: false,
    poolSize: 0,
    totalImages: 0,
    totalPeople: 0,
  },

  setVideoIndexingStatus: (videoIndexingStatus) => set({ videoIndexingStatus }),

  // --- Upload State Management ---
  setUploadState: (partial) =>
    set((s) => ({ uploadState: { ...s.uploadState, ...partial } })),
  resetUploadState: () =>
    set({
      uploadState: {
        isUploading: false,
        isCompleted: false,
        totalFiles: 0,
        currentFileIndex: 0,
        fileName: '',
        mediaType: 'photo',
        progress: 0,
        bytesUploaded: 0,
        totalBytes: 0,
        error: null,
      },
    }),

  // --- Core Actions ---
  setImages: (images) => set({ images }),
  setVideos: (videos) => set({ videos }),
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
    const { images, videos, libraryFilter } = get();
    let allItems = [];
    if (libraryFilter === 'photos') allItems = images;
    else if (libraryFilter === 'videos') allItems = videos;
    else allItems = [...images, ...videos];

    const startIdx = allItems.findIndex((item) => (item.id ?? item.path) === startId);
    const endIdx = allItems.findIndex((item) => (item.id ?? item.path) === endId);
    if (startIdx === -1 || endIdx === -1) return;
    const [lo, hi] = [Math.min(startIdx, endIdx), Math.max(startIdx, endIdx)];
    const selected = new Set(allItems.slice(lo, hi + 1).map((item) => item.id ?? item.path));
    set({ selectedImages: selected });
  },
  selectAllImages: () => {
    const { images, videos, libraryFilter } = get();
    let allItems = [];
    if (libraryFilter === 'photos') allItems = images;
    else if (libraryFilter === 'videos') allItems = videos;
    else allItems = [...images, ...videos];

    set({ selectedImages: new Set(allItems.map((item) => item.id ?? item.path)) });
  },
  clearSelection: () => set({ selectedImages: new Set() }),

  setLibraryFilter: (filter) => set({ libraryFilter: filter }),

  deleteSelectedImages: () => {
    const { images, selectedImages } = get();
    const remaining = images.filter((img) => !selectedImages.has(img.id));
    set({ images: remaining, selectedImages: new Set() });
  },

  removeVideoById: (id) => {
    const { videos } = get();
    set({ videos: videos.filter((v) => v.id !== id && v.path !== id) });
  },

  deleteSelectedMedia: (deletedImageIds = new Set(), deletedVideoIds = new Set()) => {
    const { images, videos, selectedImages } = get();
    const remainingImages = images.filter((img) => !deletedImageIds.has(img.id) && !deletedImageIds.has(img.path));
    const remainingVideos = videos.filter((vid) => !deletedVideoIds.has(vid.id) && !deletedVideoIds.has(vid.path));
    const nextSelected = new Set(selectedImages);
    deletedImageIds.forEach((id) => nextSelected.delete(id));
    deletedVideoIds.forEach((id) => nextSelected.delete(id));
    set({ images: remainingImages, videos: remainingVideos, selectedImages: nextSelected });
  },

  // --- Media Lightbox Modal ---
  openMediaModal: (type, item) => set({ activeMediaModal: { type, item } }),
  closeMediaModal: () => set({ activeMediaModal: null }),

  // --- Person Filter ---
  setPersonFilter: (person) => set({ selectedPersonFilter: person, activeView: 'library' }),

  // --- Theme Management ---
  setTheme: (theme) => {
    set({ theme });
    if (theme === 'light') {
      document.documentElement.classList.add('light-theme', 'light');
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.remove('light-theme', 'light');
      document.documentElement.classList.add('dark');
    }
  },
  toggleTheme: () => {
    const nextTheme = get().theme === 'dark' ? 'light' : 'dark';
    get().setTheme(nextTheme);
  },

  // --- Indexing & System Status ---
  // Accepts a plain object (partial update). Do NOT pass a function here.
  setIndexingStatus: (partialStatus) =>
    set((s) => ({
      indexingStatus: {
        ...s.indexingStatus,
        ...partialStatus,
        isIndexing: partialStatus.status ? partialStatus.status === 'running' : (partialStatus.isIndexing ?? s.indexingStatus.isIndexing),
      },
    })),
  setSystemStats: (partialStats) =>
    set((s) => ({ systemStats: { ...s.systemStats, ...partialStats } })),
}));
