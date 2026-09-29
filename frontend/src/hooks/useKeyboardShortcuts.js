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
      const tag = document.activeElement?.tagName;
      const isInput = tag === 'INPUT' || tag === 'TEXTAREA';

      // Escape → close modal first, then blur input, or clear selection
      if (e.key === 'Escape') {
        if (activeMediaModal) {
          closeMediaModal();
        } else if (isInput) {
          document.activeElement?.blur();
        } else {
          clearSelection();
        }
        return;
      }

      // Ctrl/Cmd + K or Ctrl/Cmd + F → focus and select search input (works from anywhere)
      if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'k' || e.key.toLowerCase() === 'f')) {
        e.preventDefault();
        setActiveView('search');
        window.dispatchEvent(new CustomEvent('focus-search-input'));
        return;
      }

      // Ignore remaining shortcuts when typing inside an input
      if (isInput) return;

      // '/' → open and focus search
      if (e.key === '/') {
        e.preventDefault();
        setActiveView('search');
        window.dispatchEvent(new CustomEvent('focus-search-input'));
        return;
      }

      // Ctrl/Cmd + B → toggle sidebar
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleSidebar();
        return;
      }

      // Ctrl/Cmd + A → select all items in library
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') {
        const state = useAppStore.getState();
        if (state.activeView === 'library' && !state.activeMediaModal) {
          e.preventDefault();
          state.selectAllImages();
          return;
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [toggleSidebar, clearSelection, setActiveView, activeMediaModal, closeMediaModal]);
}
