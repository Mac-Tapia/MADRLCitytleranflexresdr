"""T11: the delivery of a fresh campaign carries its own artifacts with hashes and an honest state."""
import json

import pytest

from tests.fresh_training.test_security_and_acceptance import CAMPAIGN_ID, _campaign, _passed_gate
from tools.eval.report_fresh_campaign import build_fresh_delivery, verify_delivery
from uc3m.application.evaluation.fresh_analysis import FrozenProtocol

ALGORITHMS = ('HAPPO', 'MASAC', 'MATD3', 'MAAC')
ENDPOINTS = (('E1', 'flexibility'), ('E2', 'co2_emissions'), ('E3', 'energy_cost'))


def _seed_rows():
    rows = []
    for a_index, algorithm in enumerate(ALGORITHMS):
        for scenario, axis in FrozenProtocol.default().endpoints:
            for seed in range(1001, 1013):
                rows.append({'campaign_id': CAMPAIGN_ID, 'algorithm': algorithm, 'scenario': scenario, 'seed': seed,
                             'split': 'validation_2024', 'endpoint': axis, 'value': 0.01*a_index + 0.001*(seed - 1000),
                             'kpi_report_sha256': 'c'*64})
    return rows


def test_report_requires_campaign_id(tmp_path):
    manifest = _campaign(tmp_path)
    payload = json.loads(manifest.read_text(encoding='utf-8'))
    payload.pop('campaign_id')
    manifest.write_text(json.dumps(payload), encoding='utf-8')
    with pytest.raises(ValueError):
        build_fresh_delivery(manifest, tmp_path/'delivery', gate_report=_passed_gate(tmp_path))


def test_delivery_contains_no_prior_result_input_reference(tmp_path):
    manifest = _campaign(tmp_path)
    delivery = build_fresh_delivery(manifest, tmp_path/'delivery', gate_report=_passed_gate(tmp_path))
    for row in delivery['files']:
        text = (tmp_path/'delivery'/row['path']).read_text(encoding='utf-8')
        if row['path'] == 'campaign_manifest.json':
            payload = json.loads(text)
            policy = payload.pop('input_policy')
            assert policy['retired_roots']  # declared prohibitions are preserved, not consumed results
            text = json.dumps(payload)
        assert 'outputs/madrl_v3_' not in text and 'outputs/_drive_madrl' not in text
    stage = manifest.parent/'stages/confirm_result.json'
    stage.write_text(stage.read_text(encoding='utf-8').replace('"status"', '"source": "outputs/_drive_madrl/x", '
                                                               '"status"'), encoding='utf-8')
    with pytest.raises(PermissionError):
        build_fresh_delivery(manifest, tmp_path/'delivery2', gate_report=_passed_gate(tmp_path))
    with pytest.raises(FileExistsError):     # a delivery is never overwritten
        build_fresh_delivery(_campaign(tmp_path/'again'), tmp_path/'delivery', gate_report=_passed_gate(tmp_path))


def test_report_values_match_seed_table(tmp_path):
    rows = _seed_rows()
    delivery = build_fresh_delivery(_campaign(tmp_path), tmp_path/'delivery', gate_report=_passed_gate(tmp_path),
                                    seed_rows=rows)
    report = json.loads((tmp_path/'delivery/scientific_report.json').read_text(encoding='utf-8'))
    table = json.loads((tmp_path/'delivery/seed_table.json').read_text(encoding='utf-8'))
    assert table['rows'] == rows and report['coverage']['complete'] is True
    for stat in report['seed_statistics']:
        values = [r['value'] for r in rows if r['algorithm'] == stat['algorithm']
                  and r['scenario'] == stat['scenario'] and r['endpoint'] == stat['endpoint']]
        assert stat['n'] == 12 and stat['mean'] == pytest.approx(sum(values)/12)
    assert report['decisions']['winner_forced'] is False
    assert delivery['state'] != 'new_campaign_scientifically_complete'   # no scientific report of the campaign itself


def test_status_never_equates_prepared_with_trained(tmp_path):
    prepared = build_fresh_delivery(_campaign(tmp_path, train=False), tmp_path/'d1', gate_report=_passed_gate(tmp_path))
    assert prepared['state'] == 'implementation_ready_for_training' and prepared['trained'] is False
    trained = build_fresh_delivery(_campaign(tmp_path/'t'), tmp_path/'d2', gate_report=_passed_gate(tmp_path))
    assert trained['state'] == 'trained_not_scientifically_complete' and trained['trained'] is True
    rejected = build_fresh_delivery(_campaign(tmp_path/'r'), tmp_path/'d3', gate_report=_passed_gate(tmp_path, skipped=1))
    assert rejected['state'] == 'rejected' and rejected['acceptance']['software_acceptance'] is False


def test_evidence_registry_rechecks_hashes(tmp_path):
    build_fresh_delivery(_campaign(tmp_path), tmp_path/'delivery', gate_report=_passed_gate(tmp_path))
    assert verify_delivery(tmp_path/'delivery').accepted
    target = tmp_path/'delivery/campaign_manifest.json'
    target.write_text(target.read_text(encoding='utf-8') + ' ', encoding='utf-8')
    result = verify_delivery(tmp_path/'delivery')
    assert not result.accepted and 'hash_mismatch:campaign_manifest.json' in result.reasons
