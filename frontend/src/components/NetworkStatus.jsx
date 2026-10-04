/**
 * Network Status Indicator — Listens to online/offline events and triggers toast notifications.
 */
import { useEffect } from 'react';
import { toast } from 'sonner';

export function NetworkStatus() {
    useEffect(() => {
        const handleOnline = () => {
            toast.success('Network connection restored');
        };
        const handleOffline = () => {
            toast.warning('Working offline — local database remains active');
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    return null;
}
