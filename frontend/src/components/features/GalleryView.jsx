/**
 * Virtualized unified media gallery - renders 100k+ photos and videos smoothly.
 * Responsive columns measured from the container, date headings, type filtering (All / Photos / Videos),
 * person filtering, and universal import.
 */
import { useEffect, useRef, useMemo, useCallback, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, Film, Image as ImageIcon } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchAllImages, uploadImages, fetchPersonPhotos } from '@/lib/coveApi';
import { fetchVideos, uploadVideos, fetchPersonVideos } from '@/lib/videoApi';
import { PhotoCard } from './PhotoCard';
import { toast } from 'sonner';

const GRID_GAP = 12;          // px between tiles, both directions
const HEADER_ROW_HEIGHT = 62; // date heading row

/** Derive column count and exact tile size from the scroll container's content width (padding excluded). */
function useGridDimensions(el) {
  const [dim, setDim] = useState({ columns: 5, itemHeight: 200 });

  useEffect(() => {
    if (!el) return;

    const calc = (contentWidth) => {
      let cols;
      if (contentWidth < 480)       cols = 2;
      else if (contentWidth < 700)  cols = 3;
      else if (contentWidth < 980)  cols = 4;
      else if (contentWidth < 1300) cols = 5;
      else if (contentWidth < 1700) cols = 6;
      else                          cols = 7;

      const width = Math.max(100, contentWidth);
      const itemWidth = Math.floor((width - GRID_GAP * (cols - 1)) / cols);
      setDim({ columns: cols, itemHeight: Math.max(80, itemWidth) });
    };

    // contentRect is the content box (padding already excluded), which is exactly the grid's width
    const ro = new ResizeObserver(([entry]) => calc(entry.contentRect.width));
    ro.observe(el);
    const cs = getComputedStyle(el);
    calc(el.clientWidth - parseFloat(cs.paddingLeft || 0) - parseFloat(cs.paddingRight || 0));

    return () => ro.disconnect();
  }, [el]);

  return dim;
}

