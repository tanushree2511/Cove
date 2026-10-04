/**
 * Semantic search - describe what you remember; CLIP finds the photos and videos that match.
 * Unifies photos and videos search with type filters and similarity ranking.
 */
import { useEffect, useCallback, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, X, Image as ImageIcon, Film } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { searchImages } from '@/lib/coveApi';
import { searchVideos } from '@/lib/videoApi';
import { PhotoCard } from './PhotoCard';

const SUGGESTIONS = [
  'a dog playing on the beach',
  'birthday cake with candles',
  'sunset over the water',
  'friends laughing around a table',
  'a snowy mountain',
  'someone riding a bike',
  'a quiet street at night',
];

export function SearchView() {
  const searchQuery      = useAppStore((s) => s.searchQuery);
  const setSearchQuery   = useAppStore((s) => s.setSearchQuery);
  const searchResults    = useAppStore((s) => s.searchResults);
  const setSearchResults = useAppStore((s) => s.setSearchResults);
  const selectedImages       = useAppStore((s) => s.selectedImages);
  const selectImage          = useAppStore((s) => s.selectImage);
  const toggleImageSelection = useAppStore((s) => s.toggleImageSelection);

  const [filter, setFilter] = useState('all'); // 'all' | 'photos' | 'videos'
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);

    // Debounce: clear previous timer before setting a new one
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      Promise.all([
        searchImages(searchQuery).catch(() => []),
        searchVideos(searchQuery).catch(() => []),
      ])
        .then(([images, videos]) => {
          const taggedImages = (images || []).map((img) => ({ ...img, type: 'photo', mediaType: 'photo' }));
          const taggedVideos = (videos || []).map((vid) => ({ ...vid, type: 'video', mediaType: 'video' }));
          const combined = [...taggedImages, ...taggedVideos].sort(
            (a, b) => (b.similarity ?? b.score ?? 0) - (a.similarity ?? a.score ?? 0)
          );
          setSearchResults(combined);
        })
        .finally(() => {
          setLoading(false);
        });
    }, 300);

    return () => clearTimeout(timerRef.current);
  }, [searchQuery, setSearchResults]);

  const handleSelect = useCallback(
    (id, shiftKey) => {
      shiftKey ? toggleImageSelection(id) : selectImage(id);
    },
    [selectImage, toggleImageSelection]
  );

  const clearSearch = () => setSearchQuery('');

  const photoCount = useMemo(
    () => searchResults.filter((item) => item.type === 'photo' || item.mediaType === 'photo' || item.mediaType === 'image').length,
    [searchResults]
  );
  const videoCount = useMemo(
    () => searchResults.filter((item) => item.type === 'video' || item.mediaType === 'video').length,
    [searchResults]
  );

  const filteredResults = useMemo(() => {
    if (filter === 'photos') {
      return searchResults.filter((item) => item.type === 'photo' || item.mediaType === 'photo' || item.mediaType === 'image');
    }
    if (filter === 'videos') {
      return searchResults.filter((item) => item.type === 'video' || item.mediaType === 'video');
    }
    return searchResults;
  }, [searchResults, filter]);

  const hasResults = searchResults.length > 0;
  const hasQuery   = searchQuery.trim().length > 0;
  const showEmpty  = hasQuery && !loading && !hasResults;

  const filterBtn = (id, label, Icon) => (
    <button
      key={id}
      onClick={() => setFilter(id)}
      className={`flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-all ${
        filter === id
          ? 'bg-foreground text-background shadow-sm'
          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      }`}
    >
      {Icon && <Icon size={13} />}
      <span>{label}</span>
    </button>
  );

  return (
    <div className="flex h-full flex-col overflow-auto">
      {/* Hero - shown before anything is typed */}
      <AnimatePresence>
        {!hasQuery && (
          <motion.div
            key="hero"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center justify-center px-6 pb-8 pt-24"
          >
            <motion.div
              className="mb-6 flex h-16 w-16 items-center justify-center rounded-3xl border border-primary/25 bg-primary/10 shadow-[0_18px_44px_-14px_hsl(var(--primary)/0.55)]"
              animate={{ y: [0, -4, 0] }}
              transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}
            >
              <Sparkles size={26} className="text-primary" />
            </motion.div>
            <h1 className="mb-3 max-w-xl text-center font-display text-[42px] font-semibold leading-[1.1] text-foreground">
              What are you looking for?
            </h1>
            <p className="mb-9 max-w-md text-center text-[15px] leading-relaxed text-muted-foreground">
              Describe a scene, a feeling or a moment in your own words. Cove looks at what is actually in your photos and videos, not at their file names.
            </p>

            <div className="flex max-w-2xl flex-wrap justify-center gap-2.5">
              {SUGGESTIONS.map((suggestion, i) => (
                <motion.button
                  key={suggestion}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.04 }}
                  onClick={() => setSearchQuery(suggestion)}
                  className="rounded-full border border-border bg-card/60 px-4 py-2 text-[13px] font-medium text-secondary-foreground transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/50 hover:bg-card hover:text-foreground"
                >
                  {suggestion}
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading */}
      <AnimatePresence>
        {loading && (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="px-7 pt-8" aria-busy="true">
            <p className="mb-6 font-display text-[22px] italic text-muted-foreground">
              Looking for &ldquo;{searchQuery}&rdquo;…
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="shimmer aspect-square rounded-2xl" style={{ animationDelay: `${i * 60}ms` }} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      <AnimatePresence>
        {showEmpty && (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center px-6 py-24 text-center"
          >
            <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full border border-border bg-card">
              <Search size={26} strokeWidth={1.3} className="text-muted-foreground" />
            </div>
            <h2 className="font-display text-[26px] font-semibold text-foreground">Nothing matches that yet</h2>
            <p className="mt-2 max-w-sm text-[14px] leading-relaxed text-muted-foreground">
              No media found for &ldquo;{searchQuery}&rdquo;. Try describing objects, scenery, activities or colours.
            </p>
            <button
              onClick={clearSearch}
              className="mt-6 flex items-center gap-1.5 rounded-full border border-border px-4 py-2 text-[13px] font-medium text-primary transition-colors hover:bg-primary/10"
            >
              <X size={13} /> Clear search
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {hasResults && !loading && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="px-7 pb-10"
          >
            <div className="flex flex-wrap items-end justify-between gap-4 pb-5 pt-7">
              <div>
                <h1 className="font-display text-[30px] font-semibold leading-none text-foreground">
                  {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
                </h1>
                <p className="mt-2 text-[14px] text-muted-foreground">
                  for <span className="font-display italic text-foreground/80">&ldquo;{searchQuery}&rdquo;</span>
                </p>
              </div>

              <div className="flex items-center gap-1 rounded-full border border-border/80 bg-card/60 p-1">
                {filterBtn('all', `All (${searchResults.length})`)}
                {filterBtn('photos', `Photos (${photoCount})`, ImageIcon)}
                {filterBtn('videos', `Videos (${videoCount})`, Film)}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
              {filteredResults.map((item, i) => (
                <motion.div
                  key={item.path ? `${item.type || item.mediaType || 'media'}_${item.path}` : `${item.type || item.mediaType || 'media'}_${item.id ?? i}`}
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: Math.min(i * 0.015, 0.4), duration: 0.2 }}
                >
                  <PhotoCard
                    image={item}
                    isSelected={selectedImages.has(item.id)}
                    onSelect={handleSelect}
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
