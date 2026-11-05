"""Analytic Hierarchy Process (AHP) weights and consistency ratio."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, cast

import numpy as np

from uc3m.multicriteria.criteria import CRITERION_IDS, DEFAULT_CRITERION_WEIGHTS

# Saaty random index (RI) by matrix order n.
_SAATY_RI: Mapping[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}

# Default pairwise matrix calibrated to recover approx. methodology weights
# C1=0.25, C2=0.25, C3=0.15, C4=0.10, C5=0.10, C6=0.15 with CR < 0.1.
# Order: C1, C2, C3, C4, C5, C6.
DEFAULT_AHP_PAIRWISE = np.asarray(
    [
        [1.0, 1.0, 2.0, 3.0, 3.0, 2.0],
        [1.0, 1.0, 2.0, 3.0, 3.0, 2.0],
        [1 / 2, 1 / 2, 1.0, 2.0, 2.0, 1.0],
        [1 / 3, 1 / 3, 1 / 2, 1.0, 1.0, 1 / 2],
        [1 / 3, 1 / 3, 1 / 2, 1.0, 1.0, 1 / 2],
        [1 / 2, 1 / 2, 1.0, 2.0, 2.0, 1.0],
    ],
    dtype=float,
)


class NonPositiveAutomaticAHP(ValueError):
    """Raw quantitative values do not define a positive AHP ratio scale."""


def _validate_pairwise(pairwise: np.ndarray) -> np.ndarray:
    """Saaty judgments are finite, strictly positive reciprocal comparisons."""
    matrix = np.asarray(pairwise, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not matrix.shape[0]:
        raise ValueError("pairwise must be a nonempty square matrix")
    if not np.all(np.isfinite(matrix)) or np.any(matrix <= 0):
        raise ValueError("pairwise must contain finite strictly positive judgments")
    if not np.allclose(np.diag(matrix), 1.0, rtol=1e-10, atol=1e-12):
        raise ValueError("pairwise diagonal must be one")
    if not np.allclose(matrix, 1.0 / matrix.T, rtol=1e-10, atol=1e-12):
        raise ValueError("pairwise judgments must be reciprocal")
    return matrix


def _principal_eigen(matrix: np.ndarray) -> Tuple[float, np.ndarray]:
    values, vectors = np.linalg.eig(matrix)
    idx = int(np.argmax(np.real(values)))
    lam = float(np.real(values[idx]))
    vec = np.real(vectors[:, idx])
    if np.sum(vec) < 0:
        vec = -vec
    weights = vec / np.sum(vec)
    return lam, weights.astype(float)


def consistency_ratio(
    pairwise: np.ndarray,
    *,
    weights: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Compute λ_max, CI and CR for a Saaty pairwise matrix."""

    matrix = _validate_pairwise(pairwise)
    n = int(matrix.shape[0])
    if weights is None:
        lam, weights = _principal_eigen(matrix)
    else:
        weights = np.asarray(weights, dtype=float)
        if weights.shape != (n,) or not np.all(np.isfinite(weights)) or np.any(weights <= 0):
            raise ValueError("weights must be a finite strictly positive vector of pairwise order")
        weights = weights / np.sum(weights)
        lam = float(np.mean((matrix @ weights) / weights))
    # A positive reciprocal matrix has lambda_max >= n. Only numerical roundoff
    # may make CI negative; a substantive negative value is never consistency.
    if not np.isfinite(lam) or lam < n - 1e-10 * max(n, 1):
        raise ValueError("invalid principal eigenvalue for positive reciprocal judgments")
    lam = max(lam, float(n))
    ci = (lam - n) / max(n - 1, 1)
    ri = float(_SAATY_RI.get(n, 1.49))
    cr = 0.0 if ri <= 0 else ci / ri
    return {
        "lambda_max": float(lam),
        "consistency_index": float(ci),
        "random_index": ri,
        "consistency_ratio": float(cr),
        "consistent": bool(cr < 0.10),
    }


