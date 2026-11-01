"""Dependency-free Pareto quality metrics with explicit objective orientation."""

from __future__ import annotations

from itertools import product
from typing import Sequence, Tuple

import numpy as np


def _matrix(points: Sequence[Sequence[float]]) -> np.ndarray:
    try:
        matrix = np.asarray(points, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("points must be a rectangular numeric matrix") from exc
    if matrix.ndim != 2:
        raise ValueError("points must be a two-dimensional matrix")
    if matrix.shape[1] == 0:
        raise ValueError("points must have at least one objective")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("points must contain only finite values")
    return matrix


def _orientation(maximize: Sequence[bool], dimensions: int) -> np.ndarray:
    if len(maximize) != dimensions or not all(
        isinstance(value, (bool, np.bool_)) for value in maximize
    ):
        raise ValueError("maximize must contain one boolean per objective")
    return np.asarray([1.0 if value else -1.0 for value in maximize], dtype=float)


def dominates(
    candidate: Sequence[float],
    other: Sequence[float],
    *,
    maximize: Sequence[bool],
) -> bool:
    pair = _matrix([candidate, other])
    oriented = pair * _orientation(maximize, pair.shape[1])
    return bool(
        np.all(oriented[0] >= oriented[1])
        and np.any(oriented[0] > oriented[1])
    )


def non_dominated_indices(
    points: Sequence[Sequence[float]],
    *,
    maximize: Sequence[bool],
) -> Tuple[int, ...]:
    matrix = _matrix(points)
    if matrix.shape[0] == 0:
        return ()
    oriented = matrix * _orientation(maximize, matrix.shape[1])
    keep = []
    for index, point in enumerate(oriented):
        dominated = any(
            other_index != index
            and np.all(other >= point)
            and np.any(other > point)
            for other_index, other in enumerate(oriented)
        )
        if not dominated:
            keep.append(index)
    return tuple(keep)


def hypervolume_3d(
    points: Sequence[Sequence[float]],
    *,
    reference: Sequence[float],
    maximize: Sequence[bool],
) -> float:
    """Exact dominated hypervolume for three objectives.

    The reference must be weakly worse than every submitted point. Dominated
    points are removed first, then the union of axis-aligned cells is summed.
    """

    matrix = _matrix(points)
    if matrix.shape[1] != 3:
        raise ValueError("hypervolume_3d requires exactly three objectives")
    direction = _orientation(maximize, 3)
    try:
        reference_array = np.asarray(reference, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("reference must be a finite three-value vector") from exc
    if reference_array.shape != (3,) or not np.all(np.isfinite(reference_array)):
        raise ValueError("reference must be a finite three-value vector")

    oriented = matrix * direction
    oriented_reference = reference_array * direction
    if np.any(oriented < oriented_reference):
        raise ValueError("reference must be no better than every point")
    if matrix.shape[0] == 0:
        return 0.0

    front = oriented[
        list(non_dominated_indices(matrix, maximize=maximize))
    ]
    coordinates = [
        np.unique(np.concatenate(([oriented_reference[axis]], front[:, axis])))
        for axis in range(3)
    ]
    volume = 0.0
    ranges = [range(max(len(values) - 1, 0)) for values in coordinates]
    for x_index, y_index, z_index in product(*ranges):
        lower = np.asarray(
            [
                coordinates[0][x_index],
                coordinates[1][y_index],
                coordinates[2][z_index],
            ]
        )
        upper = np.asarray(
            [
                coordinates[0][x_index + 1],
                coordinates[1][y_index + 1],
                coordinates[2][z_index + 1],
            ]
        )
        if np.any(np.all(front >= upper, axis=1)):
            volume += float(np.prod(upper - lower))
    return volume


def expected_utility(
    points: Sequence[Sequence[float]],
    *,
    weights: Sequence[float],
    maximize: Sequence[bool],
) -> float:
    matrix = _matrix(points)
    if matrix.shape[0] == 0:
        raise ValueError("expected utility requires at least one point")
    weight_array = np.asarray(weights, dtype=float)
    if (
        weight_array.shape != (matrix.shape[1],)
        or not np.all(np.isfinite(weight_array))
        or np.any(weight_array < 0.0)
        or not np.isclose(float(np.sum(weight_array)), 1.0)
    ):
        raise ValueError("weights must be a finite non-negative simplex")
    oriented = matrix * _orientation(maximize, matrix.shape[1])
    return float(np.mean(oriented @ weight_array))


def sparsity(points: Sequence[Sequence[float]]) -> float:
    """Deb-style spread metric: mean squared adjacent gaps per objective."""

    matrix = _matrix(points)
    if matrix.shape[0] <= 1:
        return 0.0
    squared_gaps = 0.0
    for axis in range(matrix.shape[1]):
        differences = np.diff(np.sort(matrix[:, axis]))
        squared_gaps += float(np.sum(differences**2))
    return squared_gaps / float(matrix.shape[0] - 1)
