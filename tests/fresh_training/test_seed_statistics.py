"""T9: statistics with the seed as the replication unit, no forced winner.

Mathematical units use new arrays with known solutions; no value of an earlier
campaign appears here.
"""
import itertools
import json

import pytest

from uc3m.application.evaluation import fresh_analysis as fa

ALGORITHMS = ('HAPPO', 'MASAC', 'MATD3', 'MAAC')
AXES = ('flexibility', 'co2_emissions', 'energy_cost')


def _row(algorithm, scenario, seed, endpoint, value, split='validation_2024'):
    return {'campaign_id': 'fresh_test_v1', 'algorithm': algorithm, 'scenario': scenario, 'seed': seed,
            'split': split, 'endpoint': endpoint, 'value': value, 'kpi_report_sha256': 'a'*64}


def _complete_table(effect=None):
    """One row per algorithm x protocol endpoint x seed: 3 axes and the 26 comparable KPIs."""
    rows = []
    for algorithm, (scenario, endpoint), seed in itertools.product(
            ALGORITHMS, fa.FrozenProtocol.default().endpoints, range(1001, 1013)):
        base = (effect or {}).get(algorithm, 0.0)
        rows.append(_row(algorithm, scenario, seed, endpoint, base + 0.001*(seed % 7)))
    return rows


def test_nested_native_report_extracts_new_kpis():
    comparable = fa.comparable_kpis()
    e1_kpis = comparable['flexibility'][1]
    report = {'context': {'campaign_id': 'fresh_test_v1', 'algorithm': 'MATD3', 'scenario': 'E1', 'seed': 1001,
                          'split': 'validation_2024'},
              'axis_gains': {'flexibility': 0.12, 'co2_emissions': -0.03, 'energy_cost': None},
              'comparable_kpi_gains': [{'name': k, 'gain': 0.01*i, 'available': i != 0}
                                       for i, k in enumerate(e1_kpis)],
              'values': {}, 'trace_hash': 'b'*64}
    rows = fa.rows_from_kpi_report(report, report_sha256='c'*64)
    by_endpoint = {r['endpoint']: r['value'] for r in rows}
    # E1 is scored on flexibility only: its axis gain plus its 12 comparable KPI gains.
    assert set(by_endpoint) == {'flexibility', *e1_kpis} and by_endpoint['flexibility'] == 0.12
    assert by_endpoint[e1_kpis[0]] is None and by_endpoint[e1_kpis[1]] == pytest.approx(0.01)
    assert all(r['kpi_report_sha256'] == 'c'*64 for r in rows)


def test_the_26_comparable_kpis_come_from_citylearn_v3():
    comparable = fa.comparable_kpis()
    assert {axis: (scenario, len(kpis)) for axis, (scenario, kpis) in comparable.items()} == {
        'flexibility': ('E1', 12), 'co2_emissions': ('E2', 5), 'energy_cost': ('E3', 9)}
    assert {'peak_average', 'ramping_average', 'one_minus_load_factor_average'} <= set(comparable['flexibility'][1])
    assert 'price_signal_deviation' in comparable['energy_cost'][1]
    assert len(fa.FrozenProtocol.default().endpoints) == 3 + 26


def test_every_kpi_gets_descriptives_normality_and_the_full_nonparametric_battery():
    report = fa.analyze_campaign(fa.SeedTable.from_rows(_complete_table({'MATD3': 0.2})),
                                 fa.FrozenProtocol.default())
    stats = report.seed_statistics
    assert len(stats) == 4*29
    row = next(s for s in stats if s['endpoint'] == 'ramping_average' and s['algorithm'] == 'MAAC')
    assert {'n', 'mean', 'median', 'std', 'variance', 'min', 'max', 'q1', 'q3', 'iqr', 'cv', 'skewness',
            'kurtosis_excess', 'iqm', 'ci95_mean'} <= set(row) and row['n'] == 12
    assert {'shapiro_wilk', 'anderson_darling', 'dagostino_pearson'} <= set(row['normality'])
    families = report.kpi_families
    assert set(families) == {'kpi_OE1', 'kpi_OE2', 'kpi_OE3'}
    assert [len(families[f]['omnibus']) for f in ('kpi_OE1', 'kpi_OE2', 'kpi_OE3')] == [12, 5, 9]
    assert all('kendall_w' in r for f in families.values() for r in f['omnibus'])
    assert all('cliffs_delta' in r for f in families.values() for r in f['pairwise'])
    battery = report.battery
    assert len(battery) == 29
    entry = battery[0]
    independent, paired = entry['independent_view'], entry['paired_seed_blocks']
    assert {'shapiro_wilk', 'fligner_killeen', 'kruskal_wallis', 'epsilon_squared', 'dunn_holm',
            'cliffs_delta_pairs', 'complementary'} <= set(independent)
    assert {'moods_median', 'conover_iman', 'mann_whitney', 'brunner_munzel', 'wilcoxon_paired'} <= set(
        independent['complementary'])
    assert {'friedman', 'nemenyi', 'quade', 'wilcoxon_pairs'} <= set(paired)
    json.dumps(report.as_dict(), default=str)


def test_duplicate_seed_rejected():
    rows = _complete_table()
    with pytest.raises(ValueError):
        fa.SeedTable.from_rows(rows + [rows[0]])


