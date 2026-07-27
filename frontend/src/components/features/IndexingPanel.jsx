/**
 * Indexing pipeline status — clean, stage-based progress display.
 * Reads real cove indexing job status (polled app-wide by pages/Index.jsx)
 * and can trigger a new run.
 */
import { motion } from 'framer-motion';
import { ScanLine, Eye, Brain, Network, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAppStore } from '@/store/useAppStore';
import { startIndexing } from '@/lib/coveApi';

const STAGES = [
  { id: 'scanning',   label: 'Scanning Files',        desc: 'Discovering images in your library',    icon: ScanLine },
  { id: 'detecting',  label: 'Detecting Faces',        desc: 'Running InsightFace detection',         icon: Eye },
  { id: 'embedding',  label: 'Generating Embeddings',  desc: 'Creating CLIP vectors for search',      icon: Brain },
  { id: 'clustering', label: 'Clustering Faces',       desc: 'Grouping similar faces together',       icon: Network },
];

export function IndexingPanel() {
  const indexingStatus = useAppStore((s) => s.indexingStatus);

  const handleStartIndexing = () => {
    startIndexing().then((r) => toast.info(r.message || 'Started'));
  };

  const currentStageIdx = indexingStatus.status === 'completed'
    ? STAGES.length
    : STAGES.findIndex((s) => s.id === indexingStatus.stage);

  return (
    <div className="h-full overflow-auto p-6 max-w-xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-[15px] font-semibold text-foreground mb-0.5">Indexing Status</h1>
          <p className="text-[12px] text-muted-foreground">Processing your photo library with AI</p>
        </div>
        <button
          onClick={handleStartIndexing}
          disabled={indexingStatus.isIndexing}
          className="rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {indexingStatus.isIndexing ? 'Indexing…' : 'Start Indexing'}
        </button>
      </div>

      {/* Main progress card */}
      <div className="mb-10 rounded-xl bg-card border border-border p-5 shadow-sm">
        <div className="flex items-baseline justify-between mb-3">
          <span className="text-[24px] font-semibold text-foreground mono">
            {Math.round(indexingStatus.progress)}
            <span className="text-[14px] text-muted-foreground">%</span>
          </span>
          <span className="text-[11px] text-muted-foreground mono">
            {indexingStatus.processed.toLocaleString()} / {indexingStatus.total.toLocaleString()}
          </span>
        </div>
        <div className="h-[6px] rounded-full bg-muted overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, hsl(var(--primary)), hsl(var(--accent)))' }}
            animate={{ width: `${indexingStatus.progress}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Pipeline stages */}
      <div className="space-y-2">
        {STAGES.map((stage, i) => {
          const isComplete = i < currentStageIdx;
          const isCurrent  = i === currentStageIdx;
          const isPending  = i > currentStageIdx;

          return (
            <motion.div
              key={stage.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: isPending ? 0.4 : 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className={`
                flex items-center gap-3.5 rounded-lg p-3.5 transition-all duration-200
                ${isCurrent ? 'bg-primary/5 border border-primary/20 shadow-sm' : 'border border-transparent'}
              `}
            >
              {/* Icon */}
              <div
                className={`
                  flex h-8 w-8 items-center justify-center rounded-lg flex-shrink-0
                  ${isComplete ? 'bg-success/10' : ''}
                  ${isCurrent  ? 'bg-primary/10' : ''}
                  ${isPending  ? 'bg-muted'      : ''}
                `}
              >
                {isComplete ? (
                  <CheckCircle2 size={16} className="text-success" />
                ) : (
                  <stage.icon
                    size={16}
                    className={`${isCurrent ? 'text-primary animate-pulse' : 'text-muted-foreground'}`}
                  />
                )}
              </div>

              {/* Labels */}
              <div className="flex-1 min-w-0">
                <p className={`text-[13px] font-medium ${isPending ? 'text-muted-foreground' : 'text-foreground'}`}>
                  {stage.label}
                </p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{stage.desc}</p>
              </div>

              {/* Status indicator */}
              {isCurrent && (
                <span className="relative flex h-2 w-2 flex-shrink-0">
                  <span className="absolute inset-0 rounded-full bg-primary animate-pulse" />
                  <span className="rounded-full bg-primary h-2 w-2" />
                </span>
              )}
              {isComplete && (
                <span className="text-[10px] text-success font-medium flex-shrink-0">Done</span>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
