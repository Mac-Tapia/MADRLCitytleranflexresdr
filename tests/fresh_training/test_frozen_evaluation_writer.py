"""T7/T9 link: the frozen evaluation of an attempt writes the KPI report the seed table reads.

Layout agreed with uc3m.application.evaluation.results_catalog.build_seed_table:
<attempt_root>/evaluation/<split>/kpi_report.json and evaluation_manifest.json =
{"files": {"kpi_report.json": sha256 of the raw bytes}}, with report context equal
to {campaign_id, treatment_id, algorithm, scenario, seed, split} of the attempt.
Uses a fresh verified HAPPO micro-training attempt of this campaign (copied, not mocked).
"""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from uc3m.adapters.citylearn.frozen_adapters import citylearn_frozen_adapters
from uc3m.application.evaluation.frozen_evaluation import evaluate_frozen

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO/'data/campaigns/iquitos_v5'
ADAPTERS = citylearn_frozen_adapters()   # this test is a composition root


@pytest.fixture(scope='module')
def attempt(native_attempts):
    return native_attempts['HAPPO']


def test_writes_the_report_the_seed_table_reads(attempt):
    result = evaluate_frozen(attempt, 'validation_2024', CAMPAIGN, steps=24, adapters=ADAPTERS)
    folder = attempt/'evaluation/validation_2024'
    raw = (folder/'kpi_report.json').read_bytes()
    manifest = json.loads((folder/'evaluation_manifest.json').read_text(encoding='utf-8'))
    assert manifest['schema_version'] == 2 and manifest['split'] == 'validation_2024'
    assert manifest['expected_full_split_rows'] == 8784
    assert manifest['files'] == {'kpi_report.json': hashlib.sha256(raw).hexdigest(),
        'frozen_runs.json': hashlib.sha256((folder/'frozen_runs.json').read_bytes()).hexdigest()}
    report = json.loads(raw)
    identity = json.loads((attempt/'attempt.json').read_text(encoding='utf-8'))
    assert report['context'] == {'campaign_id': 'fresh_iquitos_20261105_v5',
                                 'treatment_id': identity['treatment_id'],
                                 'algorithm': 'HAPPO', 'scenario': 'E1', 'seed': 901, 'split': 'validation_2024'}
    assert set(report['axis_gains']) == {'flexibility', 'co2_emissions', 'energy_cost'}
    # Layer B: the 26 comparable CityLearn v3 KPI gains come from evaluate_objectives of the control run.
    gains = report['comparable_kpi_gains']
    assert len(gains) == 26 and sum(1 for g in gains if g['available']) >= 20, \
        [g['name'] for g in gains if not g['available']]
    assert {g['axis'] for g in gains} == {'flexibility', 'co2_emissions', 'energy_cost'}
    assert report['thesis_indicators']                         # Layer A is reported as well
    assert all(c['passed'] for c in report['balance_checks'].values())
    # Same exogenous services for policy and baseline, and the policy never trained during evaluation.
    runs = json.loads((folder/'frozen_runs.json').read_text(encoding='utf-8'))
    assert runs['control']['ev_connection_hash'] == runs['baseline']['ev_connection_hash']
    assert runs['control']['initial_storage_kwh'] == runs['baseline']['initial_storage_kwh']
    assert runs['control']['training_updates'] == 0 and runs['baseline']['policy'] == 'rbc'
    assert result['kpi_report_sha256'] == manifest['files']['kpi_report.json']


def test_an_evaluation_is_never_overwritten(attempt):
    assert (attempt/'evaluation/validation_2024/kpi_report.json').is_file()
    with pytest.raises(FileExistsError):
        evaluate_frozen(attempt, 'validation_2024', CAMPAIGN, steps=24, adapters=ADAPTERS)


def test_test_split_stays_locked_and_unbound_attempts_are_refused(attempt, tmp_path):
    with pytest.raises(PermissionError):
        evaluate_frozen(attempt, 'test_2025', CAMPAIGN, steps=24, adapters=ADAPTERS)
    loose = tmp_path/'loose'
    shutil.copytree(attempt, loose, ignore=shutil.ignore_patterns('evaluation', 'attempt.json'))
    with pytest.raises(FileNotFoundError):       # no attempt.json: not an attempt of a campaign stage
        evaluate_frozen(loose, 'validation_2024', CAMPAIGN, steps=24, adapters=ADAPTERS)
