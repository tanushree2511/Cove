/**
 * Semantic search — CLIP-powered results grid with suggestion chips.
 * Unifies photos and videos search with type filters and similarity ranking.
 */
import { useEffect, useCallback, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, Loader2, X, Image as ImageIcon, Film } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { searchImages } from '@/lib/coveApi';
import { searchVideos } from '@/lib/videoApi';
import { PhotoCard } from './PhotoCard';

const SUGGESTIONS = [
  'beach sunset',
  'portrait photo',
  'mountain hike',
  'city skyline',
  'family dinner',
  'nature photography',
  'sports and cars',
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
            (a, b) => (b.similarity ?? 0) - (a.similarity ?? 0)
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

  return (
    <div className="h-full overflow-auto flex flex-col">
      {/* Hero — shown when no query */}
      <AnimatePresence>
        {!hasQuery && (
          <motion.div
            key="hero"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center justify-center pt-24 pb-8 px-4"
          >
            <motion.div
              className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 border border-primary/20 shadow-md"
              animate={{ y: [0, -3, 0] }}
              transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
            >
              <Sparkles size={22} className="text-primary" />
            </motion.div>
            <h1 className="text-lg font-semibold text-foreground mb-1.5">Unified AI Search</h1>
            <p className="text-[13px] text-muted-foreground mb-6 text-center max-w-sm leading-relaxed">
              Search photos and videos across your entire collection using natural language descriptions, scenes, and actions.
            </p>

            {/* Suggestion chips */}
            <div className="flex flex-wrap gap-1.5 justify-center max-w-md">
              {SUGGESTIONS.map((suggestion, i) => (
                <motion.button
                  key={suggestion}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.04 }}
                  onClick={() => setSearchQuery(suggestion)}
                  className="rounded-full border border-border bg-card hover:bg-muted/60 hover:border-primary/40 px-3 py-1.5 text-[11px] font-medium text-secondary-foreground transition-all duration-200"
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
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-center py-20"
          >
            <div className="flex items-center gap-2.5 text-[13px] text-muted-foreground">
              <Loader2 size={16} className="animate-spin text-primary" />
              Searching library for &ldquo;{searchQuery}&rdquo;…
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
            className="flex flex-col items-center justify-center py-20 text-muted-foreground"
          >
            <Search size={28} strokeWidth={1.2} className="mb-3 text-muted-foreground/50" />
            <p className="text-[13px]">No media found for &ldquo;{searchQuery}&rdquo;</p>
            <p className="text-[11px] text-muted-foreground/60 mt-1">Try describing objects, scenery, activities, or colors</p>
            <button
              onClick={clearSearch}
              className="mt-4 flex items-center gap-1.5 text-[11px] text-primary hover:underline"
            >
              <X size={12} /> Clear search
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
            className="px-5 pb-5"
          >
            <div className="flex items-center justify-between gap-2 mb-4 pt-3 border-b border-border/40 pb-3">
              <div className="flex items-baseline gap-2">
                <span className="text-[13px] font-semibold text-foreground">
                  {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
                </span>
                <span className="text-[11px] text-muted-foreground">for &ldquo;{searchQuery}&rdquo;</span>
              </div>

              {/* Type Filter Buttons */}
              <div className="flex items-center rounded-lg bg-muted/50 p-0.5 border border-border/60 text-xs">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                    filter === 'all'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  All ({searchResults.length})
                </button>
                <button
                  onClick={() => setFilter('photos')}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                    filter === 'photos'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <ImageIcon size={12} />
                  <span>Photos ({photoCount})</span>
                </button>
                <button
                  onClick={() => setFilter('videos')}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md font-medium transition-all ${
                    filter === 'videos'
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Film size={12} />
                  <span>Videos ({videoCount})</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-[3px]">
              {filteredResults.map((item, i) => (
                <motion.div
                  key={item.id}
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
