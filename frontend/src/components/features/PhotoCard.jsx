/**
 * Photo card — Apple Photos inspired with hover overlay, keyboard accessibility,
 * shimmer skeleton while loading, and selection state.
 */
import { memo, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

export const PhotoCard = memo(function PhotoCard({ image, isSelected, onSelect }) {
  const [loaded, setLoaded] = useState(false);
  const openMediaModal = useAppStore((s) => s.openMediaModal);

  const handleClick = useCallback(
    (e) => {
      if (e.shiftKey) {
        onSelect(image.id, true);
      } else {
        openMediaModal('photo', image);
      }
    },
    [image, onSelect, openMediaModal]
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
        openMediaModal('photo', image);
      }
    },
    [image, openMediaModal]
  );

  return (
    <motion.div
      role="button"
      tabIndex={0}
      aria-label={`Photo: ${image.tags?.join(', ') || 'untitled'}`}
      aria-pressed={isSelected}
      onKeyDown={handleKeyDown}
      onClick={handleClick}
      className="relative cursor-pointer overflow-hidden rounded-[6px] bg-card group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 focus:ring-offset-background"
      style={{ willChange: 'transform' }}
      whileHover={{ scale: 1.025 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    >
      {/* Shimmer skeleton while loading */}
      {!loaded && <div className="absolute inset-0 shimmer" aria-hidden="true" />}

      {/* Photo */}
      <img
        src={image.thumbnail || image.src}
        alt={image.tags?.join(', ') || 'Photo'}
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

      {/* Hover vignette */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        aria-hidden="true"
      />

      {/* Selection overlay */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
          className="absolute inset-0 ring-2 ring-primary ring-inset rounded-[6px] bg-primary/10"
        >
          <button
            onClick={handleCheckboxClick}
            aria-label="Deselect photo"
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
          aria-label="Select photo"
          className="absolute top-1.5 right-1.5 h-5 w-5 rounded-full border border-foreground/30 bg-background/40 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110 hover:border-primary"
        />
      )}
    </motion.div>
  );
});
