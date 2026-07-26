/**
 * Top command bar — Raycast-inspired with semantic search, status indicators,
 * theme toggle, and file import.
 */
import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, FolderOpen, Cpu, Zap, Sun, Moon, X } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';

export function CommandBar() {
  const [focused, setFocused] = useState(false);

  const inputRef        = useRef(null);
  const searchQuery     = useAppStore((s) => s.searchQuery);
  const setSearchQuery  = useAppStore((s) => s.setSearchQuery);
  const setActiveView   = useAppStore((s) => s.setActiveView);
  const activeView      = useAppStore((s) => s.activeView);
  const indexingStatus  = useAppStore((s) => s.indexingStatus);
  const hardwareInfo    = useAppStore((s) => s.hardwareInfo);
  const theme           = useAppStore((s) => s.theme);
  const toggleTheme     = useAppStore((s) => s.toggleTheme);
  const importFiles     = useAppStore((s) => s.importFiles);

  // Auto-focus when navigating to search view
  useEffect(() => {
    if (activeView === 'search' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [activeView]);

  const handleSearch = (value) => {
    setSearchQuery(value);
    if (value.length > 0 && activeView !== 'search') {
      setActiveView('search');
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    inputRef.current?.focus();
  };

  const handleImportClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'image/*,video/*';
    input.onchange = (e) => {
      if (e.target.files?.length) {
        const count = importFiles(e.target.files);
        toast.success(`Imported ${count} file${count > 1 ? 's' : ''}`);
      }
    };
    input.click();
  };

  return (
    <div className="flex h-[52px] items-center gap-3 border-b border-border px-4 bg-surface/50 flex-shrink-0 backdrop-blur-sm">
      {/* Search input */}
      <motion.div
        className={`
          relative flex flex-1 max-w-2xl items-center gap-2.5 rounded-lg px-3 py-[7px]
          transition-all duration-200
          ${focused
            ? 'bg-background border border-primary/50'
            : 'bg-muted/40 border border-transparent hover:bg-muted/60'}
        `}
        animate={
          focused
            ? { boxShadow: '0 0 0 3px hsl(var(--primary) / 0.12), 0 0 20px -4px hsl(var(--primary) / 0.25)' }
            : { boxShadow: 'none' }
        }
        transition={{ duration: 0.2 }}
      >
        <Search
          size={14}
          className={`flex-shrink-0 transition-colors ${focused ? 'text-primary' : 'text-muted-foreground'}`}
        />
        <input
          ref={inputRef}
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Search photos with CLIP AI…"
          aria-label="Search photos"
          className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground/70 outline-none"
        />
        {/* Clear button */}
        {searchQuery.length > 0 && (
          <button
            onMouseDown={(e) => { e.preventDefault(); handleClearSearch(); }}
            aria-label="Clear search"
            className="flex-shrink-0 p-0.5 rounded text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={12} />
          </button>
        )}
        <kbd className="hidden sm:inline-flex h-[18px] items-center rounded border border-border/60 bg-muted/50 px-1 text-[9px] font-mono text-muted-foreground flex-shrink-0">
          ⌘F
        </kbd>
      </motion.div>

      <div className="flex-1" />

      {/* Status & Actions */}
      <div className="flex items-center gap-2">
        {/* Indexing status pill */}
        {indexingStatus.isIndexing && (
          <button
            onClick={() => setActiveView('indexing')}
            title="View indexing status"
            className="flex items-center gap-1.5 rounded-full bg-success/10 border border-success/20 px-2.5 py-1 hover:bg-success/20 transition-colors"
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inset-0 rounded-full bg-success animate-pulse" />
              <span className="rounded-full bg-success h-1.5 w-1.5" />
            </span>
            <span className="text-[10px] font-medium text-success mono">
              {Math.round(indexingStatus.progress)}%
            </span>
          </button>
        )}

        {/* Hardware info */}
        <div
          className="hidden md:flex items-center gap-1 rounded-full bg-muted/40 border border-border/40 px-2.5 py-1"
          title={`CPU: ${hardwareInfo.cpuUsage}%${hardwareInfo.gpuAvailable ? ` · GPU: ${hardwareInfo.gpuUsage}%` : ''}`}
        >
          <Cpu size={11} className="text-muted-foreground" />
          <span className="text-[10px] mono text-muted-foreground">{hardwareInfo.cpuUsage}%</span>
          {hardwareInfo.gpuAvailable && (
            <>
              <span className="text-muted-foreground/30 mx-0.5">·</span>
              <Zap size={11} className="text-primary" />
              <span className="text-[10px] mono text-muted-foreground">{hardwareInfo.gpuUsage}%</span>
            </>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {/* Import Button */}
        <button
          onClick={handleImportClick}
          aria-label="Import photos or videos"
          className="flex items-center gap-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/20 px-3 py-[6px] text-[12px] font-medium text-primary transition-colors"
        >
          <FolderOpen size={13} />
          <span className="hidden sm:inline">Import</span>
        </button>
      </div>
    </div>
  );
}
