# VisionArchive AI

> A local-first, AI-powered photo management desktop app built with React and Vite.

![VisionArchive AI](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![Zustand](https://img.shields.io/badge/State-Zustand-FF4154)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

| Feature | Description |
|---|---|
| 🔍 **CLIP Semantic Search** | Search 100k+ photos using natural language descriptions |
| 👤 **Face Clustering** | Automatic person detection and grouping via InsightFace |
| ⚡ **GPU Acceleration** | FAISS vector index with optional CUDA acceleration |
| 📸 **Virtualized Gallery** | Renders 1 million+ photos at 60fps with `@tanstack/react-virtual` |
| 🎬 **Video Library** | Browse, filter, and preview videos by tag and resolution |
| 📁 **File Import** | Drag-and-drop or click-to-import photos and videos |
| 🌗 **Dark / Light Theme** | System-aware theme toggle stored in global state |
| ⌨️ **Keyboard Shortcuts** | `Ctrl+F` search · `Ctrl+B` sidebar · `Esc` close/clear |
| 📱 **Responsive Layout** | Adaptive columns from mobile (2) to ultrawide (6+) |
| 🛡️ **Error Boundary** | Graceful error recovery with reload option |

---

## Tech Stack

- **Framework**: React 18 + Vite 5
- **Styling**: Tailwind CSS v3 + shadcn/ui component primitives
- **State**: Zustand (sliced actions, no Context boilerplate)
- **Routing**: React Router v6
- **Animations**: Framer Motion (spring physics, layout animations)
- **Virtualisation**: TanStack Virtual (row virtualizer for gallery)
- **Data Fetching**: TanStack Query (with staleTime + retry config)
- **Icons**: Lucide React
- **Notifications**: Sonner

---

## Project Structure

```
src/
├── components/
│   ├── features/         # Domain-specific feature components
│   │   ├── AppSidebar    # Collapsible nav sidebar
│   │   ├── CommandBar    # Top search + status bar
│   │   ├── GalleryView   # Virtualized photo grid
│   │   ├── PhotoCard     # Individual photo tile
│   │   ├── PhotoModal    # Lightbox with EXIF metadata
│   │   ├── VideoView     # Video library browser
│   │   ├── VideoModal    # Video player dialog
│   │   ├── PeopleView    # Face cluster grid
│   │   ├── SearchView    # Semantic search results
│   │   ├── IndexingPanel # Indexing pipeline status
│   │   ├── SettingsView  # App settings & hardware info
│   │   └── SelectionBar  # Floating batch-action toolbar
│   ├── ErrorBoundary     # Global React error boundary
│   └── NetworkStatus     # Online/offline toast listener
├── hooks/
│   └── useKeyboardShortcuts  # Global keyboard handler
├── layouts/
│   └── DesktopLayout     # Root layout with sidebar + main area
├── lib/
│   └── mockApi           # Simulated AI photo backend
├── pages/
│   ├── Index             # Root page (wraps DesktopLayout)
│   └── NotFound          # 404 page
└── store/
    └── useAppStore       # Zustand global store
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

```bash
git clone https://github.com/your-username/visionarchive-ai.git
cd visionarchive-ai/frontend/cove
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Production Build

```bash
npm run build
npm run preview
```

### Tests

```bash
npm run test
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl / ⌘ + F` | Open semantic search |
| `Ctrl / ⌘ + B` | Toggle sidebar |
| `Escape` | Close modal or clear selection |
| `Shift + Click` | Multi-select photos |
| `← / →` | Navigate photos in lightbox |

---

## Architecture Notes

- **State**: All global state lives in a single Zustand store (`useAppStore`). Actions are co-located with their slice. Selectors use individual subscriptions to minimise rerenders.
- **Gallery Performance**: Uses `@tanstack/react-virtual` row virtualisation. Only visible rows are mounted in the DOM, enabling smooth scrolling through 100k+ photos.
- **Column Layout**: Responsive columns are derived from a `ResizeObserver` on the container (not `window.resize`) for pixel-accurate breakpoints inside a flex layout.
- **Search**: Debounced 300ms with a stable `useRef` timer. Typing fast does not trigger redundant API calls.
- **Indexing Progress**: Uses a `useRef` snapshot of the latest status to safely update progress from a `setInterval` without stale-closure bugs.
- **Error Handling**: An `ErrorBoundary` class component wraps the entire app. Errors are logged and a reload button is presented instead of a blank screen.

---

## License

MIT © VisionArchive AI
