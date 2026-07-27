/**
 * Root page rendering DesktopLayout with ErrorBoundary.
 * Also owns the app-wide poll of real indexing status and system stats so the
 * header/sidebar stay accurate regardless of which view is currently mounted.
 */
import { useEffect } from 'react';
import { DesktopLayout } from '@/layouts/DesktopLayout';
import { useAppStore } from '@/store/useAppStore';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { getIndexingStatus, getSystemStats } from '@/lib/coveApi';

const Index = () => {
    const setIndexingStatus = useAppStore((s) => s.setIndexingStatus);
    const setSystemStats = useAppStore((s) => s.setSystemStats);

    useEffect(() => {
        let isMounted = true;
        let lastStatus = null;

        const refreshStats = () => getSystemStats().then((stats) => {
            if (isMounted) setSystemStats(stats);
        });

        const pollIndexing = () => getIndexingStatus().then((status) => {
            if (!isMounted) return;
            setIndexingStatus(status);
            if (status.status === 'completed' && lastStatus !== 'completed') {
                refreshStats();
            }
            lastStatus = status.status;
        });

        pollIndexing();
        refreshStats();
        const interval = setInterval(pollIndexing, 1500);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [setIndexingStatus, setSystemStats]);

    return (
        <ErrorBoundary>
            <DesktopLayout />
        </ErrorBoundary>
    );
};

export default Index;
