"""SPEC-016 FR-016.1/FR-016.2, D-V6-14, D-V6-18: hourly cooling from physics with the bill as ceiling.

The monthly bills of Iquitos cannot calibrate the cooling share (2 C of thermal range); they bound it.
Cooling = capacity x part load / COP, cut to bill - base floor when it exceeds it (building flagged).
Base = bill - cooling, spread with its hourly shape and always positive. The implied daily base must
be stable between months (CV <= 15 %), otherwise the building is flagged.
"""
import numpy as np
import pytest

from uc3m.application.dataset import cooling_calibration as cc

HOURS = 24*30


def _months(n_months):
    return np.repeat(np.arange(n_months), HOURS)


def _calibrate(bills, plr=0.5, capacity=10.0, cop=3.0, base_shape=None, floor=0.30, cv_limit=15.0):
    months = _months(len(bills))
    shape = np.ones(len(months)) if base_shape is None else base_shape
    return cc.calibrate_cooling(capacity_kw_th=capacity, cop_h=np.full(len(months), cop),
                                plr_h=np.full(len(months), plr), month_h=months,
                                bill_kwh=dict(enumerate(bills)), base_shape_h=shape,
                                base_floor_fraction=floor, base_cv_limit_pct=cv_limit)


def test_part_load_follows_the_enthalpy_difference_and_the_schedule():
    h_out = np.array([40.0, 48.0, 66.5, 85.0, 90.0])
    schedule = np.array([1.0, 1.0, 0.5, 1.0, 1.0])
    plr = cc.part_load_ratio(h_out, indoor_enthalpy=48.0, design_enthalpy=85.0, schedule=schedule)
    np.testing.assert_allclose(plr, [0.0, 0.0, 0.25, 1.0, 1.0])


def test_cooling_and_base_reproduce_every_bill_and_base_is_always_positive():
    result = _calibrate([3000.0, 3100.0, 2950.0])
    for month, bill in enumerate([3000.0, 3100.0, 2950.0]):
        hours = result.month_h == month
        assert result.cooling_kwh[hours].sum() + result.base_kwh[hours].sum() == pytest.approx(bill, abs=1e-6)
    assert np.all(result.base_kwh > 0)


def test_physical_cooling_below_the_ceiling_is_kept_unchanged():
    result = _calibrate([3000.0, 3000.0])                      # physics: 0.5 x 10 / 3 x 720 h = 1200 kWh
    np.testing.assert_allclose(result.cooling_kwh, 0.5*10.0/3.0)
    assert result.capped_months == [] and result.passed and result.flags == []


def test_cooling_above_the_ceiling_is_cut_and_the_building_flagged():
    result = _calibrate([1000.0, 3000.0])                      # ceiling of month 0: 1000 x 0.70 = 700 kWh
    month0 = result.month_h == 0
    assert result.cooling_kwh[month0].sum() == pytest.approx(700.0)
    assert result.base_kwh[month0].sum() == pytest.approx(300.0)
    assert result.capped_months == [0] and not result.passed
    assert any('capped' in flag for flag in result.flags)


def test_unstable_implied_base_flags_the_building():
    result = _calibrate([1300.0, 3000.0, 6000.0])               # month 0 capped; base 390, 1800, 4800 kWh
    assert result.base_cv_pct > 15.0 and not result.passed
    assert any('base' in flag and 'CV' in flag for flag in result.flags)


def test_base_follows_its_hourly_shape_inside_each_month():
    shape = np.tile(np.r_[np.full(8, 1.0), np.full(16, 3.0)], 30)
    result = _calibrate([3000.0], base_shape=shape)
    base = result.base_kwh
    assert base[8]/base[0] == pytest.approx(3.0) and base.sum() == pytest.approx(3000.0 - 1200.0)


def test_missing_bill_or_non_positive_shape_is_rejected():
    months = _months(2)
    with pytest.raises(ValueError, match='bill'):
        cc.calibrate_cooling(capacity_kw_th=10.0, cop_h=np.full(len(months), 3.0), plr_h=np.full(len(months), 0.5),
                             month_h=months, bill_kwh={0: 3000.0}, base_shape_h=np.ones(len(months)),
                             base_floor_fraction=0.3, base_cv_limit_pct=15.0)
    with pytest.raises(ValueError, match='shape'):
        _calibrate([3000.0], base_shape=np.r_[np.zeros(1), np.ones(HOURS - 1)])
    with pytest.raises(ValueError, match='floor'):
        _calibrate([3000.0], floor=0.0)
