/**
 * Main desktop layout with collapsible sidebar, top command bar, modals, and selection bar.
 */
import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '@/store/useAppStore';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { AppSidebar } from '@/components/features/AppSidebar';
import { CommandBar } from '@/components/features/CommandBar';
import { GalleryView } from '@/components/features/GalleryView';
import { PeopleView } from '@/components/features/PeopleView';
import { VideoView } from '@/components/features/VideoView';
import { SearchView } from '@/components/features/SearchView';
import { IndexingPanel } from '@/components/features/IndexingPanel';
import { SettingsView } from '@/components/features/SettingsView';
import { PhotoModal } from '@/components/features/PhotoModal';
import { VideoModal } from '@/components/features/VideoModal';
import { SelectionBar } from '@/components/features/SelectionBar';
import { UploadProgressModal } from '@/components/features/UploadProgressModal';
import { NetworkStatus } from '@/components/NetworkStatus';

const views = {
    library: GalleryView,
    people: PeopleView,
    video: VideoView,
    search: SearchView,
    indexing: IndexingPanel,
    settings: SettingsView,
};

export function DesktopLayout() {
    useKeyboardShortcuts();
    const sidebarCollapsed    = useAppStore((s) => s.sidebarCollapsed);
    const setSidebarCollapsed = useAppStore((s) => s.setSidebarCollapsed);

    // Narrow windows (phones, split screens): start with the slim rail so the content gets the room.
    useEffect(() => {
        const mq = window.matchMedia('(max-width: 767px)');
        if (mq.matches) setSidebarCollapsed(true);
        const onChange = (e) => { if (e.matches) setSidebarCollapsed(true); };
        mq.addEventListener('change', onChange);
        return () => mq.removeEventListener('change', onChange);
    }, [setSidebarCollapsed]);
    const activeView          = useAppStore((s) => s.activeView);
    const setActiveView       = useAppStore((s) => s.setActiveView);
    const indexingStatus      = useAppStore((s) => s.indexingStatus);
    const videoIndexingStatus = useAppStore((s) => s.videoIndexingStatus);

    const isPhotoIndexing = Boolean(indexingStatus?.isIndexing || indexingStatus?.status === 'running');
    const isVideoIndexing = Boolean(videoIndexingStatus?.status === 'processing');
    const isAnyIndexing   = (isPhotoIndexing || isVideoIndexing) && activeView !== 'indexing';

    const currentMsg = isVideoIndexing
        ? (videoIndexingStatus?.message || 'AI analyzing video keyframes & faces…')
        : (indexingStatus?.message || (indexingStatus?.stage === 'detecting' ? 'Detecting Faces…' : indexingStatus?.stage === 'embedding' ? 'Generating CLIP Search Embeddings…' : indexingStatus?.stage === 'clustering' ? 'Clustering People…' : 'Indexing Library…'));

    const currentProgress = isVideoIndexing
        ? (videoIndexingStatus?.total > 0 ? (videoIndexingStatus.current / videoIndexingStatus.total) * 100 : 50)
        : (indexingStatus?.progress || 0);

    const currentProcessed = isVideoIndexing ? videoIndexingStatus?.current : indexingStatus?.processed;
    const currentTotal     = isVideoIndexing ? videoIndexingStatus?.total : indexingStatus?.total;

    const ActiveComponent = views[activeView] || GalleryView;

    return (
        <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
            <NetworkStatus />

            {/* Sidebar with spring animation */}
            <motion.div
                className="h-full flex-shrink-0 overflow-hidden"
                animate={{ width: sidebarCollapsed ? 76 : 252 }}
                transition={{ type: 'spring', stiffness: 350, damping: 32, mass: 0.8 }}
            >
                <AppSidebar />
            </motion.div>

            {/* Main content */}
            <div className="cove-canvas cove-grain relative flex min-w-0 flex-1 flex-col">
                <CommandBar />
                
                {/* Global indexing progress: a slim pill under the top bar while anything is being analysed */}
                <AnimatePresence>
                    {isAnyIndexing && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="relative z-20 flex-shrink-0 overflow-hidden px-7"
                        >
                            <div className="my-2.5 flex items-center justify-between gap-4 rounded-full border border-primary/25 bg-primary/10 py-1.5 pl-4 pr-2 text-[13px] backdrop-blur-sm">
                                <div className="flex min-w-0 items-center gap-2.5">
                                    <span className="relative flex h-2 w-2 flex-shrink-0">
                                        <span className="absolute inset-0 animate-ping rounded-full bg-primary" />
                                        <span className="h-2 w-2 rounded-full bg-primary" />
                                    </span>
                                    <span className="truncate font-medium text-foreground">{currentMsg}</span>
                                    {currentTotal > 0 && (
                                        <span className="mono tabular flex-shrink-0 text-[11.5px] text-muted-foreground">
                                            {currentProcessed} / {currentTotal}
                                        </span>
                                    )}
                                </div>
                                <div className="flex flex-shrink-0 items-center gap-3">
                                    <div className="h-1.5 w-36 overflow-hidden rounded-full bg-muted">
                                        <div
                                            className="h-full rounded-full bg-gradient-to-r from-primary to-accent transition-all duration-300"
                                            style={{ width: `${Math.max(5, currentProgress)}%` }}
                                        />
                                    </div>
                                    <span className="mono tabular w-9 text-right text-[12px] font-semibold text-primary">{Math.round(currentProgress)}%</span>
                                    <button
                                        onClick={() => setActiveView('indexing')}
                                        className="rounded-full bg-primary/15 px-3 py-1 text-[12px] font-medium text-primary transition-colors hover:bg-primary/25"
                                    >
                                        View Pipeline →
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <AnimatePresence mode="wait">
                    <motion.main
                        key={activeView}
                        className="relative z-10 flex-1 overflow-hidden"
                        initial={{ opacity: 0, y: 6, filter: 'blur(2px)' }}
                        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                        exit={{ opacity: 0, y: -6, filter: 'blur(2px)' }}
                        transition={{ duration: 0.22, ease: [0.2, 0.7, 0.2, 1] }}
                    >
                        <ActiveComponent />
                    </motion.main>
                </AnimatePresence>

                {/* Floating Batch Selection Bar */}
                <SelectionBar />
            </div>

            {/* Media Lightbox & Video Player Modals */}
            <PhotoModal />
            <VideoModal />
            <UploadProgressModal />
        </div>
    );
}
