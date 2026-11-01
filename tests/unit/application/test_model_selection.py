"""Tests for best model selection logic."""
import pytest


def _make_evaluation():
    return {
        'algorithms': {
            'HAPPO': {'mean_hypervolume': 0.45, 'variance_hypervolume': 0.01, 'n_seeds': 3},
            'MASAC': {'mean_hypervolume': 0.50, 'variance_hypervolume': 0.02, 'n_seeds': 3},
            'MATD3': {'mean_hypervolume': 0.55, 'variance_hypervolume': 0.005, 'n_seeds': 3},
            'MAAC': {'mean_hypervolume': 0.40, 'variance_hypervolume': 0.03, 'n_seeds': 3},
        },
        'campaign_complete': True,
    }


def test_selection_rule_deterministic():
    from uc3m.application.evaluation.model_selection import select_best_model
    ev = _make_evaluation()
    result1 = select_best_model(ev)
    result2 = select_best_model(ev)
    assert result1['best_algorithm'] == result2['best_algorithm']
    assert result1['best_algorithm'] == 'MATD3'


def test_selection_tiebreak_by_variance():
    from uc3m.application.evaluation.model_selection import select_best_model
    ev = _make_evaluation()
    ev['algorithms']['MASAC']['mean_hypervolume'] = 0.55
    result = select_best_model(ev)
    assert result['best_algorithm'] == 'MATD3'


def test_selection_rejects_incomplete_campaign():
    from uc3m.application.evaluation.model_selection import select_best_model
    ev = _make_evaluation()
    ev['campaign_complete'] = False
    with pytest.raises(ValueError, match='incomplete'):
        select_best_model(ev)
