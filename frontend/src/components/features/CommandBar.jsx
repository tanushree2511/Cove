/**
 * Top command bar — Raycast-inspired with semantic search, status indicators,
 * theme toggle, and file import.
 */
import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Plus, Cpu, Zap, Sun, Moon, X } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { toast } from 'sonner';
import { fetchAllImages, uploadImages } from '@/lib/coveApi';
import { fetchVideos, uploadVideos } from '@/lib/videoApi';

export function CommandBar() {
  const [focused, setFocused] = useState(false);

  const inputRef        = useRef(null);
  const fileInputRef    = useRef(null);
  const searchQuery     = useAppStore((s) => s.searchQuery);
  const setSearchQuery  = useAppStore((s) => s.setSearchQuery);
  const setActiveView   = useAppStore((s) => s.setActiveView);
  const activeView      = useAppStore((s) => s.activeView);
  const indexingStatus  = useAppStore((s) => s.indexingStatus);
  const systemStats     = useAppStore((s) => s.systemStats);
  const setImages       = useAppStore((s) => s.setImages);
  const setVideos       = useAppStore((s) => s.setVideos);
  const setIndexingStatus      = useAppStore((s) => s.setIndexingStatus);
  const setVideoIndexingStatus = useAppStore((s) => s.setVideoIndexingStatus);
  const theme                  = useAppStore((s) => s.theme);
  const toggleTheme            = useAppStore((s) => s.toggleTheme);
  const setUploadState         = useAppStore((s) => s.setUploadState);

  // Auto-focus when navigating to search view
  useEffect(() => {
    if (activeView === 'search' && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [activeView]);

  useEffect(() => {
    const handleFocusSearch = () => {
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.select();
      }
    };
    window.addEventListener('focus-search-input', handleFocusSearch);
    return () => window.removeEventListener('focus-search-input', handleFocusSearch);
  }, []);

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

  const processSelectedFiles = async (files) => {
    if (!files || files.length === 0) return;
    const photoFiles = files.filter(f => !/\.(mp4|mov|avi|mkv|webm)$/i.test(f.name) && !f.type.startsWith('video/'));
    const videoFiles = files.filter(f => /\.(mp4|mov|avi|mkv|webm)$/i.test(f.name) || f.type.startsWith('video/'));
    const mediaType = videoFiles.length > 0 && photoFiles.length === 0 ? 'video' : 'photo';

    setUploadState({
      isUploading: true,
      isCompleted: false,
      totalFiles: files.length,
      currentFileIndex: 1,
      fileName: files[0]?.name || '',
      mediaType,
      progress: 0,
      bytesUploaded: 0,
      totalBytes: files.reduce((acc, f) => acc + f.size, 0),
      error: null,
    });

    try {
      if (photoFiles.length > 0) {
        const uploadRes = await uploadImages(photoFiles, (info) => {
          setUploadState({
            progress: info.percent,
            bytesUploaded: info.loaded,
            totalBytes: info.total,
            fileName: info.fileName,
          });
        });
        if (uploadRes?.indexing_started || (uploadRes?.saved && uploadRes.saved.length > 0)) {
          setIndexingStatus({
            isIndexing: true,
            status: 'running',
            stage: 'detecting',
            progress: 0,
            processed: 0,
            total: photoFiles.length,
            message: `AI analyzing ${photoFiles.length} photo(s)...`,
          });
        }
      }

      if (videoFiles.length > 0) {
        await uploadVideos(videoFiles, (info) => {
          setUploadState({
            progress: info.percent,
            bytesUploaded: info.loaded,
            totalBytes: info.total,
            fileName: info.fileName,
          });
        });
        setVideoIndexingStatus({
          status: 'processing',
          current: 1,
          total: videoFiles.length,
          message: `AI analyzing ${videoFiles[0]?.name || 'video'} (1/${videoFiles.length})...`,
        });
      }

      setUploadState({
        isUploading: false,
        isCompleted: true,
        progress: 100,
      });

      toast.success(`Imported ${files.length} item${files.length !== 1 ? 's' : ''}`);
      fetchAllImages().then(setImages);
      fetchVideos().then(setVideos);
    } catch (err) {
      setUploadState({
        isUploading: false,
        isCompleted: false,
        error: err?.message || 'Upload failed',
      });
      toast.error(err?.message || 'Upload failed');
    }
  };

  const handleImportClick = async () => {
    if (typeof window !== 'undefined' && typeof window.showOpenFilePicker === 'function') {
      try {
        const handles = await window.showOpenFilePicker({
          multiple: true,
          types: [
            {
              description: 'Photos & Videos',
              accept: {
                'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.bmp'],
                'video/*': ['.mp4', '.mov', '.mkv', '.webm'],
              },
            },
          ],
        });
        if (handles && handles.length > 0) {
          const files = await Promise.all(handles.map((h) => h.getFile()));
          processSelectedFiles(files);
          return;
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
      }
    }
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e) => {
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if (files.length > 0) {
      processSelectedFiles(files);
    }
  };

  return (
    <div className="relative z-20 flex h-[72px] flex-shrink-0 items-center gap-4 border-b border-border/70 bg-background/60 px-7 backdrop-blur-md">
      {/* Hidden native file input element */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,video/*"
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* Search: the heart of the app - describe what you remember */}
      <motion.div
        className={`
          relative flex max-w-[640px] flex-1 items-center gap-3 rounded-2xl px-4 py-2.5
          transition-all duration-200
          ${focused
            ? 'bg-card border border-primary/60'
            : 'bg-card/60 border border-border/80 hover:bg-card hover:border-border'}
        `}
        animate={
          focused
            ? { boxShadow: '0 0 0 4px hsl(var(--primary) / 0.14), 0 14px 40px -14px hsl(var(--primary) / 0.45)' }
            : { boxShadow: 'none' }
        }
        transition={{ duration: 0.2 }}
      >
        <Sparkles
          size={17}
          className={`flex-shrink-0 transition-colors ${focused ? 'text-primary' : 'text-muted-foreground'}`}
        />
        <input
          ref={inputRef}
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Search by describing it - “dog on the beach”"
          aria-label="Search photos"
          className="flex-1 bg-transparent text-[15px] text-foreground outline-none placeholder:text-muted-foreground/70"
        />
        {searchQuery.length > 0 && (
          <button
            onMouseDown={(e) => { e.preventDefault(); handleClearSearch(); }}
            aria-label="Clear search"
            className="flex-shrink-0 rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X size={14} />
          </button>
        )}
        <kbd className="mono hidden h-6 flex-shrink-0 items-center rounded-md border border-border bg-muted/60 px-1.5 text-[10.5px] text-muted-foreground sm:inline-flex">
          ⌘K
        </kbd>
      </motion.div>

      {/* Status & actions */}
      <div className="ml-auto flex items-center gap-2.5">
        {indexingStatus.isIndexing && (
          <button
            onClick={() => setActiveView('indexing')}
            title="View indexing status"
            className="flex items-center gap-2 rounded-full border border-success/25 bg-success/10 px-3 py-1.5 transition-colors hover:bg-success/20"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inset-0 animate-pulse rounded-full bg-success" />
              <span className="h-2 w-2 rounded-full bg-success" />
            </span>
            <span className="mono text-[11px] font-medium text-success">
              {Math.round(indexingStatus.progress)}%
            </span>
          </button>
        )}

        {/* Where the work runs */}
        <div
          className="hidden items-center gap-2 rounded-full border border-border/70 bg-card/60 px-3 py-1.5 md:flex"
          title={`${systemStats.totalImages.toLocaleString()} photos · ${systemStats.poolSize} workers · ${systemStats.gpuAvailable ? 'GPU accelerated' : 'CPU only'}`}
        >
          {systemStats.gpuAvailable
            ? <Zap size={13} className="text-primary" />
            : <Cpu size={13} className="text-muted-foreground" />}
          <span className="text-[12px] text-muted-foreground">
            {systemStats.gpuAvailable ? 'GPU' : 'CPU'}
            <span className="mx-1.5 text-border">|</span>
            <span className="mono tabular">{systemStats.poolSize}</span> workers
          </span>
        </div>

        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          className="rounded-full p-2.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>

        <button
          onClick={handleImportClick}
          aria-label="Import photos"
          className="flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-[14px] font-semibold text-primary-foreground shadow-[0_8px_24px_-8px_hsl(var(--primary)/0.7)] transition-all hover:brightness-110 active:scale-[0.97]"
        >
          <Plus size={16} strokeWidth={2.6} />
          <span className="hidden sm:inline">Import</span>
        </button>
      </div>
    </div>
  );
}
