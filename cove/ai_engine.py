import queue
import threading
from contextlib import contextmanager

from insightface.app import FaceAnalysis

from vision_config import CONFIG, VisionConfig, get_logger

logger = get_logger(__name__)


class AIEngine:
    def __init__(self, instance_id: int = 0, config: VisionConfig = CONFIG):
        self.instance_id = instance_id
        self.config = config
        self._lock = threading.Lock()

        logger.info("Booting AI engine %s (providers=%s, root=%s)", instance_id, self.config.providers, self.config.assets_base)
        
        # Determine efficient batch size based on hardware
        # RTX 3050 has 4GB-6GB VRAM. We can increase throughput by batching?
        # InsightFace defaults to single image inference per call. 
        # To hit 95% GPU, we need to run multiple parallel inferences or larger images.
        
        self.app = FaceAnalysis(
            name="buffalo_s",
            root=self.config.assets_base,
            allowed_modules=["detection", "recognition"],
            providers=self.config.providers,
        )
        # Increase detection size to utilize more GPU (better accuracy too)
        # Default was 320x320 (very small for RTX 3050).
        # Dynamic scaler: 640x640 is good balance.
        # Pushing to 800x800 to force the GPU to work harder per image
        det_size = (800, 800) if self.config.use_gpu else self.config.det_size
        self.app.prepare(ctx_id=self.config.ctx_id, det_size=det_size)

        if self.config.use_gpu:
            self._apply_gpu_options()

    def _apply_gpu_options(self):
        try:
            for model in self.app.models.values():
                if hasattr(model, "session") and model.session is not None:
                    model.session.set_providers(["CUDAExecutionProvider"], [self.config.session_options])
        except Exception as exc:
            logger.warning("Failed to set GPU session options: %s", exc)

    def get_faces(self, img):
        with self._lock:
            try:
                return self.app.get(img)
            except Exception as exc:
                logger.exception("Face analysis failed: %s", exc)
                return []


class AIEnginePool:
    def __init__(self, pool_size: int = None, config: VisionConfig = CONFIG):
        self.config = config
        # Use ai_engine_pool_size which dynamically scales based on VRAM/RAM limits
        self.pool_size = pool_size or self.config.ai_engine_pool_size
        self._queue = queue.Queue()

        for idx in range(self.pool_size):
            engine = AIEngine(idx, config=self.config)
            self._queue.put(engine)

    @contextmanager
    def borrow(self):
        engine = self._queue.get()
        try:
            yield engine
        finally:
            self._queue.put(engine)