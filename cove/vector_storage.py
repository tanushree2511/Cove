import json
import logging
import os

import faiss
import numpy as np

from vision_config import CONFIG, get_logger

logger = get_logger(__name__)


class VectorStorage:
    def __init__(self, dimension: int = 512, index_path: str = CONFIG.faiss_index_path, vector_path: str = CONFIG.vector_path):
        self.dimension = dimension
        self.index_path = index_path
        self.vector_path = vector_path
        self.paths = []
        self.vector_matrix = None
        self.path_to_index = {}

        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
            except Exception as exc:
                logger.warning("Failed to read index (%s): %s", self.index_path, exc)
                self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

        # OPTIONAL: Move to GPU if available and supported
        try:
            if hasattr(faiss, 'get_num_gpus') and faiss.get_num_gpus() > 0:
                # Convert to GPU index
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        except Exception:
            pass  # Fallback to CPU silently if GPU fails

        self._load_paths()
        self._load_vectors()
        self._reindex_paths()

    def _load_paths(self):
        paths_file = f"{self.index_path}.paths"
        if not os.path.exists(paths_file):
            return
        try:
            with open(paths_file, "r") as f:
                self.paths = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            try:
                import pickle

                with open(paths_file, "rb") as f:
                    self.paths = pickle.load(f)
                with open(paths_file, "w") as f:
                    json.dump(self.paths, f)
            except Exception as inner_exc:
                logger.warning("Unable to migrate paths file: %s", inner_exc)
                self.paths = []
        except Exception as exc:
            logger.warning("Unable to load paths (%s): %s", paths_file, exc)

    def _load_vectors(self):
        if not self.vector_path or not os.path.exists(self.vector_path):
            return
        try:
            data = np.load(self.vector_path)
            self.vector_matrix = np.asarray(data, dtype="float32")
            if len(self.paths) != len(self.vector_matrix):
                logger.warning("Vector count mismatch: %d paths vs %d vectors", len(self.paths), len(self.vector_matrix))
        except Exception as exc:
            logger.warning("Failed to load cached vectors (%s): %s", self.vector_path, exc)
            self.vector_matrix = None

    def _reindex_paths(self):
        self.path_to_index = {path: idx for idx, path in enumerate(self.paths)}

    def _save_paths(self):
        paths_file = f"{self.index_path}.paths"
        self._atomic_json_dump(paths_file, self.paths)

    def _ensure_dir(self, target_path: str) -> None:
        directory = os.path.dirname(target_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _atomic_write(self, target_path: str, writer) -> None:
        self._ensure_dir(target_path)
        tmp_path = f"{target_path}.tmp"
        try:
            writer(tmp_path)
            os.replace(tmp_path, target_path)
        except Exception as exc:
            logger.warning("Failed atomic write (%s): %s", target_path, exc)
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _atomic_json_dump(self, target_path: str, data) -> None:
        def _write(path: str) -> None:
            with open(path, "w") as f:
                json.dump(data, f)

        self._atomic_write(target_path, _write)

    def _atomic_array_save(self, target_path: str, array: np.ndarray) -> None:
        def _write(path: str) -> None:
            with open(path, "wb") as f:
                np.save(f, array)

        self._atomic_write(target_path, _write)

    def _atomic_index_save(self) -> None:
        idx_to_save = self.index
        # If GPU index, convert back to CPU before saving
        try:
            if hasattr(faiss, 'index_gpu_to_cpu'):
                idx_to_save = faiss.index_gpu_to_cpu(self.index)
        except Exception:
            pass

        temp_path = f"{self.index_path}.tmp"
        self._ensure_dir(self.index_path)
        try:
            faiss.write_index(idx_to_save, temp_path)
            os.replace(temp_path, self.index_path)
        except Exception as exc:
            logger.warning("Failed to write index (%s): %s", self.index_path, exc)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _append_vectors(self, vectors: np.ndarray):
        if vectors is None or vectors.size == 0 or not self.vector_path:
            return
        if self.vector_matrix is None or len(self.vector_matrix) == 0:
            self.vector_matrix = vectors.copy()
        else:
            self.vector_matrix = np.vstack((self.vector_matrix, vectors))

    def _save_vectors(self):
        if self.vector_path is None or self.vector_matrix is None:
            return
        self._atomic_array_save(self.vector_path, self.vector_matrix)

    def add(self, vectors: np.ndarray, new_paths: list):
        if vectors.size == 0:
            return
        vectors = np.array(vectors, dtype="float32")
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.paths.extend(new_paths)
        self._append_vectors(vectors)
        self._reindex_paths()

    def search(self, query_vector: np.ndarray, k: int = 20):
        query_vector = np.atleast_2d(np.array(query_vector, dtype="float32"))
        faiss.normalize_L2(query_vector)
        distances, indices = self.index.search(query_vector, k)
        results = []
        for score, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.paths):
                results.append({"path": self.paths[idx], "score": float(score)})
        return results

    def save(self):
        self._atomic_index_save()
        self._save_paths()
        self._save_vectors()

    def get_vector_by_path(self, path: str):
        idx = self.path_to_index.get(path)
        if idx is None or self.vector_matrix is None:
            return None
        return self.vector_matrix[idx]

    def has_path(self, path: str) -> bool:
        return path in self.path_to_index