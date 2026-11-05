"""Sanity tests for the evaluation metrics against hand-computed values (run: pytest evaluation/test_metrics.py)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("COVE_USER_DATA", os.path.join(os.path.dirname(__file__), "cache", "userdata"))

from common import ranking_metrics  # noqa: E402
from exp1_cluster import bcubed, evaluate  # noqa: E402
from exp34_analyze import redundancy_filter, retrieval_metrics  # noqa: E402
from exp2_analyze import ranks_of  # noqa: E402


def test_bcubed_perfect_and_degenerate():
    truth = np.array(["a", "a", "b", "b"])
    assert bcubed(np.array([0, 0, 1, 1]), truth) == pytest.approx((1.0, 1.0, 1.0))
    p, r, f = bcubed(np.array([0, 0, 0, 0]), truth)            # everything in one cluster: perfect recall, precision 0.5
    assert (p, r) == pytest.approx((0.5, 1.0)) and f == pytest.approx(2 * 0.5 / 1.5)
    p, r, f = bcubed(np.array([0, 1, 2, 3]), truth)            # all singletons: perfect precision, recall 0.5
    assert (p, r) == pytest.approx((1.0, 0.5))


def test_bcubed_hand_example():
    # truth: {0,1,2} and {3}; prediction: {0,1} {2,3}
    truth = np.array([0, 0, 0, 1]); pred = np.array([0, 0, 1, 1])
    # precision per item: 1,1,1/2,1/2 -> 0.75 ; recall per item: 2/3,2/3,1/3,1 -> 0.6667
    p, r, _ = bcubed(pred, truth)
    assert p == pytest.approx(0.75) and r == pytest.approx((2 / 3 + 2 / 3 + 1 / 3 + 1) / 4)


def test_ari_nmi_identical_partitions():
    m = evaluate(np.array([5, 5, 7, 7, 9]), np.array(["x", "x", "y", "y", "z"]))
    assert m["ARI"] == pytest.approx(1.0) and m["NMI"] == pytest.approx(1.0) and m["clusters"] == 3


def test_ranking_metrics():
    m = ranking_metrics([1, 2, 5, 20])
    assert m["R@1"] == 0.25 and m["R@5"] == 0.75 and m["R@10"] == 0.75
    assert m["MRR"] == pytest.approx((1 + 0.5 + 0.2 + 0.05) / 4)


def test_ranks_of_counts_strictly_better_items():
    I = np.eye(3, dtype="float32")
    Q = np.array([[1, 0, 0], [0.4, 0.5, 0.1]], dtype="float32")
    assert ranks_of(Q, I, np.array([0, 0])).tolist() == [1, 2]       # second query scores image 1 higher than its own image 0


def test_video_retrieval_metrics_hand_example():
    # one query, 6 videos, relevant = {0, 3}; similarity order: 3, 1, 0, 2, 4, 5  -> hits at rank 1 and rank 3
    S = np.array([[0.5, 0.8, 0.1, 0.9, 0.0, -0.1]])
    rel = np.array([[True, False, False, True, False, False]])
    per = retrieval_metrics(S, rel)
    assert per["Hit@1"][0] == 1 and per["Recall@1"][0] == 0.5 and per["Recall@5"][0] == 1.0
    assert per["MRR"][0] == 1.0
    assert per["mAP"][0] == pytest.approx((1 / 1 + 2 / 3) / 2)       # AP = mean(precision at each relevant rank)
    assert per["P@10"][0] == pytest.approx(2 / 10)


def test_redundancy_filter_matches_app_rules():
    rng = np.random.RandomState(0)
    base = rng.rand(256).astype("float32"); base /= base.sum()
    same = [base.copy() for _ in range(14)]                               # 14 identical frames -> only the anchor + padding up to 4
    keep = redundancy_filter(same)
    assert keep[0] == 0 and len(keep) == 4                                # the app always keeps at least 4
    distinct = [np.roll(base, 37 * i) for i in range(14)]                  # clearly different frames are all kept
    assert len(redundancy_filter(distinct)) >= 10
