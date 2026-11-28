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
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from uc3m.adapters.citylearn.frozen_adapters import citylearn_frozen_adapters
from uc3m.adapters.citylearn.policy_inference import FrozenRun
from uc3m.application.evaluation import frozen_evaluation
from uc3m.application.evaluation.frozen_evaluation import evaluate_frozen
from uc3m.application.evaluation.kpi_contract import PhysicalTrace, load_citylearn_v3_kpis

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = (lambda c: REPO/c['dataset_root'])(__import__('yaml').safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8')))   # the active campaign dataset (configs/experiments/iquitos.yaml)
ADAPTERS = citylearn_frozen_adapters()   # this test is a composition root


@pytest.fixture(scope='module')
def attempt(native_attempts):
    return native_attempts['HAPPO']


def test_writes_the_report_the_seed_table_reads(attempt):
    result = evaluate_frozen(attempt, 'validation_2024', CAMPAIGN, steps=24, adapters=ADAPTERS)
    folder = attempt/'evaluation/diagnostics/validation_2024/steps_24'
    assert not (attempt/'evaluation/validation_2024').exists()
    assert Path(result['folder']) == folder
    raw = (folder/'kpi_report.json').read_bytes()
    manifest = json.loads((folder/'evaluation_manifest.json').read_text(encoding='utf-8'))
    assert manifest['schema_version'] == 2 and manifest['split'] == 'validation_2024'
    assert manifest['expected_full_split_rows'] == 8784
    assert manifest['files'] == {'kpi_report.json': hashlib.sha256(raw).hexdigest(),
        'frozen_runs.json': hashlib.sha256((folder/'frozen_runs.json').read_bytes()).hexdigest()}
    report = json.loads(raw)
    identity = json.loads((attempt/'attempt.json').read_text(encoding='utf-8'))
    assert report['context'] == {'campaign_id': __import__('yaml').safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))['campaign_id'],
                                 'treatment_id': identity['treatment_id'],
                                 'algorithm': 'HAPPO', 'scenario': 'E1', 'seed': 901, 'split': 'validation_2024'}
    assert set(report['axis_gains']) == {'flexibility', 'co2_emissions', 'energy_cost'}
    # Layer B: the 26 comparable CityLearn v3 KPI gains come from evaluate_objectives of the control run.
    gains = report['comparable_kpi_gains']
    assert len(gains) == 26 and sum(1 for g in gains if g['available']) >= 20, \
        [g['name'] for g in gains if not g['available']]
    assert {g['axis'] for g in gains} == {'flexibility', 'co2_emissions', 'energy_cost'}
    assert report['thesis_indicators']                         # Layer A is reported as well
    assert len(report['citylearn_v3_kpis']) == 54
    assert report['citylearn_v3_building_kpis']
    assert all(row['available'] or row['cause'] for row in report['citylearn_v3_kpis'])
    assert all(c['passed'] for c in report['balance_checks'].values())
    # Same exogenous services for policy and baseline, and the policy never trained during evaluation.
    runs = json.loads((folder/'frozen_runs.json').read_text(encoding='utf-8'))
    assert runs['control']['ev_connection_hash'] == runs['baseline']['ev_connection_hash']
    assert runs['control']['initial_storage_kwh'] == runs['baseline']['initial_storage_kwh']
    assert runs['control']['training_updates'] == 0 and runs['baseline']['policy'] == 'rbc'
    assert result['kpi_report_sha256'] == manifest['files']['kpi_report.json']


def test_an_evaluation_is_never_overwritten(attempt):
    assert (attempt/'evaluation/diagnostics/validation_2024/steps_24/kpi_report.json').is_file()
    with pytest.raises(FileExistsError):
        evaluate_frozen(attempt, 'validation_2024', CAMPAIGN, steps=24, adapters=ADAPTERS)


def test_test_split_stays_locked_and_unbound_attempts_are_refused(attempt, tmp_path):
    with pytest.raises(PermissionError):
        evaluate_frozen(attempt, 'test_2025', CAMPAIGN, steps=24, adapters=ADAPTERS)
    loose = tmp_path/'loose'
    shutil.copytree(attempt, loose, ignore=shutil.ignore_patterns('evaluation', 'attempt.json'))
    with pytest.raises(FileNotFoundError):       # no attempt.json: not an attempt of a campaign stage
        evaluate_frozen(loose, 'validation_2024', CAMPAIGN, steps=24, adapters=ADAPTERS)


