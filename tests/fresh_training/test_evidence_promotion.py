"""P09/A10/A14: selection, inference and accepted evidence are separate decisions.

Evidence is accepted only through ``register_verified_evidence`` (content hash and
campaign rechecked); an ``accepted=True`` flag or a manifest status never verifies a
file, and accepted references are read back against their hash. A descriptive
candidate is the best ranked algorithm over verified, finite runs; an inferential
winner exists only when the omnibus test and the post hoc comparison against the
runner-up are both significant. A complete study may end without a winner.
"""
import hashlib
import json
import math

import pytest

from uc3m.application.evaluation.model_selection import select_best_model
from uc3m.application.thesis.evidence_registry import EvidenceRegistry
from uc3m.multicriteria.stats_tests import decide_oe_winner, run_oe_battery

CAMPAIGN = 'fresh_iquitos_20261101_v1'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- evidence ---------------------------------------------------------------------------------------

def test_accepted_flag_never_verifies_a_file(tmp_path):
    registry = EvidenceRegistry()
    with pytest.raises(ValueError, match='register_verified_evidence'):
        registry.register('J-01', str(tmp_path/'missing.json'), 'claimed', accepted=True)
    editorial = registry.register('J-02', 'docs/x.md', 'editorial reference')
    assert editorial.accepted is False


def test_nonexistent_changed_or_foreign_evidence_not_accepted(tmp_path):
    registry = EvidenceRegistry()
    with pytest.raises(PermissionError):
        registry.register_verified_evidence(tmp_path/'missing.json', '0'*64, CAMPAIGN, 'validation')
    report = tmp_path/'report.json'
    report.write_text(json.dumps({'campaign_id': CAMPAIGN, 'value': 1}), encoding='utf-8')
    ref = registry.register_verified_evidence(report, _sha(report), CAMPAIGN, 'validation')
    assert ref.accepted and ref.sha256 == _sha(report) and ref.campaign_id == CAMPAIGN
    assert [r.artifact_path for r in registry.get_references(accepted_only=True)] == [str(report)]
    report.write_text(json.dumps({'campaign_id': CAMPAIGN, 'value': 2}), encoding='utf-8')
    assert registry.get_references(accepted_only=True) == []
    report.unlink()
    assert registry.get_references(accepted_only=True) == []
    foreign = tmp_path/'foreign.json'
    foreign.write_text(json.dumps({'campaign_id': 'fresh_other_v1'}), encoding='utf-8')
    with pytest.raises(PermissionError):
        registry.register_verified_evidence(foreign, _sha(foreign), CAMPAIGN, 'validation')


def test_manifest_status_is_not_acceptance(tmp_path):
    manifest = tmp_path/'jury.json'
    manifest.write_text(json.dumps({'observations': [
        {'id': 'J-01', 'description': 'stat truth', 'status': 'resolved', 'evidence_path': 'docs/old.json'},
        {'id': 'J-02', 'description': 'pending', 'status': 'open'}]}), encoding='utf-8')
    registry = EvidenceRegistry()
    registry.load_from_manifest(manifest)
    assert registry.get_references(accepted_only=True) == []
    assert registry.summary() == {'total': 2, 'accepted': 0, 'pending': 2}


# --- inference -------------------------------------------------------------------------------------

RANKS = {'MATD3': 9.0, 'MASAC': 7.0, 'HAPPO': 4.0, 'MAAC': 2.0}
GROUPS = {'MATD3': [0.9, 0.8, 0.85], 'MASAC': [0.6, 0.65, 0.7], 'HAPPO': [0.4, 0.3, 0.35], 'MAAC': [0.1, 0.2, 0.15]}


def _dunn(significant):
    return [{'algorithm_a': 'MATD3', 'algorithm_b': 'MASAC', 'significant': significant, 'p_holm': 0.01}]


