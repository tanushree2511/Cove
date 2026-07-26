/**
 * Video Player Modal — Interactive video details modal with playback representation.
 */
import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Play, Download, Film, Calendar, HardDrive, Tag } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';

export function VideoModal() {
  const activeMediaModal = useAppStore((s) => s.activeMediaModal);
  const closeMediaModal  = useAppStore((s) => s.closeMediaModal);

  const isVideoModal = activeMediaModal?.type === 'video';
  const video        = activeMediaModal?.item;

  useEffect(() => {
    if (!isVideoModal) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') closeMediaModal();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isVideoModal, closeMediaModal]);

  const handleDownload = () => {
    toast.success(`Downloading "${video?.title}"…`);
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
            {/* ── Video Player Display ── */}
            <div className="relative flex-1 bg-black flex items-center justify-center overflow-hidden">
              <img
                src={video.thumb}
                alt={video.title}
                className="w-full h-full object-cover opacity-60"
              />
              <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => toast.info(`Playing "${video.title}"`)}
                  aria-label={`Play ${video.title}`}
                  className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-xl"
                >
                  <Play size={24} fill="currentColor" className="ml-1" />
                </motion.button>
              </div>

              {/* Info bar */}
              <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-md rounded-xl p-3 flex items-center justify-between text-white text-[12px]">
                <span className="font-semibold truncate mr-3">{video.title}</span>
                <span className="mono flex-shrink-0">{video.duration} · {video.res}</span>
              </div>
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
                  <h3 className="font-semibold text-foreground text-sm leading-snug">{video.title}</h3>
                  <span className="inline-block mt-1.5 px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold">
                    {video.res}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar size={14} />
                  <span>{video.date}</span>
                </div>

                <div className="flex items-center gap-2 text-muted-foreground">
                  <HardDrive size={14} />
                  <span className="mono">{video.size}</span>
                </div>

                {video.tags?.length > 0 && (
                  <div className="pt-2 border-t border-border">
                    <span className="flex items-center gap-1.5 font-medium text-foreground mb-1.5 text-[12px]">
                      <Tag size={13} className="text-muted-foreground" />
                      Tags
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {video.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground capitalize"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
