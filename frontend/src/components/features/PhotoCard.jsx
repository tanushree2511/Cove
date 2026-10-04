import { memo, useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { Check, Play, Film, Loader2 } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

/**
 * One tile of the library grid: a photo or a video. Rounded, lifts and gets a coral ring on hover; videos carry a glass
 * play badge and their first AI label.
 */
export const PhotoCard = memo(function PhotoCard({ image, isSelected, onSelect }) {
  const [loaded, setLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);
  const videoRef = useRef(null);
  const openMediaModal = useAppStore((s) => s.openMediaModal);

  const isVideo =
    image.type === 'video' ||
    image.mediaType === 'video' ||
    image.media_type === 'video' ||
    Boolean(image.video_id) ||
    /\.(mp4|mov|avi|mkv|webm)$/i.test(image.path || image.filename || image.url || '');

  const isProcessing =
    isVideo &&
    (image.label === 'Processing AI tags...' ||
     image.status === 'processing' ||
     (!image.thumbnail && !image.thumb));

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
    if (isVideo && videoRef.current) {
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    if (isVideo && videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0.5;
    }
  };

  const firstLabel = isVideo && image.label && image.label !== 'Processing AI tags...'
    ? String(image.label).split(',')[0].trim()
    : null;

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
      className="tile group aspect-square cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      style={{ willChange: 'transform' }}
      whileTap={{ scale: 0.985 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    >
      {/* skeleton while the picture loads */}
      {!loaded && <div className="shimmer absolute inset-0" aria-hidden="true" />}

      {isVideo ? (
        <div className="relative h-full w-full bg-muted/40">
          {isProcessing ? (
            <div className="flex h-full w-full flex-col items-center justify-center bg-muted/60 p-3 text-center">
              <Loader2 size={24} className="mb-2 animate-spin text-primary" />
              <span className="text-[12px] font-medium text-foreground">Getting ready…</span>
              <span className="mt-0.5 line-clamp-1 text-[11px] text-muted-foreground">Picking key moments</span>
            </div>
          ) : !imgError ? (
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
              className={`aspect-square h-full w-full bg-muted object-cover transition-all duration-500 ease-out ${loaded ? 'opacity-100' : 'opacity-0'}`}
            />
          ) : (
            <div className="flex h-full w-full flex-col items-center justify-center bg-muted/50 p-3 text-center">
              <Film size={26} className="mb-1 text-primary/70" />
              <span className="line-clamp-2 px-1 text-[11px] text-muted-foreground">{image.title || 'Video'}</span>
            </div>
          )}

          {/* video badge: glass play glyph, top right */}
          <div className="pointer-events-none absolute right-2.5 top-2.5 z-10 flex h-7 w-7 items-center justify-center rounded-full border border-white/15 bg-black/45 text-white backdrop-blur-md">
            <Play size={12} className="ml-0.5 fill-current" />
          </div>

          {!isProcessing && (
            <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center opacity-0 transition-opacity duration-200 group-hover:opacity-100">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-[0_10px_30px_-6px_hsl(var(--primary)/0.8)] transition-transform group-hover:scale-105">
                <Play size={22} className="ml-1 fill-current" />
              </div>
            </div>
          )}
        </div>
      ) : (
        <img
          src={image.thumbnail || image.src}
          alt={image.title || image.tags?.join(', ') || 'Photo'}
          loading="lazy"
          decoding="async"
          onLoad={() => setLoaded(true)}
          className={`aspect-square h-full w-full object-cover transition-all duration-700 ease-out ${loaded ? 'scale-100 opacity-100' : 'scale-[1.04] opacity-0'}`}
          style={{ transform: 'translateZ(0)' }}
        />
      )}

      {/* the video's first AI label, bottom left */}
      {firstLabel && (
        <div className="pointer-events-none absolute bottom-2.5 left-2.5 z-10 max-w-[85%] truncate rounded-full border border-white/15 bg-black/50 px-2.5 py-1 text-[11px] font-medium capitalize text-white backdrop-blur-md">
          {firstLabel}
        </div>
      )}

      {/* hover vignette */}
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-transparent to-black/20 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        aria-hidden="true"
      />

      {/* selected: coral frame, check */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
          className="absolute inset-0 z-20 rounded-2xl bg-primary/15 ring-[3px] ring-inset ring-primary"
        >
          <button
            onClick={handleCheckboxClick}
            aria-label="Deselect item"
            className="absolute left-2.5 top-2.5 flex h-6 w-6 items-center justify-center rounded-full bg-primary shadow-lg"
          >
            <Check size={14} className="text-primary-foreground" strokeWidth={3.2} />
          </button>
        </motion.div>
      )}

      {/* hover select circle */}
      {!isSelected && (
        <button
          onClick={handleCheckboxClick}
          aria-label="Select item"
          className="absolute left-2.5 top-2.5 z-20 h-6 w-6 rounded-full border-2 border-white/70 bg-black/25 opacity-0 backdrop-blur-sm transition-all duration-200 hover:scale-110 hover:border-primary group-hover:opacity-100"
        />
      )}
    </motion.div>
  );
});
