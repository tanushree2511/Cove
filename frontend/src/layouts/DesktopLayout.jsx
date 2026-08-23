/**
 * Main desktop layout with collapsible sidebar, top command bar, modals, and selection bar.
 */
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
                animate={{ width: sidebarCollapsed ? 52 : 230 }}
                transition={{ type: 'spring', stiffness: 350, damping: 32, mass: 0.8 }}
            >
                <AppSidebar />
            </motion.div>

            {/* Main content */}
            <div className="flex flex-1 flex-col min-w-0 bg-background relative">
                <CommandBar />
                
                {/* Global Indexing Progress Bar */}
                <AnimatePresence>
                    {isAnyIndexing && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="bg-primary/10 border-b border-primary/20 px-4 py-1.5 flex items-center justify-between text-xs backdrop-blur-sm z-20 flex-shrink-0 overflow-hidden"
                        >
                            <div className="flex items-center gap-2">
                                <span className="relative flex h-2 w-2">
                                    <span className="absolute inset-0 rounded-full bg-primary animate-ping" />
                                    <span className="rounded-full bg-primary h-2 w-2" />
                                </span>
                                <span className="font-medium text-foreground">
                                    {currentMsg}
                                </span>
                                {currentTotal > 0 && (
                                    <span className="text-muted-foreground mono text-[11px]">
                                        ({currentProcessed} / {currentTotal})
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-3">
                                <div className="w-32 h-1.5 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary transition-all duration-300 rounded-full"
                                        style={{ width: `${Math.max(5, currentProgress)}%` }}
                                    />
                                </div>
                                <span className="mono font-semibold text-primary text-[11px]">{Math.round(currentProgress)}%</span>
                                <button
                                    onClick={() => setActiveView('indexing')}
                                    className="text-[11px] text-primary hover:underline font-medium"
                                >
                                    View Pipeline →
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <AnimatePresence mode="wait">
                    <motion.main
                        key={activeView}
                        className="flex-1 overflow-hidden"
                        initial={{ opacity: 0, y: 4, filter: 'blur(2px)' }}
                        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                        exit={{ opacity: 0, y: -4, filter: 'blur(2px)' }}
                        transition={{ duration: 0.18, ease: [0.25, 0.1, 0.25, 1] }}
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
