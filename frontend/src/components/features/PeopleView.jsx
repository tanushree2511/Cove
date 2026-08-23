/**
 * People view — unified face clusters from both photos and videos.
 * Paginated, interactive avatars with inline renaming.
 * Clicking a person filters the unified library.
 */
import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Loader2, ChevronLeft, ChevronRight, Edit2, Check, X, Film, Image as ImageIcon } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchClusters, renamePerson } from '@/lib/coveApi';
import { fetchAllVideoPersons, renameVideoPerson } from '@/lib/videoApi';
import { toast } from 'sonner';

const PAGE_SIZE = 200;

export function PeopleView() {
  const setPersonFilter = useAppStore((s) => s.setPersonFilter);
  const setActiveView   = useAppStore((s) => s.setActiveView);

  const [people, setPeople]       = useState([]);
  const [total, setTotal]         = useState(0);
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

      // Combine photo clusters with video people
      const combined = [...photoPeople, ...videoPersons];
      setPeople(combined);
      setTotal(combined.length);
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

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <Loader2 size={24} className="animate-spin text-primary" />
        <p className="text-[13px] text-muted-foreground">Loading people across photos and videos…</p>
      </div>
    );
  }

  if (!loading && total === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-5">
        <motion.div
          className="h-16 w-16 rounded-2xl bg-muted/50 flex items-center justify-center"
          animate={{ y: [0, -4, 0] }}
          transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
        >
          <Users size={28} strokeWidth={1.2} className="text-muted-foreground" />
        </motion.div>
        <div className="text-center space-y-1.5">
          <h2 className="text-base font-medium text-foreground">No people found</h2>
          <p className="text-[13px] text-muted-foreground">Import photos or videos with recognizable faces to discover and group people</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3 flex-shrink-0 border-b border-border/40">
        <div className="flex items-baseline gap-2">
          <h1 className="text-[15px] font-semibold text-foreground">People</h1>
          <span className="text-[11px] text-muted-foreground mono">{total.toLocaleString()} people recognized</span>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadPage(page - 1)}
              disabled={page === 0 || loading}
              className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={15} />
            </button>
            <span className="text-[12px] text-muted-foreground mono">
              {page + 1} / {totalPages}
            </span>
            <button
              onClick={() => loadPage(page + 1)}
              disabled={page >= totalPages - 1 || loading}
              className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-30 transition-colors"
            >
              <ChevronRight size={15} />
            </button>
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto px-5 py-5">
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-5">
          {people.map((cluster, i) => (
            <motion.div
              key={cluster.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.015, 0.5), duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
              onClick={() => handlePersonClick(cluster)}
              role="button"
              tabIndex={0}
              aria-label={`Filter by ${cluster.name}, ${cluster.count} occurrences`}
              className="flex flex-col items-center gap-2.5 cursor-pointer group text-left relative select-none"
            >
              {/* Avatar */}
              <motion.div
                whileHover={{ scale: 1.06 }}
                whileTap={{ scale: 0.96 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className="relative h-20 w-20 rounded-full overflow-hidden bg-muted/60 ring-2 ring-transparent group-hover:ring-primary/50 transition-all duration-200 shadow-sm"
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
                  className="h-full w-full items-center justify-center bg-muted text-muted-foreground font-semibold text-sm"
                  style={{ display: cluster.thumbnail ? 'none' : 'flex' }}
                >
                  {cluster.name ? cluster.name.charAt(0).toUpperCase() : '?'}
                </div>

                {/* Source badge indicator */}
                <div className="absolute bottom-0 right-0 p-1 bg-black/60 backdrop-blur-sm rounded-tl-md text-white">
                  {cluster.sourceType === 'video' ? <Film size={10} /> : <ImageIcon size={10} />}
                </div>
              </motion.div>

              {/* Name & Count */}
              <div className="w-full text-center px-1">
                {editingId === cluster.id ? (
                  <div
                    className="flex items-center justify-center gap-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveRename(e, cluster);
                        if (e.key === 'Escape') cancelEditing(e);
                      }}
                      autoFocus
                      className="w-24 px-1.5 py-0.5 text-[11px] rounded border border-primary bg-background text-foreground text-center focus:outline-none"
                    />
                    <button
                      onClick={(e) => saveRename(e, cluster)}
                      className="p-1 text-primary hover:bg-primary/10 rounded"
                    >
                      <Check size={12} />
                    </button>
                    <button
                      onClick={cancelEditing}
                      className="p-1 text-muted-foreground hover:bg-muted rounded"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-1 group/name">
                    <span className="text-[12px] font-medium text-foreground truncate max-w-[100px]">
                      {cluster.name}
                    </span>
                    <button
                      onClick={(e) => startEditing(e, cluster)}
                      className="opacity-0 group-hover/name:opacity-100 hover:text-primary text-muted-foreground transition-opacity"
                    >
                      <Edit2 size={10} />
                    </button>
                  </div>
                )}
                <span className="text-[10px] text-muted-foreground mono block">
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
