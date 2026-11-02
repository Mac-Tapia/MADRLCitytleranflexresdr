from __future__ import annotations

import numpy as np
import pytest

from uc3m.domain.pareto import (
    dominates,
    expected_utility,
    hypervolume_3d,
    non_dominated_indices,
    sparsity,
)


def test_dominance_requires_no_worse_and_at_least_one_strict_improvement() -> None:
    assert dominates([2.0, 1.0], [1.0, 1.0], maximize=[True, True])
    assert not dominates([1.0, 1.0], [1.0, 1.0], maximize=[True, True])
    assert dominates([1.0, 2.0], [2.0, 1.0], maximize=[False, True])


def test_non_dominated_indices_preserve_duplicates_and_remove_dominated() -> None:
    points = [[1.0, 1.0], [2.0, 2.0], [2.0, 2.0], [2.0, 1.0]]

    assert non_dominated_indices(points, maximize=[True, True]) == (1, 2)


def test_hypervolume_3d_is_exact_for_small_union_and_ignores_dominated() -> None:
    points = [[1.0, 1.0, 1.0], [2.0, 0.5, 1.0], [0.5, 0.5, 0.5]]

    assert hypervolume_3d(
        points, reference=[0.0, 0.0, 0.0], maximize=[True, True, True]
    ) == pytest.approx(1.5)


def test_hypervolume_supports_explicit_cost_orientation() -> None:
    points = [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]

    value = hypervolume_3d(
        points,
        reference=[3.0, 0.0, 0.0],
        maximize=[False, True, True],
    )

    assert value == pytest.approx(5.0)


def test_hypervolume_rejects_reference_that_is_not_worse_than_every_point() -> None:
    with pytest.raises(ValueError, match="reference"):
        hypervolume_3d(
            [[1.0, 1.0, 1.0]],
            reference=[1.5, 0.0, 0.0],
            maximize=[True, True, True],
        )


def test_expected_utility_and_sparsity_are_deterministic() -> None:
    assert expected_utility(
        [[1.0, 2.0], [3.0, 4.0]],
        weights=[0.25, 0.75],
        maximize=[True, True],
    ) == pytest.approx(2.75)
    assert sparsity([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]) == pytest.approx(2.0)
    assert sparsity([[1.0, 1.0]]) == 0.0


@pytest.mark.parametrize(
    "points",
    [
        [[np.nan, 1.0]],
        [[np.inf, 1.0]],
        [[1.0], [1.0, 2.0]],
    ],
)
def test_pareto_metrics_reject_invalid_points(points: list[list[float]]) -> None:
    with pytest.raises(ValueError):
        non_dominated_indices(points, maximize=[True, True])


def test_hypervolume_nd_matches_3d_and_analytic_boxes():
    from uc3m.domain.pareto import hypervolume, hypervolume_3d

    points = [[3.0, 1.0, 2.0], [1.0, 3.0, 1.0], [2.0, 2.0, 3.0]]
    reference = [0.0, 0.0, 0.0]
    maximize = [True, True, True]
    assert hypervolume(points, reference=reference, maximize=maximize) == pytest.approx(
        hypervolume_3d(points, reference=reference, maximize=maximize), abs=1e-12)
    # A single 7-D box and two overlapping 2-D boxes, exactly.
    assert hypervolume([[2.0]*7], reference=[0.0]*7, maximize=[True]*7) == pytest.approx(128.0)
    assert hypervolume([[1.0, 8.0], [8.0, 1.0]], reference=[0.0, 0.0],
                       maximize=[True, True]) == pytest.approx(8 + 8 - 1)
    # Minimized axes use the same exact volume.
    assert hypervolume([[1.0, 1.0]], reference=[10.0, 10.0], maximize=[False, False]) == pytest.approx(81.0)


def test_hypervolume_nd_is_order_independent_and_rejects_bad_reference():
    from uc3m.domain.pareto import hypervolume

    points = [[1.0, 4.0, 2.0, 3.0], [4.0, 1.0, 3.0, 2.0], [2.0, 2.0, 4.0, 4.0]]
    forward = hypervolume(points, reference=[0.0]*4, maximize=[True]*4)
    backward = hypervolume(points[::-1], reference=[0.0]*4, maximize=[True]*4)
    assert forward == pytest.approx(backward, abs=1e-12)
    with pytest.raises(ValueError):
        hypervolume(points, reference=[2.0]*4, maximize=[True]*4)
