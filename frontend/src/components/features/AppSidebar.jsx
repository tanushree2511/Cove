/**
 * Collapsible left sidebar — Linear.app / Arc Browser inspired.
 * Icon-only compact mode with spring animation, active indicator, and tooltips.
 */
import { motion, AnimatePresence } from 'framer-motion';
import {
  Images, Users, Search, Activity, Settings,
  ChevronsLeft, ChevronsRight, Sparkles, Film,
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

const NAV_ITEMS = [
  { id: 'library',  label: 'Library',  icon: Images   },
  { id: 'people',   label: 'People',   icon: Users    },
  { id: 'video',    label: 'Videos',   icon: Film     },
  { id: 'search',   label: 'Search',   icon: Search   },
  { id: 'indexing', label: 'Indexing', icon: Activity },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function AppSidebar() {
  const collapsed      = useAppStore((s) => s.sidebarCollapsed);
  const activeView     = useAppStore((s) => s.activeView);
  const setActiveView  = useAppStore((s) => s.setActiveView);
  const toggleSidebar  = useAppStore((s) => s.toggleSidebar);

  return (
    <div className="flex h-full flex-col bg-sidebar select-none border-r border-sidebar-border">
      {/* Logo header */}
      <div className="flex h-[52px] items-center gap-2 px-3 flex-shrink-0">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 flex-shrink-0 border border-primary/20">
          <Sparkles size={14} className="text-primary" />
        </div>
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="flex-1 min-w-0"
            >
              <span className="text-[13px] font-semibold text-foreground tracking-tight">
                VisionArchive
              </span>
              <span className="text-[10px] text-primary ml-1 font-bold">PRO</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-1.5 px-2 space-y-0.5" aria-label="Main navigation">
        <AnimatePresence>
          {!collapsed && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="px-2 pb-1.5 pt-1 text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60"
            >
              Navigate
            </motion.p>
          )}
        </AnimatePresence>

        {NAV_ITEMS.map((item) => {
          const isActive = activeView === item.id;
          return (
            <motion.button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
              title={collapsed ? item.label : undefined}
              className={`
                relative flex w-full items-center gap-2.5 rounded-md px-2.5 py-[7px] text-[13px]
                transition-colors duration-100
                ${collapsed ? 'justify-center' : ''}
                ${isActive
                  ? 'text-foreground font-medium'
                  : 'text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent/60'}
              `}
              whileTap={{ scale: 0.98 }}
            >
              {/* Active background pill */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active-bg"
                  className="absolute inset-0 rounded-md bg-sidebar-accent"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
              {/* Active left indicator bar */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-indicator"
                  className="absolute -left-2 top-1/2 -translate-y-1/2 w-[3px] h-3.5 rounded-r-full bg-primary"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}

              <item.icon
                size={16}
                strokeWidth={isActive ? 2 : 1.5}
                className={`relative z-10 flex-shrink-0 ${isActive ? 'text-primary' : ''}`}
              />

              <AnimatePresence mode="wait">
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    transition={{ duration: 0.12 }}
                    className="relative z-10 truncate whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          );
        })}
      </nav>

      {/* Indexing mini-status */}
      <IndexingMini collapsed={collapsed} />

      {/* Collapse toggle */}
      <div className="p-2 flex-shrink-0 border-t border-sidebar-border/60">
        <button
          onClick={toggleSidebar}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="flex w-full items-center justify-center gap-2 rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/60 transition-colors"
        >
          {collapsed ? <ChevronsRight size={14} /> : <ChevronsLeft size={14} />}
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-[11px]"
              >
                Collapse
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </div>
  );
}

function IndexingMini({ collapsed }) {
  const { isIndexing, progress, stage } = useAppStore((s) => s.indexingStatus);
  if (!isIndexing) return null;

  return (
    <div className="mx-2 mb-1 rounded-md bg-sidebar-accent/50 p-2 border border-border/40">
      <div className="flex items-center gap-2">
        {/* Pulsing dot */}
        <div className="relative h-1.5 w-1.5 flex-shrink-0">
          <span className="absolute inset-0 rounded-full bg-success" />
          <span className="absolute inset-0 rounded-full bg-success animate-pulse" />
        </div>

        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 min-w-0"
            >
              <p className="text-[10px] text-muted-foreground capitalize truncate">{stage}</p>
              <div className="mt-1 h-[3px] rounded-full bg-muted overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-primary to-accent rounded-full"
                  animate={{ width: `${progress}%` }}
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
