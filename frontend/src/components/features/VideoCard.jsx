import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Loader2 } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

export function VideoCard({ video }) {
  const [hovered, setHovered] = useState(false);
  const openMediaModal = useAppStore((s) => s.openMediaModal);

  const isProcessing =
    !video.thumb ||
    video.label === 'Processing AI tags...' ||
    video.status === 'processing';

  return (
    <div
      onClick={() => openMediaModal('video', video)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openMediaModal('video', video);
        }
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      role="button"
      tabIndex={0}
      aria-label={`Play ${video.title}`}
      className="group cursor-pointer rounded-xl overflow-hidden border border-border bg-card hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary flex flex-col h-full"
    >
      {/* Thumbnail */}
      <div className="relative overflow-hidden bg-muted/40" style={{ height: 150 }}>
        {isProcessing ? (
          <div className="w-full h-full flex flex-col items-center justify-center bg-muted/60 p-4 text-center">
            <Loader2 size={24} className="text-primary animate-spin mb-1.5" />
            <span className="text-[11px] font-medium text-foreground">Processing Video...</span>
            <span className="text-[10px] text-muted-foreground mt-0.5">Extracting keyframes</span>
          </div>
        ) : (
          <>
            <video
              src={video.thumb}
              preload="metadata"
              muted
              playsInline
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/80 via-transparent to-transparent" />

            {/* Play overlay */}
            <AnimatePresence>
              {hovered && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.15 }}
                  className="absolute inset-0 flex items-center justify-center"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-background/50 backdrop-blur-sm border border-foreground/20">
                    <Play size={14} className="text-foreground ml-0.5 fill-current" />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {video.label && (
              <div className="absolute top-2 right-2 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide bg-primary text-primary-foreground capitalize">
                {video.label}
              </div>
            )}
          </>
        )}
      </div>

      {/* Info */}
      <div className="p-3 bg-card flex-1">
        <p className="text-[13px] font-medium text-foreground truncate mb-1">{video.title}</p>
        {video.date && (
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>{video.date}</span>
          </div>
        )}
      </div>
    </div>
  );
}
