/**
 * VideoView - browse the indexed video library, filter by AI tag, open the player.
 * Backed by the real video-processing API (videoModules/api.py via /api/video).
 */
import { useEffect, useMemo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, Plus, Play, Loader2, ExternalLink } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchVideos, uploadVideos } from '@/lib/videoApi';
import { toast } from 'sonner';

const TOP_TAGS = 14;   // how many tag chips are shown before "More tags"

/**
 * The videoModules Streamlit UI (video-ui, port 8502) still owns a few features
 * not yet built natively here: bulk folder import, face clustering/identities,
 * and label correction. Link out to it rather than silently dropping them.
 */
function openAdvancedTools() {
  const url = `${window.location.protocol}//${window.location.hostname}:8502`;
  window.open(url, '_blank', 'noopener,noreferrer');
}

/** "Hammer Throw, Soccer Juggling" -> ["hammer throw", "soccer juggling"] (a video can carry several AI tags) */
const tagsOf = (video) =>
  String(video.label || '')
    .split(',')
    .map((t) => t.trim().toLowerCase())
    .filter((t) => t && t !== 'processing ai tags...');

export function VideoView() {
  const videos         = useAppStore((s) => s.videos);
  const setVideos      = useAppStore((s) => s.setVideos);
  const openMediaModal = useAppStore((s) => s.openMediaModal);
  const setUploadState = useAppStore((s) => s.setUploadState);

  const [filter, setFilter] = useState('all');
  const [showAllTags, setShowAllTags] = useState(false);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);

  const loadVideos = useCallback(() => {
    setLoading(true);
    return fetchVideos()
      .then(setVideos)
      .catch(() => toast.error('Failed to load videos'))
      .finally(() => setLoading(false));
  }, [setVideos]);

  // Initial fetch - runs only once
  useEffect(() => {
    if (videos.length > 0) return;
    loadVideos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Individual tags, most common first (before: one chip per distinct label *combination* - ~90 chips for 100 videos)
  const tagCounts = useMemo(() => {
    const counts = new Map();
    videos.forEach((v) => tagsOf(v).forEach((t) => counts.set(t, (counts.get(t) || 0) + 1)));
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }, [videos]);

  const visibleTags = showAllTags ? tagCounts : tagCounts.slice(0, TOP_TAGS);
  const filteredVideos = filter === 'all' ? videos : videos.filter((v) => tagsOf(v).includes(filter));

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
      <div className="flex h-full flex-col px-7 pt-8" aria-busy="true">
        <div className="shimmer mb-8 h-9 w-44 rounded-xl" />
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="shimmer aspect-[16/11] rounded-3xl" style={{ animationDelay: `${i * 70}ms` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-auto">
      {/* Header */}
      <div className="flex-shrink-0 px-7 pb-4 pt-7">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-[36px] font-semibold leading-none text-foreground">Videos</h1>
            <p className="tabular mt-2.5 text-[14px] text-muted-foreground">
              {videos.length.toLocaleString()} {videos.length === 1 ? 'video' : 'videos'}
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={openAdvancedTools}
              aria-label="Open advanced tools (bulk import, identities, label correction — opens in new tab)"
              title="Bulk import, identities, and label correction"
              className="flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-2 text-[13px] font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
            >
              <ExternalLink size={14} />
              Advanced Tools
            </button>
            <button
              onClick={handleImport}
              disabled={importing}
              aria-label="Import videos"
              className="flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-[13px] font-semibold text-primary-foreground shadow-[0_8px_24px_-8px_hsl(var(--primary)/0.7)] transition-all hover:brightness-110 active:scale-[0.97] disabled:opacity-60"
            >
              {importing ? <Loader2 size={14} className="animate-spin" /> : <Plus size={15} strokeWidth={2.6} />}
              {importing ? 'Indexing…' : 'Import Videos'}
            </button>
          </div>
        </div>

        {/* Tag chips */}
        {tagCounts.length > 0 && (
          <div role="group" aria-label="Filter videos by label" className="mt-6 flex flex-wrap items-center gap-2">
            {[['all', videos.length], ...visibleTags].map(([tag, count]) => (
              <button
                key={tag}
                onClick={() => setFilter(tag)}
                aria-pressed={filter === tag}
                className={`flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[13px] font-medium capitalize transition-all duration-150 ${
                  filter === tag
                    ? 'bg-foreground text-background shadow-sm'
                    : 'border border-border bg-card/50 text-secondary-foreground hover:border-primary/40 hover:text-foreground'
                }`}
              >
                {tag}
                <span className={`tabular text-[11px] ${filter === tag ? 'text-background/60' : 'text-muted-foreground'}`}>{count}</span>
              </button>
            ))}
            {tagCounts.length > TOP_TAGS && (
              <button
                onClick={() => setShowAllTags((v) => !v)}
                className="rounded-full px-3.5 py-1.5 text-[13px] font-medium text-primary transition-colors hover:bg-primary/10"
              >
                {showAllTags ? 'Show fewer tags' : `More tags (${tagCounts.length - TOP_TAGS})`}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Empty state */}
      {videos.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 px-6">
          <motion.div
            className="flex h-24 w-24 items-center justify-center rounded-3xl border border-border bg-card"
            animate={{ y: [0, -5, 0] }}
            transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}
          >
            <Film size={36} strokeWidth={1.2} className="text-primary" />
          </motion.div>
          <div className="max-w-[400px] space-y-2 text-center">
            <h2 className="font-display text-[28px] font-semibold text-foreground">No videos yet</h2>
            <p className="text-[15px] leading-relaxed text-muted-foreground">
              Import videos and Cove will tag what happens in them, so you can search by describing a moment.
            </p>
          </div>
          <button
            onClick={handleImport}
            disabled={importing}
            className="flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-[14px] font-semibold text-primary-foreground shadow-[0_14px_36px_-10px_hsl(var(--primary)/0.8)] transition-all hover:brightness-110 active:scale-[0.97] disabled:opacity-60"
          >
            {importing ? <Loader2 size={15} className="animate-spin" /> : <Plus size={16} strokeWidth={2.6} />}
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
            className="grid grid-cols-1 gap-5 px-7 pb-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
          >
            {filteredVideos.map((v, i) => {
              const tags = tagsOf(v);
              return (
                <motion.div
                  key={v.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(i * 0.025, 0.5), duration: 0.24 }}
                  onClick={() => openMediaModal('video', v)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      openMediaModal('video', v);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  aria-label={`Play ${v.title}`}
                  className="tile group aspect-auto cursor-pointer rounded-3xl border border-border/60 bg-card focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  {/* Cover: the video's still image (this used to be a <video> pointed at a JPEG, i.e. a black box) */}
                  <div className="relative aspect-[16/10] overflow-hidden bg-muted">
                    <img
                      src={v.thumb}
                      alt={v.title}
                      loading="lazy"
                      decoding="async"
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
                    />
                    <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-black/5 to-black/10" />

                    {/* play */}
                    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                      <div className="flex h-14 w-14 items-center justify-center rounded-full border border-white/25 bg-black/40 text-white opacity-80 backdrop-blur-md transition-all duration-200 group-hover:scale-110 group-hover:border-transparent group-hover:bg-primary group-hover:text-primary-foreground group-hover:opacity-100">
                        <Play size={20} className="ml-0.5 fill-current" />
                      </div>
                    </div>

                    {/* first tags */}
                    {tags.length > 0 && (
                      <div className="pointer-events-none absolute bottom-3 left-3 right-3 flex flex-wrap gap-1.5">
                        {tags.slice(0, 2).map((t) => (
                          <span key={t} className="truncate rounded-full border border-white/15 bg-black/50 px-2.5 py-1 text-[11px] font-medium capitalize text-white backdrop-blur-md">
                            {t}
                          </span>
                        ))}
                        {tags.length > 2 && (
                          <span className="rounded-full border border-white/15 bg-black/50 px-2 py-1 text-[11px] font-medium text-white/80 backdrop-blur-md">+{tags.length - 2}</span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="px-4 py-3">
                    <p className="truncate text-[14px] font-medium text-foreground">{v.title}</p>
                    {v.date && <p className="mt-0.5 text-[12px] text-muted-foreground">{v.date}</p>}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </AnimatePresence>
      )}

      {/* Empty filter state */}
      {videos.length > 0 && filteredVideos.length === 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <Film size={30} strokeWidth={1.2} className="mb-3 text-muted-foreground/40" />
          <p className="text-[14px]">No videos tagged &ldquo;{filter}&rdquo;</p>
          <p className="mt-1 text-[12px] text-muted-foreground/60">Try a different tag</p>
        </motion.div>
      )}
    </div>
  );
}
