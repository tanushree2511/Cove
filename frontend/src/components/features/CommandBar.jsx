/**
 * Top command bar — Raycast-inspired with semantic search, status indicators,
 * theme toggle, and file import.
 */
import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, FolderOpen, Cpu, Zap, Sun, Moon, X } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';
import { fetchImages, uploadImages } from '@/lib/coveApi';

export function CommandBar() {
  const [focused, setFocused] = useState(false);

  const inputRef        = useRef(null);
  const searchQuery     = useAppStore((s) => s.searchQuery);
  const setSearchQuery  = useAppStore((s) => s.setSearchQuery);
  const setActiveView   = useAppStore((s) => s.setActiveView);
  const activeView      = useAppStore((s) => s.activeView);
  const indexingStatus  = useAppStore((s) => s.indexingStatus);
  const systemStats     = useAppStore((s) => s.systemStats);
  const setImages       = useAppStore((s) => s.setImages);
  const theme           = useAppStore((s) => s.theme);
  const toggleTheme     = useAppStore((s) => s.toggleTheme);

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
    input.accept = 'image/jpeg,image/png';
    input.onchange = async (e) => {
      if (!e.target.files?.length) return;
      try {
        const result = await uploadImages(e.target.files);
        toast.success(
          `Uploaded ${result.count} image${result.count !== 1 ? 's' : ''}` +
            (result.indexing_started ? ' — indexing started' : '')
        );
        fetchImages(0, 1000).then(setImages);
        if (result.indexing_started) setActiveView('indexing');
      } catch {
        toast.error('Upload failed');
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

        {/* System info */}
        <div
          className="hidden md:flex items-center gap-1 rounded-full bg-muted/40 border border-border/40 px-2.5 py-1"
          title={`${systemStats.totalImages.toLocaleString()} photos · ${systemStats.poolSize} workers · ${systemStats.gpuAvailable ? 'GPU accelerated' : 'CPU only'}`}
        >
          <Cpu size={11} className="text-muted-foreground" />
          <span className="text-[10px] mono text-muted-foreground">{systemStats.poolSize}w</span>
          <span className="text-muted-foreground/30 mx-0.5">·</span>
          <Zap size={11} className={systemStats.gpuAvailable ? 'text-primary' : 'text-muted-foreground/50'} />
          <span className="text-[10px] mono text-muted-foreground">{systemStats.gpuAvailable ? 'GPU' : 'CPU'}</span>
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
          aria-label="Import photos"
          className="flex items-center gap-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/20 px-3 py-[6px] text-[12px] font-medium text-primary transition-colors"
        >
          <FolderOpen size={13} />
          <span className="hidden sm:inline">Import</span>
        </button>
      </div>
    </div>
  );
}
