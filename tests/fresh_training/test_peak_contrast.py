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
