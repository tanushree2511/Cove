/**
 * Root page rendering DesktopLayout with ErrorBoundary.
 * Also owns the app-wide poll of real indexing status and system stats so the
 * header/sidebar stay accurate regardless of which view is currently mounted.
 */
import { useEffect } from 'react';
import { DesktopLayout } from '@/layouts/DesktopLayout';
import { useAppStore } from '@/store/useAppStore';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { getIndexingStatus, getSystemStats, fetchImages, fetchClusters } from '@/lib/coveApi';
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
            fetchImages(0, 1000).then((imgs) => {
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

        const pollIndexing = () => {
            getIndexingStatus().then((status) => {
                if (!isMounted || !status) return;
                setIndexingStatus(status);
                if (status.status === 'completed' && lastPhotoStatus === 'running') {
                    refreshStats();
                    refreshPhotos();
                }
                lastPhotoStatus = status.status;
            }).catch(() => {});

            getVideoJobStatus().then((vStatus) => {
                if (!isMounted || !vStatus) return;
                setVideoIndexingStatus(vStatus.bulk_index || { status: 'idle' });
                const currentStatus = vStatus.bulk_index?.status;
                if (currentStatus === 'completed' && lastVideoStatus === 'processing') {
                    refreshVideos();
                }
                lastVideoStatus = currentStatus;
            }).catch(() => {});
        };

        // Initial fetch
        pollIndexing();
        refreshStats();
        refreshPhotos();
        refreshVideos();

        const interval = setInterval(pollIndexing, 1200);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [setIndexingStatus, setVideoIndexingStatus, setSystemStats, setVideos, setImages, setClusters]);

    return (
        <ErrorBoundary>
            <DesktopLayout />
        </ErrorBoundary>
    );
};

export default Index;
