/**
 * Root page rendering DesktopLayout with ErrorBoundary.
 */
import { useEffect } from 'react';
import { DesktopLayout } from '@/layouts/DesktopLayout';
import { useAppStore } from '@/store/useAppStore';
import { ErrorBoundary } from '@/components/ErrorBoundary';

const Index = () => {
    const setHardwareInfo = useAppStore((s) => s.setHardwareInfo);
    const setIndexingStatus = useAppStore((s) => s.setIndexingStatus);

    useEffect(() => {
        setHardwareInfo({ cpuUsage: 34, gpuUsage: 67, gpuAvailable: true });
        setIndexingStatus({
            isIndexing: true,
            stage: 'embedding',
            progress: 67,
            processed: 67432,
            total: 100000,
        });
    }, [setHardwareInfo, setIndexingStatus]);

    return (
        <ErrorBoundary>
            <DesktopLayout />
        </ErrorBoundary>
    );
};

export default Index;
