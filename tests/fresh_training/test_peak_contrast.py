"""SPEC-016 FR-016.8 (T4 of docs/plans/modulo3b_iquitos_v6.md): generated peak against the bill's peak.

Per building and month: the hourly peak of the dataset against the peak the bill implies, E / (LF x hours).
Only months with a load factor count; synthetic months (B01, D-V6-36) are reported but kept out of the
statistics. The threshold is the owner's: without it the gate reports and never passes or fails silently.
"""
import numpy as np
import pytest

from uc3m.application.dataset import construction as cn
from uc3m.application.dataset import peak_contrast as pc


def _record(building, month, energy, load_factor, provenance='measured', flags=()):
    return cn.MonthlyRecord(building, 2023, month, energy, 0.2*energy, 0.8*energy, provenance, 'billing',
                            'measured', ('x',), flags, load_factor, 1.0)


def test_each_month_compares_the_hourly_peak_with_the_bill_implied_peak():
    month = np.repeat([1, 2], [744, 672])
    load = np.full(len(month), 10.0)
    load[5], load[800] = 25.0, 12.0
    rows = pc.peak_contrast({3: load}, month, [_record(3, 1, 7440.0, 0.5), _record(3, 2, 6720.0, 0.8)])
    jan, feb = rows
    assert jan['implied_peak_kw'] == pytest.approx(7440.0/(0.5*744)) and jan['hourly_peak_kw'] == pytest.approx(25.0)
    assert jan['ratio'] == pytest.approx(25.0/20.0) and feb['ratio'] == pytest.approx(12.0/12.5)


def test_months_without_load_factor_or_flagged_are_skipped_and_synthetic_are_marked():
    month = np.repeat([1, 2, 3], 24)
    rows = pc.peak_contrast({1: np.ones(72), 2: np.ones(72)}, month,
                            [_record(2, 1, 24.0, None), _record(2, 2, 24.0, 0.5, flags=('partial_month_suspect',)),
                             _record(1, 3, 24.0, 0.5, provenance='synthetic')])
    assert [(r['building_id'], r['month']) for r in rows] == [(1, 3)] and rows[0]['synthetic'] is True
    summary = pc.summarize(rows, threshold=None)
    assert summary['months'] == 0 and summary['synthetic_months'] == 1


def test_the_gate_needs_the_owners_threshold():
    rows = [{'building_id': 3, 'year': 2023, 'month': m, 'ratio': r, 'synthetic': False}
            for m, r in ((1, 1.05), (2, 1.4), (3, 0.7))]
    pending = pc.summarize(rows, threshold=None)
    assert pending['status'] == 'threshold_pending_owner' and pending['passed'] is None
    assert pending['share_within'] == {'0.1': pytest.approx(1/3), '0.2': pytest.approx(1/3),
                                       '0.3': pytest.approx(2/3), '0.5': pytest.approx(1.0)}
    decided = pc.summarize(rows, threshold=0.3)
    assert decided['passed'] is False and [(f['building_id'], f['month']) for f in decided['outside']] == [(3, 2)]


def _month(hours=720):
    t = np.arange(hours)
    block = np.isin(t % 24, [18, 19, 20, 21, 22])
    base = 10.0 + 8.0*np.sin(2*np.pi*(t % 24)/24)
    other = np.where((t % 24 >= 10) & (t % 24 < 16), 5.0, 1.0)
    return base, other, block


def test_reshaping_brings_a_high_peak_to_the_threshold_and_keeps_each_block_energy():
    # FR-016.8: a month outside the threshold is re-distilled; only the base load's shape changes, mean-preserving
    # inside each bill block (D-V6-15), so the bill energies are reproduced exactly.
    base, other, block = _month()
    target = 0.9*float((base + other).max())      # flat base gives 16.7 of 19.0: reachable
    new, status = pc.reshape_month(base, other, block, target_peak_kw=target)
    assert status == 'resolved' and float((new + other).max()) == pytest.approx(target, rel=1e-6)
    assert new[block].sum() == pytest.approx(base[block].sum()) and new[~block].sum() == pytest.approx(base[~block].sum())
    assert np.all(new >= -1e-12)


def test_reshaping_raises_a_low_peak_without_negative_load():
    base, other, block = _month()
    target = 1.05*float((base + other).max())     # non-negative stretch tops at 20.5: reachable
    new, status = pc.reshape_month(base, other, block, target_peak_kw=target)
    assert status == 'resolved' and float((new + other).max()) == pytest.approx(target, rel=1e-6)
    assert np.all(new >= -1e-12) and new.sum() == pytest.approx(base.sum())


def test_a_peak_the_base_cannot_reach_is_declared_unresolved_not_forced():
    base, other, block = _month()
    flat_floor = float((np.where(block, base[block].mean(), base[~block].mean()) + other).max())
    new, status = pc.reshape_month(base, other, block, target_peak_kw=0.5*flat_floor)
    assert status == 'unresolved' and new[block].sum() == pytest.approx(base[block].sum())


def test_only_peaks_above_the_bill_fail_and_low_ones_are_reported():
    # D-V6-48: the bill's maximum demand is a 15-minute value and the dataset is hourly, so an hourly peak below it
    # is expected; only a generated peak above (1 + threshold) x the bill-implied peak fails the gate.
    rows = [{'building_id': 3, 'year': 2023, 'month': m, 'ratio': r, 'synthetic': False}
            for m, r in ((1, 1.05), (2, 1.6), (3, 0.3))]
    summary = pc.summarize(rows, threshold=0.5)
    assert summary['passed'] is False and [(f['month']) for f in summary['outside']] == [2]
    assert [f['month'] for f in summary['below']] == [3] and '15-minute' in summary['below_note']
    assert pc.summarize([rows[0], rows[2]], threshold=0.5)['passed'] is True
