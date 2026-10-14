"""Evaluation metrics, statistical analysis, and protocol tools."""

from src.evaluation.metrics import (
    compute_hypervolume,
    compute_scalarized_regret,
    pareto_prune,
)
from src.evaluation.stats import bootstrap_ci, holm_adjust, paired_permutation_test

__all__ = [
    "bootstrap_ci",
    "compute_hypervolume",
    "compute_scalarized_regret",
    "holm_adjust",
    "paired_permutation_test",
    "pareto_prune",
]
