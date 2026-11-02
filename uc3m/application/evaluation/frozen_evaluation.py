"""Frozen evaluation of one trained attempt against a fresh RBC on a split (T7 -> T9).

    evaluate_frozen(attempt_root, 'validation_2024', campaign_root)

Writes, once and never over an existing one:
  <attempt_root>/evaluation/<split>/kpi_report.json       KPI contract report (trace-based)
  <attempt_root>/evaluation/<split>/evaluation_manifest.json  {"files": {"kpi_report.json": sha256}}
  <attempt_root>/evaluation/<split>/frozen_runs.json      control and baseline run records
The report context is the attempt's identity {campaign_id, treatment_id, algorithm,
scenario, seed, split}; results_catalog.build_seed_table reads exactly this layout.
The policy and the baseline share split, scenario, seed and episode length, so they
see the same EV services, initial storage and exogenous signals.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

from uc3m.application.evaluation.kpi_contract import compute_fresh_kpis, load_kpi_catalog, load_thesis_indicators
from uc3m.application.training.fresh_policy import read_attempt

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = REPO/'configs/evaluation/kpis.yaml'


def _run_record(run) -> Dict[str, object]:
    record = {field.name: getattr(run, field.name) for field in dataclasses.fields(run)
              if field.name not in ('trace', 'citylearn_v3_report')}
    record['trace_exogenous_hash'] = run.trace.exogenous_hash
    return record


def evaluate_frozen(attempt_root: Path, split_id: str, campaign_root: Path, *, adapters,
                    steps: Optional[int] = None, seed: Optional[int] = None,
                    catalog_path: Path = DEFAULT_CATALOG) -> Dict[str, object]:
    """``adapters`` (uc3m.adapters.citylearn.frozen_adapters.citylearn_frozen_adapters()) is
    injected by a composition root: load_native_policy, run_frozen_episode, rbc_policy and
    extra_measures (CityLearn v3 rules such as price_signal_deviation)."""
    attempt_root, campaign_root = Path(attempt_root), Path(campaign_root)
    folder = attempt_root/'evaluation'/split_id
    if (folder/'kpi_report.json').exists():
        raise FileExistsError(f'{folder} already holds an evaluation; it is never overwritten')
    if not (attempt_root/'attempt.json').is_file():
        raise FileNotFoundError(f'{attempt_root} has no attempt.json: not an attempt of a campaign stage')
    record = read_attempt(attempt_root)
    treatment = json.loads((attempt_root/'resolved_treatment.json').read_text(encoding='utf-8'))
    evidence = json.loads((attempt_root/'learning_evidence.json').read_text(encoding='utf-8'))
    if treatment.get('treatment_id') != record['treatment_id']:
        raise PermissionError(f'{attempt_root}: resolved treatment and attempt record disagree')
    algorithm, scenario = str(treatment['algorithm']), str(treatment['scenario'])
    run_seed = int(record['seed'] if seed is None else seed)
    split_dir = campaign_root/'splits'/split_id

    policy = adapters.load_native_policy(algorithm, attempt_root)   # fails closed on unverified or tampered models
    control = adapters.run_frozen_episode(split_dir, policy, campaign_root, steps=steps, seed=run_seed,
                                          scenario=scenario)
    baseline = adapters.run_frozen_episode(split_dir, adapters.rbc_policy(), campaign_root, steps=steps, seed=run_seed,
                                  scenario=scenario)
    if (control.ev_connection_hash != baseline.ev_connection_hash
            or control.initial_storage_kwh != baseline.initial_storage_kwh
            or control.trace.exogenous_hash != baseline.trace.exogenous_hash):
        raise RuntimeError('policy and baseline did not see the same EV services, storage and signals')
    if control.training_updates:
        raise RuntimeError(f'{algorithm}: {control.training_updates} optimizer steps during frozen evaluation')

    context = {'campaign_id': evidence['campaign_id'], 'treatment_id': record['treatment_id'],
               'algorithm': algorithm, 'scenario': scenario, 'seed': int(record['seed']), 'split': split_id}
    report = compute_fresh_kpis(control.trace, baseline.trace, load_kpi_catalog(catalog_path), context=context,
                                thesis_indicators=load_thesis_indicators(catalog_path),
                                citylearn_v3_report=control.citylearn_v3_report,
                                extra_measures=adapters.extra_measures)
    folder.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(report.as_dict(), indent=2, default=str).encode('utf-8')
    (folder/'kpi_report.json').write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (folder/'evaluation_manifest.json').write_text(json.dumps({'files': {'kpi_report.json': digest}}, indent=2),
                                                   encoding='utf-8')
    (folder/'frozen_runs.json').write_text(json.dumps({'control': _run_record(control),
                                                       'baseline': _run_record(baseline)}, indent=2, default=str),
                                           encoding='utf-8')
    return {'folder': str(folder), 'kpi_report_sha256': digest, 'axis_gains': dict(report.axis_gains)}
