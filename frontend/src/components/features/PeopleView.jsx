/**
 * People view — face clusters displayed as avatar cards.
 * Clicking a person filters the photo library to show only their photos.
 */
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, Loader2 } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { fetchClusters } from '@/lib/mockApi';
import { toast } from 'sonner';

export function PeopleView() {
  const clusters       = useAppStore((s) => s.clusters);
  const setClusters    = useAppStore((s) => s.setClusters);
  const setPersonFilter = useAppStore((s) => s.setPersonFilter);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (clusters.length > 0) return;
    setLoading(true);
    fetchClusters()
      .then(setClusters)
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handlePersonClick = (cluster) => {
    setPersonFilter({ id: cluster.id, name: cluster.name });
    toast.info(`Showing photos of ${cluster.name}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <Loader2 size={24} className="animate-spin text-primary" />
        <p className="text-[13px] text-muted-foreground">Detecting faces…</p>
      </div>
    );
  }

  if (clusters.length === 0) {
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
          <p className="text-[13px] text-muted-foreground">Index your photos to discover and group faces</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-5">
      <div className="flex items-baseline gap-2 mb-5">
        <h1 className="text-[15px] font-semibold text-foreground">People</h1>
        <span className="text-[11px] text-muted-foreground mono">{clusters.length} people</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-5">
        {clusters.map((cluster, i) => (
          <motion.button
            key={cluster.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03, duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
            onClick={() => handlePersonClick(cluster)}
            aria-label={`Filter by ${cluster.name}, ${cluster.imageCount} photos`}
            className="flex flex-col items-center gap-2.5 cursor-pointer group text-left"
          >
            {/* Avatar */}
            <motion.div
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.96 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="relative w-20 h-20 rounded-full overflow-hidden ring-2 ring-border group-hover:ring-primary/60 transition-all duration-300 shadow-md"
            >
              <img
                src={cluster.previewUrl}
                alt={cluster.name}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                loading="lazy"
                decoding="async"
              />
              <div className="absolute inset-0 bg-primary/0 group-hover:bg-primary/10 transition-colors duration-300" />
            </motion.div>

            {/* Info */}
            <div className="text-center min-w-0 w-full">
              <p className="text-[12px] font-medium text-foreground truncate px-1 group-hover:text-primary transition-colors">
                {cluster.name}
              </p>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {cluster.imageCount.toLocaleString()} photos
              </p>
            </div>

            {/* Confidence bar */}
            <div className="w-10 h-[2px] rounded-full bg-muted overflow-hidden" title={`${Math.round(cluster.confidence * 100)}% confidence`}>
              <motion.div
                className="h-full bg-primary/60 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${cluster.confidence * 100}%` }}
                transition={{ delay: i * 0.03 + 0.3, duration: 0.5 }}
              />
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
