import numpy as np
import pytest

pytest.importorskip("faiss")
pytest.importorskip("sklearn")

from engines.cluster_engine import ClusterEngine


def _unit(v):
    v = np.asarray(v, dtype="float32")
    return v / np.linalg.norm(v)


def test_distinct_people_stay_separate():
    # three people along orthogonal axes, each with a few slightly-noisy faces
    rng = np.random.default_rng(0)
    faces, truth = [], []
    for person in range(3):
        axis = np.zeros(8)
        axis[person] = 1.0
        for _ in range(4):
            faces.append(_unit(axis + rng.normal(0, 0.05, 8)))
            truth.append(person)
    labels = ClusterEngine(min_cluster_size=1).fit_predict(np.array(faces))
    assert len(set(labels)) == 3
    for person in range(3):
        assert len({labels[i] for i, t in enumerate(truth) if t == person}) == 1


def test_merge_pass_rejoins_a_person_split_by_the_leader_pass():
    # v1 is 0.42 away from v2/v3 (below the 0.45 leader threshold) so the leader pass starts a second
    # cluster for v2+v3; their centroid is ~0.43 from v1, above the 0.40 merge threshold.
    v1 = _unit([1, 0, 0, 0])
    v2 = _unit([0.42, 0.9075, 0, 0])
    v3 = _unit([0.42, 0.797, 0.434, 0])
    faces = np.array([v1, v2, v3])

    split = ClusterEngine(min_cluster_size=1, merge_threshold=None).fit_predict(faces.copy())
    merged = ClusterEngine(min_cluster_size=1).fit_predict(faces.copy())
    assert len(set(split)) == 2
    assert len(set(merged)) == 1


def test_min_cluster_size_marks_small_clusters_as_noise():
    faces = np.array([_unit([1, 0, 0]), _unit([1, 0.01, 0]), _unit([0, 0, 1])])
    labels = ClusterEngine(min_cluster_size=2).fit_predict(faces)
    assert labels[0] == labels[1] != -1
    assert labels[2] == -1


def test_empty_input():
    assert len(ClusterEngine().fit_predict(np.empty((0, 512), dtype="float32"))) == 0
