"""T8: hyperparameters are selected on fresh validation only, with the same budget for every algorithm.

The protocol comes from the real campaign DAG; validation rows are synthetic,
with known answers, because selection is a pure decision over them.
"""
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from uc3m.application.training import fresh_campaign as fc
from uc3m.application.training.fresh_tuning import (SelectionBlocked, build_weight_sensitivity, protocol_from_dag,
                                                    select_hyperparameters, validation_row)

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN_ID = 'fresh_iquitos_20261105_v5'


@pytest.fixture(scope='module')
def dag():
    return fc.build_dag(fc.load_campaign_config(REPO/'configs/experiments/iquitos.yaml', REPO), REPO)


@pytest.fixture(scope='module')
def protocol(dag):
    return protocol_from_dag(dag, CAMPAIGN_ID)


def _report(gains, balanced=True):
    return {'trace_hash': 'a'*64, 'baseline_trace_hash': 'b'*64, 'axis_gains': dict(gains),
            'balance_checks': {'energy': {'passed': balanced}}}


def _rows(protocol, algorithm, score_of, *, feasible=lambda c: True, split='validation_2024'):
    rows = []
    for candidate, scenario, seed in sorted(protocol.expected[algorithm]):
        gain = score_of(candidate, seed)
        treatment = protocol.treatments[(algorithm, candidate, scenario, seed)]
        rows.append(validation_row(treatment, {'training_complete': feasible(candidate), 'reasons': []},
                                   _report({'flexibility': gain, 'co2_emissions': gain, 'energy_cost': gain}),
                                   evaluation_manifest_sha256=hashlib.sha256(f'{candidate}{scenario}{seed}'.encode()).hexdigest(),
                                   split=split, campaign_id=CAMPAIGN_ID))
    return rows


def test_equal_hpo_budget_across_algorithms(dag, protocol):
    hpo = [t for t in dag.treatments if t.stage == 'hpo']
    grid = {f'c{i}' for i in range(1, 9)}
    for algorithm in ('HAPPO', 'MASAC', 'MATD3', 'MAAC'):
        rows = [t for t in hpo if t.algorithm == algorithm]
        # Every distinct configuration gets the same 3 scenarios x 3 development seeds x 10 x 8760 steps.
        per_candidate = {}
        for t in rows:
            per_candidate.setdefault(t.candidate, []).append(t.episodes*t.episode_time_steps)
        assert {len(v) for v in per_candidate.values()} == {9}
        assert {sum(v) for v in per_candidate.values()} == {9*10*8760}
        # Every grid point the algorithm searches is covered; a collapsed point is a native clamp, not a skip.
        # SPEC-015 D-M3-8: on iquitos_v6 MASAC searches only rnn_hidden_dim 128, 4 of the 8 points.
        from uc3m.application.training.fresh_campaign import algorithm_candidates
        searched = set(algorithm_candidates(algorithm, {c: dag.candidates[c] for c in grid},
                                            dag.config['_algorithm_config']))
        collapsed = dag.collapsed_candidates['hpo'][algorithm]
        assert set(itertools.chain.from_iterable(collapsed.values())) == searched
        assert searched == grid or algorithm == 'MASAC'
        assert protocol.equivalents[algorithm] == collapsed
    # Native capacity (no rnn_hidden_dim clamp): no configuration collapses. HAPPO, MATD3 and MAAC keep 8 distinct
    # configurations; MASAC searches 4 on iquitos_v6 (D-M3-8, 105 GiB for rnn 256): 252 treatments in total.
    for algorithm in ('HAPPO', 'MASAC', 'MATD3', 'MAAC'):
        assert all(len(group) == 1 for group in dag.collapsed_candidates['hpo'][algorithm].values()), algorithm
    assert len(hpo) == (3*8 + 4)*9            # D-M3-8: MASAC searches 4 of the 8 grid points on iquitos_v6


def test_only_new_validation_can_select(protocol):
    good = _rows(protocol, 'MATD3', lambda c, s: 0.1)
    freeze = select_hyperparameters(good, protocol)
    assert freeze.campaign_id == CAMPAIGN_ID and freeze.algorithm == 'MATD3'
    for split in ('train_2023', 'test_2025'):
        with pytest.raises(PermissionError):
            select_hyperparameters(_rows(protocol, 'MATD3', lambda c, s: 0.1, split=split), protocol)
    foreign = [dict(row, campaign_id='iquitos_v4_multiseed') for row in good]
    with pytest.raises(PermissionError):
        select_hyperparameters(foreign, protocol)


