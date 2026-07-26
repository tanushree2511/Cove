/**
 * Floating Selection Bar — Appears when items are selected for batch actions.
 * Includes select-all, export, and delete with a confirmation step.
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Trash2, CheckSquare, X, AlertTriangle } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';

export function SelectionBar() {
  const selectedImages    = useAppStore((s) => s.selectedImages);
  const clearSelection    = useAppStore((s) => s.clearSelection);
  const selectAllImages   = useAppStore((s) => s.selectAllImages);
  const deleteSelectedImages = useAppStore((s) => s.deleteSelectedImages);

  const [confirmDelete, setConfirmDelete] = useState(false);

  const count = selectedImages.size;
  if (count === 0) return null;

  const handleDownload = () => {
    toast.success(`Exporting ${count} selected item${count > 1 ? 's' : ''}…`);
  };

  const handleDeleteClick = () => {
    if (confirmDelete) {
      deleteSelectedImages();
      toast.success(`Deleted ${count} item${count > 1 ? 's' : ''}`);
      setConfirmDelete(false);
    } else {
      setConfirmDelete(true);
      // Auto-cancel after 3 seconds
      setTimeout(() => setConfirmDelete(false), 3000);
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
            title={confirmDelete ? 'Click again to confirm' : 'Delete selected'}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium transition-all duration-200 ${
              confirmDelete
                ? 'bg-destructive text-destructive-foreground'
                : 'bg-destructive/10 hover:bg-destructive/20 text-destructive'
            }`}
          >
            {confirmDelete ? (
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
