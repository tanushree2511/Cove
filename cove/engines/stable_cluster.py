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

Pose-aware similarity (optional, `pose_bonus` > 0).
    The same person seen frontal and in profile has a lower cosine similarity than two frontal photos, so one fixed
    threshold splits them. With per-face yaw estimates (from the detector's 5 landmarks, free at run time), every
    pairwise similarity is replaced by  s + pose_bonus * min(1, | |yaw_i| - |yaw_j| | / pose_scale)  before any
    threshold is applied. It depends only on the pair, so order independence is unchanged; pose_bonus = 0 is the
    plain method.

User corrections (optional) - must-link / cannot-link constraints.
    `add_must_link(i, j)` ("these two are the same person") and `add_cannot_link(i, j)` ("these are different people")
    are stored with the clusterer and obeyed on every read, so re-clustering or adding photos never undoes them.
    With constraints present, labels() builds the same partition by a constrained maximum-spanning-forest pass:
    must-links first, then the core links in decreasing similarity (each union skipped if it would put a
    cannot-linked pair together), then attachment, then the average-linkage centroid merge with the same rule.
    Every step depends only on the set of faces, their similarities and the set of constraints, never on the order
    faces or constraints arrived in. With no constraints the result equals the unconstrained path.
"""
import faiss
import numpy as np


class StableIncrementalClusterer:
    def __init__(self, link_threshold: float = 0.45, min_neighbors: int = 2,
                 merge_threshold=0.40, quality_min=None, dim: int = 512, attach_threshold=None,
                 weak_threshold=None, support: int = 3, pose_bonus: float = 0.0, pose_scale: float = 1.0):
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
        self.pose_bonus = max(0.0, float(pose_bonus))
        self.pose_scale = max(1e-6, float(pose_scale))
        self._yaw = []         # |yaw| per face (0 when unknown)
        self.quality_min = quality_min
        self.index = faiss.IndexFlatIP(dim)
        self.adj = []          # adj[i] = list of (j, sim) with sim >= attach_threshold, j != i
        self.eligible = []     # quality gate per face
        self.core = []
        self.parent = []
        self._X = []           # unit vectors (for centroids)
        self.must = set()      # user corrections: (i, j) face-id pairs, i < j
        self.cannot = set()

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
    def add(self, embeddings, norms=None, yaws=None):
        """Add a batch of faces. `embeddings`: (n, d) raw or unit vectors. `norms`: raw embedding norms
        used as the quality signal (defaults to the norms of `embeddings`). `yaws`: optional per-face yaw estimates
        (used only when pose_bonus > 0). Returns the new face ids."""
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
            self._yaw.append(0.0 if yaws is None else abs(float(yaws[k])))

        # neighbours of every new face among ALL faces (old + new); faiss returns sim > radius
        pb = self.pose_bonus
        lims, D, I = self.index.range_search(X, self.radius - pb - 1e-6)
        touched = set(new_ids)
        for k, i in enumerate(new_ids):
            for sim, j in zip(D[lims[k]:lims[k + 1]], I[lims[k]:lims[k + 1]]):
                j = int(j)
                if j == i:
                    continue
                if pb:
                    sim = float(sim) + pb * min(1.0, abs(self._yaw[i] - self._yaw[j]) / self.pose_scale)
                    if sim < self.radius - 1e-6:
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

    # ---------------------------------------------------------------- user corrections
    def add_must_link(self, i, j):
        """The user says faces i and j are the same person."""
        i, j = int(i), int(j)
        if i != j:
            self.must.add((min(i, j), max(i, j)))

    def add_cannot_link(self, i, j):
        """The user says faces i and j are different people (takes precedence over a conflicting must-link)."""
        i, j = int(i), int(j)
        if i != j:
            self.cannot.add((min(i, j), max(i, j)))

    # ---------------------------------------------------------------- read
    def labels(self):
        """Cluster label per face id (insertion order)."""
        n = len(self)
        if n == 0:
            return np.array([], dtype=int)
        if self.must or self.cannot:
            return self._labels_constrained()
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

    def _labels_constrained(self):
        n = len(self)
        par = list(range(n))
        enemies = {}                                   # root -> faces that may never join it
        for a, b in self.cannot:
            enemies.setdefault(a, set()).add(b)
            enemies.setdefault(b, set()).add(a)

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        def try_union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return True
            ea, eb = enemies.get(ra, ()), enemies.get(rb, ())
            if any(find(e) == rb for e in ea) or any(find(e) == ra for e in eb):
                return False
            if ra < rb:
                ra, rb = rb, ra                         # ra joins rb; its "never join" list moves with it
            par[ra] = rb
            moved = enemies.pop(ra, None)
            if moved:
                enemies.setdefault(rb, set()).update(moved)
            return True

        for a, b in sorted(self.must):                 # 1. the user's "same person" first
            try_union(a, b)
        lt = self.link_threshold                       # 2. core links, strongest first
        edges = [(s, i, j) for i in range(n) if self.core[i] for j, s in self.adj[i]
                 if j > i and self.core[j] and s >= lt]
        if self.weak_threshold is not None:
            w = self.weak_threshold
            nb = [{j for j, s in self.adj[i] if s >= w} for i in range(n)]
            edges += [(s, i, j) for i in range(n) if self.core[i] for j, s in self.adj[i]
                      if j > i and self.core[j] and w <= s < lt and len(nb[i] & nb[j]) >= self.support]
        for s, i, j in sorted(edges, key=lambda e: (-e[0], e[1], e[2])):
            try_union(i, j)
        has_core = set(find(i) for i in range(n) if self.core[i])
        att = []                                       # 3. attachment of non-core faces, best match first
        for i in range(n):
            if self.core[i] or find(i) in has_core:
                continue
            cands = sorted(((s, j) for j, s in self.adj[i] if self.core[j] and s >= self.attach_threshold),
                           key=lambda c: (-c[0], c[1]))
            if cands:
                att.append((cands[0][0], i, cands))
        for _, i, cands in sorted(att, key=lambda a: (-a[0], a[1])):
            for _, j in cands:
                if try_union(i, j):
                    break
        roots = np.array([find(i) for i in range(n)])
        ids, lab = np.unique(roots, return_inverse=True)
        if self.merge_threshold is None or len(ids) < 2 or len(ids) > 20000:
            return lab
        X = np.stack(self._X)                          # 4. constrained average-linkage merge of centroids
        k = len(ids)
        cent = np.zeros((k, X.shape[1]), dtype="float64")
        np.add.at(cent, lab, X)
        cent /= (np.linalg.norm(cent, axis=1, keepdims=True) + 1e-12)
        S = cent @ cent.T
        bad = np.zeros((k, k), dtype=bool)
        for a, b in self.cannot:
            bad[lab[a], lab[b]] = bad[lab[b], lab[a]] = True
        size = np.ones(k)
        alive = np.ones(k, dtype=bool)
        grp = np.arange(k)
        np.fill_diagonal(S, -np.inf)
        while True:
            M = np.where(bad, -np.inf, S)
            f = int(np.argmax(M))
            a, b = divmod(f, k)
            if not np.isfinite(M[a, b]) or M[a, b] < self.merge_threshold:
                break
            a, b = min(a, b), max(a, b)
            row = (size[a] * S[a] + size[b] * S[b]) / (size[a] + size[b])
            S[a, :] = row
            S[:, a] = row
            S[a, a] = -np.inf
            S[b, :] = -np.inf
            S[:, b] = -np.inf
            bad[a] |= bad[b]
            bad[:, a] = bad[a]
            size[a] += size[b]
            alive[b] = False
            grp[grp == b] = a
        return np.unique(grp[lab], return_inverse=True)[1]

    def fit_predict(self, embeddings, norms=None):
        """Batch convenience: add everything in one call and return labels."""
        self.add(embeddings, norms)
        return self.labels()
