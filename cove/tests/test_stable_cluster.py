import numpy as np
from sklearn.metrics import adjusted_rand_score

from engines.stable_cluster import StableIncrementalClusterer


def _blobs(n_id=30, per=6, dim=64, noise=0.35, seed=0):
    rng = np.random.RandomState(seed)
    centers = rng.randn(n_id, dim)
    X = np.repeat(centers, per, axis=0) + noise * rng.randn(n_id * per, dim)
    y = np.repeat(np.arange(n_id), per)
    return X.astype("float32"), y


def _run(X, order, batch, **kw):
    c = StableIncrementalClusterer(dim=X.shape[1], **kw)
    for s in range(0, len(order), batch):
        c.add(X[order[s:s + batch]])
    lab = c.labels()
    back = np.empty(len(X), dtype=int)
    back[order] = lab
    return back


def test_recovers_identities():
    X, y = _blobs()
    lab = _run(X, np.arange(len(X)), len(X), link_threshold=0.5, min_neighbors=2)
    assert adjusted_rand_score(y, lab) > 0.95


def test_result_independent_of_order_and_batching():
    X, y = _blobs(seed=1, noise=0.6)
    ref = _run(X, np.arange(len(X)), len(X), link_threshold=0.4, min_neighbors=2)
    rng = np.random.RandomState(5)
    for batch in (1, 7, 50):
        perm = rng.permutation(len(X))
        assert adjusted_rand_score(ref, _run(X, perm, batch, link_threshold=0.4, min_neighbors=2)) == 1.0


def test_quality_gate_blocks_low_quality_bridge():
    # two identities joined only through one low-quality face
    a = np.array([[1, 0, 0]] * 3, dtype="float32") + 0.01
    b = np.array([[0, 1, 0]] * 3, dtype="float32") + 0.01
    bridge = np.array([[0.7, 0.7, 0]], dtype="float32") * 0.1     # small norm = low quality
    X = np.vstack([a, b, bridge])
    c = StableIncrementalClusterer(dim=3, link_threshold=0.6, min_neighbors=2, merge_threshold=None, quality_min=0.5)
    lab = c.fit_predict(X)
    assert lab[0] != lab[3]
    c2 = StableIncrementalClusterer(dim=3, link_threshold=0.6, min_neighbors=2, merge_threshold=None)
    lab2 = c2.fit_predict(X)
    assert lab2[0] == lab2[3]     # without the gate the bridge chains them


def test_empty():
    c = StableIncrementalClusterer(dim=8)
    assert len(c.labels()) == 0
    assert c.add(np.zeros((0, 8))) == []


def test_attach_threshold_keeps_order_independence_and_recovers_weak_faces():
    X, y = _blobs(n_id=20, per=6, seed=3, noise=0.8)
    kw = dict(link_threshold=0.45, min_neighbors=1, attach_threshold=0.30)
    ref = _run(X, np.arange(len(X)), len(X), **kw)
    rng = np.random.RandomState(9)
    for batch in (1, 13):
        assert adjusted_rand_score(ref, _run(X, rng.permutation(len(X)), batch, **kw)) == 1.0
    strict = _run(X, np.arange(len(X)), len(X), link_threshold=0.45, min_neighbors=1)
    assert adjusted_rand_score(y, ref) >= adjusted_rand_score(y, strict)


def test_supported_weak_links_order_independent_and_need_support():
    X, y = _blobs(n_id=20, per=8, seed=4, noise=0.9)
    kw = dict(link_threshold=0.5, min_neighbors=1, attach_threshold=0.35, weak_threshold=0.35, support=3)
    ref = _run(X, np.arange(len(X)), len(X), **kw)
    rng = np.random.RandomState(2)
    for batch in (1, 17):
        assert adjusted_rand_score(ref, _run(X, rng.permutation(len(X)), batch, **kw)) == 1.0
    # a lone weak pair with no shared neighbours must NOT be joined
    a = np.array([[1, 0, 0], [1, 0.05, 0]], dtype="float32"); b = np.array([[0.4, 0.92, 0], [0.4, 0.92, 0.05]], dtype="float32")
    c = StableIncrementalClusterer(dim=3, link_threshold=0.9, min_neighbors=1, merge_threshold=None, weak_threshold=0.3, support=3)
    lab = c.fit_predict(np.vstack([a, b]))
    assert lab[0] != lab[2]
