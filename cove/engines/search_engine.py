import os
from typing import Optional, Union, List

import numpy as np
from PIL import Image
import onnxruntime as ort
from tokenizers import Tokenizer

from config.vision_config import CONFIG, VisionConfig, get_logger

logger = get_logger(__name__)


class SearchEngine:
    def __init__(self, model_dir: str = CONFIG.model_dir, config: VisionConfig = CONFIG):
        self.config = config
        self.model_dir = model_dir
        self.providers = self.config.providers

        image_model = os.path.join(self.model_dir, "clip_image.onnx")
        text_model = os.path.join(self.model_dir, "clip_text.onnx")
        tokenizer_path = os.path.join(self.model_dir, "tokenizer.json")

        logger.info("Loading CLIP models from %s", self.model_dir)
        try:
            sess_options = ort.SessionOptions()
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.intra_op_num_threads = 2
            sess_options.inter_op_num_threads = 1

            self.img_session = ort.InferenceSession(
                image_model,
                sess_options=sess_options,
                providers=self.providers,
                provider_options=self.config.provider_options,
            )
            self.txt_session = ort.InferenceSession(
                text_model,
                sess_options=sess_options,
                providers=self.providers,
                provider_options=self.config.provider_options,
            )
            self.tokenizer = Tokenizer.from_file(tokenizer_path)
            self.tokenizer.enable_padding(length=77)
            self.tokenizer.enable_truncation(max_length=77)
        except Exception as exc:
            logger.exception("Failed to load CLIP models: %s", exc)
            raise

    def get_image_embedding(self, image_input: Union[str, Image.Image]) -> Optional[np.ndarray]:
        """
        Computes the L2-normalized 512-D CLIP vision embedding.
        Preprocesses images using standard CLIP ViT pipeline:
        1. Aspect-ratio preserving resize (shortest edge to target size) with Bicubic interpolation.
        2. Center crop to square input dimensions.
        3. Pixel rescaling to [0, 1].
        4. Standard OpenAI CLIP normalization (mean=[0.48145466, 0.4578275, 0.40821073], std=[0.26862954, 0.26130258, 0.27577711]).
        """
        try:
            if isinstance(image_input, str):
                img = Image.open(image_input).convert("RGB")
            else:
                img = image_input.convert("RGB")

            inp = self.img_session.get_inputs()[0]
            target_h = inp.shape[2] if len(inp.shape) > 2 and isinstance(inp.shape[2], int) else 224
            target_w = inp.shape[3] if len(inp.shape) > 3 and isinstance(inp.shape[3], int) else 224

            # Aspect-ratio preserving resize of shortest edge
            w, h = img.size
            if w < h:
                new_w = target_w
                new_h = max(target_h, int(h * (target_w / w)))
            else:
                new_h = target_h
                new_w = max(target_w, int(w * (target_h / h)))
            img = img.resize((new_w, new_h), Image.Resampling.BICUBIC)

            # Center crop to target_w x target_h
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            img = img.crop((left, top, left + target_w, top + target_h))

            # Rescale & Normalize
            img_data = np.array(img, dtype=np.float32) / 255.0
            mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
            std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
            img_data = (img_data - mean) / std

            # NCHW format
            img_data = np.transpose(img_data, (2, 0, 1))
            img_data = np.expand_dims(img_data, axis=0)

            inputs = {self.img_session.get_inputs()[0].name: img_data}
            embedding = self.img_session.run(None, inputs)[0].flatten()
            norm = np.linalg.norm(embedding)
            return embedding / (norm + 1e-6)

        except Exception as exc:
            logger.exception("Image encoding failed: %s", exc)
            return None

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
