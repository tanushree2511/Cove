import os
import time
from typing import Optional, Union, List

import numpy as np
from PIL import Image
from tokenizers import Tokenizer

from config.vision_config import CONFIG, VisionConfig, get_logger
from config.hardware import cpu_config
from config.runtime import create_session

logger = get_logger(__name__)


# (model id, image file, text file), best first. Embeddings from different models are NOT interchangeable,
# so anything that persists vectors records `SearchEngine.model_id` and rebuilds when it changes.
# ViT-B/16 (full precision) vs the legacy ViT-B/32 (int8): COCO-1k text->image Recall@1 51% vs 39%.
CLIP_MODELS = (
    ("clip-vit-b16-fp32", "clip_b16_image.onnx", "clip_b16_text.onnx"),
    ("clip-vit-b32-int8", "clip_image.onnx", "clip_text.onnx"),
)
LEGACY_MODEL_ID = CLIP_MODELS[-1][0]


def resolve_clip_model(model_dir: str):
    """Pick the best CLIP model whose files are present (COVE_CLIP_MODEL=b32 forces the legacy one)."""
    forced = os.getenv("COVE_CLIP_MODEL", "").lower()
    candidates = CLIP_MODELS[-1:] if forced in ("b32", "legacy") else CLIP_MODELS
    for model_id, image_file, text_file in candidates:
        if os.path.isfile(os.path.join(model_dir, image_file)) and os.path.isfile(os.path.join(model_dir, text_file)):
            return model_id, os.path.join(model_dir, image_file), os.path.join(model_dir, text_file)
    model_id, image_file, text_file = candidates[0]
    return model_id, os.path.join(model_dir, image_file), os.path.join(model_dir, text_file)


_CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
_CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)


