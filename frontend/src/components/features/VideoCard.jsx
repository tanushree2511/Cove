import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

export function VideoCard({ video }) {
  const [hovered, setHovered] = useState(false);
  const openMediaModal = useAppStore((s) => s.openMediaModal);

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
      <div className="relative overflow-hidden bg-black" style={{ height: 150 }}>
        <video
          src={video.thumb}
          preload="metadata"
          muted
          playsInline
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />

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
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm border border-white/30">
                <Play size={14} fill="white" className="text-white ml-0.5" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {video.label && (
          <div className="absolute top-2 right-2 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide bg-primary text-primary-foreground capitalize">
            {video.label}
          </div>
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
