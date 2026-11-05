"""Order-stable incremental face clustering.

Stage 1 - incremental core-face graph (union-find).
    Two faces are linked when their cosine similarity is >= `link_threshold` AND both are *core* faces.
    A face is core when it has >= `min_neighbors` other faces above the threshold and its quality
    (raw embedding norm, optional) is >= `quality_min`. Both conditions only ever switch from false to true
    as faces are added, so the set of links only grows; union-find can therefore absorb every new batch
    without re-clustering, and the resulting core partition depends only on the SET of faces seen,
    not on the order they arrived in. Non-core faces attach to their most similar core neighbour
    (resolved at read time from the final graph, so also order-free); faces with none stay singletons.
    This is the IncrementalDBSCAN idea (Ester et al., VLDB 1998) with a quality gate.

Stage 1b (optional) - supported weak links.
    Two core faces whose similarity is only in [weak_threshold, link_threshold) - e.g. the same person in profile
    or decades apart - are joined only if they also share >= `support` common neighbours (faces similar to BOTH,
    at >= weak_threshold). A single accidental look-alike pair cannot pass this test, so weak links cannot chain
    two different people the way a lower link threshold does. It is computed at read time from the final
    neighbourhood graph, so it is still independent of insertion order.

Stage 2 - deterministic average-linkage merge of cluster centroids at `merge_threshold`
    (same as ClusterEngine stage 2), re-run on read; it only touches centroids, so it is cheap.
"""
import faiss
import numpy as np


class StableIncrementalClusterer:
    def __init__(self, link_threshold: float = 0.45, min_neighbors: int = 2,
                 merge_threshold=0.40, quality_min=None, dim: int = 512, attach_threshold=None,
                 weak_threshold=None, support: int = 3):
        self.link_threshold = float(link_threshold)
        # Non-core faces (e.g. blurred / old / compressed photos) attach to their most similar core face if the
        # similarity is >= attach_threshold (default: link_threshold). A looser attach threshold recovers degraded
        # photos without letting them CHAIN two people together (only core-core links merge clusters).
        self.attach_threshold = float(link_threshold if attach_threshold is None else min(attach_threshold, link_threshold))
        self.min_neighbors = max(0, int(min_neighbors))
        self.weak_threshold = None if weak_threshold is None else min(float(weak_threshold), self.link_threshold)
        self.support = max(1, int(support))
        self.radius = self.attach_threshold if self.weak_threshold is None else min(self.attach_threshold, self.weak_threshold)
        self.merge_threshold = merge_threshold
        self.quality_min = quality_min
        self.index = faiss.IndexFlatIP(dim)
        self.adj = []          # adj[i] = list of (j, sim) with sim >= attach_threshold, j != i
        self.eligible = []     # quality gate per face
        self.core = []
        self.parent = []
        self._X = []           # unit vectors (for centroids)

    # ---------------------------------------------------------------- union-find
    def _find(self, a):
        p = self.parent
        while p[a] != a:
            p[a] = p[p[a]]
            a = p[a]
        return a

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            if ra < rb:
                ra, rb = rb, ra
            self.parent[ra] = rb

    def __len__(self):
        return self.index.ntotal

    # ---------------------------------------------------------------- incremental update
    def add(self, embeddings, norms=None):
        """Add a batch of faces. `embeddings`: (n, d) raw or unit vectors. `norms`: raw embedding norms
        used as the quality signal (defaults to the norms of `embeddings`). Returns the new face ids."""
        E = np.asarray(embeddings, dtype="float32")
        if E.ndim == 1:
            E = E.reshape(1, -1)
        if len(E) == 0:
            return []
        q = np.linalg.norm(E, axis=1) if norms is None else np.asarray(norms, dtype="float32")
        X = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
        start = self.index.ntotal
        self.index.add(X)
        new_ids = list(range(start, start + len(X)))
        for k in range(len(X)):
            self.adj.append([])
            self.eligible.append(self.quality_min is None or bool(q[k] >= self.quality_min))
            self.core.append(False)
            self.parent.append(start + k)
            self._X.append(X[k])

        # neighbours of every new face among ALL faces (old + new); faiss returns sim > radius
        lims, D, I = self.index.range_search(X, self.radius - 1e-6)
        touched = set(new_ids)
        for k, i in enumerate(new_ids):
            for sim, j in zip(D[lims[k]:lims[k + 1]], I[lims[k]:lims[k + 1]]):
                j = int(j)
                if j == i:
                    continue
                self.adj[i].append((j, float(sim)))
                if j < start:                      # old face gains a new neighbour (new-new pairs appear twice already)
                    self.adj[j].append((i, float(sim)))
                    touched.add(j)

        # faces that just became core link to every core neighbour
        lt = self.link_threshold
        newly_core = [i for i in sorted(touched)
                      if not self.core[i] and self.eligible[i] and sum(s >= lt for _, s in self.adj[i]) >= self.min_neighbors]
        for i in newly_core:
            self.core[i] = True
        for i in newly_core:
            for j, s in self.adj[i]:
                if s >= lt and self.core[j]:
                    self._union(i, j)
        return new_ids

    # ---------------------------------------------------------------- read
    def labels(self):
        """Cluster label per face id (insertion order)."""
        n = len(self)
        if n == 0:
            return np.array([], dtype=int)
        parent = list(self.parent)                     # read-time copy: weak links never alter the incremental state
        find = self._find
        if self.weak_threshold is not None:
            w, lt = self.weak_threshold, self.link_threshold
            nb = [{j for j, s in self.adj[i] if s >= w} for i in range(n)]
            saved, self.parent = self.parent, parent
            for i in range(n):
                if not self.core[i]:
                    continue
                for j, s in self.adj[i]:
                    if j > i and self.core[j] and w <= s < lt and find(i) != find(j)                             and len(nb[i] & nb[j]) >= self.support:
                        self._union(i, j)
            self.parent = saved
        lab = np.full(n, -1, dtype=int)
        saved, self.parent = self.parent, parent
        for i in range(n):
            if self.core[i]:
                lab[i] = self._find(i)
        for i in range(n):
            if not self.core[i]:
                best, best_sim = None, -2.0
                for j, s in self.adj[i]:
                    if self.core[j] and s >= self.attach_threshold and (s > best_sim or (s == best_sim and best is not None and j < best)):
                        best, best_sim = j, s
                lab[i] = self._find(best) if best is not None else i
        self.parent = saved
        lab = np.unique(lab, return_inverse=True)[1]
        return self._merge(lab)

    def _merge(self, lab):
        ids = np.unique(lab)
        if self.merge_threshold is None or len(ids) < 2 or len(ids) > 20000:
            return lab
        from sklearn.cluster import AgglomerativeClustering
        X = np.stack(self._X)
        cent = np.zeros((len(ids), X.shape[1]), dtype="float32")
        np.add.at(cent, lab, X)
        cent /= (np.linalg.norm(cent, axis=1, keepdims=True) + 1e-9)
        merged = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                         distance_threshold=1.0 - self.merge_threshold).fit_predict(cent)
        return merged[lab]

    def fit_predict(self, embeddings, norms=None):
        """Batch convenience: add everything in one call and return labels."""
        self.add(embeddings, norms)
        return self.labels()
