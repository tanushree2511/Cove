/**
 * Global keyboard shortcut handler.
 *
 * Shortcuts:
 *   Ctrl/Cmd + F  → Focus semantic search
 *   Ctrl/Cmd + B  → Toggle sidebar
 *   Escape        → Close modal or clear selection
 */
import { useEffect } from 'react';
import { useAppStore } from '@/store/useAppStore';

export function useKeyboardShortcuts() {
  const toggleSidebar    = useAppStore((s) => s.toggleSidebar);
  const clearSelection   = useAppStore((s) => s.clearSelection);
  const setActiveView    = useAppStore((s) => s.setActiveView);
  const activeMediaModal = useAppStore((s) => s.activeMediaModal);
  const closeMediaModal  = useAppStore((s) => s.closeMediaModal);

  useEffect(() => {
    const handler = (e) => {
      // Ignore shortcuts when focus is inside a text input
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') {
        // Only allow Escape from inputs
        if (e.key !== 'Escape') return;
      }

      // Ctrl/Cmd + F → open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        setActiveView('search');
        return;
      }

      // Ctrl/Cmd + B → toggle sidebar
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        toggleSidebar();
        return;
      }

      // Escape → close modal first, then clear selection
      if (e.key === 'Escape') {
        if (activeMediaModal) {
          closeMediaModal();
        } else {
          clearSelection();
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [toggleSidebar, clearSelection, setActiveView, activeMediaModal, closeMediaModal]);
}
