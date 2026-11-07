"""SPEC-016 FR-016.6 and D-V6-7: BESS for the solar surplus and the vehicles, on the day of largest surplus.

Energy = daily PV surplus + daily EV energy not covered directly by PV, on the design-year day of
largest surplus, over the usable window and the efficiency of a commercial model of CityLearn's catalog.
Power = max(hourly surplus, EV charging power). Units of that model are connected in parallel until
both are covered. Without surplus and without vehicles there is no battery.
"""
from pathlib import Path

import numpy as np
import pytest

from uc3m.application.dataset import bess_sizing as bs

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO/'CityLearn/data/misc/battery_choices.yaml'


def _day(values):
    return np.asarray(values, dtype=float)


def test_the_catalog_model_is_the_first_with_every_parameter_declared():
    model = bs.select_catalog_model(bs.load_battery_catalog(CATALOG))
    assert model.name == 'PowerPlus LiFe2433P'
    assert (model.capacity_kwh, model.nominal_power_kw, model.efficiency, model.depth_of_discharge) == \
        (3.3, 1.61, 0.96, 1.0)
    assert model.loss_coefficient == pytest.approx(0.00159817)


def test_energy_is_sized_on_the_day_of_largest_surplus():
    model = bs.BatteryModel('unit', capacity_kwh=10.0, nominal_power_kw=5.0, efficiency=0.9, depth_of_discharge=0.8,
                            loss_coefficient=0.0)
    surplus = np.zeros(48)
    surplus[10:14] = 3.0
    surplus[24 + 10:24 + 14] = 6.0                                   # day 2: 24 kWh
    ev = np.zeros(48)
    ev[24 + 18:24 + 20] = 4.0                                        # 8 kWh after sunset
    size = bs.size_bess(surplus_kwh_h=surplus, ev_kwh_h=ev, ev_charging_power_kw=7.4, model=model)
    assert size.design_day == 1
    target = (24.0 + 8.0)/(0.9*0.8)
    assert size.required_kwh == pytest.approx(target)
    assert size.units == int(np.ceil(max(target/10.0, 7.4/5.0)))
    assert size.capacity_kwh == pytest.approx(size.units*10.0) and size.nominal_power_kw == pytest.approx(size.units*5.0)
    assert size.nominal_power_kw >= max(6.0, 7.4)


def test_ev_energy_covered_directly_by_pv_is_not_stored_twice():
    model = bs.BatteryModel('unit', capacity_kwh=1.0, nominal_power_kw=1.0, efficiency=1.0, depth_of_discharge=1.0,
                            loss_coefficient=0.0)
    surplus = np.zeros(24)
    surplus[12] = 5.0
    ev = np.zeros(24)
    ev[12] = 2.0                                                     # 2 kWh at noon from PV
    ev[20] = 3.0
    size = bs.size_bess(surplus_kwh_h=surplus, ev_kwh_h=ev, ev_charging_power_kw=3.0, model=model)
    assert size.required_kwh == pytest.approx(5.0 + 3.0)                              # surplus + uncovered EV


def test_no_surplus_and_no_vehicles_gives_no_battery():
    model = bs.select_catalog_model(bs.load_battery_catalog(CATALOG))
    size = bs.size_bess(surplus_kwh_h=np.zeros(48), ev_kwh_h=np.zeros(48), ev_charging_power_kw=0.0, model=model)
    assert size.units == 0 and size.capacity_kwh == 0.0 and size.nominal_power_kw == 0.0


def test_negative_or_misaligned_series_are_rejected():
    model = bs.select_catalog_model(bs.load_battery_catalog(CATALOG))
    with pytest.raises(ValueError):
        bs.size_bess(surplus_kwh_h=-np.ones(24), ev_kwh_h=np.zeros(24), ev_charging_power_kw=0.0, model=model)
    with pytest.raises(ValueError):
        bs.size_bess(surplus_kwh_h=np.zeros(24), ev_kwh_h=np.zeros(23), ev_charging_power_kw=0.0, model=model)
    with pytest.raises(ValueError):
        bs.size_bess(surplus_kwh_h=np.zeros(25), ev_kwh_h=np.zeros(25), ev_charging_power_kw=0.0, model=model)


def test_peak_shifting_sizes_the_battery_when_it_needs_more_than_the_surplus():
    # D-V6-30: energy = max(surplus + uncovered EV; shifted peak-block energy), power = max of the three.
    model = bs.BatteryModel('unit', capacity_kwh=10.0, nominal_power_kw=5.0, efficiency=0.9, depth_of_discharge=0.8,
                            loss_coefficient=0.0)
    hours = np.arange(48)
    surplus = np.where(hours % 24 == 12, 2.0, 0.0)                      # 2 kWh/day of surplus
    block = np.isin(hours % 24, [18, 19, 20, 21, 22])
    block_import = np.where(block, 100.0, 0.0)
    block_import[24 + 20] = 150.0                                       # largest block peak of the year
    size = bs.size_bess(surplus_kwh_h=surplus, ev_kwh_h=np.zeros(48), ev_charging_power_kw=0.0, model=model,
                        block_import_kwh_h=block_import, peak_block_h=block, shift_fraction=0.20)
    shaved_kw = 0.20*150.0
    assert size.shaved_kw == pytest.approx(shaved_kw)
    assert size.required_kwh == pytest.approx(max(2.0/(0.9*0.8), shaved_kw*5/(0.9*0.8)))
    assert size.required_kw == pytest.approx(shaved_kw) and size.sizing_function == 'peak_shift'


def test_surplus_still_sizes_the_battery_when_it_dominates():
    model = bs.BatteryModel('unit', capacity_kwh=10.0, nominal_power_kw=5.0, efficiency=1.0, depth_of_discharge=1.0,
                            loss_coefficient=0.0)
    hours = np.arange(24)
    surplus = np.where((hours >= 10) & (hours < 15), 20.0, 0.0)        # 100 kWh of surplus
    block = np.isin(hours, [18, 19, 20, 21, 22])
    size = bs.size_bess(surplus_kwh_h=surplus, ev_kwh_h=np.zeros(24), ev_charging_power_kw=0.0, model=model,
                        block_import_kwh_h=np.where(block, 10.0, 0.0), peak_block_h=block, shift_fraction=0.20)
    assert size.required_kwh == pytest.approx(100.0) and size.sizing_function == 'surplus_ev'
