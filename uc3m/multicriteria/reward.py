"""Multiobjective reward helper aligned to the selection methodology.

Uses the scalar form:

    R_i = -(w1 * C_i + w2 * E_CO2,i - w3 * F_i)

with min-max or z-score normalization so EUR, kgCO2 and kWh are comparable.
Complements CityLearn ``CityLearnV3MADRLRewardFunction`` without replacing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Optional, Sequence, Tuple

import numpy as np

NormalizeMode = Literal["minmax", "zscore", "none"]


@dataclass(frozen=True)
class MultiObjectiveWeights:
    w_cost: float = 1.0 / 3.0
    w_co2: float = 1.0 / 3.0
    w_flex: float = 1.0 / 3.0

    def as_array(self) -> np.ndarray:
        raw = np.asarray([self.w_cost, self.w_co2, self.w_flex], dtype=float)
        total = float(raw.sum())
        if total <= 0:
            return np.full(3, 1.0 / 3.0)
        return raw / total


def _minmax(values: np.ndarray) -> np.ndarray:
    lo = float(np.min(values))
    hi = float(np.max(values))
    if not np.isfinite(lo) or not np.isfinite(hi) or abs(hi - lo) < 1e-12:
        return np.zeros_like(values, dtype=float)
    return (values - lo) / (hi - lo)


def _zscore(values: np.ndarray) -> np.ndarray:
    mean = float(np.mean(values))
    std = float(np.std(values))
    if not np.isfinite(std) or std < 1e-12:
        return np.zeros_like(values, dtype=float)
    return (values - mean) / std


def normalize_components(
    cost: Sequence[float],
    co2: Sequence[float],
    flexibility: Sequence[float],
    *,
    mode: NormalizeMode = "minmax",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Normalize cost / CO2 / flexibility series to a common scale."""

    c = np.asarray(cost, dtype=float)
    e = np.asarray(co2, dtype=float)
    f = np.asarray(flexibility, dtype=float)
    if not (c.shape == e.shape == f.shape):
        raise ValueError("cost, co2 and flexibility must share the same shape")
    if mode == "none":
        return c, e, f
    if mode == "zscore":
        return _zscore(c), _zscore(e), _zscore(f)
    if mode == "minmax":
        return _minmax(c), _minmax(e), _minmax(f)
    raise ValueError(f"Unknown normalize mode: {mode}")


def multiobjective_reward(
    cost: Sequence[float],
    co2: Sequence[float],
    flexibility: Sequence[float],
    *,
    weights: Optional[MultiObjectiveWeights] = None,
    mode: NormalizeMode = "minmax",
) -> np.ndarray:
    """Vectorized R_i = -(w1*C_i + w2*E_CO2,i - w3*F_i) after normalization."""

    w = (weights or MultiObjectiveWeights()).as_array()
    c_n, e_n, f_n = normalize_components(cost, co2, flexibility, mode=mode)
    return -(w[0] * c_n + w[1] * e_n - w[2] * f_n)


def equal_step_budget_mask(
    steps_by_algorithm: Mapping[str, int],
    *,
    budget: Optional[int] = None,
) -> Mapping[str, int]:
    """Return the common interaction budget (min steps) for fair comparison."""

    if not steps_by_algorithm:
        return {}
    limit = int(budget) if budget is not None else int(min(steps_by_algorithm.values()))
    return {algo: min(int(n), limit) for algo, n in steps_by_algorithm.items()}
