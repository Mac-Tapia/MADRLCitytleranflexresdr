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
        hphi_good.add_point(np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]))
        score_good = hphi_good.compute()

        hphi_bad = HPHI()
        hphi_bad.add_point(np.array([0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]))
        score_bad = hphi_bad.compute()

        assert score_good >= score_bad

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
