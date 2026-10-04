/**
 * Video Player Modal — plays the selected video from the video backend,
 * with metadata sidebar and audio-extraction shortcut.
 */
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, Film, Calendar, Tag, Music, Loader2, Trash2, AlertCircle } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { extractAudio, deleteSingleVideo, fetchVideos } from '@/lib/videoApi';
import { toast } from 'sonner';

export function VideoModal() {
  const activeMediaModal = useAppStore((s) => s.activeMediaModal);
  const closeMediaModal  = useAppStore((s) => s.closeMediaModal);

  const isVideoModal = activeMediaModal?.type === 'video';
  const video        = activeMediaModal?.item;

  const [extracting, setExtracting] = useState(false);
  const [videoError, setVideoError] = useState(false);

  useEffect(() => {
    setVideoError(false);
  }, [video?.id, video?.src]);

  useEffect(() => {
    if (!isVideoModal) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') closeMediaModal();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVideoModal, closeMediaModal]);

  const handleDownload = () => {
    const a = document.createElement('a');
    a.href = video.src;
    a.download = video.title;
    a.click();
  };

  const handleExtractAudio = async () => {
    setExtracting(true);
    try {
      const audioUrl = await extractAudio(video.path);
      const audio = new Audio(audioUrl);
      audio.play();
      toast.success('Audio extracted — playing now');
    } catch (err) {
      toast.error(err.message || 'No audio track found');
    } finally {
      setExtracting(false);
    }
  };

  return (
    <AnimatePresence>
      {isVideoModal && video && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Video player"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4"
        >
          <div className="absolute inset-0" onClick={closeMediaModal} />

          <motion.div
            key={video.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="relative z-10 flex flex-col md:flex-row w-full max-w-4xl h-[80vh] rounded-2xl overflow-hidden bg-card border border-border shadow-2xl"
          >
            {/* ── Video Player ── */}
            <div className="relative flex-1 bg-black flex items-center justify-center overflow-hidden">
              {videoError ? (
                <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                  <div className="h-12 w-12 rounded-full bg-destructive/10 border border-destructive/20 flex items-center justify-center mb-3">
                    <AlertCircle size={24} className="text-destructive" />
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-1">Unable to stream video</h3>
                  <p className="text-xs text-zinc-400 mb-4 leading-relaxed">
                    The video stream returned an error or could not be found on the server.
                  </p>
                  <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-2.5 w-full text-left font-mono text-[11px] text-zinc-400 truncate">
                    {video.path || video.title}
                  </div>
                </div>
              ) : (
                <video
                  key={video.id}
                  src={video.src}
                  controls
                  autoPlay
                  onError={() => setVideoError(true)}
                  className="w-full h-full object-contain"
                />
              )}
            </div>

            {/* ── Video Info Sidebar ── */}
            <div className="w-full md:w-72 flex flex-col border-t md:border-t-0 md:border-l border-border bg-card p-5 overflow-y-auto flex-shrink-0">
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-border mb-4">
                <span className="text-[13px] font-semibold text-foreground flex items-center gap-1.5">
                  <Film size={15} className="text-primary" />
                  Video Details
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleDownload}
                    title="Download"
                    aria-label="Download video"
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  >
                    <Download size={16} />
                  </button>
                  <button
                    onClick={closeMediaModal}
                    title="Close"
                    aria-label="Close video player"
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>

              {/* Details */}
              <div className="space-y-4 text-[12px]">
                <div>
                  <h3 className="font-semibold text-foreground text-sm leading-snug break-all">{video.title}</h3>
                </div>

                {video.date && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar size={14} />
                    <span>{video.date}</span>
                  </div>
                )}

                {video.label && (
                  <div className="pt-2 border-t border-border">
                    <span className="flex items-center gap-1.5 font-medium text-foreground mb-1.5 text-[12px]">
                      <Tag size={13} className="text-muted-foreground" />
                      Detected Action
                    </span>
                    <span className="inline-block rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground capitalize">
                      {video.label}
                    </span>
                  </div>
                )}

                <div className="pt-2 border-t border-border space-y-2">
                  <button
                    onClick={handleExtractAudio}
                    disabled={extracting}
                    className="flex items-center gap-1.5 w-full justify-center rounded-lg bg-muted hover:bg-muted/70 px-3 py-2 text-[12px] font-medium text-foreground transition-colors disabled:opacity-50"
                  >
                    {extracting ? <Loader2 size={13} className="animate-spin" /> : <Music size={13} />}
                    Extract Audio
                  </button>

                  <button
                    onClick={async () => {
                      if (!window.confirm(`Are you sure you want to delete "${video.title}"?`)) return;
                      try {
                        const target = video.id ?? video.path;
                        await deleteSingleVideo(target);
                        useAppStore.getState().removeVideoById(target);
                        fetchVideos().then((vids) => useAppStore.getState().setVideos(vids));
                        closeMediaModal();
                        toast.success('Video deleted from library');
                      } catch (err) {
                        toast.error(err?.message || 'Failed to delete video');
                      }
                    }}
                    className="flex items-center gap-1.5 w-full justify-center rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive px-3 py-2 text-[12px] font-medium transition-colors"
                  >
                    <Trash2 size={13} />
                    Delete Video
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