def ahp_priority_weights(
    pairwise: Optional[np.ndarray] = None,
    *,
    labels: Sequence[str] = CRITERION_IDS,
    require_consistent: bool = True,
) -> Dict[str, Any]:
    """Derive normalized priority weights from an AHP pairwise matrix."""

    matrix = _validate_pairwise(pairwise if pairwise is not None else DEFAULT_AHP_PAIRWISE)
    if len(labels) != matrix.shape[0]:
        raise ValueError("labels length must match pairwise order")
    lam, weights = _principal_eigen(matrix)
    cr_info = consistency_ratio(matrix, weights=weights)
    if require_consistent and not cr_info["consistent"]:
        raise ValueError(
            f"AHP consistency ratio CR={cr_info['consistency_ratio']:.4f} >= 0.1"
        )
    weight_map = {str(label): float(w) for label, w in zip(labels, weights)}
    return {
        "weights": weight_map,
        "lambda_max": lam,
        **cr_info,
        "method": "ahp_eigen",
    }


def ahp_rank_alternatives(
    decision_matrix: Mapping[str, Mapping[str, float]],
    *,
    criteria_kind: Mapping[str, str],
    criteria_pairwise: Optional[np.ndarray] = None,
    alternative_pairwise: Optional[Mapping[str, np.ndarray]] = None,
) -> Dict[str, Any]:
    """AHP-only ranking (without TOPSIS).

    If ``alternative_pairwise`` is omitted, builds per-criterion pairwise
    comparisons from the quantitative decision matrix (ratio of scores,
    inverted for cost criteria), then aggregates with criterion weights.
    """

    alternatives = list(decision_matrix.keys())
    criteria = list(next(iter(decision_matrix.values())).keys())
    crit_weights = ahp_priority_weights(criteria_pairwise, labels=criteria)
    w = cast(Dict[str, float], crit_weights["weights"])

    local_priority: Dict[str, Dict[str, float]] = {}
    for cid in criteria:
        if alternative_pairwise and cid in alternative_pairwise:
            local = cast(
                Dict[str, float],
                ahp_priority_weights(
                    alternative_pairwise[cid],
                    labels=alternatives,
                    require_consistent=False,
                )["weights"],
            )
        else:
            values = np.asarray(
                [float(decision_matrix[a][cid]) for a in alternatives],
                dtype=float,
            )
            if not np.all(np.isfinite(values)) or np.any(values <= 0):
                raise NonPositiveAutomaticAHP(
                    f"automatic AHP criterion {cid} requires finite strictly positive values; "
                    "provide positive reciprocal alternative_pairwise judgments for this criterion"
                )
            kind = str(criteria_kind.get(cid, "benefit")).lower()
            # Benefit: larger better; cost: invert so smaller becomes preferred.
            scores = values if kind == "benefit" else 1.0 / values
            # Build consistent ratio pairwise from scores.
            pairwise = np.outer(scores, 1.0 / scores)
            local = cast(
                Dict[str, float],
                ahp_priority_weights(
                    pairwise,
                    labels=alternatives,
                    require_consistent=False,
                )["weights"],
            )
        local_priority[cid] = {a: float(local[a]) for a in alternatives}

    global_scores = {
        alt: float(sum(w[cid] * local_priority[cid][alt] for cid in criteria))
        for alt in alternatives
    }
    ranking = sorted(global_scores.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "scores": global_scores,
        "ranking": [{"algorithm": a, "score": s, "rank": i + 1} for i, (a, s) in enumerate(ranking)],
        "criterion_weights": w,
        "local_priorities": local_priority,
        "consistency": {
            "criteria_cr": crit_weights["consistency_ratio"],
            "criteria_consistent": crit_weights["consistent"],
        },
        "method": "ahp_only",
    }


def default_weights_or_ahp(
    *,
    use_ahp: bool = True,
    pairwise: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Return AHP weights when consistent, else methodology defaults."""

    if not use_ahp:
        return dict(DEFAULT_CRITERION_WEIGHTS)
    try:
        result = ahp_priority_weights(pairwise, require_consistent=True)
        weights = cast(Dict[str, float], result["weights"])
        return {k: float(v) for k, v in weights.items()}
    except ValueError:
        return dict(DEFAULT_CRITERION_WEIGHTS)
