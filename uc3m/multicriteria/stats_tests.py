"""Non-parametric significance tests for MADRL algorithm comparison."""

from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

try:
    from scipy import stats
except ImportError:  # pragma: no cover
    stats = None


def _require_scipy() -> None:
    if stats is None:
        raise ImportError("scipy is required for Wilcoxon / Kruskal-Wallis tests")


def wilcoxon_signed_rank(
    x: Sequence[float],
    y: Sequence[float],
    *,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> Dict[str, object]:
    """Wilcoxon signed-rank test for paired algorithm comparisons."""

    _require_scipy()
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.shape != b.shape:
        raise ValueError("x and y must have the same shape for paired Wilcoxon")
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if a.size < 1:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "n": 0,
            "status": "insufficient_data",
            "alpha": float(alpha),
        }
    # Zero differences are dropped by scipy; guard tiny samples.
    if np.allclose(a, b):
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "n": int(a.size),
            "status": "identical_samples",
            "alpha": float(alpha),
        }
    try:
        result = stats.wilcoxon(a, b, alternative=alternative, zero_method="wilcox")
        p = float(result.pvalue)
        return {
            "statistic": float(result.statistic),
            "p_value": p,
            "significant": bool(p < alpha),
            "n": int(a.size),
            "status": "ok",
            "alpha": float(alpha),
            "alternative": alternative,
        }
    except ValueError as exc:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "n": int(a.size),
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }


def kruskal_wallis(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Kruskal-Wallis omnibus test across algorithms."""

    _require_scipy()
    labels = []
    samples = []
    for name, values in groups.items():
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            continue
        labels.append(str(name))
        samples.append(arr)
    if len(samples) < 2:
        return {
            "H": None,
            "p_value": None,
            "significant": False,
            "n_groups": len(samples),
            "groups": labels,
            "status": "insufficient_groups",
            "alpha": float(alpha),
        }
    H, p = stats.kruskal(*samples)
    return {
        "H": float(H),
        "p_value": float(p),
        "significant": bool(float(p) < alpha),
        "n_groups": len(samples),
        "groups": labels,
        "status": "ok",
        "alpha": float(alpha),
    }


def pairwise_wilcoxon(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> List[Dict[str, object]]:
    """All pairwise Wilcoxon signed-rank comparisons."""

    rows: List[Dict[str, object]] = []
    for a, b in combinations(list(groups.keys()), 2):
        result = wilcoxon_signed_rank(groups[a], groups[b], alpha=alpha)
        rows.append(
            {
                "algorithm_a": a,
                "algorithm_b": b,
                **result,
            }
        )
    return rows


def significance_gate_top_metrics(
    per_seed_metrics: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    top_criteria: Sequence[str] = ("C1", "C2"),
    first: str,
    second: str,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Check whether 1st vs 2nd differ significantly on the heaviest criteria.

    ``per_seed_metrics`` maps criterion -> algorithm -> seed values.
    For cost criteria, lower is better; tests remain two-sided on raw values.
    """

    details = {}
    any_significant = False
    for cid in top_criteria:
        if cid not in per_seed_metrics:
            details[cid] = {"status": "missing_criterion"}
            continue
        by_algo = per_seed_metrics[cid]
        if first not in by_algo or second not in by_algo:
            details[cid] = {"status": "missing_algorithm"}
            continue
        test = wilcoxon_signed_rank(by_algo[first], by_algo[second], alpha=alpha)
        details[cid] = test
        any_significant = any_significant or bool(test.get("significant"))
    return {
        "first": first,
        "second": second,
        "top_criteria": list(top_criteria),
        "any_significant": bool(any_significant),
        "defensible": bool(any_significant),
        "details": details,
        "alpha": float(alpha),
    }
