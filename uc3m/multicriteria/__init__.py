"""Multicriteria MADRL algorithm selection (TOPSIS + AHP).

Implements the six evaluation dimensions, empirical consolidation helpers,
statistical tests, and the TOPSIS/AHP decision pipeline for HAPPO, MAAC,
MASAC and MATD3 under energy flexibility, CO2 and cost objectives.
"""

from __future__ import annotations

from uc3m.multicriteria.ahp import (
    DEFAULT_AHP_PAIRWISE,
    ahp_priority_weights,
    ahp_rank_alternatives,
    consistency_ratio,
)
from uc3m.multicriteria.criteria import (
    CRITERION_SPECS,
    DEFAULT_CRITERION_WEIGHTS,
    ALGORITHMS,
    MetricAggregate,
    SelectionCriterion,
    aggregate_seed_values,
    compute_dimension_metrics,
    mean_std_report,
)
from uc3m.multicriteria.pipeline import (
    ILLUSTRATIVE_DECISION_MATRIX,
    run_selection_pipeline,
)
from uc3m.multicriteria.topsis import topsis_rank

__all__ = [
    "ALGORITHMS",
    "CRITERION_SPECS",
    "DEFAULT_AHP_PAIRWISE",
    "DEFAULT_CRITERION_WEIGHTS",
    "ILLUSTRATIVE_DECISION_MATRIX",
    "MetricAggregate",
    "SelectionCriterion",
    "aggregate_seed_values",
    "ahp_priority_weights",
    "ahp_rank_alternatives",
    "compute_dimension_metrics",
    "consistency_ratio",
    "mean_std_report",
    "run_selection_pipeline",
    "topsis_rank",
]
