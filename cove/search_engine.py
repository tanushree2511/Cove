import os

import numpy as np
from PIL import Image
import onnxruntime as ort
from tokenizers import Tokenizer

from vision_config import CONFIG, VisionConfig, get_logger

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
            # Apply GPU specific options to maximize throughput
            sess_options = ort.SessionOptions()
            if self.config.use_gpu:
                # Allow ONNX to use more threads internally even on GPU to speed up data transfer
                sess_options.intra_op_num_threads = 4
                sess_options.inter_op_num_threads = 4
            else:
                import multiprocessing
                sess_options.intra_op_num_threads = multiprocessing.cpu_count()
                
            self.img_session = ort.InferenceSession(image_model, sess_options=sess_options, providers=self.providers)
            self.txt_session = ort.InferenceSession(text_model, sess_options=sess_options, providers=self.providers)
            self.tokenizer = Tokenizer.from_file(tokenizer_path)
        except Exception as exc:
            logger.exception("Failed to load CLIP models: %s", exc)
            raise

    def get_image_embedding(self, image_input):
        try:
            if isinstance(image_input, str):
                img = Image.open(image_input).convert("RGB")
            else:
                img = image_input.convert("RGB")

            img = img.resize((224, 224))
            img_data = np.array(img, dtype=np.float32) / 255.0

            mean = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
            std = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)
            img_data = (img_data - mean) / std
            img_data = np.transpose(img_data, (2, 0, 1))
            img_data = np.expand_dims(img_data, axis=0)

            inputs = {self.img_session.get_inputs()[0].name: img_data}
            embedding = self.img_session.run(None, inputs)[0]
            norm = np.linalg.norm(embedding)
            return embedding.flatten() / (norm + 1e-6)

        except Exception as exc:
            logger.exception("Image encoding failed: %s", exc)
            return None

    def get_text_embedding(self, text):
        self.tokenizer.enable_padding(length=77)
        self.tokenizer.enable_truncation(max_length=77)
        encoding = self.tokenizer.encode(text)

        input_ids = np.array([encoding.ids], dtype=np.int64)
        inputs = {"input_ids": input_ids}
        if "attention_mask" in [i.name for i in self.txt_session.get_inputs()]:
            inputs["attention_mask"] = np.array([encoding.attention_mask], dtype=np.int64)

        outputs = self.txt_session.run(None, inputs)
        embedding = next((out for out in outputs if out.shape[-1] == 512), outputs[-1])
        norm = np.linalg.norm(embedding)
        return embedding.flatten() / (norm + 1e-6)
