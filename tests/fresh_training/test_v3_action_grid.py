"""SPEC-015 D-M3-7, D-M3-9 and D-M3-10: one action grid of 5 levels per equipment for the 4 MADRL (v3 layer).

HAPPO and MATD3 keep their continuous output and the environment rounds it to the nearest level; MASAC and MAAC
choose one level per equipment (multi-discrete, one branch per equipment). The levels span each action's range.
"""
import numpy as np
import pytest
from gymnasium import spaces

from citylearn.v3 import action_grid as ag


def _grid():
    return ag.ActionGrid([spaces.Box(low=np.array([-1.0, 0.0, -1.0]), high=np.array([1.0, 1.0, 1.0])),
                          spaces.Box(low=np.array([-1.0]), high=np.array([1.0]))])


def test_five_levels_over_the_range_of_each_action():
    grid = _grid()
    assert ag.LEVELS == 5
    np.testing.assert_allclose(grid.levels(0, 0), [-1.0, -0.5, 0.0, 0.5, 1.0])
    np.testing.assert_allclose(grid.levels(0, 1), [0.0, 0.25, 0.5, 0.75, 1.0])     # air conditioning 0..1
    assert grid.branches == [3, 1] and grid.max_branches == 3


def test_continuous_actions_are_rounded_to_the_nearest_level():
    grid = _grid()
    np.testing.assert_allclose(grid.round(0, [0.37, 0.61, -0.9]), [0.5, 0.5, -1.0])
    np.testing.assert_allclose(grid.round(1, [0.2]), [0.0])
    np.testing.assert_allclose(grid.round(0, [2.0, -3.0, 0.74]), [1.0, 0.0, 0.5])  # out of range clipped first


def test_multi_discrete_indices_decode_per_equipment_and_padding_is_masked():
    grid = _grid()
    np.testing.assert_allclose(grid.decode(0, [4, 0, 2]), [1.0, 0.0, 0.0])
    np.testing.assert_allclose(grid.decode(1, [1, 3, 3]), [-0.5])                  # padded branches ignored
    mask = grid.avail_mask(1)
    assert mask.shape == (3*ag.LEVELS,)
    assert mask[:ag.LEVELS].all()                                                  # real branch: every level
    for branch in (1, 2):                                                          # padding: one fixed level
        block = mask[branch*ag.LEVELS:(branch + 1)*ag.LEVELS]
        assert block.sum() == 1 and block[ag.PAD_LEVEL]
    onehot = grid.onehot(0, [4, 0, 2])
    assert onehot.shape == (3*ag.LEVELS,) and onehot.sum() == 3
    assert list(grid.indices_from_onehot(onehot)) == [4, 0, 2]


def test_the_same_values_reach_the_environment_from_both_interfaces():
    """D-M3-7: a discrete choice and a continuous output on the same level give the same action."""
    grid = _grid()
    rng = np.random.default_rng(0)
    for _ in range(50):
        idx = rng.integers(0, ag.LEVELS, size=3)
        values = grid.decode(0, idx)
        np.testing.assert_allclose(grid.round(0, values + rng.uniform(-0.05, 0.05, 3)*np.array([1, 0.5, 1])), values)


def test_invalid_indices_are_refused():
    grid = _grid()
    with pytest.raises(ValueError):
        grid.decode(0, [5, 0, 0])
    with pytest.raises(ValueError):
        grid.decode(0, [0, 0])
