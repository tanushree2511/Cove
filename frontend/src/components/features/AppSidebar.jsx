/**
 * Left navigation: the Cove wordmark, two groups of destinations, live indexing status, and a quiet reminder that
 * everything stays on this device. Collapses to an icon rail.
 */
import { motion, AnimatePresence } from 'framer-motion';
import {
  Images, Users, Search, Activity, Settings,
  ChevronsLeft, ChevronsRight, Film, Lock,
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { CoveMark } from '@/components/CoveMark';

const GROUPS = [
  {
    label: 'Browse',
    items: [
      { id: 'library',  label: 'Library',  icon: Images },
      { id: 'people',   label: 'People',   icon: Users  },
      { id: 'video',    label: 'Videos',   icon: Film   },
      { id: 'search',   label: 'Search',   icon: Search },
    ],
  },
  {
    label: 'Manage',
    items: [
      { id: 'indexing', label: 'Indexing', icon: Activity },
      { id: 'settings', label: 'Settings', icon: Settings },
    ],
  },
];

export function AppSidebar() {
  const collapsed      = useAppStore((s) => s.sidebarCollapsed);
  const activeView     = useAppStore((s) => s.activeView);
  const setActiveView  = useAppStore((s) => s.setActiveView);
  const toggleSidebar  = useAppStore((s) => s.toggleSidebar);

  return (
    <div className="flex h-full flex-col bg-sidebar select-none border-r border-sidebar-border">
      {/* Brand */}
      <div className={`flex h-[72px] items-center flex-shrink-0 ${collapsed ? 'justify-center px-0' : 'gap-3 px-5'}`}>
        <CoveMark size={34} className="flex-shrink-0 drop-shadow-[0_6px_14px_hsl(var(--primary)/0.35)]" />
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="min-w-0 leading-none"
            >
              <div className="font-display text-[26px] font-semibold tracking-tight text-foreground">Cove</div>
              <div className="mt-1 text-[11px] text-muted-foreground">your photos &amp; videos, kept close</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 pb-2" aria-label="Main navigation">
        {GROUPS.map((group) => (
          <div key={group.label} className="mb-4">
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="eyebrow px-3 pb-2 pt-3"
                >
                  {group.label}
                </motion.p>
              )}
            </AnimatePresence>
            {collapsed && <div className="mx-3 my-3 h-px bg-sidebar-border" />}

            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = activeView === item.id;
                return (
                  <motion.button
                    key={item.id}
                    onClick={() => setActiveView(item.id)}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={collapsed ? item.label : undefined}
                    className={`
                      relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-[14px]
                      transition-colors duration-150
                      ${collapsed ? 'justify-center' : ''}
                      ${isActive
                        ? 'text-foreground font-medium'
                        : 'text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent/70'}
                    `}
                    whileTap={{ scale: 0.98 }}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active-bg"
                        className="absolute inset-0 rounded-xl bg-sidebar-accent ring-1 ring-inset ring-border/60"
                        transition={{ type: 'spring', stiffness: 500, damping: 36 }}
                      />
                    )}
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-indicator"
                        className="absolute -left-3 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-primary shadow-[0_0_12px_hsl(var(--primary)/0.8)]"
                        transition={{ type: 'spring', stiffness: 500, damping: 36 }}
                      />
                    )}

                    <item.icon
                      size={19}
                      strokeWidth={isActive ? 2.1 : 1.6}
                      className={`relative z-10 flex-shrink-0 ${isActive ? 'text-primary' : ''}`}
                    />

                    <AnimatePresence mode="wait">
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          transition={{ duration: 0.12 }}
                          className="relative z-10 flex flex-1 items-center justify-between gap-1.5 truncate whitespace-nowrap"
                        >
                          <span>{item.label}</span>
                          {item.id === 'indexing' && <IndexingNavBadge />}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </motion.button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Indexing mini-status */}
      <IndexingMini collapsed={collapsed} />

      {/* Footer: privacy note + collapse */}
      <div className="flex-shrink-0 border-t border-sidebar-border/70 p-3">
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mb-2 flex items-start gap-2 rounded-xl px-3 py-2 text-[11.5px] leading-snug text-muted-foreground"
            >
              <Lock size={13} className="mt-0.5 flex-shrink-0 text-success" />
              <span>Private by design. Your library never leaves this device.</span>
            </motion.div>
          )}
        </AnimatePresence>
        <button
          onClick={toggleSidebar}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="flex w-full items-center justify-center gap-2 rounded-xl p-2 text-muted-foreground transition-colors hover:bg-sidebar-accent/70 hover:text-foreground"
        >
          {collapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
          <AnimatePresence>
            {!collapsed && (
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-[12px]">
                Collapse
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </div>
  );
}

function IndexingNavBadge() {
  const photoStatus = useAppStore((s) => s.indexingStatus);
  const videoStatus = useAppStore((s) => s.videoIndexingStatus);

  const isPhotoActive = Boolean(photoStatus?.isIndexing || photoStatus?.status === 'running');
  const isVideoActive = Boolean(videoStatus?.status === 'processing');

  if (!isPhotoActive && !isVideoActive) return null;

  return (
    <span className="relative flex h-2 w-2">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
    </span>
  );
}

function IndexingMini({ collapsed }) {
  const photoStatus = useAppStore((s) => s.indexingStatus);
  const videoStatus = useAppStore((s) => s.videoIndexingStatus);

  const isPhotoActive = Boolean(photoStatus?.isIndexing || photoStatus?.status === 'running');
  const isVideoActive = Boolean(videoStatus?.status === 'processing');

  if (!isPhotoActive && !isVideoActive) return null;

  const stage = isVideoActive
    ? `Analysing videos · ${videoStatus.current || 0}/${videoStatus.total || 1}`
    : (photoStatus.stage || 'indexing');

  const progress = isVideoActive
    ? (videoStatus.total > 0 ? (videoStatus.current / videoStatus.total) * 100 : 50)
    : (photoStatus.progress || 0);

  return (
    <div className="mx-3 mb-3 rounded-xl border border-border/50 bg-sidebar-accent/60 p-3">
      <div className="flex items-center gap-2.5">
        <div className="relative h-2 w-2 flex-shrink-0">
          <span className="absolute inset-0 rounded-full bg-primary" />
          <span className="absolute inset-0 animate-pulse rounded-full bg-primary" />
        </div>

        <AnimatePresence>
          {!collapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="min-w-0 flex-1">
              <p className="truncate text-[11.5px] capitalize text-muted-foreground">{stage}</p>
              <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-muted">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                  animate={{ width: `${Math.max(5, progress)}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
