/**
 * Floating Selection Bar — Appears when items are selected for batch actions.
 * Includes select-all, export, and delete with a confirmation step.
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Trash2, CheckSquare, X, AlertTriangle } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';
import { deleteImages, fetchClusters, fetchImages } from '@/lib/coveApi';
import { deleteVideos, fetchVideos } from '@/lib/videoApi';

export function SelectionBar() {
  const selectedImages      = useAppStore((s) => s.selectedImages);
  const clearSelection      = useAppStore((s) => s.clearSelection);
  const selectAllImages     = useAppStore((s) => s.selectAllImages);
  const images              = useAppStore((s) => s.images);
  const videos              = useAppStore((s) => s.videos);
  const setImages           = useAppStore((s) => s.setImages);
  const setVideos           = useAppStore((s) => s.setVideos);
  const setClusters         = useAppStore((s) => s.setClusters);
  const deleteSelectedMedia = useAppStore((s) => s.deleteSelectedMedia);

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const count = selectedImages.size;
  if (count === 0) return null;

  const handleDownload = () => {
    toast.success(`Exporting ${count} selected item${count > 1 ? 's' : ''}…`);
  };

  const handleDeleteClick = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      // Auto-cancel after 3 seconds
      setTimeout(() => setConfirmDelete(false), 3000);
      return;
    }

    setConfirmDelete(false);
    setDeleting(true);
    try {
      const selectedList = Array.from(selectedImages);
      const photoPaths = [];
      const videoIds = [];
      const videoPaths = [];
      const deletedPhotoIds = new Set();
      const deletedVideoIds = new Set();

      selectedList.forEach((id) => {
        const isVid = videos.some((v) => v.id === id || v.path === id) || /\.(mp4|mov|avi|mkv|webm)$/i.test(String(id));
        if (isVid) {
          const v = videos.find((v) => v.id === id || v.path === id);
          if (v?.id && typeof v.id === 'number') videoIds.push(v.id);
          else videoPaths.push(String(id));
          deletedVideoIds.add(id);
          if (v?.id) deletedVideoIds.add(v.id);
          if (v?.path) deletedVideoIds.add(v.path);
        } else {
          photoPaths.push(String(id));
          deletedPhotoIds.add(id);
        }
      });

      const promises = [];
      if (photoPaths.length > 0) promises.push(deleteImages(photoPaths));
      if (videoIds.length > 0 || videoPaths.length > 0) promises.push(deleteVideos({ videoIds, paths: videoPaths }));

      await Promise.all(promises);
      deleteSelectedMedia(deletedPhotoIds, deletedVideoIds);
      clearSelection();

      const details = [];
      if (photoPaths.length > 0) details.push(`${photoPaths.length} photo${photoPaths.length > 1 ? 's' : ''}`);
      if (deletedVideoIds.size > 0) details.push(`${deletedVideoIds.size} video${deletedVideoIds.size > 1 ? 's' : ''}`);
      toast.success(`Deleted ${details.join(' and ')}`);

      if (photoPaths.length > 0) {
        fetchImages(0, 1000).then(setImages);
        fetchClusters().then(setClusters);
      }
      if (deletedVideoIds.size > 0) {
        fetchVideos().then(setVideos);
      }
    } catch (err) {
      toast.error(err?.message || 'Delete failed');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 80, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        role="toolbar"
        aria-label="Selection actions"
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 rounded-full bg-card/90 border border-primary/30 px-4 py-2.5 shadow-2xl backdrop-blur-xl"
      >
        {/* Count */}
        <div className="flex items-center gap-2 border-r border-border pr-3">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
            {count > 99 ? '99+' : count}
          </span>
          <span className="text-[12px] font-medium text-foreground">Selected</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={selectAllImages}
            title="Select all photos"
            className="flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
          >
            <CheckSquare size={13} />
            <span>Select All</span>
          </button>

          <button
            onClick={handleDownload}
            title="Export selected"
            className="flex items-center gap-1.5 rounded-full bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1 text-[11px] font-medium transition-colors"
          >
            <Download size={13} />
            <span>Export</span>
          </button>

          <button
            onClick={handleDeleteClick}
            disabled={deleting}
            title={confirmDelete ? 'Click again to confirm' : 'Delete selected'}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium transition-all duration-200 disabled:opacity-50 ${
              confirmDelete
                ? 'bg-destructive text-destructive-foreground'
                : 'bg-destructive/10 hover:bg-destructive/20 text-destructive'
            }`}
          >
            {deleting ? (
              <span>Deleting…</span>
            ) : confirmDelete ? (
              <>
                <AlertTriangle size={13} />
                <span>Confirm?</span>
              </>
            ) : (
              <>
                <Trash2 size={13} />
                <span>Delete</span>
              </>
            )}
          </button>

          <button
            onClick={() => { clearSelection(); setConfirmDelete(false); }}
            aria-label="Clear selection"
            className="p-1 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors ml-1"
          >
            <X size={14} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
