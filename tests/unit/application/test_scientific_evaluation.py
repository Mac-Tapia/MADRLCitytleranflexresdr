"""Tests for scientific evaluation of the experimental campaign."""
import numpy as np
import pytest


def _make_kpis(cost=0.9, co2=0.85, peak=0.95):
    return {'cost_total': cost, 'co2_emissions': co2, 'peak_demand': peak}


def test_evaluate_requires_all_kpi_dimensions():
    from uc3m.application.evaluation.scientific_evaluation import validate_kpis
    valid = _make_kpis()
    assert validate_kpis(valid) is True
    incomplete = {'cost_total': 0.9}
    assert validate_kpis(incomplete) is False


def test_multiseed_statistics_require_minimum_3_seeds():
    from uc3m.application.evaluation.scientific_evaluation import compute_multiseed_stats
    values = [0.9, 0.91, 0.92]
    stats = compute_multiseed_stats(values)
    assert 'mean' in stats
    assert 'std' in stats
    assert 'iqm' in stats
    assert stats['n_seeds'] == 3
    with pytest.raises(ValueError, match='minimum 3 seeds'):
        compute_multiseed_stats([0.9, 0.91])


def test_pareto_front_computed_across_algorithms():
    from uc3m.application.evaluation.scientific_evaluation import compute_pareto_summary
    points = [
        {'algorithm': 'A', 'objectives': [0.8, 0.7, 0.9]},
        {'algorithm': 'B', 'objectives': [0.9, 0.8, 0.85]},
        {'algorithm': 'C', 'objectives': [0.7, 0.6, 0.95]},
    ]
    summary = compute_pareto_summary(points, maximize=[False, False, False])
    assert 'front_indices' in summary
    assert 'hypervolume' in summary
    assert isinstance(summary['front_indices'], (list, tuple))
