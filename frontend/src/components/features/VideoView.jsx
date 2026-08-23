/**
 * VideoView — Browse the indexed video library with label filters and a video player dialog.
 * Backed by the real video-processing API (videoModules/api.py via /api/video).
 */
import { useEffect, useMemo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, Plus, Play, Loader2, ExternalLink } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchVideos, uploadVideos } from '@/lib/videoApi';
import { toast } from 'sonner';

/**
 * The videoModules Streamlit UI (video-ui, port 8502) still owns a few features
 * not yet built natively here: bulk folder import, face clustering/identities,
 * and label correction. Link out to it rather than silently dropping them.
 */
function openAdvancedTools() {
  const url = `${window.location.protocol}//${window.location.hostname}:8502`;
  window.open(url, '_blank', 'noopener,noreferrer');
}

export function VideoView() {
  const videos         = useAppStore((s) => s.videos);
  const setVideos      = useAppStore((s) => s.setVideos);
  const openMediaModal = useAppStore((s) => s.openMediaModal);
  const setUploadState = useAppStore((s) => s.setUploadState);

  const [filter, setFilter] = useState('all');
  const [hoveredId, setHoveredId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);

  const loadVideos = useCallback(() => {
    setLoading(true);
    return fetchVideos()
      .then(setVideos)
      .catch(() => toast.error('Failed to load videos'))
      .finally(() => setLoading(false));
  }, [setVideos]);

  // Initial fetch — runs only once
  useEffect(() => {
    if (videos.length > 0) return;
    loadVideos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filters = useMemo(() => {
    const labels = new Set(videos.map((v) => v.label).filter(Boolean));
    return ['all', ...labels];
  }, [videos]);

  const filteredVideos = filter === 'all' ? videos : videos.filter((v) => v.label === filter);

  const handleImport = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'video/*,.mp4,.mkv,.avi,.mov,.webm,.MP4,.MKV,.AVI,.MOV';
    input.style.position = 'fixed';
    input.style.top = '-9999px';
    document.body.appendChild(input);

    input.onchange = async (e) => {
      const files = e.target.files;
      if (!files || files.length === 0) {
        input.remove();
        return;
      }
      setImporting(true);
      setUploadState({
        isUploading: true,
        isCompleted: false,
        totalFiles: files.length,
        currentFileIndex: 1,
        fileName: files[0]?.name || '',
        mediaType: 'video',
        progress: 0,
        bytesUploaded: 0,
        totalBytes: Array.from(files).reduce((acc, f) => acc + f.size, 0),
        error: null,
      });

      try {
        const { count, total } = await uploadVideos(files, (info) => {
          setUploadState({
            currentFileIndex: info.fileIndex,
            fileName: info.fileName,
            progress: info.percent,
            bytesUploaded: info.loaded,
            totalBytes: info.total,
          });
        });

        setUploadState({
          isUploading: false,
          isCompleted: true,
          progress: 100,
        });

        if (count > 0) toast.success(`Indexed ${count} of ${total} video${total > 1 ? 's' : ''}`);
        if (count < total) toast.error(`${total - count} video${total - count > 1 ? 's' : ''} failed to index`);
        await loadVideos();
      } catch (err) {
        setUploadState({
          isUploading: false,
          isCompleted: false,
          error: err?.message || 'Video import failed',
        });
        toast.error(err?.message || 'Import failed');
      } finally {
        setImporting(false);
        input.remove();
      }
    };
    input.click();
  }, [loadVideos, setUploadState]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <Loader2 size={24} className="animate-spin text-primary" />
        <p className="text-[13px] text-muted-foreground">Loading your videos…</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto flex flex-col">
      {/* Header */}
      <div className="px-5 pt-5 pb-3 flex-shrink-0">
        <div className="flex items-start justify-between mb-1">
          <div>
            <h1 className="text-[15px] font-semibold text-foreground tracking-tight flex items-center gap-2">
              <Film size={16} className="text-primary" />
              Videos
            </h1>
            <p className="text-[12px] text-muted-foreground mt-0.5">
              <span className="font-medium text-foreground">{videos.length}</span> videos
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={openAdvancedTools}
              aria-label="Open advanced tools (bulk import, identities, label correction — opens in new tab)"
              title="Bulk import, identities, and label correction"
              className="flex items-center gap-1.5 rounded-md bg-muted hover:bg-muted/70 text-muted-foreground hover:text-foreground px-3 py-1.5 text-[12px] font-medium transition-colors border border-border"
            >
              <ExternalLink size={13} />
              Advanced Tools
            </button>
            <button
              onClick={handleImport}
              disabled={importing}
              aria-label="Import videos"
              className="flex items-center gap-1.5 rounded-md bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 text-[12px] font-medium transition-colors border border-primary/20 disabled:opacity-50"
            >
              {importing ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
              {importing ? 'Indexing…' : 'Import Videos'}
            </button>
          </div>
        </div>

        {/* Filter chips */}
        {filters.length > 1 && (
          <div role="group" aria-label="Filter videos by label" className="flex flex-wrap gap-1.5 mt-3">
            {filters.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                aria-pressed={filter === f}
                className={`rounded-full px-3 py-1 text-[11px] font-medium transition-all duration-150 capitalize ${
                  filter === f
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-card border border-border text-secondary-foreground hover:border-primary/40 hover:text-foreground'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Empty state */}
      {videos.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 gap-5">
          <motion.div
            className="h-16 w-16 rounded-2xl bg-muted/50 flex items-center justify-center"
            animate={{ y: [0, -4, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
          >
            <Film size={28} strokeWidth={1.2} className="text-muted-foreground" />
          </motion.div>
          <div className="text-center space-y-1.5">
            <h2 className="text-base font-medium text-foreground">No videos yet</h2>
            <p className="text-[13px] text-muted-foreground max-w-[260px]">
              Import videos to index and browse them with AI-powered search
            </p>
          </div>
          <button
            onClick={handleImport}
            disabled={importing}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-md disabled:opacity-50"
          >
            {importing ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            Import Videos
          </button>
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={filter}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="px-5 pb-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
          >
            {filteredVideos.map((v, i) => (
              <motion.div
                key={v.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.22 }}
                onClick={() => openMediaModal('video', v)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openMediaModal('video', v);
                  }
                }}
                onMouseEnter={() => setHoveredId(v.id)}
                onMouseLeave={() => setHoveredId(null)}
                role="button"
                tabIndex={0}
                aria-label={`Play ${v.title}`}
                className="group cursor-pointer rounded-xl overflow-hidden border border-border bg-card hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {/* Thumbnail */}
                <div className="relative overflow-hidden bg-black" style={{ height: 150 }}>
                  <video
                    src={v.thumb}
                    preload="metadata"
                    muted
                    playsInline
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />

                  {/* Play overlay */}
                  <AnimatePresence>
                    {hoveredId === v.id && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        transition={{ duration: 0.15 }}
                        className="absolute inset-0 flex items-center justify-center"
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm border border-white/30">
                          <Play size={14} fill="white" className="text-white ml-0.5" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {v.label && (
                    <div className="absolute top-2 right-2 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide bg-primary text-primary-foreground capitalize">
                      {v.label}
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="p-3">
                  <p className="text-[13px] font-medium text-foreground truncate mb-1">{v.title}</p>
                  {v.date && (
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>{v.date}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>
      )}

      {/* Empty filter state */}
      {videos.length > 0 && filteredVideos.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-20 text-muted-foreground"
        >
          <Film size={28} strokeWidth={1.2} className="mb-3 text-muted-foreground/40" />
          <p className="text-[13px]">No videos tagged &ldquo;{filter}&rdquo;</p>
          <p className="text-[11px] text-muted-foreground/50 mt-1">Try a different filter</p>
        </motion.div>
      )}
    </div>
  );
}
