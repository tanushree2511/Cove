/**
 * VideoView — Browse video library with tag filters and video player dialog.
 */
import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Film, Plus, Play } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';

const VIDEO_DATA = [
  { id: 1,  title: 'Summer Trip 2024',   duration: '3:24',  res: '4K',    date: 'Jun 2024', size: '1.2 GB',  thumb: 'https://picsum.photos/seed/vid1/400/225',  tags: ['travel', 'outdoor'] },
  { id: 2,  title: 'Birthday Party',     duration: '12:07', res: '1080p', date: 'Mar 2024', size: '820 MB', thumb: 'https://picsum.photos/seed/vid2/400/225',  tags: ['family', 'celebration'] },
  { id: 3,  title: 'Mountain Hike',      duration: '5:41',  res: '4K',    date: 'Feb 2024', size: '2.1 GB',  thumb: 'https://picsum.photos/seed/vid3/400/225',  tags: ['nature', 'travel'] },
  { id: 4,  title: 'City Time-lapse',    duration: '1:08',  res: '4K',    date: 'Jan 2024', size: '340 MB', thumb: 'https://picsum.photos/seed/vid4/400/225',  tags: ['urban'] },
  { id: 5,  title: 'Sunset Beach',       duration: '7:55',  res: '1080p', date: 'Dec 2023', size: '650 MB', thumb: 'https://picsum.photos/seed/vid5/400/225',  tags: ['nature', 'travel'] },
  { id: 6,  title: 'Wedding Highlights', duration: '18:30', res: '4K',    date: 'Nov 2023', size: '4.8 GB',  thumb: 'https://picsum.photos/seed/vid6/400/225',  tags: ['family', 'celebration'] },
  { id: 7,  title: 'Forest Walk',        duration: '4:12',  res: '1080p', date: 'Oct 2023', size: '490 MB', thumb: 'https://picsum.photos/seed/vid7/400/225',  tags: ['nature'] },
  { id: 8,  title: 'Cooking Session',    duration: '22:15', res: '1080p', date: 'Sep 2023', size: '1.8 GB',  thumb: 'https://picsum.photos/seed/vid8/400/225',  tags: ['indoor'] },
  { id: 9,  title: 'Road Trip Day 1',    duration: '9:03',  res: '4K',    date: 'Aug 2023', size: '3.2 GB',  thumb: 'https://picsum.photos/seed/vid9/400/225',  tags: ['travel'] },
  { id: 10, title: 'Kids Playing',       duration: '6:47',  res: '1080p', date: 'Jul 2023', size: '720 MB', thumb: 'https://picsum.photos/seed/vid10/400/225', tags: ['family'] },
  { id: 11, title: 'Drone Footage',      duration: '2:33',  res: '4K',    date: 'Jun 2023', size: '980 MB', thumb: 'https://picsum.photos/seed/vid11/400/225', tags: ['outdoor', 'travel'] },
  { id: 12, title: 'Concert Night',      duration: '45:00', res: '1080p', date: 'May 2023', size: '6.1 GB',  thumb: 'https://picsum.photos/seed/vid12/400/225', tags: ['celebration'] },
];

const FILTERS = ['all', 'travel', 'nature', 'family', 'urban', 'outdoor', 'celebration', 'indoor'];

/** Parse a size string like "1.2 GB" or "820 MB" into a GB float */
function parseSizeGB(sizeStr) {
  const n = parseFloat(sizeStr);
  return sizeStr.includes('GB') ? n : n / 1024;
}

const totalGB = VIDEO_DATA.reduce((acc, v) => acc + parseSizeGB(v.size), 0).toFixed(1);

