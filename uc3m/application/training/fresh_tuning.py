"""HPO selection and weight sensitivity of the fresh campaign (T8, design §5).

Selection reads only validation rows of this campaign's HPO stage. A candidate
is feasible when every one of its treatments (3 scenarios x 3 development
seeds) completed training and its validation episode balanced energy with
finite gains on the three axes. Among feasible candidates the score is the mean
of the axis gains against a freshly run RBC with equal 1/3 weights (not the
training weights); ties go to the lower variance across development seeds,
then to the lexicographic candidate id. No feasible candidate blocks the
algorithm: the least bad one is never promoted. One configuration per
algorithm is frozen for E1/E2/E3 alike.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from statistics import mean, pvariance
from typing import Dict, List, Mapping, Sequence, Set, Tuple

from uc3m.application.training.fresh_campaign import HYPERPARAMETERS, freeze_configuration
from uc3m.domain.campaigns import ConfigurationFreeze

VALIDATION_SPLIT = 'validation_2024'
AXES = ('flexibility', 'co2_emissions', 'energy_cost')
SELECTION_RULE = ('feasible on validation_2024; max mean axis gain vs fresh RBC with weights 1/3; '
                  'tie: min variance across development seeds, then candidate id')
ROW_KEYS = {'campaign_id', 'stage', 'split', 'algorithm', 'candidate', 'scenario', 'seed', 'effective_hyperparameters',
            'training_complete', 'energy_balance_passed', 'axis_gains', 'trace_hash', 'baseline_trace_hash',
            'evaluation_manifest_sha256'}
SCORE_DECIMALS = 12


class SelectionBlocked(RuntimeError):
    """No candidate of an algorithm can be frozen from the evidence at hand."""


@dataclass(frozen=True)
class TuningProtocol:
    campaign_id: str
    # algorithm -> {(candidate, scenario, seed)} the HPO stage plans.
    expected: Mapping[str, Set[Tuple[str, str, int]]]
    treatments: Mapping[Tuple[str, str, str, int], Mapping[str, object]]
    hyperparameters: Mapping[Tuple[str, str], Mapping[str, float]]
    # algorithm -> kept candidate -> grid candidates it stands for (native clamps).
    equivalents: Mapping[str, Mapping[str, List[str]]]


def protocol_from_dag(dag, campaign_id: str) -> TuningProtocol:
    expected, treatments, hyper = {}, {}, {}
    for t in dag.treatments:
        if t.stage != 'hpo':
            continue
        expected.setdefault(t.algorithm, set()).add((t.candidate, t.scenario, t.seed))
        row = t.as_dict()
        treatments[(t.algorithm, t.candidate, t.scenario, t.seed)] = row
        hyper[(t.algorithm, t.candidate)] = dict(row['effective_hyperparameters'])
    return TuningProtocol(campaign_id, expected, treatments, hyper,
                          dict(dag.collapsed_candidates.get('hpo', {})))


def validation_row(treatment: Mapping[str, object], completion: Mapping[str, object], kpi_report: Mapping[str, object],
                   *, evaluation_manifest_sha256: str, split: str, campaign_id: str) -> Dict[str, object]:
    """One HPO treatment evaluated frozen on a split: the only input selection accepts."""
    gains = kpi_report.get('axis_gains') or {}
    return {'campaign_id': campaign_id, 'stage': treatment['stage'], 'split': split,
            'algorithm': treatment['algorithm'], 'candidate': treatment['candidate'],
            'scenario': treatment['scenario'], 'seed': int(treatment['seed']),
            'effective_hyperparameters': dict(treatment['effective_hyperparameters']),
            'training_complete': bool(completion.get('training_complete')),
            'energy_balance_passed': bool(kpi_report.get('balance_checks')) and all(
                c.get('passed') is True for c in kpi_report['balance_checks'].values()),
            'axis_gains': {axis: gains.get(axis) for axis in AXES},
            'trace_hash': kpi_report.get('trace_hash'), 'baseline_trace_hash': kpi_report.get('baseline_trace_hash'),
            'evaluation_manifest_sha256': evaluation_manifest_sha256}


def _feasible(row) -> bool:
    gains = [row['axis_gains'].get(axis) for axis in AXES]
    return (row['training_complete'] and row['energy_balance_passed']
            and all(g is not None and math.isfinite(float(g)) for g in gains))


def select_hyperparameters(validation_rows: Sequence[Mapping[str, object]], protocol: TuningProtocol) -> ConfigurationFreeze:
    rows = [dict(r) for r in validation_rows]
    for row in rows:
        if set(row) != ROW_KEYS:
            raise ValueError(f'validation row keys differ from the contract: {sorted(set(row) ^ ROW_KEYS)}')
        if row['campaign_id'] != protocol.campaign_id:
            raise PermissionError(f"row of {row['campaign_id']} cannot select for {protocol.campaign_id}")
        if row['split'] != VALIDATION_SPLIT or row['stage'] != 'hpo':
            raise PermissionError(f"only {VALIDATION_SPLIT} rows of the hpo stage select; got {row['stage']}/{row['split']}")
    algorithms = {row['algorithm'] for row in rows}
    if len(algorithms) != 1:
        raise ValueError(f'one algorithm per selection, got {sorted(algorithms)}')
    algorithm = algorithms.pop()
    keys = [(r['candidate'], r['scenario'], r['seed']) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != protocol.expected[algorithm]:
        raise SelectionBlocked(f'{algorithm}: validation rows do not cover the planned HPO grid exactly '
                               f'({len(set(keys))}/{len(protocol.expected[algorithm])})')
    by_candidate: Dict[str, List[dict]] = {}
    for row in rows:
        if row['effective_hyperparameters'] != protocol.hyperparameters[(algorithm, row['candidate'])]:
            raise ValueError(f"{algorithm}/{row['candidate']}: hyperparameters differ from the planned candidate")
        by_candidate.setdefault(row['candidate'], []).append(row)
    scored = []
    for candidate, members in sorted(by_candidate.items()):
        if not all(_feasible(r) for r in members):
            continue
        per_row = [mean(float(r['axis_gains'][a]) for a in AXES) for r in members]
        by_seed: Dict[int, List[float]] = {}
        for r, value in zip(members, per_row):
            by_seed.setdefault(r['seed'], []).append(value)
        score = round(mean(per_row), SCORE_DECIMALS)
        spread = round(pvariance([mean(v) for v in by_seed.values()]), SCORE_DECIMALS)
        scored.append((-score, spread, candidate))
    if not scored:
        raise SelectionBlocked(f'{algorithm}: no feasible HPO candidate on {VALIDATION_SPLIT}')
    _, spread, chosen = min(scored)
    hyper = protocol.hyperparameters[(algorithm, chosen)]
    reason = json.dumps({'chosen': chosen, 'stands_for': protocol.equivalents.get(algorithm, {}).get(chosen, [chosen]),
                         'rule_weights': [1/3, 1/3, 1/3],
                         'ranking': [{'candidate': c, 'score': -s, 'seed_variance': v} for s, v, c in sorted(scored)],
                         'infeasible': sorted(set(by_candidate) - {c for _, _, c in scored})})
    return freeze_configuration(protocol.campaign_id, algorithm, {k: hyper[k] for k in HYPERPARAMETERS},
                                sorted({r['evaluation_manifest_sha256'] for r in rows}),
                                selection_rule=SELECTION_RULE, candidates=sorted(by_candidate), reason=reason)


def build_weight_sensitivity(dag) -> List[Dict[str, object]]:
    """The weight-extreme treatments of the DAG (p=0.55/0.65, 5:3 rest); the centre is the confirmation."""
    return [t.as_dict() for t in dag.treatments if t.stage == 'sensitivity']
