import { memo, useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Check, Play, Film } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

export const PhotoCard = memo(function PhotoCard({ image, isSelected, onSelect }) {
  const [loaded, setLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [hovered, setHovered] = useState(false);
  const videoRef = useRef(null);
  const openMediaModal = useAppStore((s) => s.openMediaModal);

  const isVideo =
    image.type === 'video' ||
    image.mediaType === 'video' ||
    /\.(mp4|mov|avi|mkv|webm)$/i.test(image.path || '') ||
    Boolean(image.label);

  const handleClick = useCallback(
    (e) => {
      if (e.shiftKey) {
        onSelect(image.id, true);
      } else {
        openMediaModal(isVideo ? 'video' : 'photo', image);
      }
    },
    [image, isVideo, onSelect, openMediaModal]
  );

  const handleCheckboxClick = useCallback(
    (e) => {
      e.stopPropagation();
      onSelect(image.id, true);
    },
    [image.id, onSelect]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openMediaModal(isVideo ? 'video' : 'photo', image);
      }
    },
    [image, isVideo, openMediaModal]
  );

  const handleMouseEnter = () => {
    setHovered(true);
    if (isVideo && videoRef.current) {
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    setHovered(false);
    if (isVideo && videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0.5;
    }
  };

  return (
    <motion.div
      role="button"
      tabIndex={0}
      aria-label={`${isVideo ? 'Video' : 'Photo'}: ${image.title || image.tags?.join(', ') || 'untitled'}`}
      aria-pressed={isSelected}
      onKeyDown={handleKeyDown}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="relative cursor-pointer overflow-hidden rounded-[8px] bg-muted/30 group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 focus:ring-offset-background aspect-square"
      style={{ willChange: 'transform' }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    >
      {/* Shimmer skeleton while loading */}
      {!loaded && <div className="absolute inset-0 shimmer" aria-hidden="true" />}

      {/* Render Video or Photo */}
      {isVideo ? (
        <div className="relative w-full h-full bg-slate-900">
          {!imgError ? (
            <img
              src={image.thumbnail || image.thumb}
              alt={image.title || 'Video preview'}
              loading="lazy"
              decoding="async"
              onLoad={() => setLoaded(true)}
              onError={() => {
                setImgError(true);
                setLoaded(true);
              }}
              className={`
                w-full h-full object-cover aspect-square bg-black
                transition-all duration-300 ease-out
                ${loaded ? 'opacity-100' : 'opacity-0'}
              `}
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-primary/20 p-3 text-center">
              <Film size={26} className="text-primary/70 mb-1" />
              <span className="text-[10px] text-muted-foreground line-clamp-2 px-1">
                {image.title || 'Video'}
              </span>
            </div>
          )}
          {/* Subtle Video duration / badge indicator */}
          <div className="absolute top-2 right-2 z-10 flex items-center gap-1 rounded-md bg-black/70 px-1.5 py-0.5 text-[10px] font-semibold text-white backdrop-blur-md shadow-sm pointer-events-none">
            <Film size={11} className="text-primary" />
            <span>VIDEO</span>
          </div>
          {/* Play button overlay on hover */}
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transform group-hover:scale-105 transition-transform">
              <Play size={18} className="fill-current ml-0.5" />
            </div>
          </div>
        </div>
      ) : (
        <img
          src={image.thumbnail || image.src}
          alt={image.title || image.tags?.join(', ') || 'Photo'}
          loading="lazy"
          decoding="async"
          onLoad={() => setLoaded(true)}
          className={`
            w-full h-full object-cover aspect-square
            transition-all duration-500 ease-out
            ${loaded ? 'opacity-100 scale-100' : 'opacity-0 scale-[1.02]'}
          `}
          style={{ transform: 'translateZ(0)' }}
        />
      )}

      {/* Video Indicator Badge */}
      {isVideo && (
        <div className="absolute bottom-2 left-2 z-10 flex items-center gap-1 rounded-md bg-black/70 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-md shadow-sm max-w-[85%] truncate pointer-events-none">
          <span className="truncate">{image.label ? image.label : image.title}</span>
        </div>
      )}

      {/* Hover vignette */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-background/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        aria-hidden="true"
      />

      {/* Selection overlay */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
          className="absolute inset-0 ring-2 ring-primary ring-inset rounded-[8px] bg-primary/10"
        >
          <button
            onClick={handleCheckboxClick}
            aria-label="Deselect item"
            className="absolute top-1.5 right-1.5 h-5 w-5 rounded-full bg-primary flex items-center justify-center shadow-lg"
          >
            <Check size={12} className="text-primary-foreground" strokeWidth={3} />
          </button>
        </motion.div>
      )}

      {/* Hover checkbox (unselected) */}
      {!isSelected && (
        <button
          onClick={handleCheckboxClick}
          aria-label="Select item"
          className="absolute top-1.5 right-1.5 h-5 w-5 rounded-full border border-foreground/30 bg-background/40 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110 hover:border-primary"
        />
      )}
    </motion.div>
  );
});
