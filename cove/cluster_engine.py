import faiss
import numpy as np

class ClusterEngine:
    def __init__(self, min_cluster_size: int = 3, threshold: float = 0.55):
        """
        Greedy Clustering (First-Leader) - Replaces HDBSCAN
        """
        self.min_cluster_size = max(1, min_cluster_size)
        self.threshold = threshold

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        print(f"   [Clustering] Greedy First-Leader (Threshold={self.threshold})...")

        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)
        if embeddings.size == 0:
            return np.array([], dtype=int)

        embeddings = embeddings.astype('float32')
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        leader_index = faiss.IndexFlatIP(dim)
        
        # Hardware Optimization: Move clustering index to GPU if available
        try:
            if hasattr(faiss, 'get_num_gpus') and faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                leader_index = faiss.index_cpu_to_gpu(res, 0, leader_index)
        except Exception:
            pass # Fallback to CPU silently

        labels = np.full(len(embeddings), -1, dtype=int)
        cluster_count = 0
        
        for i, vector in enumerate(embeddings):
            vector = vector.reshape(1, -1)
            
            if leader_index.ntotal == 0:
                leader_index.add(vector)
                labels[i] = cluster_count
                cluster_count += 1
                continue
            
            dists, idxs = leader_index.search(vector, 1)
            if dists[0][0] >= self.threshold:
                labels[i] = idxs[0][0]
            else:
                leader_index.add(vector)
                labels[i] = cluster_count
                cluster_count += 1

        unique, counts = np.unique(labels, return_counts=True)
        valid_clusters = unique[counts >= self.min_cluster_size]
        return np.array([lbl if lbl in valid_clusters else -1 for lbl in labels])