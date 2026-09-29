/**
 * Settings view — real system stats, theme controls, library info, and app info.
 */
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '@/store/useAppStore';
import { Images, Users, Zap, HardDrive, Folder, Info, RefreshCw, Sun, Moon } from 'lucide-react';
import { toast } from 'sonner';
import { getSystemStats } from '@/lib/coveApi';

export function SettingsView() {
  const systemStats  = useAppStore((s) => s.systemStats);
  const setSystemStats = useAppStore((s) => s.setSystemStats);
  const theme        = useAppStore((s) => s.theme);
  const setTheme     = useAppStore((s) => s.setTheme);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getSystemStats()
      .then((stats) => {
        if (stats) setSystemStats(stats);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [setSystemStats]);

  const cards = [
    {
      label: 'Photos Indexed',
      value: systemStats.totalImages.toLocaleString(),
      icon:  Images,
      color: 'text-primary',
    },
    {
      label: 'People Detected',
      value: systemStats.totalPeople.toLocaleString(),
      icon:  Users,
      color: 'text-accent',
    },
    {
      label: 'Acceleration',
      value: systemStats.gpuAvailable ? 'GPU' : 'CPU only',
      icon:  systemStats.gpuAvailable ? Zap : HardDrive,
      color: systemStats.gpuAvailable ? 'text-success' : 'text-muted-foreground',
    },
  ];

  const refreshStats = () => {
    setLoading(true);
    getSystemStats()
      .then((stats) => {
        if (stats) setSystemStats(stats);
        toast.success('System stats refreshed');
      })
      .catch(() => toast.error('Failed to refresh system stats'))
      .finally(() => setLoading(false));
  };

  return (
    <div className="h-full overflow-auto p-6 max-w-xl mx-auto">
      {/* Page header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-[15px] font-semibold text-foreground mb-0.5">Settings</h1>
          <p className="text-[12px] text-muted-foreground">Configure VisionArchive AI preferences</p>
        </div>
        <button
          onClick={refreshStats}
          disabled={loading}
          aria-label="Refresh system stats"
          className="p-2 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground disabled:opacity-50 transition-colors"
          title="Refresh System Stats"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* System stat cards */}
      <section className="mb-8" aria-labelledby="stats-heading">
        <p id="stats-heading" className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60 mb-3">
          Library &amp; Acceleration
        </p>
        <div className="grid grid-cols-3 gap-3">
          {cards.map((card, i) => (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="rounded-xl border border-border bg-card p-4 text-center shadow-sm"
            >
              <card.icon size={16} className={`mx-auto mb-2 ${card.color}`} />
              <p className="text-[18px] font-semibold text-foreground mono">{card.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{card.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Appearance */}
      <section className="mb-8" aria-labelledby="appearance-heading">
        <p id="appearance-heading" className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60 mb-3">
          Appearance
        </p>
        <div className="rounded-xl border border-border bg-card p-4 flex items-center justify-between">
          <div>
            <p className="text-[13px] font-medium text-foreground">Theme Mode</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">Choose your preferred colour scheme</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setTheme('dark')}
              aria-pressed={theme === 'dark'}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors ${
                theme === 'dark'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:text-foreground'
              }`}
            >
              <Moon size={13} /> Dark
            </button>
            <button
              onClick={() => setTheme('light')}
              aria-pressed={theme === 'light'}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium transition-colors ${
                theme === 'light'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:text-foreground'
              }`}
            >
              <Sun size={13} /> Light
            </button>
          </div>
        </div>
      </section>

      {/* Library Storage */}
      <section className="mb-8" aria-labelledby="storage-heading">
        <p id="storage-heading" className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/60 mb-3">
          Library Storage
        </p>
        <div className="rounded-xl border border-border bg-card p-4 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[13px] text-foreground">
              <Folder size={14} className="text-muted-foreground" />
              Photo Library Directory
            </div>
            <span className="text-[11px] mono text-muted-foreground">test_images/ (cove photo directory)</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[13px] text-foreground">
              <HardDrive size={14} className="text-muted-foreground" />
              Vector Index Storage
            </div>
            <span className="text-[11px] mono text-muted-foreground">Managed automatically (FAISS)</span>
          </div>
        </div>
      </section>

      {/* About */}
      <div className="rounded-xl border border-border bg-card p-4 flex items-center gap-3 shadow-sm">
        <Info size={16} className="text-primary flex-shrink-0" />
        <div>
          <p className="text-[13px] font-medium text-foreground">VisionArchive AI v1.0.0</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            CLIP Embeddings · InsightFace · FAISS · Local-first Architecture
          </p>
        </div>
      </div>
    </div>
  );
}