export function GalleryView() {
  const images               = useAppStore((s) => s.images);
  const setImages            = useAppStore((s) => s.setImages);
  const videos               = useAppStore((s) => s.videos);
  const setVideos            = useAppStore((s) => s.setVideos);
  const selectedImages       = useAppStore((s) => s.selectedImages);
  const selectImage          = useAppStore((s) => s.selectImage);
  const toggleImageSelection = useAppStore((s) => s.toggleImageSelection);
  const selectedPersonFilter = useAppStore((s) => s.selectedPersonFilter);
  const setPersonFilter      = useAppStore((s) => s.setPersonFilter);
  const libraryFilter        = useAppStore((s) => s.libraryFilter);
  const setLibraryFilter     = useAppStore((s) => s.setLibraryFilter);
  const setUploadState         = useAppStore((s) => s.setUploadState);
  const setIndexingStatus      = useAppStore((s) => s.setIndexingStatus);
  const setVideoIndexingStatus = useAppStore((s) => s.setVideoIndexingStatus);

  const parentRef    = useRef(null);
  const [gridEl, setGridEl] = useState(null); // state, not a ref: the grid mounts only after the loading/empty states
  const setGridRef = useCallback((node) => { parentRef.current = node; setGridEl(node); }, []);
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const { columns, itemHeight } = useGridDimensions(gridEl);

  const [personPhotos, setPersonPhotos] = useState(null);

  // Initial fetch of both photos and videos
  useEffect(() => {
    if (images.length > 0 && videos.length > 0) return;
    setLoading(true);
    Promise.all([
      fetchAllImages().then(setImages).catch(() => []),
      fetchVideos().then(setVideos).catch(() => []),
    ]).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch media paths for the selected person when filter changes
  useEffect(() => {
    if (!selectedPersonFilter) {
      setPersonPhotos(null);
      return;
    }

    const isVideoPerson =
      selectedPersonFilter.sourceType === 'video' ||
      String(selectedPersonFilter.id).startsWith('video_');

    if (isVideoPerson) {
      fetchPersonVideos(selectedPersonFilter.sourceId || selectedPersonFilter.id)
        .then((paths) => {
          const set = new Set();
          paths.forEach((p) => {
            const norm = String(p).replace(/\\/g, '/');
            const fn = norm.split('/').pop();
            set.add(norm);
            set.add(fn);
            set.add(`uploaded_videos/${fn}`);
          });
          setPersonPhotos(set);
        })
        .catch((err) => {
          toast.error(`Failed to load videos for ${selectedPersonFilter.name}: ${err?.message}`);
          setPersonPhotos(null);
        });
    } else {
      fetchPersonPhotos(selectedPersonFilter.sourceId || selectedPersonFilter.id)
        .then((res) => {
          const set = new Set();
          (res.photos || []).forEach((p) => {
            const norm = String(p).replace(/\\/g, '/');
            const fn = norm.split('/').pop();
            set.add(norm);
            set.add(fn);
          });
          setPersonPhotos(set);
        })
        .catch((err) => {
          toast.error(`Failed to load items for ${selectedPersonFilter.name}: ${err?.message}`);
          setPersonPhotos(null);
        });
    }
  }, [selectedPersonFilter]);

  // Combine and filter photos + videos with guaranteed deduplication
  const combinedMedia = useMemo(() => {
    let list = [];
    const seen = new Set();
    const addUnique = (item) => {
      const key = (item.path || item.id || item.src || '').replace(/\\/g, '/');
      if (key && !seen.has(key)) {
        seen.add(key);
        list.push(item);
      }
    };

    if (libraryFilter === 'all' || libraryFilter === 'photos') {
      images.forEach((img) => addUnique({ ...img, type: 'photo', mediaType: 'photo' }));
    }
    if (libraryFilter === 'all' || libraryFilter === 'videos') {
      videos.forEach((vid) => addUnique({ ...vid, type: 'video', mediaType: 'video' }));
    }

    // Person filter if active
    if (selectedPersonFilter) {
      if (!personPhotos) return [];
      list = list.filter((item) => {
        const itemPath = (item.path || item.id || '').replace(/\\/g, '/');
        const filename = itemPath.split('/').pop();
        return (
          personPhotos.has(itemPath) ||
          personPhotos.has(filename) ||
          personPhotos.has(item.id) ||
          personPhotos.has(`uploaded_videos/${filename}`)
        );
      });
    }

    return list;
  }, [images, videos, libraryFilter, selectedPersonFilter, personPhotos]);

  // Group media by date, chunk into virtualizer rows
  const { rows } = useMemo(() => {
    const groups = new Map();
    for (const item of combinedMedia) {
      const date = item.date || 'Recent';
      if (!groups.has(date)) groups.set(date, []);
      groups.get(date).push(item);
    }

    const rows = [];
    Array.from(groups.entries())
      .sort(([a], [b]) => b.localeCompare(a))
      .forEach(([date, items]) => {
        rows.push({ type: 'header', date });
        for (let i = 0; i < items.length; i += columns) {
          rows.push({ type: 'images', images: items.slice(i, i + columns) });
        }
      });

    return { rows };
  }, [combinedMedia, columns]);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => (rows[index]?.type === 'header' ? HEADER_ROW_HEIGHT : itemHeight + GRID_GAP),
    overscan: 8,
  });

  // Row heights are estimates from the measured tile size; when the size or column count changes (first measurement,
  // window resize, collapsing the sidebar) the virtualizer must forget its cached sizes, otherwise rows keep the
  // first guess and end up overlapping their neighbours.
  useEffect(() => {
    virtualizer.measure();
  }, [itemHeight, columns, virtualizer]);

  const handleSelect = useCallback(
    (id, shiftKey) => {
      shiftKey ? toggleImageSelection(id) : selectImage(id);
    },
    [selectImage, toggleImageSelection]
  );

  const processSelectedFiles = async (files) => {
    if (!files || files.length === 0) return;
    const photoFiles = files.filter(f => !/\.(mp4|mov|avi|mkv|webm)$/i.test(f.name) && !f.type.startsWith('video/'));
    const videoFiles = files.filter(f => /\.(mp4|mov|avi|mkv|webm)$/i.test(f.name) || f.type.startsWith('video/'));

    const mediaType = videoFiles.length > 0 && photoFiles.length === 0 ? 'video' : 'photo';

    setUploadState({
      isUploading: true,
      isCompleted: false,
      totalFiles: files.length,
      currentFileIndex: 1,
      fileName: files[0]?.name || '',
      mediaType,
      progress: 0,
      bytesUploaded: 0,
      totalBytes: files.reduce((acc, f) => acc + f.size, 0),
      error: null,
    });

    try {
      if (photoFiles.length > 0) {
        const uploadRes = await uploadImages(photoFiles, (info) => {
          setUploadState({
            progress: info.percent,
            bytesUploaded: info.loaded,
            totalBytes: info.total,
            fileName: info.fileName,
          });
        });
        if (uploadRes?.indexing_started || (uploadRes?.saved && uploadRes.saved.length > 0)) {
          setIndexingStatus({
            isIndexing: true,
            status: 'running',
            stage: 'detecting',
            progress: 0,
            processed: 0,
            total: photoFiles.length,
            message: `AI analyzing ${photoFiles.length} photo(s)...`,
          });
        }
      }

      if (videoFiles.length > 0) {
        await uploadVideos(videoFiles, (info) => {
          setUploadState({
            progress: info.percent,
            bytesUploaded: info.loaded,
            totalBytes: info.total,
            fileName: info.fileName,
          });
        });
        setVideoIndexingStatus({
          status: 'processing',
          current: 1,
          total: videoFiles.length,
          message: `AI analyzing ${videoFiles[0]?.name || 'video'} (1/${videoFiles.length})...`,
        });
      }

      setUploadState({
        isUploading: false,
        isCompleted: true,
        progress: 100,
      });

      toast.success(`Imported ${files.length} item${files.length !== 1 ? 's' : ''}`);
      fetchAllImages().then(setImages);
      fetchVideos().then(setVideos);
    } catch (err) {
      setUploadState({
        isUploading: false,
        isCompleted: false,
        error: err?.message || 'Upload failed',
      });
      toast.error(err?.message || 'Upload failed');
    }
  };

  const handleImportClick = async () => {
    if (typeof window !== 'undefined' && typeof window.showOpenFilePicker === 'function') {
      try {
        const handles = await window.showOpenFilePicker({
          multiple: true,
          types: [
            {
              description: 'Photos & Videos',
              accept: {
                'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.bmp'],
                'video/*': ['.mp4', '.mov', '.mkv', '.webm'],
              },
            },
          ],
        });
        if (handles && handles.length > 0) {
          const files = await Promise.all(handles.map((h) => h.getFile()));
          processSelectedFiles(files);
          return;
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
      }
    }
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e) => {
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if (files.length > 0) {
      processSelectedFiles(files);
    }
  };

  const formatDate = (dateStr) => {
    if (dateStr === 'Recent') return 'Recent';
    const d = new Date(dateStr);
    return isNaN(d.getTime())
      ? dateStr
      : d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };

  // Loading: a faint outline of the grid, so the page doesn't jump when the photos arrive
  if (loading) {
    return (
      <div className="flex h-full flex-col px-7 pt-8" aria-busy="true">
        <div className="shimmer mb-8 h-9 w-48 rounded-xl" />
        <div
          className="grid flex-1 gap-3 overflow-hidden"
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)`, gridAutoRows: `${itemHeight}px` }}
        >
          {Array.from({ length: columns * 3 }).map((_, i) => (
            <div key={i} className="shimmer rounded-2xl" style={{ animationDelay: `${i * 60}ms` }} />
          ))}
        </div>
        <p className="py-4 text-center text-[13px] text-muted-foreground">Opening your library…</p>
      </div>
    );
  }

  // Empty state
  if (images.length === 0 && videos.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-7 px-6">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          className="hidden"
          onChange={handleFileInputChange}
        />
        <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}>
          <EmptyCove />
        </motion.div>
        <div className="max-w-[420px] space-y-2 text-center">
          <h2 className="font-display text-[30px] font-semibold leading-tight text-foreground">Your cove is empty</h2>
          <p className="text-[15px] leading-relaxed text-muted-foreground">
            Bring in photos and videos and Cove will sort them for you: searchable by what is in them, grouped by who is in them. All of it stays on this device.
          </p>
        </div>
        <button
          onClick={handleImportClick}
          className="flex items-center gap-2 rounded-full bg-primary px-7 py-3.5 text-[15px] font-semibold text-primary-foreground shadow-[0_14px_36px_-10px_hsl(var(--primary)/0.8)] transition-all hover:brightness-110 active:scale-[0.97]"
        >
          <Plus size={18} strokeWidth={2.6} />
          Import Photos &amp; Videos
        </button>
      </div>
    );
  }

  const totalCount = images.length + videos.length;

  const filterBtn = (id, label, Icon) => (
    <button
      key={id}
      onClick={() => setLibraryFilter(id)}
      className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-all ${
        libraryFilter === id
          ? 'bg-foreground text-background shadow-sm'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      }`}
    >
      {Icon && <Icon size={13} />}
      <span>{label}</span>
    </button>
  );

  return (
    <div className="flex h-full flex-col">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,video/*"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Page header: serif title, count, type filter, person chip */}
      <div className="flex flex-shrink-0 flex-wrap items-end justify-between gap-x-6 gap-y-4 px-7 pb-3 pt-7">
        <div className="min-w-0">
          <div className="flex items-baseline gap-3">
            <h1 className="font-display text-[36px] font-semibold leading-none text-foreground">Library</h1>
            <span className="tabular text-[14px] text-muted-foreground">
              {combinedMedia.length.toLocaleString()} items
            </span>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-full border border-border/80 bg-card/60 p-1">
              {filterBtn('all', `All (${totalCount})`)}
              {filterBtn('photos', `Photos (${images.length})`, ImageIcon)}
              {filterBtn('videos', `Videos (${videos.length})`, Film)}
            </div>

            <AnimatePresence>
              {selectedPersonFilter && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 py-1.5 pl-4 pr-2 text-[13px] font-medium text-primary"
                >
                  <span>Person: {selectedPersonFilter.name}</span>
                  <button
                    onClick={() => setPersonFilter(null)}
                    aria-label="Clear person filter"
                    className="rounded-full p-1 transition-colors hover:bg-primary/20"
                  >
                    <X size={13} />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <AnimatePresence>
            {selectedImages.size > 0 && (
              <motion.span
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="tabular rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1.5 text-[13px] font-medium text-primary"
              >
                {selectedImages.size} selected
              </motion.span>
            )}
          </AnimatePresence>
          <button
            onClick={handleImportClick}
            aria-label="Import media into library"
            className="flex items-center gap-2 rounded-full border border-border bg-card/70 px-4 py-2 text-[13px] font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-card"
          >
            <Plus size={15} className="text-primary" />
            Import
          </button>
        </div>
      </div>

      {/* Virtualised grid */}
      <div ref={setGridRef} className="flex-1 overflow-auto px-7 pb-10">
        <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative', width: '100%' }}>
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index];
            if (!row) return null;

            if (row.type === 'header') {
              return (
                <div
                  key={virtualRow.key}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${HEADER_ROW_HEIGHT}px`,
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  className="flex items-end gap-4 pb-3"
                >
                  <h2 className="whitespace-nowrap font-display text-[21px] font-medium italic text-foreground/90">
                    {formatDate(row.date)}
                  </h2>
                  <div className="mb-2 h-px flex-1 bg-border/70" />
                </div>
              );
            }

            return (
              <div
                key={virtualRow.key}
                data-index={virtualRow.index}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  paddingBottom: `${GRID_GAP}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  display: 'grid',
                  gridTemplateColumns: `repeat(${columns}, 1fr)`,
                  columnGap: `${GRID_GAP}px`,
                }}
              >
                {row.images.map((item) => (
                  <PhotoCard
                    key={item.id}
                    image={item}
                    isSelected={selectedImages.has(item.id)}
                    onSelect={handleSelect}
                  />
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/** A small illustration for the empty library: a low sun over a bay, layered tide lines. */
function EmptyCove() {
  return (
    <svg width="220" height="150" viewBox="0 0 220 150" fill="none" aria-hidden="true">
      <circle cx="150" cy="52" r="42" fill="hsl(var(--primary))" opacity="0.12" />
      <circle cx="150" cy="52" r="26" fill="hsl(var(--primary))" opacity="0.95" />
      <path d="M0 96c26-12 52-12 78 0s52 12 78 0 52-12 66 0V150H0z" fill="hsl(var(--info))" opacity="0.22" />
      <path d="M0 112c26-10 52-10 78 0s52 10 78 0 52-10 66 0V150H0z" fill="hsl(var(--info))" opacity="0.34" />
      <path d="M0 128c26-8 52-8 78 0s52 8 78 0 52-8 66 0V150H0z" fill="hsl(var(--accent))" opacity="0.5" />
    </svg>
  );
}
