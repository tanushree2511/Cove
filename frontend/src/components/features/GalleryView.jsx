/**
 * Virtualized unified media gallery — renders 100k+ photos and videos at 60fps.
 * Dynamic responsive columns via ResizeObserver, sticky date headers,
 * type filtering (All / Photos / Videos), person filtering support, and universal import.
 */
import { useEffect, useRef, useMemo, useCallback, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { motion, AnimatePresence } from 'framer-motion';
import { Images, FolderOpen, Loader2, X, Film, Image as ImageIcon, Sparkles } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchImages, uploadImages, fetchPersonPhotos } from '@/lib/coveApi';
import { fetchVideos, uploadVideos, fetchPersonVideos } from '@/lib/videoApi';
import { PhotoCard } from './PhotoCard';
import { toast } from 'sonner';

/** Derive column count and accurate item height from container width */
function useGridDimensions(containerRef) {
  const [dim, setDim] = useState({ columns: 5, itemHeight: 200 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const calc = (width) => {
      let cols = 5;
      if (width < 480)  cols = 2;
      else if (width < 640)  cols = 3;
      else if (width < 900)  cols = 4;
      else if (width < 1280) cols = 5;
      else cols = 6;

      // Padding on left + right is px-5 (40px)
      const contentWidth = Math.max(100, width - 40);
      const gap = 4;
      const itemWidth = Math.floor((contentWidth - (gap * (cols - 1))) / cols);
      const itemHeight = Math.max(80, itemWidth);

      setDim({ columns: cols, itemHeight });
    };

    const ro = new ResizeObserver(([entry]) => {
      calc(entry.contentRect.width);
    });
    ro.observe(el);
    calc(el.offsetWidth);

    return () => ro.disconnect();
  }, [containerRef]);

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
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const { columns, itemHeight } = useGridDimensions(parentRef);

  const [personPhotos, setPersonPhotos] = useState(null);

  // Initial fetch of both photos and videos
  useEffect(() => {
    if (images.length > 0 && videos.length > 0) return;
    setLoading(true);
    Promise.all([
      fetchImages(0, 1000).then(setImages).catch(() => []),
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
    estimateSize: (index) => (rows[index]?.type === 'header' ? 44 : itemHeight + 4),
    overscan: 8,
  });

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
      fetchImages(0, 1000).then(setImages);
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
    if (dateStr === 'Recent') return 'Recent Media';
    const d = new Date(dateStr);
    return isNaN(d.getTime())
      ? dateStr
      : d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <Loader2 size={24} className="animate-spin text-primary" />
        <p className="text-[13px] text-muted-foreground">Loading your library…</p>
      </div>
    );
  }

  // Empty state
  if (images.length === 0 && videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-5">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          className="hidden"
          onChange={handleFileInputChange}
        />
        <motion.div
          className="h-16 w-16 rounded-2xl bg-muted/50 flex items-center justify-center"
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
        >
          <Images size={28} strokeWidth={1.2} className="text-muted-foreground" />
        </motion.div>
        <div className="text-center space-y-1.5">
          <h2 className="text-base font-medium text-foreground">No media in library</h2>
          <p className="text-[13px] text-muted-foreground max-w-[280px]">
            Import photos or videos to start exploring, organizing, and searching with AI
          </p>
        </div>
        <button
          onClick={handleImportClick}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-md"
        >
          <FolderOpen size={14} />
          Import Photos & Videos
        </button>
      </div>
    );
  }

  const totalCount = images.length + videos.length;

  return (
    <div className="flex flex-col h-full">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,video/*"
        className="hidden"
        onChange={handleFileInputChange}
      />
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 py-3 flex-shrink-0 border-b border-border/40 bg-surface/30 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-baseline gap-2">
            <h1 className="text-[15px] font-semibold text-foreground">Library</h1>
            <span className="text-[11px] text-muted-foreground mono">
              {combinedMedia.length.toLocaleString()} items
            </span>
          </div>

          {/* Unified Type Filters */}
          <div className="flex items-center rounded-lg bg-muted/50 p-0.5 border border-border/60 text-xs">
            <button
              onClick={() => setLibraryFilter('all')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                libraryFilter === 'all'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => setLibraryFilter('photos')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                libraryFilter === 'photos'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <ImageIcon size={12} />
              <span>Photos ({images.length})</span>
            </button>
            <button
              onClick={() => setLibraryFilter('videos')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                libraryFilter === 'videos'
                  ? 'bg-card text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Film size={12} />
              <span>Videos ({videos.length})</span>
            </button>
          </div>

          {/* Active person filter pill */}
          <AnimatePresence>
            {selectedPersonFilter && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex items-center gap-1.5 rounded-full bg-primary/10 border border-primary/20 px-3 py-1 text-[11px] font-medium text-primary"
              >
                <span>Person: {selectedPersonFilter.name}</span>
                <button
                  onClick={() => setPersonFilter(null)}
                  aria-label="Clear person filter"
                  className="p-0.5 rounded-full hover:bg-primary/20 transition-colors"
                >
                  <X size={12} />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center gap-2">
          <AnimatePresence>
            {selectedImages.size > 0 && (
              <motion.span
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="text-[11px] text-primary font-medium bg-primary/10 rounded-full px-2.5 py-0.5 border border-primary/20"
              >
                {selectedImages.size} selected
              </motion.span>
            )}
          </AnimatePresence>
          <button
            onClick={handleImportClick}
            aria-label="Import media into library"
            className="flex items-center gap-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/20 px-3 py-1.5 text-[12px] font-medium text-primary transition-colors"
          >
            <FolderOpen size={13} />
            Import
          </button>
        </div>
      </div>

      {/* Virtualized grid */}
      <div ref={parentRef} className="flex-1 overflow-auto px-5 pb-5 pt-2">
        <div
          style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative', width: '100%' }}
        >
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
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  className="pt-4 pb-2 text-[12px] font-semibold text-foreground/80 tracking-tight"
                >
                  {formatDate(row.date)}
                </div>
              );
            }

            return (
              <div
                key={virtualRow.key}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${itemHeight}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  display: 'grid',
                  gridTemplateColumns: `repeat(${columns}, 1fr)`,
                  gap: '4px',
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