def test_no_significance_no_inferential_winner():
    result = decide_oe_winner(RANKS, _dunn(True), GROUPS, omnibus_p=0.30)
    assert result['inferential_winner'] is None
    assert result['winners'] == []
    assert result['descriptive_leader'] == 'MATD3'
    assert result['status'] == 'no_inferential_winner'


def test_omnibus_is_required_before_any_winner():
    result = decide_oe_winner(RANKS, _dunn(True), GROUPS)
    assert result['inferential_winner'] is None and result['status'] == 'omnibus_not_provided'


def test_significant_omnibus_and_posthoc_name_an_inferential_winner():
    result = decide_oe_winner(RANKS, _dunn(True), GROUPS, omnibus_p=0.01)
    assert result['inferential_winner'] == 'MATD3' and result['winners'] == ['MATD3']


def test_runner_up_not_separated_has_no_inferential_winner():
    result = decide_oe_winner(RANKS, _dunn(False), GROUPS, omnibus_p=0.01)
    assert result['inferential_winner'] is None
    assert result['winners'] == ['MATD3', 'MASAC']
    assert result['descriptive_leader'] == 'MATD3'


@pytest.mark.parametrize('p', [math.nan, -0.1, 1.5, True])
def test_invalid_omnibus_p_is_refused(p):
    with pytest.raises(ValueError):
        decide_oe_winner(RANKS, _dunn(True), GROUPS, omnibus_p=p)


def test_battery_without_difference_has_no_winner():
    groups = {name: [0.5, 0.5, 0.5] for name in ('HAPPO', 'MASAC', 'MATD3', 'MAAC')}
    result = run_oe_battery(groups, objective='OE.1', higher_is_better=True, complementary=False,
                            expected_n_seeds=3)
    assert result['winner']['inferential_winner'] is None
    assert result['winner']['winners'] == []


# --- descriptive selection ---------------------------------------------------------------------------

def _evaluation(**inference):
    evaluation = {'campaign_complete': True, 'algorithms': {
        'HAPPO': {'mean_hypervolume': 0.45, 'variance_hypervolume': 0.010, 'n_seeds': 12},
        'MATD3': {'mean_hypervolume': 0.55, 'variance_hypervolume': 0.005, 'n_seeds': 12}}}
    if inference:
        evaluation['inference'] = inference
    return evaluation


def test_descriptive_candidate_is_not_an_inferential_winner():
    result = select_best_model(_evaluation())
    assert result['descriptive_candidate'] == 'MATD3' == result['best_algorithm']
    assert result['selection_kind'] == 'descriptive'
    assert result['inferential_winner'] is None
    assert result['inferential_status'] == 'not_evaluated'


def test_inferential_winner_needs_significant_omnibus_and_posthoc():
    assert select_best_model(_evaluation(omnibus_p_holm=0.20, winner='MATD3', posthoc_significant=True))[
        'inferential_winner'] is None
    assert select_best_model(_evaluation(omnibus_p_holm=0.01, winner='MATD3', posthoc_significant=False))[
        'inferential_winner'] is None
    decided = select_best_model(_evaluation(omnibus_p_holm=0.01, winner='MATD3', posthoc_significant=True))
    assert decided['inferential_winner'] == 'MATD3' and decided['inferential_status'] == 'detected'


@pytest.mark.parametrize('field, value', [('mean_hypervolume', math.nan), ('variance_hypervolume', math.inf),
                                          ('mean_hypervolume', True), ('n_seeds', 0), ('n_seeds', True),
                                          ('n_seeds', 11)])
def test_descriptive_candidate_requires_verified_runs(field, value):
    evaluation = _evaluation()
    evaluation['algorithms']['MATD3'][field] = value
    with pytest.raises(ValueError):
        select_best_model(evaluation)


def test_full_tie_is_broken_by_algorithm_id():
    evaluation = _evaluation()
    evaluation['algorithms']['HAPPO'].update(mean_hypervolume=0.55, variance_hypervolume=0.005)
    assert select_best_model(evaluation)['descriptive_candidate'] == 'HAPPO'