def test_episode_rows_do_not_increase_n():
    rows = _complete_table()
    episodes = [dict(r, episode=e) for r in rows[:3] for e in range(50)]
    with pytest.raises(ValueError):  # per-episode rows are not replicas
        fa.SeedTable.from_rows(rows + episodes)
    table = fa.SeedTable.from_rows(rows)
    assert table.n_seeds('MATD3', 'E1', 'flexibility') == 12


def test_fractional_iqm():
    # 10 values: quartile cut at 2.5 -> weights 0.5 on the 3rd and 8th sorted values.
    values = list(range(1, 11))
    expected = (0.5*3 + 4 + 5 + 6 + 7 + 0.5*8)/5
    assert fa.iqm(values) == pytest.approx(expected)
    assert fa.iqm([1.0, 2.0, 3.0, 4.0]) == pytest.approx(2.5)


def test_bootstrap_by_seed():
    values = [0.1, 0.2, 0.15, 0.3, 0.25, 0.05, 0.12, 0.18, 0.22, 0.28, 0.09, 0.14]
    low, high = fa.bootstrap_ci(values, statistic='mean', resamples=10000, seed=7001)
    again = fa.bootstrap_ci(values, statistic='mean', resamples=10000, seed=7001)
    assert (low, high) == again and low < sum(values)/len(values) < high
    assert fa.bootstrap_ci([0.2]*12, statistic='mean', resamples=200, seed=7001) == pytest.approx((0.2, 0.2))


def test_common_hv_reference():
    assert fa.HV_REFERENCE == (-1.0, -1.0, -1.0)
    clipped, saturated = fa.clip_gains((1.7, -0.2, 0.4))
    assert clipped == (1.0, -0.2, 0.4) and saturated == ('flexibility',)
    assert fa.hypervolume([(0.0, 0.0, 0.0)]) == pytest.approx(1.0)  # box from -1 to 0 in 3 axes
    assert fa.hypervolume([(1.0, 1.0, 1.0)]) == pytest.approx(8.0)
    assert fa.hypervolume([(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]) == pytest.approx(1.0)
    assert fa.hypervolume([(0.0, -1.0, 1.0), (1.0, 0.0, -1.0)]) == pytest.approx(0.0)


def test_missing_treatment_blocks_acceptance():
    rows = [r for r in _complete_table() if not (r['algorithm'] == 'MAAC' and r['seed'] == 1012)]
    report = fa.analyze_campaign(fa.SeedTable.from_rows(rows), fa.FrozenProtocol.default())
    assert report.coverage['complete'] is False
    assert 'MAAC/E1/seed_1012' in report.coverage['missing']
    assert report.decisions['scientifically_complete'] is False


def test_negative_results_can_be_scientifically_complete():
    report = fa.analyze_campaign(fa.SeedTable.from_rows(_complete_table()), fa.FrozenProtocol.default())
    assert report.coverage['complete'] is True
    assert report.decisions['scientifically_complete'] is True
    assert report.decisions['algorithm_difference'] == 'not_detected'
    assert len(report.test_families['pairwise']) == 18 and len(report.test_families['omnibus']) == 3
    assert len(report.test_families['versus_baseline']) == 12
    assert all(r['p_holm'] >= r['p_value'] for r in report.test_families['pairwise'] if r['p_value'] is not None)
    json.dumps(report.as_dict())  # serializable for delivery


def test_detected_difference_is_reported_with_holm():
    report = fa.analyze_campaign(fa.SeedTable.from_rows(_complete_table({'MATD3': 0.2})),
                                 fa.FrozenProtocol.default())
    assert report.decisions['algorithm_difference'] == 'detected'
    flexibility = next(r for r in report.test_families['omnibus'] if r['endpoint'] == 'flexibility')
    assert flexibility['scenario'] == 'E1' and flexibility['p_holm'] < 0.05


def test_axes_and_endpoints_come_from_the_kpi_catalog():
    """The seed table has no axis list of its own: it must equal the catalog's axes."""
    from pathlib import Path
    from uc3m.application.evaluation.kpi_contract import load_kpi_catalog
    catalog = load_kpi_catalog(Path(__file__).resolve().parents[2]/'configs/evaluation/kpis.yaml')
    assert tuple(fa.AXES) == tuple(catalog.axes)
    protocol = fa.FrozenProtocol.default()
    assert {axis for _, axis in protocol.confirmatory_endpoints} == set(catalog.axes)
    assert all(catalog.axes[axis] for axis in catalog.axes)     # every axis has primary KPIs


def test_catalog_kpi_rules_equal_citylearn_v3():
    """The application reads CityLearn v3 KPI rules from the catalog; they must equal CityLearn's own."""
    from citylearn.v3 import objectives
    from uc3m.application.evaluation import kpi_contract as kc
    groups = {'flexibility': objectives.OE1_FLEXIBILITY_KPIS, 'co2_emissions': objectives.OE2_EMISSIONS_KPIS,
              'energy_cost': objectives.OE3_COST_KPIS}
    probe = {n: 1.0 for n in set().union(*groups.values()) | {'price_signal_deviation_baseline'}}
    codes = {'flexibility': 'OE1', 'co2_emissions': 'OE2', 'energy_cost': 'OE3'}
    expected = {axis: (objectives.OBJECTIVE_AXES[codes[axis]].scenario,
                       tuple(k for k in kpis if not k.endswith('_baseline')
                             and objectives._baseline_for(k, probe) is not None))
                for axis, kpis in groups.items()}
    assert kc.comparable_kpi_names() == expected
    for kpis in groups.values():
        for name in kpis:
            assert kc.lower_is_better(name) == (name not in objectives.HIGHER_IS_BETTER), name
