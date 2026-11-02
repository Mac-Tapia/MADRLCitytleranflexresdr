"""
Tests para uc3m.reward.hphi — HPHI Holistic Pareto Hypervolume Index.
"""
from __future__ import annotations

import numpy as np
import pytest

from uc3m.reward.hphi import HPHI, compute_global_score


class TestHPHI:
    def test_init_default(self):
        hphi = HPHI()
        assert hphi is not None

    def test_hphi_empty_frontera(self):
        """Frontera vacía → HPHI = 0."""
        hphi = HPHI()
        score = hphi.compute()  # sin add_point() previo → frontera vacía
        assert score == pytest.approx(0.0, abs=1e-9)

    def test_hphi_single_point_ideal(self):
        """Un punto añadido → HPHI ∈ [0, 1]."""
        hphi = HPHI()
        hphi.add_point(np.zeros(7))
        score = hphi.compute()
        assert 0.0 <= score <= 1.0

    def test_hphi_range_zero_to_one(self):
        """HPHI ∈ [0, 1] por construcción."""
        hphi = HPHI()
        rng = np.random.default_rng(42)
        points = rng.uniform(0, 1, size=(10, 7))
        for pt in points:
            hphi.add_point(pt)
        score = hphi.compute()
        assert 0.0 <= score <= 1.0 + 1e-6

    def test_hphi_better_solution_higher_score(self):
        """Una frontera mejor → HPHI mayor o igual."""
        # Frontera buena: valores altos (más cercanos al ideal en maximización)
        hphi_good = HPHI()
        hphi_good.add_point(np.full(7, -0.1))
        score_good = hphi_good.compute()

        hphi_bad = HPHI()
        hphi_bad.add_point(np.full(7, -0.9))
        score_bad = hphi_bad.compute()

        assert score_good > score_bad

    def test_hphi_update_accumulates_points(self):
        """update() acumula puntos y compute() trabaja sobre ellos."""
        hphi = HPHI()
        if not hasattr(hphi, 'update'):
            pytest.skip("update() no implementado")
        hphi.update(np.array([0.2, 0.3, 0.1, 0.0, 0.0, 0.1, 0.0]))
        hphi.update(np.array([0.1, 0.2, 0.2, 0.0, 0.0, 0.2, 0.0]))
        score = hphi.compute_accumulated()
        assert 0.0 <= score <= 1.0 + 1e-6

    def test_hphi_reset(self):
        """reset() vacía la frontera acumulada."""
        hphi = HPHI()
        if not hasattr(hphi, 'reset'):
            pytest.skip("reset() no implementado")
        if hasattr(hphi, 'update'):
            hphi.update(np.zeros(7))
        hphi.reset()
        if hasattr(hphi, 'compute_accumulated'):
            score = hphi.compute_accumulated()
            assert score == pytest.approx(0.0)


class TestComputeGlobalScore:
    def test_returns_float(self):
        """compute_global_score() retorna un float."""
        scores = np.array([0.5, 0.7, 0.3, 0.8, 0.6])
        result = compute_global_score(scores)
        assert isinstance(float(result), float)

    def test_all_ones_returns_one(self):
        """Si todos los HPHI = 1 → score global = 1."""
        scores = np.ones(5)
        result = compute_global_score(scores)
        assert float(result) == pytest.approx(1.0, abs=1e-6)

    def test_all_zeros_returns_zero(self):
        """Si todos los HPHI = 0 → score global = 0."""
        scores = np.zeros(5)
        result = compute_global_score(scores)
        assert float(result) == pytest.approx(0.0, abs=1e-6)

    def test_nonnegative(self):
        scores = np.array([0.3, 0.5, 0.2])
        assert float(compute_global_score(scores)) >= 0.0


class TestHPHIAnalytic:
    """P08/A12: the axes are maximized (ideal 0, nadir -10); the reference never moves."""

    def test_2d_point_inside_reference_is_081(self):
        hphi = HPHI(n_obj=2, nadir=np.array([-10.0, -10.0]), ideal=np.array([0.0, 0.0]))
        hphi.add_point([-1.0, -1.0])
        assert hphi.compute() == pytest.approx(0.81, abs=1e-12)

    def test_7d_ideal_point_is_one(self):
        hphi = HPHI()
        hphi.add_point(np.zeros(7))
        assert hphi.compute() == pytest.approx(1.0, abs=1e-9)

    def test_nadir_point_is_zero(self):
        hphi = HPHI(n_obj=2, nadir=np.array([-10.0, -10.0]), ideal=np.zeros(2))
        hphi.add_point([-10.0, -10.0])
        assert hphi.compute() == pytest.approx(0.0, abs=1e-12)

    def test_better_point_scores_higher(self):
        good, bad = HPHI(n_obj=2), HPHI(n_obj=2)
        good.add_point([-1.0, -2.0])
        bad.add_point([-5.0, -6.0])
        assert good.compute() > bad.compute()

    def test_monotone_when_adding_a_point(self):
        hphi = HPHI(n_obj=2)
        hphi.add_point([-1.0, -8.0])
        before = hphi.compute()
        hphi.add_point([-8.0, -1.0])
        assert hphi.compute() > before
        # normalized boxes 0.9x0.2 and 0.2x0.9 overlap in 0.2x0.2
        assert hphi.compute() == pytest.approx(0.32, abs=1e-12)

    def test_point_order_does_not_matter(self):
        a, b = HPHI(n_obj=2), HPHI(n_obj=2)
        points = [[-1.0, -8.0], [-8.0, -1.0], [-4.0, -4.0]]
        for p in points:
            a.add_point(p)
        for p in reversed(points):
            b.add_point(p)
        assert a.compute() == pytest.approx(b.compute(), abs=1e-12)

    def test_reference_is_fixed_by_points_and_reset(self):
        hphi = HPHI(n_obj=2, nadir=np.array([-10.0, -10.0]), ideal=np.zeros(2))
        hphi.add_point([-12.0, -1.0])     # worse than nadir on one axis: no volume
        assert hphi.compute() == pytest.approx(0.0, abs=1e-12)
        hphi.reset()
        hphi.add_point([-1.0, -1.0])
        assert hphi.compute() == pytest.approx(0.81, abs=1e-12)
        assert np.array_equal(hphi.nadir, [-10.0, -10.0]) and np.array_equal(hphi.ideal, [0.0, 0.0])

    def test_point_beyond_ideal_is_flagged_not_hidden(self):
        hphi = HPHI(n_obj=2)
        hphi.add_point([0.5, -1.0])
        assert hphi.compute() == pytest.approx(0.9, abs=1e-12)
        assert hphi.summary()["Saturated_points"] == 1.0

    def test_invalid_reference_is_rejected(self):
        with pytest.raises(ValueError):
            HPHI(n_obj=2, nadir=np.zeros(2), ideal=np.zeros(2))

    def test_non_finite_point_is_rejected(self):
        hphi = HPHI(n_obj=2)
        with pytest.raises(ValueError):
            hphi.add_point([np.nan, -1.0])
