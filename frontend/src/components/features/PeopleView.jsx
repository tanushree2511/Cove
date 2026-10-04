/**
 * People view - unified face clusters from both photos and videos.
 * Paginated, interactive avatars with inline renaming.
 * Clicking a person filters the unified library.
 */
import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Users, ChevronLeft, ChevronRight, Pencil, Check, X, Film, Image as ImageIcon } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchClusters, renamePerson } from '@/lib/coveApi';
import { fetchAllVideoPersons, renameVideoPerson } from '@/lib/videoApi';
import { toast } from 'sonner';

const PAGE_SIZE = 200;

export function PeopleView() {
  const setPersonFilter = useAppStore((s) => s.setPersonFilter);
  const setActiveView   = useAppStore((s) => s.setActiveView);

  const [people, setPeople]       = useState([]);
  const [total, setTotal]         = useState(0);        // everyone: all photo clusters + all video people
  const [photoTotal, setPhotoTotal] = useState(0);      // photo clusters only - this is what the pager pages over
  const [page, setPage]           = useState(0);
  const [loading, setLoading]     = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName]   = useState('');

  const loadPage = useCallback(async (pageIndex) => {
    setLoading(true);
    try {
      const [photoResult, videoPersons] = await Promise.all([
        fetchClusters(pageIndex * PAGE_SIZE, PAGE_SIZE).catch(() => ({ people: [], total: 0 })),
        fetchAllVideoPersons().catch(() => []),
      ]);

      const photoPeople = (photoResult.people ?? []).map((p) => ({
        ...p,
        id: `photo_${p.id}`,
        sourceId: p.id,
        sourceType: 'photo',
        thumbnail: p.thumbnail || p.previewUrl,
        count: p.count ?? p.imageCount ?? p.photo_count ?? 1,
      }));

      // The pager walks the photo clusters; video people are listed once, on the first page. (This used to count
      // "this page's clusters + all video people" as the total, so a library with 666 clusters showed
      // "286 people / 2 pages", repeated the video people on every page and made later pages unreachable.)
      const serverPhotoTotal = photoResult.total ?? photoPeople.length;
      setPeople(pageIndex === 0 ? [...photoPeople, ...videoPersons] : photoPeople);
      setPhotoTotal(serverPhotoTotal);
      setTotal(serverPhotoTotal + videoPersons.length);
      setPage(pageIndex);
    } catch (err) {
      toast.error(`Failed to load people: ${err?.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPage(0);
  }, [loadPage]);

  const totalPages = Math.max(1, Math.ceil(photoTotal / PAGE_SIZE));

  const handlePersonClick = (cluster) => {
    if (editingId === cluster.id) return;
    setPersonFilter({
      id: cluster.id,
      sourceId: cluster.sourceId,
      sourceType: cluster.sourceType,
      name: cluster.name,
    });
    setActiveView('library');
    toast.info(`Showing media with ${cluster.name}`);
  };

  const startEditing = (e, cluster) => {
    e.stopPropagation();
    setEditingId(cluster.id);
    setEditName(cluster.name);
  };

  const cancelEditing = (e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditName('');
  };

  const saveRename = async (e, cluster) => {
    e.stopPropagation();
    const trimmed = editName.trim();
    if (!trimmed || trimmed === cluster.name) {
      setEditingId(null);
      return;
    }
    try {
      if (cluster.sourceType === 'video') {
        await renameVideoPerson(cluster.sourceId, trimmed);
      } else {
        await renamePerson(cluster.sourceId || cluster.id, trimmed);
      }
      setPeople((prev) =>
        prev.map((p) => (p.id === cluster.id ? { ...p, name: trimmed } : p))
      );
      toast.success(`Renamed to ${trimmed}`);
    } catch (err) {
      toast.error(`Failed to rename: ${err?.message}`);
    } finally {
      setEditingId(null);
    }
  };

  if (loading && people.length === 0) {
    return (
      <div className="flex h-full flex-col px-7 pt-8" aria-busy="true">
        <div className="shimmer mb-8 h-9 w-40 rounded-xl" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8">
          {Array.from({ length: 16 }).map((_, i) => (
            <div key={i} className="shimmer h-[168px] rounded-3xl" style={{ animationDelay: `${i * 50}ms` }} />
          ))}
        </div>
      </div>
    );
  }

  if (!loading && total === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-6 px-6">
        <motion.div
          className="flex h-24 w-24 items-center justify-center rounded-full border border-border bg-card"
          animate={{ y: [0, -5, 0] }}
          transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}
        >
          <Users size={36} strokeWidth={1.2} className="text-primary" />
        </motion.div>
        <div className="max-w-[400px] space-y-2 text-center">
          <h2 className="font-display text-[28px] font-semibold text-foreground">No people yet</h2>
          <p className="text-[15px] leading-relaxed text-muted-foreground">
            When your photos and videos contain faces, Cove groups them by person here, on this device, without sending anything anywhere.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex flex-shrink-0 items-end justify-between gap-4 px-7 pb-4 pt-7">
        <div>
          <h1 className="font-display text-[36px] font-semibold leading-none text-foreground">People</h1>
          <p className="tabular mt-2.5 text-[14px] text-muted-foreground">{total.toLocaleString()} people recognized</p>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-1 rounded-full border border-border/80 bg-card/60 p-1">
            <button
              onClick={() => loadPage(page - 1)}
              disabled={page === 0 || loading}
              aria-label="Previous page"
              className="rounded-full p-2 transition-colors hover:bg-muted disabled:opacity-30"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="mono tabular px-2 text-[12.5px] text-muted-foreground">
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => loadPage(page + 1)}
              disabled={page >= totalPages - 1 || loading}
              aria-label="Next page"
              className="rounded-full p-2 transition-colors hover:bg-muted disabled:opacity-30"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto px-7 pb-10 pt-2">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8">
          {people.map((cluster, i) => (
            <motion.div
              key={cluster.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.012, 0.4), duration: 0.28, ease: [0.2, 0.7, 0.2, 1] }}
              onClick={() => handlePersonClick(cluster)}
              role="button"
              tabIndex={0}
              aria-label={`Filter by ${cluster.name}, ${cluster.count} occurrences`}
              className="group relative flex cursor-pointer select-none flex-col items-center gap-3 rounded-3xl border border-transparent bg-card/40 px-3 pb-4 pt-5 text-left transition-all duration-200 hover:border-border hover:bg-card focus-visible:border-primary"
            >
              {/* Avatar */}
              <motion.div
                whileTap={{ scale: 0.96 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className="relative h-24 w-24 overflow-hidden rounded-full bg-muted ring-2 ring-border/70 ring-offset-4 ring-offset-transparent transition-all duration-300 group-hover:scale-105 group-hover:ring-primary"
              >
                {cluster.thumbnail ? (
                  <img
                    src={cluster.thumbnail}
                    alt={cluster.name}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling && (e.target.nextSibling.style.display = 'flex');
                    }}
                  />
                ) : null}
                <div
                  className="font-display h-full w-full items-center justify-center bg-muted text-2xl font-semibold text-muted-foreground"
                  style={{ display: cluster.thumbnail ? 'none' : 'flex' }}
                >
                  {cluster.name ? cluster.name.charAt(0).toUpperCase() : '?'}
                </div>
              </motion.div>

              {/* where this person was found */}
              <div className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full border border-border/70 bg-background/70 text-muted-foreground backdrop-blur-sm" title={cluster.sourceType === 'video' ? 'Found in videos' : 'Found in photos'}>
                {cluster.sourceType === 'video' ? <Film size={11} /> : <ImageIcon size={11} />}
              </div>

              {/* Name & count */}
              <div className="w-full px-1 text-center">
                {editingId === cluster.id ? (
                  <div className="flex items-center justify-center gap-1" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveRename(e, cluster);
                        if (e.key === 'Escape') cancelEditing(e);
                      }}
                      autoFocus
                      className="w-28 rounded-full border border-primary bg-background px-3 py-1 text-center text-[13px] text-foreground focus:outline-none"
                    />
                    <button onClick={(e) => saveRename(e, cluster)} aria-label="Save name" className="rounded-full p-1.5 text-primary hover:bg-primary/10">
                      <Check size={14} />
                    </button>
                    <button onClick={cancelEditing} aria-label="Cancel rename" className="rounded-full p-1.5 text-muted-foreground hover:bg-muted">
                      <X size={14} />
                    </button>
                  </div>
                ) : (
                  <div className="group/name flex items-center justify-center gap-1.5">
                    <span className="max-w-[110px] truncate text-[14px] font-medium text-foreground">{cluster.name}</span>
                    <button
                      onClick={(e) => startEditing(e, cluster)}
                      aria-label={`Rename ${cluster.name}`}
                      className="text-muted-foreground opacity-0 transition-opacity hover:text-primary group-hover/name:opacity-100 focus-visible:opacity-100"
                    >
                      <Pencil size={12} />
                    </button>
                  </div>
                )}
                <span className="tabular mt-0.5 block text-[12px] text-muted-foreground">
                  {cluster.count} {cluster.count === 1 ? 'item' : 'items'}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