@pytest.fixture
def synthetic_writer_inputs(tmp_path, monkeypatch):
    root = tmp_path/'dataset'
    folder = root/'splits/validation_2024'
    folder.mkdir(parents=True)
    (folder/'schema.json').write_text(json.dumps({'buildings': {'Building_1': {'include': True}}}), encoding='utf-8')
    attempt = tmp_path/'attempt'
    attempt.mkdir()
    (attempt/'attempt.json').write_text('{}', encoding='utf-8')
    definitions = load_citylearn_v3_kpis(frozen_evaluation.DEFAULT_CATALOG)
    undefined = {'community_import_share', 'community_local_traded_total',
                 'community_local_traded_daily_average', 'price_signal_deviation'}
    axes = {'OE1': {'kpis': {}}, 'OE2': {'kpis': {}}, 'OE3': {'kpis': {}}}
    for definition in definitions:
        name = definition['name']
        axes[definition['objective']]['kpis'][name] = {
            'value': None if name in undefined else 1.0,
            'comparison': {'available': name not in undefined, 'baseline': 1.0},
        }
    trace = PhysicalTrace(
        tuple((datetime(2024, 1, 1) + timedelta(hours=hour)).isoformat() for hour in range(24)),
        3600, ('Building_1',),
        {'Building_1': {'net_power': (1.0, 2.0)*12, 'price': (0.1,)*24, 'battery_throughput': (0.0,)*24}},
        {'price': (0.1,)*24, 'carbon_intensity': (0.5,)*24},
        {'net_power': 'kW', 'price': 'USD/kWh', 'battery_throughput': 'kWh', 'carbon_intensity': 'kgCO2/kWh'},
        'USD', 'fixture', 'a'*64,
    )
    run = FrozenRun('control', 'validation_2024', trace, 24, 0, 'b'*64, 0, 0, 0,
                    citylearn_v3_report={'axes': axes,
                                         'building_objective_kpis': [{'building': 'Building_1', 'value': 1.0}]})
    trusted = SimpleNamespace(manifest={}, resolved={'algorithm': 'HAPPO', 'scenario': 'E1'},
                              record={'seed': 901, 'treatment_id': 'treatment'},
                              evidence={'campaign_id': 'fixture'})
    monkeypatch.setattr(frozen_evaluation, 'read_trusted_attempt', lambda _: trusted)
    adapters = SimpleNamespace(**vars(ADAPTERS))
    adapters.load_native_policy = lambda *_: 'control'
    adapters.rbc_policy = lambda: 'rbc'
    adapters.run_frozen_episode = lambda _split, policy, *_args, **_kwargs: replace(run, policy=policy)
    return attempt, root, adapters, trusted


def test_short_report_is_separate_and_its_unavailable_kpis_have_causes(synthetic_writer_inputs):
    attempt, root, adapters, _ = synthetic_writer_inputs
    result = evaluate_frozen(attempt, 'validation_2024', root, steps=24, adapters=adapters)
    assert Path(result['folder']) == attempt/'evaluation/diagnostics/validation_2024/steps_24'
    report = json.loads((Path(result['folder'])/'kpi_report.json').read_text(encoding='utf-8'))
    counts = {row['name']: row['cause'] for row in report['citylearn_v3_kpis'] if not row['available']}
    assert len(report['citylearn_v3_kpis']) == 54 and not (attempt/'evaluation/validation_2024').exists()
    assert counts['price_signal_deviation'] == 'constant_price_signal'
    assert counts['community_import_share'] == 'community_market_disabled'


@pytest.mark.parametrize('change, problem', [
    ({'completed_steps': 23}, 'requested 24 steps'),
    ({'training_updates': 1}, 'was not frozen'),
])
def test_rejects_partial_or_mutating_evaluations(synthetic_writer_inputs, change, problem):
    attempt, root, adapters, _ = synthetic_writer_inputs
    original = adapters.run_frozen_episode
    adapters.run_frozen_episode = lambda *args, **kwargs: replace(original(*args, **kwargs), **change)
    with pytest.raises(RuntimeError, match=problem):
        evaluate_frozen(attempt, 'validation_2024', root, steps=24, adapters=adapters)
    assert not (attempt/'evaluation').exists()


def test_bill_tariff_mismatch_is_refused_before_any_rollout(synthetic_writer_inputs):
    attempt, root, adapters, trusted = synthetic_writer_inputs
    trusted.manifest['inputs'] = {'bill_tariffs': {'sha256': '0'*64}}
    adapters.run_frozen_episode = lambda *_a, **_kw: pytest.fail('unexpected rollout')
    with pytest.raises(PermissionError, match='bill tariffs'):
        evaluate_frozen(attempt, 'validation_2024', root, steps=24, adapters=adapters)