class SearchEngine:
    def __init__(self, model_dir: str = CONFIG.model_dir, config: VisionConfig = CONFIG):
        self.config = config
        self.model_dir = model_dir

        self.model_id, image_model, text_model = resolve_clip_model(self.model_dir)
        tokenizer_path = os.path.join(self.model_dir, "tokenizer.json")

        # Which providers / threads / batch size to use was measured for this machine (config/runtime.py).
        profile = self.config.runtime_profile
        image_cfg = profile.config if profile else cpu_config("cpu", os.cpu_count() or 1, 8)
        self.batch_size = profile.clip_batch_size if profile else 8
        self.providers = image_cfg.providers
        # The text encoder is tiny (77 tokens) - always run it on the CPU: no accelerator start-up/compile cost
        # for a second model, and it behaves identically on every platform.
        text_cfg = cpu_config("cpu-text", min(4, image_cfg.intra_threads if not image_cfg.accelerator else (os.cpu_count() or 2)), 1)

        logger.info("Loading CLIP models (%s) from %s on %s (batch %d)", self.model_id, self.model_dir, image_cfg.name, self.batch_size)
        try:
            self.img_session = create_session(image_model, image_cfg)
            self.txt_session = create_session(text_model, text_cfg)
            self.tokenizer = Tokenizer.from_file(tokenizer_path)
            self.tokenizer.enable_padding(length=77)
            self.tokenizer.enable_truncation(max_length=77)
        except Exception as exc:
            logger.exception("Failed to load CLIP models: %s", exc)
            raise

        inp = self.img_session.get_inputs()[0]
        self._img_input_name = inp.name
        self._target_h = inp.shape[2] if len(inp.shape) > 2 and isinstance(inp.shape[2], int) else 224
        self._target_w = inp.shape[3] if len(inp.shape) > 3 and isinstance(inp.shape[3], int) else 224
        self._batching_ok = True   # flips to False if the model turns out to accept only batch size 1

    def _preprocess(self, image_input: Union[str, Image.Image]) -> np.ndarray:
        """Standard CLIP ViT preprocessing -> float32 [3, H, W]:
        1. Aspect-ratio preserving resize (shortest edge to target size) with Bicubic interpolation.
        2. Center crop to square input dimensions.
        3. Pixel rescaling to [0, 1].
        4. Standard OpenAI CLIP normalization.
        """
        if isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        else:
            img = image_input.convert("RGB")

        target_h, target_w = self._target_h, self._target_w
        w, h = img.size
        if w < h:
            new_w = target_w
            new_h = max(target_h, int(h * (target_w / w)))
        else:
            new_h = target_h
            new_w = max(target_w, int(w * (target_h / h)))
        img = img.resize((new_w, new_h), Image.Resampling.BICUBIC)

        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        data = (np.array(img, dtype=np.float32) / 255.0 - _CLIP_MEAN) / _CLIP_STD
        return np.ascontiguousarray(np.transpose(data, (2, 0, 1)))

    def _run_batch(self, batch: np.ndarray) -> np.ndarray:
        t0 = time.perf_counter()
        out = self.img_session.run(None, {self._img_input_name: batch})[0]
        profile = self.config.runtime_profile
        if profile is not None:   # feed real throughput back so the app adapts to load / thermal throttling
            profile.observe_throughput(len(batch), time.perf_counter() - t0)
        out = out.reshape(len(batch), -1)
        return out / (np.linalg.norm(out, axis=1, keepdims=True) + 1e-6)

    def get_image_embeddings(self, images: List[Union[str, Image.Image]], batch_size: Optional[int] = None) -> List[Optional[np.ndarray]]:
        """L2-normalised 512-D CLIP vision embeddings for many images (None for any that fail to load).

        Images are pre-processed in parallel threads (decode/resize is CPU work that would otherwise leave the
        model idle) and fed to the model in batches - larger matrix products keep the hardware busier than
        one-image-at-a-time calls."""
        n = len(images)
        results: List[Optional[np.ndarray]] = [None] * n
        if n == 0:
            return results
        batch_size = max(1, batch_size or self.batch_size)

        def prep(i):
            try:
                return i, self._preprocess(images[i])
            except Exception as exc:
                logger.warning("Could not read image %s: %s", images[i] if isinstance(images[i], str) else "<frame>", exc)
                return i, None

        if n > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(n, max(2, self.config.effective_workers))) as pool:
                prepped = list(pool.map(prep, range(n)))
        else:
            prepped = [prep(0)]
        ok = [(i, x) for i, x in prepped if x is not None]

        step = batch_size if self._batching_ok else 1
        for start in range(0, len(ok), step):
            chunk = ok[start:start + step]
            batch = np.stack([x for _, x in chunk])
            try:
                embs = self._run_batch(batch)
            except Exception as exc:
                if len(chunk) > 1:   # model may only accept batch size 1 -> degrade gracefully, once
                    logger.warning("Batched CLIP inference failed (%s); switching to one image at a time", exc)
                    self._batching_ok = False
                    embs = np.concatenate([self._run_batch(x[None]) for _, x in chunk])
                else:
                    logger.exception("Image encoding failed: %s", exc)
                    continue
            for (i, _), e in zip(chunk, embs):
                results[i] = e
        return results

    def get_image_embedding(self, image_input: Union[str, Image.Image]) -> Optional[np.ndarray]:
        """Computes the L2-normalized 512-D CLIP vision embedding for one image."""
        return self.get_image_embeddings([image_input])[0]

    def _encode_single_text(self, text: str) -> np.ndarray:
        encoding = self.tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)
        inputs = {"input_ids": input_ids}
        if "attention_mask" in [i.name for i in self.txt_session.get_inputs()]:
            inputs["attention_mask"] = np.array([encoding.attention_mask], dtype=np.int64)

        outputs = self.txt_session.run(None, inputs)
        embedding = next((out for out in outputs if out.shape[-1] == 512), outputs[0]).flatten()
        norm = np.linalg.norm(embedding)
        return embedding / (norm + 1e-6)

    def get_text_embedding(self, query: str) -> Optional[np.ndarray]:
        """
        Computes the L2-normalized 512-D CLIP text embedding.
        Uses prompt templating for short natural language queries to maximize retrieval quality.
        """
        try:
            q = query.strip()
            if not q:
                return None

            lower = q.lower()
            if lower.startswith("a photo of") or lower.startswith("a picture of"):
                # Already fully phrased prompt
                return self._encode_single_text(q)

            # Ensemble prompts to capture both literal and descriptive contexts
            templates = [q]
            words = q.split()
            starts_vowel = lower[0] in "aeiou" if lower else False
            article = "an" if starts_vowel else "a"
            if len(words) == 1:
                templates.extend([
                    f"a photo of {article} {q}",
                    f"a photograph of {article} {q}",
                    f"a picture of {article} {q}",
                    f"a close-up photo of {article} {q}",
                    f"a photo of the {q}",
                    f"a photo of {q}",
                ])
            else:
                templates.extend([
                    f"a photo of {q}",
                    f"a photograph of {q}",
                    f"a picture showing {q}",
                    f"an image of {q}",
                ])
                if not q[0].isupper():
                    templates.append(f"a photo of {article} {q}")

            vectors = [self._encode_single_text(t) for t in templates]
            avg = np.mean(vectors, axis=0)
            norm = np.linalg.norm(avg)
            return avg / (norm + 1e-6)

        except Exception as exc:
            logger.exception("Text encoding failed: %s", exc)
            return None