def test_no_test_or_historical_score_in_selection(protocol):
    rows = _rows(protocol, 'HAPPO', lambda c, s: 0.1)
    with pytest.raises(ValueError):           # rows are strict: no extra score can steer the choice
        select_hyperparameters([dict(rows[0], test_score=9.0)] + rows[1:], protocol)
    with pytest.raises(ValueError):
        select_hyperparameters([dict(rows[0], historical_rank=1)] + rows[1:], protocol)
    # The choice depends only on validation gains, with equal 1/3 weights and the declared tie-breaks.
    best = select_hyperparameters(_rows(protocol, 'HAPPO', lambda c, s: 0.5 if c == 'c6' else 0.1), protocol)
    assert best.hyperparameters == protocol.hyperparameters[('HAPPO', 'c6')]
    noisy = {901: 0.0, 902: 0.4, 903: 0.2}
    tied = select_hyperparameters(_rows(protocol, 'HAPPO', lambda c, s: noisy[s] if c == 'c1' else 0.2), protocol)
    assert tied.hyperparameters == protocol.hyperparameters[('HAPPO', 'c2')]   # same mean, lower seed variance
    flat = select_hyperparameters(_rows(protocol, 'HAPPO', lambda c, s: 0.2), protocol)
    assert flat.hyperparameters == protocol.hyperparameters[('HAPPO', 'c1')]   # lexicographic last resort
    assert json.loads(flat.reason)['rule_weights'] == [1/3, 1/3, 1/3]


def test_all_infeasible_blocks_selection(protocol):
    with pytest.raises(SelectionBlocked):
        select_hyperparameters(_rows(protocol, 'MAAC', lambda c, s: 0.9, feasible=lambda c: False), protocol)
    only_one = _rows(protocol, 'MAAC', lambda c, s: 0.9 if c == 'c8' else 0.1, feasible=lambda c: c != 'c8')
    assert select_hyperparameters(only_one, protocol).hyperparameters != protocol.hyperparameters[('MAAC', 'c8')]
    with pytest.raises(SelectionBlocked):     # a missing treatment is not a smaller grid
        select_hyperparameters(_rows(protocol, 'MAAC', lambda c, s: 0.1)[1:], protocol)
    unbalanced = _rows(protocol, 'MAAC', lambda c, s: 0.1)
    unbalanced = [dict(r, energy_balance_passed=False) for r in unbalanced]
    with pytest.raises(SelectionBlocked):
        select_hyperparameters(unbalanced, protocol)


def test_weight_extremes_preserve_cyclic_order(dag):
    rows = build_weight_sensitivity(dag)
    assert len(rows) == 72 and {r['seed'] for r in rows} == {1001, 1002, 1003}
    assert {r['episodes'] for r in rows} == {50} and {r['requires'][0] for r in rows} == {'configuration_freeze'}
    base = {'E1': (0.60, 0.15, 0.25), 'E2': (0.25, 0.60, 0.15), 'E3': (0.15, 0.25, 0.60)}
    expected = {0.55: (0.55, 0.28125, 0.16875), 0.65: (0.65, 0.21875, 0.13125)}
    for row in rows:
        b, w = base[row['scenario']], row['weights']
        order = sorted(range(3), key=lambda i: -b[i])          # dominant, secondary, residual
        assert sorted(range(3), key=lambda i: -w[i]) == order
        p = round(w[order[0]], 2)
        assert tuple(round(w[i], 5) for i in order) == expected[p] and abs(sum(w) - 1) < 1e-12


def test_pilot_not_counted_as_confirmation(dag, protocol):
    pilot = [t for t in dag.treatments if t.stage == 'pilot']
    confirm = [t for t in dag.treatments if t.stage == 'confirm']
    assert pilot and confirm and not {t.treatment_id for t in pilot} & {t.treatment_id for t in confirm}
    assert max(t.episodes for t in pilot) < min(t.episodes for t in confirm)
    rows = _rows(protocol, 'MATD3', lambda c, s: 0.1)
    with pytest.raises(PermissionError):       # pilot rows never enter HPO selection
        select_hyperparameters([dict(r, stage='pilot') for r in rows], protocol)
