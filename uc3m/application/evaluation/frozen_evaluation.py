"""Frozen evaluation of one trained attempt against a fresh RBC on a split (T7 -> T9).

    evaluate_frozen(attempt_root, 'validation_2024', campaign_root)

Writes, once and never over an existing one:
  <attempt_root>/evaluation/<split>/kpi_report.json       KPI contract report (trace-based)
  <attempt_root>/evaluation/<split>/evaluation_manifest.json  {"files": {"kpi_report.json": sha256}}
  <attempt_root>/evaluation/<split>/frozen_runs.json      control and baseline run records
The report context is the attempt's identity {campaign_id, treatment_id, algorithm,
scenario, seed, split}; results_catalog.build_seed_table reads exactly this layout.
Explicit short diagnostics are stored under evaluation/diagnostics instead.
The policy and the baseline share split, scenario, seed and episode length, so they
see the same EV services, initial storage and exogenous signals.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional

from uc3m.application.evaluation.kpi_contract import (
    compute_fresh_kpis, load_kpi_catalog, load_thesis_indicators, validate_kpi_report,
)
from uc3m.application.training.attempt_trust import read_trusted_attempt
from uc3m.application.training.integrity import _file_sha256
from uc3m.application.dataset.provenance import contained_path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = REPO/'configs/evaluation/kpis.yaml'
SPLIT_HOURS = {'train_2023': 8760, 'validation_2024': 8784, 'test_2025': 8760}


def _run_record(run) -> Dict[str, object]:
    record = {field.name: getattr(run, field.name) for field in dataclasses.fields(run)
              if field.name not in ('trace', 'citylearn_v3_report')}
    record['trace_exogenous_hash'] = run.trace.exogenous_hash
    record['trace_hash'] = run.trace.trace_hash()
    return record


def _evaluation_catalog(trusted, campaign_root, catalog_path, adapters):
    inputs = trusted.manifest.get('inputs') or {}
    split = inputs.get('split_manifest')
    if split:
        source = contained_path(REPO, split['path'])
        if source.parent != campaign_root.resolve() or _file_sha256(source) != split['sha256']:
            raise PermissionError('evaluation dataset differs from the frozen campaign split manifest')
    catalog = inputs.get('kpi_catalog')
    if catalog:
        source = contained_path(REPO, catalog['path'])
        if (catalog_path is not None and Path(catalog_path).resolve() != source
                or _file_sha256(source) != catalog['sha256']):
            raise PermissionError('evaluation KPI catalog differs from the frozen campaign input')
        catalog_path = source
    bill = inputs.get('bill_tariffs')
    if bill and getattr(adapters, 'bill_tariffs_sha256', None) != bill['sha256']:
        raise PermissionError('evaluation bill tariffs differ from the frozen campaign input')
    return Path(catalog_path) if catalog_path is not None else DEFAULT_CATALOG


def _kpi_unavailability(schema, trace):
    reasons = {}
    if not (schema.get('community_market') or {}).get('enabled', False):
        reasons.update(dict.fromkeys(('community_import_share', 'community_local_traded_daily_average',
                                      'community_local_traded_total'), 'community_market_disabled'))
    prices = trace.district_series.get('price')
    if prices is None:
        reasons['price_signal_deviation'] = 'no_common_district_price'
    elif max(prices) - min(prices) <= 1e-12:
        reasons['price_signal_deviation'] = 'constant_price_signal'
    return reasons


def evaluate_frozen(attempt_root: Path, split_id: str, campaign_root: Path, *, adapters,
                    steps: Optional[int] = None, seed: Optional[int] = None,
                    catalog_path: Optional[Path] = None) -> Dict[str, object]:
    """``adapters`` (uc3m.adapters.citylearn.frozen_adapters.citylearn_frozen_adapters()) is
    injected by a composition root: load_native_policy, run_frozen_episode, rbc_policy and
    extra_measures (CityLearn v3 rules such as price_signal_deviation)."""
    attempt_root, campaign_root = Path(attempt_root), Path(campaign_root)
    if split_id not in SPLIT_HOURS:
        raise ValueError('unknown frozen evaluation split')
    expected_rows = SPLIT_HOURS[split_id]
    horizon = expected_rows if steps is None else steps
    if type(horizon) is not int or not 0 < horizon <= expected_rows:
        raise ValueError(f'{split_id}: evaluation steps must be in [1, {expected_rows}]')
    relative = f'evaluation/{split_id}' if horizon == expected_rows else f'evaluation/diagnostics/{split_id}/steps_{horizon}'
    folder = contained_path(attempt_root, relative)
    if folder.exists():
        raise FileExistsError(f'{folder} already holds an evaluation; it is never overwritten')
    if not (attempt_root/'attempt.json').is_file():
        raise FileNotFoundError(f'{attempt_root} has no attempt.json: not an attempt of a campaign stage')
    trusted = read_trusted_attempt(attempt_root)
    catalog_path = _evaluation_catalog(trusted, campaign_root, catalog_path, adapters)
    record, treatment, evidence = trusted.record, trusted.resolved, trusted.evidence
    algorithm, scenario = str(treatment['algorithm']), str(treatment['scenario'])
    if seed is not None and (type(seed) is not int or seed != record['seed']):
        raise PermissionError('evaluation seed must equal the bound attempt seed')
    run_seed = record['seed']
    split_dir = campaign_root/'splits'/split_id
    access = {}
    if split_id == 'test_2025':
        from uc3m.application.evaluation.test_access import verify_test_unlock
        verify_test_unlock(trusted.manifest_path)
        access['manifest_path'] = trusted.manifest_path

    policy = adapters.load_native_policy(algorithm, attempt_root)   # fails closed on unverified or tampered models
    catalog = getattr(policy, 'scenario_catalog_path', None)
    if catalog is not None:
        access['scenario_catalog'] = catalog
    control = adapters.run_frozen_episode(split_dir, policy, campaign_root, steps=horizon, seed=run_seed,
                                          scenario=scenario, **access)
    baseline = adapters.run_frozen_episode(split_dir, adapters.rbc_policy(), campaign_root, steps=horizon, seed=run_seed,
                                  scenario=scenario, **access)
    schema = json.loads((split_dir/'schema.json').read_text(encoding='utf-8'))
    expected_buildings = {name for name, attributes in schema['buildings'].items() if attributes.get('include', True)}
    for run in (control, baseline):
        if run.completed_steps != horizon or len(run.trace.timestamps) != horizon:
            raise RuntimeError(f'{run.policy}: evaluation does not cover the requested {horizon} steps')
        if set(run.trace.building_ids) != expected_buildings or len(run.trace.building_ids) != len(expected_buildings):
            raise RuntimeError(f'{run.policy}: evaluation does not cover every enabled building in the split')
        if (run.training_updates or run.contract.get('grad_enabled_during_act')
                or run.contract.get('parameter_hash_before') != run.contract.get('parameter_hash_after')):
            raise RuntimeError(f'{run.policy}: policy was not frozen during evaluation')
    if (control.ev_connection_hash != baseline.ev_connection_hash
            or control.initial_storage_kwh != baseline.initial_storage_kwh
            or control.trace.exogenous_hash != baseline.trace.exogenous_hash):
        raise RuntimeError('policy and baseline did not see the same EV services, storage and signals')
    context = {'campaign_id': evidence['campaign_id'], 'treatment_id': record['treatment_id'],
               'algorithm': algorithm, 'scenario': scenario, 'seed': int(record['seed']), 'split': split_id}
    kpi_catalog = load_kpi_catalog(catalog_path)
    report = compute_fresh_kpis(control.trace, baseline.trace, kpi_catalog, context=context,
                                thesis_indicators=load_thesis_indicators(catalog_path),
                                citylearn_v3_report=control.citylearn_v3_report,
                                citylearn_v3_catalog_path=catalog_path,
                                citylearn_v3_unavailable=_kpi_unavailability(schema, control.trace),
                                extra_measures=adapters.extra_measures)
    validation = validate_kpi_report(report, kpi_catalog)
    if not validation.passed:
        raise ValueError('invalid KPI report: ' + ', '.join(validation.reasons))
    unavailable = [row['name'] for row in report.citylearn_v3_kpis if row['availability'] == 'unavailable']
    if horizon == expected_rows and unavailable:
        raise ValueError('full evaluation has undefined CityLearn v3 KPIs: ' + ', '.join(unavailable))
    payload = report.as_dict()
    payload['bill_tariffs_sha256'] = getattr(adapters, 'bill_tariffs_sha256', None)
    payload['citylearn_v3_building_kpis'] = control.citylearn_v3_report.get('building_objective_kpis') or []
    payload['comparison_references'] = {'trace': 'rbc', 'citylearn_v3': 'citylearn_native_baseline'}
    raw = json.dumps(payload, indent=2, default=str, allow_nan=False).encode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Drive sync ignores .partial_ directories until the complete report is renamed.
    with tempfile.TemporaryDirectory(prefix='.partial_evaluation_', dir=folder.parent) as scratch:
        staging = Path(scratch)
        (staging/'kpi_report.json').write_bytes(raw)
        runs = json.dumps({'control': _run_record(control), 'baseline': _run_record(baseline)},
                          indent=2, default=str, allow_nan=False).encode('utf-8')
        (staging/'frozen_runs.json').write_bytes(runs)
        (staging/'evaluation_manifest.json').write_text(json.dumps({
            'schema_version': 2, 'split': split_id, 'expected_full_split_rows': expected_rows,
            'files': {'kpi_report.json': digest, 'frozen_runs.json': hashlib.sha256(runs).hexdigest()}},
            indent=2), encoding='utf-8')
        staging.rename(folder)
    return {'folder': str(folder), 'kpi_report_sha256': digest, 'axis_gains': dict(report.axis_gains)}
