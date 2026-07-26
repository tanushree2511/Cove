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
    const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);
    const activeView = useAppStore((s) => s.activeView);

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
        </div>
    );
}
