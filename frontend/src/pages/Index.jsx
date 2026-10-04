/**
 * Root page rendering DesktopLayout with ErrorBoundary.
 * Also owns the app-wide poll of real indexing status and system stats so the
 * header/sidebar stay accurate regardless of which view is currently mounted.
 */
import { useEffect } from 'react';
import { DesktopLayout } from '@/layouts/DesktopLayout';
import { useAppStore } from '@/store/useAppStore';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { getIndexingStatus, getSystemStats, fetchAllImages, fetchClusters } from '@/lib/coveApi';
import { getVideoJobStatus, fetchVideos, fetchAllVideoPersons } from '@/lib/videoApi';

const Index = () => {
    const setIndexingStatus      = useAppStore((s) => s.setIndexingStatus);
    const setVideoIndexingStatus = useAppStore((s) => s.setVideoIndexingStatus);
    const setSystemStats         = useAppStore((s) => s.setSystemStats);
    const setVideos              = useAppStore((s) => s.setVideos);
    const setImages              = useAppStore((s) => s.setImages);
    const setClusters            = useAppStore((s) => s.setClusters);

    useEffect(() => {
        let isMounted = true;
        let lastPhotoStatus = null;
        let lastVideoStatus = null;

        const refreshStats = () => getSystemStats().then((stats) => {
            if (isMounted && stats) setSystemStats(stats);
        }).catch(() => {});

        const refreshPhotos = () => {
            fetchAllImages().then((imgs) => {
                if (isMounted && imgs) setImages(imgs);
            }).catch(() => {});
            fetchClusters().then((cls) => {
                if (isMounted && cls) setClusters(cls);
            }).catch(() => {});
        };

        const refreshVideos = () => {
            fetchVideos().then((vids) => {
                if (isMounted && vids) setVideos(vids);
            }).catch(() => {});
            fetchAllVideoPersons().then(() => {}).catch(() => {});
        };

        let timeoutId = null;

        const scheduleNextPoll = (delay) => {
            if (!isMounted) return;
            if (timeoutId) clearTimeout(timeoutId);
            timeoutId = setTimeout(runPoll, delay);
        };

        const runPoll = async () => {
            if (!isMounted || document.hidden) return;

            let photoRunning = false;
            let videoRunning = false;

            try {
                const status = await getIndexingStatus();
                if (isMounted && status) {
                    setIndexingStatus(status);
                    photoRunning = Boolean(status.isIndexing || status.status === 'running');
                    if (status.status === 'completed' && lastPhotoStatus === 'running') {
                        refreshStats();
                        refreshPhotos();
                    }
                    lastPhotoStatus = status.status;
                }
            } catch {
                // Ignore transient errors
            }

            try {
                const vStatus = await getVideoJobStatus();
                if (isMounted && vStatus) {
                    const bulkStatus = vStatus.bulk_index || { status: 'idle' };
                    setVideoIndexingStatus(bulkStatus);
                    videoRunning = bulkStatus.status === 'processing';
                    if (bulkStatus.status === 'completed' && lastVideoStatus === 'processing') {
                        refreshVideos();
                    }
                    lastVideoStatus = bulkStatus.status;
                }
            } catch {
                // Ignore transient errors
            }

            if (!isMounted) return;
            // Adaptive backoff: 1.5s while indexing, 10s when idle
            const nextInterval = (photoRunning || videoRunning) ? 1500 : 10000;
            scheduleNextPoll(nextInterval);
        };

        const handleVisibilityChange = () => {
            if (!document.hidden && isMounted) {
                runPoll();
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        // Initial fetch
        runPoll();
        refreshStats();
        refreshPhotos();
        refreshVideos();

        return () => {
            isMounted = false;
            if (timeoutId) clearTimeout(timeoutId);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [setIndexingStatus, setVideoIndexingStatus, setSystemStats, setVideos, setImages, setClusters]);

    return (
        <ErrorBoundary>
            <DesktopLayout />
        </ErrorBoundary>
    );
};

export default Index;
