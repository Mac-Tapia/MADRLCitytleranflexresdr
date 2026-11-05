"""P10/A11: the results catalog reads the fresh campaign it is given, never the newest folder.

``discover_attempts(manifest_path)`` lists the attempts of that campaign's stage
results; acceptance is the single public rule
``fresh_acceptance.treatment_trust_reasons``. ``build_seed_table`` opens, for the
accepted attempts of one stage, ``<attempt_root>/evaluation/<split>/kpi_report.json``
whose sha256 is recorded in ``evaluation_manifest.json`` next to it, and binds every
row to the report hash, campaign, treatment, algorithm, scenario, seed and split.
"""
import hashlib
import json
from pathlib import Path

import pytest

from tests.fresh_training.test_attempt_acceptance import _stage_learner
from uc3m.application.evaluation import fresh_analysis as fa
from uc3m.application.evaluation import results_catalog as rc
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
SPLIT = 'validation_2024'


def _campaign(tmp_path, name='campaign', mutate=None):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/name)
    manifest_path = tmp_path/name/'campaign_manifest.json'
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    fc.run_stage(manifest_path, 'pilot', _stage_learner(algorithm_config, 17, mutate), REPO, authorized=True)
    return manifest_path


def _write_report(attempt, *, gains=None, **context_overrides):
    folder = attempt.attempt_root/'evaluation'/SPLIT
    folder.mkdir(parents=True, exist_ok=True)
    context = {'campaign_id': attempt.campaign_id, 'treatment_id': attempt.treatment_id,
               'algorithm': attempt.algorithm, 'scenario': attempt.scenario, 'seed': attempt.seed,
               'split': SPLIT, **context_overrides}
    report = {'context': context,
              'axis_gains': gains or {'flexibility': 0.1, 'co2_emissions': 0.2, 'energy_cost': 0.3}}
    path = folder/'kpi_report.json'
    path.write_text(json.dumps(report), encoding='utf-8')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder/'evaluation_manifest.json').write_text(json.dumps({'files': {'kpi_report.json': digest}}),
                                                   encoding='utf-8')
    return path, digest


def test_fresh_attempt_is_visible_in_catalog(tmp_path):
    manifest_path = _campaign(tmp_path)
    attempts = rc.discover_attempts(manifest_path)
    assert len(attempts) == 4
    assert {a.algorithm for a in attempts} == {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
    for attempt in attempts:
        assert attempt.accepted and attempt.reasons == () and attempt.stage == 'pilot'
        assert attempt.seed == 901 and attempt.scenario == 'E1'
        assert attempt.attempt_root.is_dir() and attempt.campaign_id == 'fresh_iquitos_20261105_v5'


def test_report_requires_explicit_campaign(tmp_path):
    with pytest.raises(FileNotFoundError):
        rc.discover_attempts(tmp_path/'missing/campaign_manifest.json')
    with pytest.raises(TypeError):
        rc.discover_attempts(None)


def test_untrusted_attempt_is_visible_only_with_its_reasons(tmp_path):
    manifest_path = _campaign(tmp_path)
    attempt = rc.discover_attempts(manifest_path)[0]
    checkpoint = attempt.attempt_root/'native/checkpoints/model.pt'
    checkpoint.write_bytes(b'tampered')
    accepted = rc.discover_attempts(manifest_path)
    assert attempt.treatment_id not in {a.treatment_id for a in accepted}
    everything = rc.discover_attempts(manifest_path, accepted_only=False)
    refused = next(a for a in everything if a.treatment_id == attempt.treatment_id)
    assert refused.accepted is False and any('untrusted_checkpoint' in r for r in refused.reasons)


def test_each_campaign_lists_only_its_own_attempts(tmp_path):
    first = _campaign(tmp_path, 'first')
    second = _campaign(tmp_path, 'second')
    roots_first = {a.attempt_root for a in rc.discover_attempts(first)}
    roots_second = {a.attempt_root for a in rc.discover_attempts(second)}
    assert roots_first and roots_second and not roots_first & roots_second


def test_seed_row_binds_kpi_hash_campaign_policy_and_split(tmp_path):
    manifest_path = _campaign(tmp_path)
    attempts = rc.discover_attempts(manifest_path)
    digests = {a.treatment_id: _write_report(a)[1] for a in attempts}
    table = rc.build_seed_table(manifest_path, stage='pilot', split=SPLIT)
    # Rows per report come from the single row rule (axis + comparable KPIs of its scenario).
    per_report = len(fa.rows_from_kpi_report(
        json.loads((attempts[0].attempt_root/'evaluation'/SPLIT/'kpi_report.json').read_text(encoding='utf-8')),
        report_sha256='0'*64))
    assert per_report >= 1 and len(table.rows) == 4*per_report
    for row in table.rows:
        assert row['split'] == SPLIT and row['seed'] == 901
        assert row['kpi_report_sha256'] in digests.values()
    assert table.values('HAPPO', 'E1', 'flexibility', SPLIT) == {901: 0.1}


def test_tampered_report_is_refused(tmp_path):
    manifest_path = _campaign(tmp_path)
    attempt = rc.discover_attempts(manifest_path)[0]
    path, _ = _write_report(attempt)
    path.write_text(path.read_text(encoding='utf-8').replace('0.1', '0.9'), encoding='utf-8')
    with pytest.raises(ValueError, match='sha256'):
        rc.build_seed_table(manifest_path, stage='pilot', split=SPLIT)


@pytest.mark.parametrize('overrides', [{'seed': 902}, {'campaign_id': 'fresh_other_v1'},
                                       {'split': 'test_2025'}, {'algorithm': 'PPO'}, {'treatment_id': 'x'}])
def test_report_context_must_match_the_attempt(tmp_path, overrides):
    manifest_path = _campaign(tmp_path)
    attempt = rc.discover_attempts(manifest_path)[0]
    _write_report(attempt, **overrides)
    with pytest.raises(ValueError, match='context'):
        rc.build_seed_table(manifest_path, stage='pilot', split=SPLIT)


def test_missing_report_is_a_missing_measurement_not_a_row(tmp_path):
    manifest_path = _campaign(tmp_path)
    attempts = rc.discover_attempts(manifest_path)
    for attempt in attempts[1:]:
        _write_report(attempt)
    table = rc.build_seed_table(manifest_path, stage='pilot', split=SPLIT)
    assert {r['algorithm'] for r in table.rows} == {a.algorithm for a in attempts[1:]}
    assert attempts[0].algorithm not in {r['algorithm'] for r in table.rows}


def test_other_stages_are_never_mixed_into_the_table(tmp_path):
    manifest_path = _campaign(tmp_path)
    for attempt in rc.discover_attempts(manifest_path):
        _write_report(attempt)
    table = rc.build_seed_table(manifest_path, stage='confirm', split=SPLIT)
    assert table.rows == ()
