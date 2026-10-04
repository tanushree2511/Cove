/**
 * Settings view - real system stats, theme controls, library info, and app info.
 */
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '@/store/useAppStore';
import { Images, Users, Zap, HardDrive, Folder, RefreshCw, Sun, Moon } from 'lucide-react';
import { toast } from 'sonner';
import { getSystemStats } from '@/lib/coveApi';
import { CoveMark } from '@/components/CoveMark';

function Section({ id, title, children }) {
  return (
    <section className="mb-9" aria-labelledby={id}>
      <p id={id} className="eyebrow mb-3">{title}</p>
      {children}
    </section>
  );
}

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
      label: 'Photos indexed',
      value: systemStats.totalImages.toLocaleString(),
      icon:  Images,
      color: 'text-primary',
    },
    {
      label: 'People detected',
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

  const themeBtn = (id, label, Icon) => (
    <button
      onClick={() => setTheme(id)}
      aria-pressed={theme === id}
      className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-[13px] font-medium transition-all ${
        theme === id ? 'bg-foreground text-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
      }`}
    >
      <Icon size={14} /> {label}
    </button>
  );

  return (
    <div className="h-full overflow-auto px-7 pb-12 pt-7">
      <div className="mx-auto max-w-2xl">
        {/* Page header */}
        <div className="mb-9 flex items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-[36px] font-semibold leading-none text-foreground">Settings</h1>
            <p className="mt-2.5 text-[14px] text-muted-foreground">Configure Cove preferences</p>
          </div>
          <button
            onClick={refreshStats}
            disabled={loading}
            aria-label="Refresh system stats"
            className="rounded-full border border-border bg-card/70 p-2.5 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
            title="Refresh System Stats"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        <Section id="stats-heading" title="Library & acceleration">
          <div className="grid grid-cols-3 gap-3">
            {cards.map((card, i) => (
              <motion.div
                key={card.label}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="rounded-3xl border border-border bg-card/70 p-5"
              >
                <card.icon size={18} className={`mb-4 ${card.color}`} />
                <p className="tabular font-display text-[28px] font-semibold leading-none text-foreground">{card.value}</p>
                <p className="mt-2 text-[12px] text-muted-foreground">{card.label}</p>
              </motion.div>
            ))}
          </div>
        </Section>

        <Section id="appearance-heading" title="Appearance">
          <div className="flex items-center justify-between gap-4 rounded-3xl border border-border bg-card/70 p-5">
            <div>
              <p className="text-[14px] font-medium text-foreground">Theme Mode</p>
              <p className="mt-0.5 text-[12.5px] text-muted-foreground">Choose your preferred colour scheme</p>
            </div>
            <div className="flex items-center gap-1 rounded-full border border-border/80 bg-background/40 p-1">
              {themeBtn('dark', 'Dark', Moon)}
              {themeBtn('light', 'Light', Sun)}
            </div>
          </div>
        </Section>

        <Section id="storage-heading" title="Library storage">
          <div className="divide-y divide-border/70 rounded-3xl border border-border bg-card/70">
            <div className="flex items-center justify-between gap-4 px-5 py-4">
              <div className="flex items-center gap-2.5 text-[14px] text-foreground">
                <Folder size={15} className="text-muted-foreground" />
                Photo Library Directory
              </div>
              <span className="mono text-[12px] text-muted-foreground">test_images/ (cove photo directory)</span>
            </div>
            <div className="flex items-center justify-between gap-4 px-5 py-4">
              <div className="flex items-center gap-2.5 text-[14px] text-foreground">
                <HardDrive size={15} className="text-muted-foreground" />
                Vector Index Storage
              </div>
              <span className="mono text-[12px] text-muted-foreground">Managed automatically (FAISS)</span>
            </div>
          </div>
        </Section>

        <div className="flex items-center gap-4 rounded-3xl border border-border bg-card/70 p-5">
          <CoveMark size={40} />
          <div>
            <p className="font-display text-[18px] font-semibold text-foreground">Cove v1.0.0</p>
            <p className="mt-0.5 text-[12.5px] text-muted-foreground">
              CLIP Embeddings · InsightFace · FAISS · Local-first Architecture
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
