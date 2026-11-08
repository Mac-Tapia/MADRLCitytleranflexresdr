"""Module 4, task 4.1 (SPEC-005 and SPEC-009): the three statistics defects recorded in STATUS are reproduced.

STATUS listed: the IQM of compute_multiseed_stats returned the median with 3 seeds; decide_oe_winner declared a winner
without looking at the Kruskal-Wallis p-value; select_best_model required no significance and did not check the runs.
Each assertion below is the correct behaviour; it must hold on the current code.
"""
import math

import pytest

from uc3m.application.evaluation.model_selection import select_best_model
from uc3m.application.evaluation.scientific_evaluation import compute_multiseed_stats
from uc3m.multicriteria.stats_tests import decide_oe_winner


def test_iqm_of_three_seeds_uses_fractional_weights_not_the_median():
    stats = compute_multiseed_stats([1.0, 2.0, 10.0])
    expected = (0.25*1.0 + 2.0 + 0.25*10.0)/1.5                    # cuts at 0.75 and 2.25 of 3 sorted values
    assert stats['iqm'] == pytest.approx(expected)
    assert not math.isclose(stats['iqm'], 2.0)                        # the median


def test_no_winner_without_a_significant_omnibus():
    ranks = {'HAPPO': 3.0, 'MASAC': 2.0, 'MATD3': 1.0}
    groups = {'HAPPO': [3.0, 3.1, 2.9], 'MASAC': [2.0, 2.1, 1.9], 'MATD3': [1.0, 1.1, 0.9]}
    pairs = [{'a': 'HAPPO', 'b': 'MASAC', 'p_adj': 0.001, 'significant': True}]
    for omnibus in (0.2, None):
        decision = decide_oe_winner(ranks, pairs, groups, omnibus_p=omnibus)
        assert decision['inferential_winner'] is None and decision['winners'] == []
        assert decision['descriptive_leader'] == 'HAPPO'


def _evaluation(**extra):
    algorithms = {name: {'mean_hypervolume': hv, 'variance_hypervolume': 0.1, 'n_seeds': 3}
                  for name, hv in (('HAPPO', 0.9), ('MASAC', 0.8), ('MATD3', 0.7), ('MAAC', 0.6))}
    return {'campaign_complete': True, 'algorithms': algorithms, **extra}


def test_selection_refuses_incomplete_campaigns_and_unequal_seeds():
    with pytest.raises(ValueError, match='incomplete'):
        select_best_model(_evaluation(campaign_complete=False))
    unequal = _evaluation()
    unequal['algorithms']['MAAC']['n_seeds'] = 2
    with pytest.raises(ValueError, match='seeds'):
        select_best_model(unequal)


def test_selection_without_inference_is_only_descriptive():
    result = select_best_model(_evaluation())
    assert result['selection_kind'] == 'descriptive' and result['inferential_winner'] is None
    assert result['inferential_status'] == 'not_evaluated'
    not_significant = select_best_model(_evaluation(inference={'omnibus_p_holm': 0.3, 'posthoc_significant': True,
                                                               'winner': 'HAPPO'}))
    assert not_significant['inferential_winner'] is None
    detected = select_best_model(_evaluation(inference={'omnibus_p_holm': 0.01, 'posthoc_significant': True,
                                                        'winner': 'HAPPO'}))
    assert detected['inferential_winner'] == 'HAPPO' and detected['inferential_status'] == 'detected'
