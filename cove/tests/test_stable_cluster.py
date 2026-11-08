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


def _clusterer(**kw):
    cfg = dict(link_threshold=0.5, min_neighbors=1, attach_threshold=0.35, merge_threshold=0.45, dim=64)
    cfg.update(kw)
    return StableIncrementalClusterer(**cfg)


def test_constrained_path_equals_plain_path_without_constraints():
    X, _ = _blobs(noise=0.9)
    c = _clusterer()
    c.add(X)
    assert adjusted_rand_score(c.labels(), c._labels_constrained()) == 1.0


def test_user_corrections_are_obeyed_and_survive_new_photos():
    X, y = _blobs(noise=0.9, seed=3)
    c = _clusterer(merge_threshold=0.0)          # merge everything unless the user says otherwise
    c.add(X[:120])
    c.add_cannot_link(0, 6)                       # person 0 vs person 1
    c.add_must_link(12, 13)
    lab = c.labels()
    assert lab[0] != lab[6] and lab[12] == lab[13]
    c.add(X[120:])                                # new photos arrive: corrections still hold
    lab = c.labels()
    assert lab[0] != lab[6] and lab[12] == lab[13]


def test_cannot_link_splits_a_wrong_merge():
    X, y = _blobs(n_id=2, per=10, noise=0.9, seed=1)
    c = _clusterer(merge_threshold=-1.0)          # forces one cluster
    c.add(X)
    assert len(set(c.labels())) == 1
    c.add_cannot_link(0, 10)
    assert len(set(c.labels())) >= 2


def test_constraints_keep_order_independence():
    X, y = _blobs(noise=0.9, seed=5)
    rng = np.random.RandomState(0)
    pairs_c = [(0, 7), (30, 40)]
    pairs_m = [(1, 2), (50, 55)]
    ref = None
    for t in range(4):
        perm = np.arange(len(X)) if t == 0 else rng.permutation(len(X))
        inv = np.empty_like(perm); inv[perm] = np.arange(len(X))
        c = _clusterer()
        for s in range(0, len(X), 37):
            c.add(X[perm][s:s + 37])
        for a, b in (pairs_c if t % 2 else pairs_c[::-1]):
            c.add_cannot_link(inv[a], inv[b])
        for a, b in pairs_m:
            c.add_must_link(inv[a], inv[b])
        lab = c.labels()[inv]
        ref = lab if ref is None else ref
        assert adjusted_rand_score(ref, lab) == 1.0


def test_many_cannot_links_always_hold_in_any_order():
    X, y = _blobs(n_id=6, per=15, noise=1.2, seed=7)
    rng = np.random.RandomState(1)
    pairs = []
    while len(pairs) < 25:
        a, b = rng.randint(len(X), size=2)
        if y[a] != y[b]:
            pairs.append((int(a), int(b)))
    ref = None
    for t in range(5):
        perm = np.arange(len(X)) if t == 0 else rng.permutation(len(X))
        inv = np.empty_like(perm); inv[perm] = np.arange(len(X))
        c = _clusterer(merge_threshold=-1.0)      # merge pressure everywhere: only the constraints hold people apart
        c.add(X[perm])
        for a, b in [pairs[i] for i in rng.permutation(len(pairs))]:
            c.add_cannot_link(inv[a], inv[b])
        lab = c.labels()[inv]
        assert all(lab[a] != lab[b] for a, b in pairs)
        ref = lab if ref is None else ref
        assert adjusted_rand_score(ref, lab) == 1.0


def test_pose_bonus_keeps_order_independence_and_zero_bonus_is_plain():
    X, y = _blobs(noise=0.9, seed=11)
    yaw = np.random.RandomState(2).uniform(-1, 1, len(X))
    plain = _clusterer(); plain.add(X)
    zero = _clusterer(pose_bonus=0.0); zero.add(X, None, yaw)
    assert adjusted_rand_score(plain.labels(), zero.labels()) == 1.0
    ref = None
    rng = np.random.RandomState(4)
    for t in range(4):
        perm = np.arange(len(X)) if t == 0 else rng.permutation(len(X))
        inv = np.empty_like(perm); inv[perm] = np.arange(len(X))
        c = _clusterer(pose_bonus=0.1, pose_scale=0.5)
        for s in range(0, len(X), 29):
            c.add(X[perm][s:s + 29], None, yaw[perm][s:s + 29])
        lab = c.labels()[inv]
        ref = lab if ref is None else ref
        assert adjusted_rand_score(ref, lab) == 1.0


def test_contradictory_corrections_resolved_independent_of_order():
    # user says 0~3 same, 3~6 same, but 0 != 6: the cannot-link wins and one must-link must be dropped;
    # which one is dropped must not depend on the order in which faces were added (round-2 review, DA m1)
    rng = np.random.RandomState(0)
    d = 16
    c0, c1, c2 = rng.randn(3, d)
    X = np.vstack([c + 0.05 * rng.randn(3, d) for c in (c0, c1, c2)]).astype("float32")
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    outcomes = set()
    for t in range(12):
        o = np.random.RandomState(t).permutation(len(X))
        inv = np.empty_like(o)
        inv[o] = np.arange(len(X))
        c = StableIncrementalClusterer(link_threshold=0.9, min_neighbors=1, attach_threshold=0.8,
                                       merge_threshold=0.95, dim=d)
        c.add(X[o])
        c.add_must_link(inv[0], inv[3])
        c.add_must_link(inv[3], inv[6])
        c.add_cannot_link(inv[0], inv[6])
        lab = c.labels()[inv]
        assert lab[0] != lab[6]
        outcomes.add((lab[0] == lab[3], lab[3] == lab[6]))
    assert len(outcomes) == 1
