import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, CheckCircle2, AlertCircle, X, ArrowRight, Film, Image as ImageIcon, Loader2, Sparkles } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

export function UploadProgressModal() {
  const uploadState = useAppStore((s) => s.uploadState);
  const resetUploadState = useAppStore((s) => s.resetUploadState);
  const setActiveView = useAppStore((s) => s.setActiveView);
  const indexingStatus = useAppStore((s) => s.indexingStatus);

  const isVisible = Boolean(
    uploadState &&
    (uploadState.isUploading || uploadState.isCompleted || uploadState.error)
  );

  const isVideo = uploadState?.mediaType === 'video';
  const Icon = isVideo ? Film : ImageIcon;

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={resetUploadState}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
          />

          {/* Center Card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: 'spring', stiffness: 350, damping: 28 }}
            className="relative w-full max-w-md rounded-2xl bg-card border border-border/80 p-6 shadow-2xl overflow-hidden z-10"
          >
            {/* Close button */}
            <button
              onClick={resetUploadState}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Close"
            >
              <X size={16} />
            </button>

            {/* Header / Icon */}
            <div className="flex items-center gap-3.5 mb-5">
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-xl transition-colors ${
                  uploadState.error
                    ? 'bg-destructive/15 text-destructive'
                    : uploadState.isCompleted
                    ? 'bg-success/15 text-success'
                    : 'bg-primary/15 text-primary'
                }`}
              >
                {uploadState.error ? (
                  <AlertCircle size={24} />
                ) : uploadState.isCompleted ? (
                  <CheckCircle2 size={24} />
                ) : (
                  <UploadCloud size={24} className="animate-pulse" />
                )}
              </div>

              <div>
                <h3 className="text-base font-semibold text-foreground tracking-tight">
                  {uploadState.error
                    ? 'Import Failed'
                    : uploadState.isCompleted
                    ? 'Import Complete!'
                    : `Importing ${uploadState.totalFiles || ''} ${isVideo ? 'Video' : 'Photo'}${uploadState.totalFiles !== 1 ? 's' : ''}`}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-[260px]">
                  {uploadState.error
                    ? uploadState.error
                    : uploadState.isCompleted
                    ? `Successfully added ${uploadState.totalFiles} item${uploadState.totalFiles !== 1 ? 's' : ''} to library`
                    : uploadState.fileName
                    ? `Uploading: ${uploadState.fileName}`
                    : 'Sending files to server…'}
                </p>
              </div>
            </div>

            {/* Progress Section */}
            <div className="space-y-3 mb-6 bg-muted/40 p-4 rounded-xl border border-border/50">
              <div className="flex items-baseline justify-between text-xs mono">
                <span className="text-muted-foreground font-medium">
                  {uploadState.totalBytes > 0
                    ? `${formatBytes(uploadState.bytesUploaded)} / ${formatBytes(uploadState.totalBytes)}`
                    : `File ${uploadState.currentFileIndex || 1} of ${uploadState.totalFiles || 1}`}
                </span>
                <span className="text-sm font-bold text-primary mono">
                  {Math.round(uploadState.progress)}%
                </span>
              </div>

              {/* Animated Progress Bar */}
              <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${
                    uploadState.error
                      ? 'bg-destructive'
                      : uploadState.isCompleted
                      ? 'bg-success'
                      : 'bg-primary'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(4, uploadState.progress)}%` }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                />
              </div>

              {/* Sub-step indicator */}
              <div className="flex items-center gap-2 pt-1 text-[11px] text-muted-foreground">
                {uploadState.isUploading && (
                  <>
                    <Loader2 size={12} className="animate-spin text-primary" />
                    <span>Transferring media & writing to disk…</span>
                  </>
                )}
                {uploadState.isCompleted && (
                  <>
                    <Sparkles size={12} className="text-success" />
                    <span className="text-success font-medium">
                      {indexingStatus?.isIndexing ? 'AI Face & CLIP indexing running in background' : 'Ready in library'}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={resetUploadState}
                className="px-4 py-2 text-xs font-medium rounded-lg border border-border hover:bg-muted text-foreground transition-colors"
              >
                {uploadState.isCompleted ? 'Done' : 'Close'}
              </button>

              {uploadState.isCompleted && (
                <button
                  onClick={() => {
                    setActiveView('indexing');
                    resetUploadState();
                  }}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
                >
                  <span>View Pipeline</span>
                  <ArrowRight size={13} />
                </button>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
