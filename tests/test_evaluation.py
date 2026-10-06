import pytest
import numpy as np
from src.evaluation.metrics import pareto_prune, compute_hypervolume, compute_scalarized_regret
from src.evaluation.stats import bootstrap_ci, paired_statistical_test


def test_pareto_prune():
    # Points in 2D
    # (10, 5) and (5, 10) are non-dominated
    # (3, 3) is dominated by both
    # (10, 5) and (10, 5) duplicate
    points = np.array([
        [10.0, 5.0],
        [5.0, 10.0],
        [3.0, 3.0],
        [8.0, 2.0],
        [10.0, 5.0]
    ])

    frontier = pareto_prune(points)
    # The non-dominated set should contain [10, 5] and [5, 10]
    assert len(frontier) == 2
    # Verify [3, 3] and [8, 2] are pruned out
    for pt in frontier:
        assert (np.array_equal(pt, [10.0, 5.0]) or np.array_equal(pt, [5.0, 10.0]))


def test_compute_hypervolume():
    # 2D points: box of size 10x10 from (0,0) with point (10, 10)
    ref_point = np.array([0.0, 0.0])
    points = np.array([[10.0, 10.0]])

    hv = compute_hypervolume(points, ref_point)
    assert pytest.approx(hv, 0.01) == 100.0

    # Empty points should give 0.0
    assert compute_hypervolume(np.empty((0, 2)), ref_point) == 0.0


def test_compute_scalarized_regret():
    reference_front = np.array([
        [10.0, 0.0],
        [0.0, 10.0]
    ])
    preferences = np.array([
        [1.0, 0.0],  # optimal is [10, 0] -> val 10
        [0.0, 1.0]   # optimal is [0, 10] -> val 10
    ])

    # Case 1: Agent achieves optimal returns -> regret = 0
    agent_returns = np.array([
        [10.0, 0.0],
        [0.0, 10.0]
    ])
    res = compute_scalarized_regret(agent_returns, reference_front, preferences)
    assert res["mean_regret"] == 0.0
    assert res["worst_decile_regret"] == 0.0

    # Case 2: Agent achieves sub-optimal returns
    sub_returns = np.array([
        [5.0, 0.0],  # optimal 10, actual 5 -> regret 5
        [0.0, 2.0]   # optimal 10, actual 2 -> regret 8
    ])
    res2 = compute_scalarized_regret(sub_returns, reference_front, preferences)
    assert pytest.approx(res2["mean_regret"], 0.01) == 6.5
    assert res2["worst_decile_regret"] > 6.5
    assert pytest.approx(res2["max_regret"], 0.01) == 8.0


def test_bootstrap_ci():
    data = np.array([10.0, 12.0, 11.0, 13.0, 10.5])
    mean_val, lower, upper = bootstrap_ci(data, n_boot=1000, ci=0.95)

    assert pytest.approx(mean_val, 0.01) == float(np.mean(data))
    assert lower <= mean_val <= upper


def test_paired_statistical_test():
    # Seeds where method A consistently outperforms method B
    scores_a = np.array([100.0, 105.0, 110.0, 95.0, 108.0])
    scores_b = np.array([80.0, 85.0, 90.0, 75.0, 88.0])

    res = paired_statistical_test(scores_a, scores_b, alternative="greater")
    assert res["mean_diff"] == 20.0
    assert res["is_significant_005"] is True
