/**
 * Unified Indexing & AI Pipeline panel — provides clear visual feedback,
 * animated progress bars, and controls for Photos and Videos.
 */
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ScanLine, Eye, Brain, Network, CheckCircle2, Film, Image as ImageIcon, Sparkles, RefreshCw, Users } from 'lucide-react';
import { toast } from 'sonner';
import { useAppStore } from '@/store/useAppStore';
import { startIndexing, fetchClusters } from '@/lib/coveApi';
import { startVideoIndexing, getVideoJobStatus, startVideoClustering, fetchAllVideoPersons } from '@/lib/videoApi';

const PHOTO_STAGES = [
  { id: 'scanning',   label: 'Scanning Photos',        desc: 'Discovering photo files',              icon: ScanLine },
  { id: 'detecting',  label: 'Detecting Faces',         desc: 'Running InsightFace detection',         icon: Eye },
  { id: 'embedding',  label: 'Generating Embeddings',   desc: 'Creating CLIP vectors for search',      icon: Brain },
  { id: 'clustering', label: 'Clustering Identities',   desc: 'Grouping similar faces together',       icon: Network },
];

const VIDEO_STAGES = [
  { id: 'extraction', label: 'Frame Extraction',       desc: 'Sampling story keyframes across video', icon: Film },
  { id: 'faces',      label: 'Video Face Recognition', desc: 'InsightFace face extraction & alignment', icon: Eye },
  { id: 'embedding',  label: 'CLIP Multi-Frame Vectors',desc: 'Temporal visual embeddings',          icon: Brain },
  { id: 'clustering', label: 'Identity Clustering',    desc: 'Merging same person across video frames', icon: Network },
];

