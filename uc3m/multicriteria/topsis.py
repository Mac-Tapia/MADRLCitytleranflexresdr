"""TOPSIS ranking for multicriteria MADRL algorithm selection."""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

import numpy as np
import pandas as pd

from uc3m.multicriteria.criteria import CRITERION_SPECS, DEFAULT_CRITERION_WEIGHTS


def decision_matrix_to_frame(
    decision_matrix: Mapping[str, Mapping[str, float]],
    *,
    criteria: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Convert ``{algorithm: {C1: x, ...}}`` to a DataFrame (rows=algorithms)."""

    frame = pd.DataFrame.from_dict(decision_matrix, orient="index")
    if criteria is not None:
        frame = frame.loc[:, list(criteria)]
    return frame.astype(float)


def vector_normalize(matrix: np.ndarray) -> np.ndarray:
    """r_ij = x_ij / sqrt(sum_i x_ij^2)."""

    x = np.asarray(matrix, dtype=float)
    denom = np.sqrt(np.sum(np.square(x), axis=0))
    denom = np.where(denom < 1e-12, 1.0, denom)
    return x / denom


def topsis_rank(
    decision_matrix: Mapping[str, Mapping[str, float]],
    *,
    weights: Optional[Mapping[str, float]] = None,
    criteria_kind: Optional[Mapping[str, str]] = None,
) -> Dict[str, object]:
    """Full TOPSIS pipeline → relative closeness C_i* and ranking."""

    frame = decision_matrix_to_frame(decision_matrix)
    algorithms = list(frame.index.astype(str))
    criteria = list(frame.columns.astype(str))
    x = frame.to_numpy(dtype=float)

    kind: MutableMapping[str, str] = {}
    for cid in criteria:
        if criteria_kind and cid in criteria_kind:
            kind[cid] = str(criteria_kind[cid]).lower()
        elif cid in CRITERION_SPECS:
            kind[cid] = CRITERION_SPECS[cid].kind
        else:
            kind[cid] = "benefit"

    w_map = dict(weights or DEFAULT_CRITERION_WEIGHTS)
    w = np.asarray([float(w_map.get(cid, 0.0)) for cid in criteria], dtype=float)
    if float(w.sum()) <= 0:
        w = np.full(len(criteria), 1.0 / max(len(criteria), 1))
    else:
        w = w / w.sum()

    r = vector_normalize(x)
    v = r * w[None, :]

    ideal_best = np.zeros(len(criteria), dtype=float)
    ideal_worst = np.zeros(len(criteria), dtype=float)
    for j, cid in enumerate(criteria):
        col = v[:, j]
        if kind[cid] == "cost":
            ideal_best[j] = float(np.min(col))
            ideal_worst[j] = float(np.max(col))
        else:
            ideal_best[j] = float(np.max(col))
            ideal_worst[j] = float(np.min(col))

    d_pos = np.sqrt(np.sum(np.square(v - ideal_best[None, :]), axis=1))
    d_neg = np.sqrt(np.sum(np.square(v - ideal_worst[None, :]), axis=1))
    closeness = d_neg / np.clip(d_pos + d_neg, 1e-12, None)

    rows: List[Dict[str, object]] = []
    order = np.argsort(-closeness)
    for rank, idx in enumerate(order, start=1):
        rows.append(
            {
                "rank": int(rank),
                "algorithm": algorithms[int(idx)],
                "closeness": float(closeness[int(idx)]),
                "distance_positive": float(d_pos[int(idx)]),
                "distance_negative": float(d_neg[int(idx)]),
            }
        )

    return {
        "ranking": rows,
        "weights": {cid: float(wj) for cid, wj in zip(criteria, w)},
        "criteria_kind": dict(kind),
        "normalized": pd.DataFrame(r, index=algorithms, columns=criteria),
        "weighted": pd.DataFrame(v, index=algorithms, columns=criteria),
        "ideal_positive": {cid: float(val) for cid, val in zip(criteria, ideal_best)},
        "ideal_negative": {cid: float(val) for cid, val in zip(criteria, ideal_worst)},
        "closeness": {algo: float(c) for algo, c in zip(algorithms, closeness)},
        "method": "topsis",
    }


def weight_sweep_sensitivity(
    decision_matrix: Mapping[str, Mapping[str, float]],
    *,
    base_weights: Optional[Mapping[str, float]] = None,
    relative_delta: float = 0.20,
    n_samples: int = 64,
    seed: int = 0,
    criteria_kind: Optional[Mapping[str, str]] = None,
) -> Dict[str, object]:
    """Resample weights ±``relative_delta`` and track winner stability."""

    rng = np.random.default_rng(seed)
    base = dict(base_weights or DEFAULT_CRITERION_WEIGHTS)
    criteria = list(base.keys())
    winners: List[str] = []
    score_rows: List[Dict[str, object]] = []

    for i in range(int(n_samples)):
        noisy = {}
        for cid in criteria:
            scale = 1.0 + float(rng.uniform(-relative_delta, relative_delta))
            noisy[cid] = max(1e-9, float(base[cid]) * scale)
        total = sum(noisy.values())
        noisy = {k: v / total for k, v in noisy.items()}
        result = topsis_rank(
            decision_matrix,
            weights=noisy,
            criteria_kind=criteria_kind,
        )
        winner = str(result["ranking"][0]["algorithm"])
        winners.append(winner)
        score_rows.append(
            {
                "sample": i,
                "winner": winner,
                "weights": noisy,
                "closeness": dict(result["closeness"]),
            }
        )

    counts: Dict[str, int] = {}
    for w in winners:
        counts[w] = counts.get(w, 0) + 1
    majority_winner = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None
    return {
        "relative_delta": float(relative_delta),
        "n_samples": int(n_samples),
        "winner_counts": counts,
        "majority_winner": majority_winner,
        "stability_ratio": float(counts.get(majority_winner, 0) / max(len(winners), 1)),
        "samples": score_rows,
    }


def pareto_nondominated(
    points: Mapping[str, Mapping[str, float]],
    *,
    maximize: Optional[Iterable[str]] = None,
    minimize: Optional[Iterable[str]] = None,
) -> List[str]:
    """Return algorithms on the Pareto front for the given objectives."""

    maximize_set = set(maximize or ())
    minimize_set = set(minimize or ())
    if not maximize_set and not minimize_set:
        raise ValueError("Specify at least one maximize/minimize objective")

    names = list(points.keys())
    objectives = list(maximize_set | minimize_set)

    def better(a: str, b: str) -> bool:
        """True if ``a`` dominates ``b`` (all <= / >= and strict in one)."""

        a_vals = points[a]
        b_vals = points[b]
        not_worse = True
        strict = False
        for obj in objectives:
            av = float(a_vals[obj])
            bv = float(b_vals[obj])
            if obj in maximize_set:
                if av < bv:
                    not_worse = False
                    break
                if av > bv:
                    strict = True
            else:
                if av > bv:
                    not_worse = False
                    break
                if av < bv:
                    strict = True
        return not_worse and strict

    front = []
    for cand in names:
        dominated = any(better(other, cand) for other in names if other != cand)
        if not dominated:
            front.append(cand)
    return front
