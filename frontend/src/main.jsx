import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// self-hosted fonts (no network calls): Fraunces for titles, DM Sans for the interface, JetBrains Mono for numbers
import '@fontsource-variable/fraunces/full.css';
import '@fontsource-variable/dm-sans';
import '@fontsource-variable/jetbrains-mono';
import App from './App.jsx';
import './index.css';
import { useAppStore } from './store/useAppStore';

if (typeof window !== 'undefined') {
  window.__useAppStore = useAppStore;
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