export function IndexingPanel() {
  const indexingStatus = useAppStore((s) => s.indexingStatus);
  const images         = useAppStore((s) => s.images);
  const videos         = useAppStore((s) => s.videos);
  const setClusters    = useAppStore((s) => s.setClusters);

  const [videoStatus, setVideoStatus] = useState({
    bulk_index: { status: 'idle', current: 0, total: 0, message: '' },
    clustering: { status: 'idle', current: 0, total: 0, message: '' },
  });
  const [triggering, setTriggering] = useState(false);
  const [clusteringActive, setClusteringActive] = useState(false);

  useEffect(() => {
    let active = true;
    const poll = () => {
      getVideoJobStatus()
        .then((res) => {
          if (active && res) setVideoStatus(res);
        })
        .catch(() => {});
    };
    poll();
    const interval = setInterval(poll, 1200);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const isVideoProcessing =
    videoStatus.bulk_index?.status === 'processing' ||
    videoStatus.clustering?.status === 'processing';

  const isAnyIndexing = indexingStatus.isIndexing || isVideoProcessing || triggering;

  const videoProgressPercent = videoStatus.bulk_index?.total > 0
    ? Math.round((videoStatus.bulk_index.current / videoStatus.bulk_index.total) * 100)
    : videoStatus.bulk_index?.status === 'completed' ? 100 : 0;

  const handleStartUnifiedIndexing = async () => {
    setTriggering(true);
    try {
      await Promise.allSettled([
        startIndexing(),
        startVideoIndexing(),
      ]);
      toast.success('Started indexing library!');
    } catch (err) {
      toast.error(`Failed to start indexing: ${err?.message}`);
    } finally {
      setTriggering(false);
    }
  };

  const handleReclusterFaces = async () => {
    setClusteringActive(true);
    try {
      await startVideoClustering();
      toast.success('Re-clustering video faces into clean identities...');
      setTimeout(() => {
        fetchAllVideoPersons().then(() => {});
        fetchClusters().then(setClusters);
      }, 2500);
    } catch (err) {
      toast.error(`Clustering failed: ${err?.message}`);
    } finally {
      setClusteringActive(false);
    }
  };

  const currentPhotoStageIdx = indexingStatus.status === 'completed'
    ? PHOTO_STAGES.length
    : PHOTO_STAGES.findIndex((s) => s.id === indexingStatus.stage);

  return (
    <div className="h-full overflow-auto p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-[16px] font-semibold text-foreground mb-0.5">Indexing & AI Pipeline</h1>
          <p className="text-[12px] text-muted-foreground">
            {images.length} photos and {videos.length} videos in library
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReclusterFaces}
            disabled={clusteringActive || isVideoProcessing}
            className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-[12px] font-medium text-foreground hover:bg-muted transition-colors shadow-sm disabled:opacity-50"
          >
            <Users size={14} className={clusteringActive ? 'animate-spin' : ''} />
            <span>Re-cluster Faces</span>
          </button>
          <button
            onClick={handleStartUnifiedIndexing}
            disabled={isAnyIndexing}
            className="flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnyIndexing ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span>Indexing Library…</span>
              </>
            ) : (
              <>
                <Sparkles size={14} />
                <span>Start Indexing</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Progress Summary Card */}
      <div className="mb-8 rounded-xl bg-card border border-border p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider block mb-1">
              Library Status
            </span>
            <span className="text-[20px] font-semibold text-foreground">
              {isAnyIndexing ? 'Processing Media with AI…' : 'Library Up to Date'}
            </span>
          </div>
          <div className="text-right mono text-xs text-muted-foreground space-y-0.5">
            <div>{images.length} Photos</div>
            <div>{videos.length} Videos</div>
          </div>
        </div>

        {/* Photo Indexing Progress Bar */}
        {(indexingStatus.isIndexing || indexingStatus.status === 'running') && (
          <div className="space-y-2 pt-2 border-t border-border/50">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground truncate max-w-[70%]">
                📷 {indexingStatus.message || 'Processing photos with AI…'}
              </span>
              <span className="mono font-semibold text-foreground">
                {indexingStatus.processed || 0} / {indexingStatus.total || 1} ({Math.round(indexingStatus.progress || 0)}%)
              </span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-primary"
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(5, indexingStatus.progress || 0)}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
          </div>
        )}

        {/* Video Indexing Progress Bar */}
        {videoStatus.bulk_index?.status === 'processing' && (
          <div className="space-y-2 pt-2 border-t border-border/50">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground truncate max-w-[70%]">
                🎬 {videoStatus.bulk_index.message || 'Processing videos…'}
              </span>
              <span className="mono font-semibold text-foreground">
                {videoStatus.bulk_index.current} / {videoStatus.bulk_index.total} ({videoProgressPercent}%)
              </span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-primary"
                initial={{ width: 0 }}
                animate={{ width: `${videoProgressPercent}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
          </div>
        )}

        {/* Video Clustering Status */}
        {videoStatus.clustering?.status === 'processing' && (
          <div className="p-2.5 rounded-lg bg-primary/10 border border-primary/20 text-xs text-primary flex items-center gap-2">
            <RefreshCw size={13} className="animate-spin flex-shrink-0" />
            <span>{videoStatus.clustering.message || 'Clustering video faces into unique people…'}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Photo Pipeline Card */}
        <div className="rounded-xl border border-border/80 bg-card/60 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3.5 pb-2.5 border-b border-border/40">
            <ImageIcon size={16} className="text-primary" />
            <h2 className="text-[13px] font-semibold text-foreground">Photo Pipeline</h2>
          </div>

          <div className="space-y-2">
            {PHOTO_STAGES.map((stage, i) => {
              const isComplete = i < currentPhotoStageIdx;
              const isCurrent  = i === currentPhotoStageIdx && indexingStatus.isIndexing;
              const isPending  = !isComplete && !isCurrent;

              return (
                <div
                  key={stage.id}
                  className={`flex items-center gap-3 rounded-lg p-2.5 transition-all text-xs ${
                    isCurrent ? 'bg-primary/10 border border-primary/20' : 'border border-transparent'
                  }`}
                >
                  <div
                    className={`flex h-7 w-7 items-center justify-center rounded-lg flex-shrink-0 ${
                      isComplete ? 'bg-success/15 text-success' : isCurrent ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {isComplete ? <CheckCircle2 size={14} /> : <stage.icon size={14} className={isCurrent ? 'animate-pulse' : ''} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium ${isPending ? 'text-muted-foreground' : 'text-foreground'}`}>
                      {stage.label}
                    </p>
                    <p className="text-[10px] text-muted-foreground truncate">{stage.desc}</p>
                  </div>
                  {isComplete && <span className="text-[10px] text-success font-medium">Done</span>}
                </div>
              );
            })}
          </div>
        </div>

        {/* Video Pipeline Card */}
        <div className="rounded-xl border border-border/80 bg-card/60 p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3.5 pb-2.5 border-b border-border/40">
            <Film size={16} className="text-primary" />
            <h2 className="text-[13px] font-semibold text-foreground">Video Pipeline</h2>
          </div>

          <div className="space-y-2">
            {VIDEO_STAGES.map((stage, i) => {
              const isProcessing = isVideoProcessing;
              return (
                <div
                  key={stage.id}
                  className="flex items-center gap-3 rounded-lg p-2.5 border border-transparent text-xs"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg flex-shrink-0 bg-primary/10 text-primary">
                    <stage.icon size={14} className={isProcessing ? 'animate-pulse' : ''} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground">{stage.label}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{stage.desc}</p>
                  </div>
                  <span className="text-[10px] text-success font-medium">Active</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
