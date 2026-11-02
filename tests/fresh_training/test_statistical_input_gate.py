"""P03/A05: invalid statistical inputs never produce a complete study; no difference is allowed.

A seed row carries a finite real value (or None for a missing measurement), an
integer seed and the full hash of the KPI report it came from. Rows outside the
frozen protocol (algorithm, seed, split, scenario/endpoint pair) are refused
instead of becoming extra replicas. A legitimate campaign whose gains are all
equal is complete with no detected difference; an unidentified SciPy error or a
NaN p-value is never turned into p = 1.
"""
import math

import pytest

from uc3m.application.evaluation import fresh_analysis as fa

PROTOCOL = fa.FrozenProtocol.default()
SHA = 'a'*64


# Default values differ between algorithms (real differences); all-equal columns are the degenerate case.
def _rows(value=lambda algorithm, scenario, seed: 0.1*seed % 1 + 0.01*PROTOCOL.algorithms.index(algorithm)):
    rows = []
    for algorithm in PROTOCOL.algorithms:
        for scenario, axis in PROTOCOL.endpoints:
            for seed in PROTOCOL.seeds:
                rows.append({'campaign_id': 'fresh_iquitos_20261101_v1', 'algorithm': algorithm,
                             'scenario': scenario, 'seed': seed, 'split': PROTOCOL.split, 'endpoint': axis,
                             'value': value(algorithm, scenario, seed), 'kpi_report_sha256': SHA})
    return rows


def _with(rows, index=0, **changes):
    rows = [dict(r) for r in rows]
    rows[index].update(changes)
    return rows


@pytest.mark.parametrize('value', [math.nan, math.inf, -math.inf, True, False, '0.1'])
def test_nan_inf_bool_never_complete(value):
    with pytest.raises(ValueError):
        fa.SeedTable.from_rows(_with(_rows(), value=value))


@pytest.mark.parametrize('seed', [True, '1001', 1001.0, -1])
def test_seed_must_be_an_integer(seed):
    with pytest.raises(ValueError):
        fa.SeedTable.from_rows(_with(_rows(), seed=seed))


@pytest.mark.parametrize('digest', ['', 'abc', 'A'*64, None])
def test_kpi_report_hash_must_be_a_full_sha256(digest):
    with pytest.raises(ValueError):
        fa.SeedTable.from_rows(_with(_rows(), kpi_report_sha256=digest))


def test_duplicate_or_foreign_seed_rejected():
    rows = _rows()
    with pytest.raises(ValueError):
        fa.SeedTable.from_rows(rows + [dict(rows[0])])
    foreign = fa.SeedTable.from_rows(rows + [dict(rows[0], seed=9999)])
    with pytest.raises(ValueError, match='protocol'):
        fa.analyze_campaign(foreign, PROTOCOL)


@pytest.mark.parametrize('changes', [{'algorithm': 'PPO'}, {'split': 'test_2025'},
                                     {'endpoint': 'co2_emissions'}, {'scenario': 'E4'}])
def test_rows_outside_the_protocol_are_refused(changes):
    rows = _rows()
    # E1 is scored on flexibility only: another KPI is not an additional replica.
    extra = dict(rows[0], **changes)
    table = fa.SeedTable.from_rows(rows + [extra])
    with pytest.raises(ValueError, match='protocol'):
        fa.analyze_campaign(table, PROTOCOL)


def test_missing_cell_is_incomplete():
    rows = _rows()
    del rows[5]
    report = fa.analyze_campaign(fa.SeedTable.from_rows(rows), PROTOCOL)
    assert report.decisions['scientifically_complete'] is False
    assert report.coverage['missing']


def test_valid_all_zero_gains_no_difference_complete():
    report = fa.analyze_campaign(fa.SeedTable.from_rows(_rows(lambda a, s, seed: 0.0)), PROTOCOL)
    assert report.decisions['scientifically_complete'] is True
    assert report.decisions['algorithm_difference'] == 'not_detected'
    assert report.decisions['winner_forced'] is False
    for family in report.test_families.values():
        assert all(row['p_value'] is not None and 0.0 <= row['p_value'] <= 1.0 for row in family)


def test_unidentified_scipy_error_is_not_p_one(monkeypatch):
    from scipy import stats

    def broken(*args, **kwargs):
        raise ValueError('unexpected internal failure')

    monkeypatch.setattr(stats, 'friedmanchisquare', broken)
    table = fa.SeedTable.from_rows(_rows())
    with pytest.raises(ValueError, match='unexpected internal failure'):
        fa.analyze_campaign(table, PROTOCOL)


def test_nan_p_value_with_real_differences_is_not_p_one(monkeypatch):
    from scipy import stats

    class Result:
        pvalue = math.nan
        statistic = math.nan

    monkeypatch.setattr(stats, 'friedmanchisquare', lambda *a, **k: Result())
    table = fa.SeedTable.from_rows(_rows())
    with pytest.raises(ValueError, match='p-value'):
        fa.analyze_campaign(table, PROTOCOL)