export function VideoView() {
  const [filter,    setFilter]    = useState('all');
  const [hoveredId, setHoveredId] = useState(null);
  const openMediaModal = useAppStore((s) => s.openMediaModal);
  const importFiles    = useAppStore((s) => s.importFiles);

  const videos = filter === 'all'
    ? VIDEO_DATA
    : VIDEO_DATA.filter((v) => v.tags.includes(filter));

  const handleImport = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'video/*';
    input.onchange = (e) => {
      if (e.target.files?.length) {
        const count = importFiles(e.target.files);
        toast.success(`Imported ${count} video${count > 1 ? 's' : ''}`);
      }
    };
    input.click();
  }, [importFiles]);

  return (
    <div className="h-full overflow-auto flex flex-col">
      {/* Header */}
      <div className="px-5 pt-5 pb-3 flex-shrink-0">
        <div className="flex items-start justify-between mb-1">
          <div>
            <h1 className="text-[15px] font-semibold text-foreground tracking-tight flex items-center gap-2">
              <Film size={16} className="text-primary" />
              Videos
            </h1>
            <p className="text-[12px] text-muted-foreground mt-0.5">
              <span className="font-medium text-foreground">{VIDEO_DATA.length}</span> videos
              {' · '}
              <span className="font-medium text-foreground">{totalGB} GB</span>
            </p>
          </div>
          <button
            onClick={handleImport}
            aria-label="Import videos"
            className="flex items-center gap-1.5 rounded-md bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1.5 text-[12px] font-medium transition-colors border border-primary/20"
          >
            <Plus size={13} />
            Import Videos
          </button>
        </div>

        {/* Filter chips */}
        <div role="group" aria-label="Filter videos by tag" className="flex flex-wrap gap-1.5 mt-3">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              aria-pressed={filter === f}
              className={`rounded-full px-3 py-1 text-[11px] font-medium transition-all duration-150 capitalize ${
                filter === f
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-card border border-border text-secondary-foreground hover:border-primary/40 hover:text-foreground'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Video grid */}
      <AnimatePresence mode="wait">
        <motion.div
          key={filter}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="px-5 pb-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
        >
          {videos.map((v, i) => (
            <motion.div
              key={v.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.22 }}
              onClick={() => openMediaModal('video', v)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  openMediaModal('video', v);
                }
              }}
              onMouseEnter={() => setHoveredId(v.id)}
              onMouseLeave={() => setHoveredId(null)}
              role="button"
              tabIndex={0}
              aria-label={`Play ${v.title}, ${v.duration}, ${v.res}`}
              className="group cursor-pointer rounded-xl overflow-hidden border border-border bg-card hover:border-primary/40 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {/* Thumbnail */}
              <div className="relative overflow-hidden" style={{ height: 150 }}>
                <img
                  src={v.thumb}
                  alt={v.title}
                  loading="lazy"
                  decoding="async"
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />

                {/* Play overlay */}
                <AnimatePresence>
                  {hoveredId === v.id && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.15 }}
                      className="absolute inset-0 flex items-center justify-center"
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm border border-white/30">
                        <Play size={14} fill="white" className="text-white ml-0.5" />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Resolution badge */}
                <div
                  className={`absolute top-2 right-2 rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wide ${
                    v.res === '4K'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-black/60 text-white backdrop-blur-sm'
                  }`}
                >
                  {v.res}
                </div>

                {/* Duration badge */}
                <div className="absolute bottom-2 right-2 rounded-md bg-black/60 backdrop-blur-sm px-2 py-0.5 text-[10px] font-medium text-white">
                  {v.duration}
                </div>
              </div>

              {/* Info */}
              <div className="p-3">
                <p className="text-[13px] font-medium text-foreground truncate mb-1">{v.title}</p>
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>{v.date}</span>
                  <span className="mono">{v.size}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>

      {/* Empty filter state */}
      {videos.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-20 text-muted-foreground"
        >
          <Film size={28} strokeWidth={1.2} className="mb-3 text-muted-foreground/40" />
          <p className="text-[13px]">No videos tagged &ldquo;{filter}&rdquo;</p>
          <p className="text-[11px] text-muted-foreground/50 mt-1">Try a different filter</p>
        </motion.div>
      )}
    </div>
  );
}
