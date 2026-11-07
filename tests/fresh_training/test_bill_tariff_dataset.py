"""SPEC-016 FR-016.7 and D-V6-8: the power tariff lives in the dataset and the hourly bill cost adds up.

The reward must not read project files, so each building gets an hourly tariff file with the energy
rate, the demand rate and the 18:00-23:00 block. The hourly cost is energy x price plus the increase of
the capacity charge when the power exceeds the peak the month carried in the block; summed over the
month it equals the bill without the fixed charge. The first hour of a month starts from a peak of 0.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from uc3m.application.dataset import bill_tariff as bt
from uc3m.application.evaluation.bill_cost import load_bill_tariffs

REPO = Path(__file__).resolve().parents[2]
RATES = load_bill_tariffs(REPO/'data/tariffs/osinergmin/bill_tariffs.csv')


def _calendar(year=2023):
    stamps = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:00', freq='h')
    return stamps.year.to_numpy(), stamps.month.to_numpy(), stamps.hour.to_numpy()


def test_hourly_tariff_file_carries_the_official_rates_and_the_block():
    year, month, hour = _calendar()
    table = bt.hourly_bill_tariff(RATES, building=11, year=year, month=month, hour=hour)
    assert list(table) == list(bt.COLUMNS) and all(len(table[c]) == 8760 for c in bt.COLUMNS)
    for m in (1, 6, 12):
        rate = RATES[(11, 2023, m)]
        assert np.allclose(table['energy_usd_kwh'][month == m], rate.energy_usd_kwh)
        assert np.allclose(table['demand_usd_kw_month'][month == m], rate.demand_usd_kw_month)
    assert set(hour[table['peak_block'] == 1]) == {18, 19, 20, 21, 22}


def test_missing_rate_is_rejected_never_zero():
    year, month, hour = _calendar(2031)
    with pytest.raises(ValueError, match='tariff'):
        bt.hourly_bill_tariff(RATES, building=11, year=year, month=month, hour=hour)


def test_hourly_cost_adds_up_to_the_bill_without_fixed_charge():
    rng = np.random.default_rng(0)
    hours = np.arange(24*31)
    in_block = np.isin(hours % 24, [18, 19, 20, 21, 22])
    power = rng.uniform(-20, 120, len(hours))                    # negative: export, credited (net billing)
    price, demand = 0.11, 13.8
    costs, peak = [], 0.0                                        # first hour of the month: no previous peak
    for p, block in zip(power, in_block):
        cost, peak = bt.incremental_bill_cost(p, energy_usd_kwh=price, demand_usd_kw_month=demand,
                                              peak_so_far_kw=peak, in_block=bool(block))
        costs.append(cost)
    expected = power.sum()*price + demand*max(0.0, power[in_block].max())
    assert sum(costs) == pytest.approx(expected, rel=1e-12)


def test_first_block_hour_of_a_month_charges_its_whole_power():
    cost, peak = bt.incremental_bill_cost(50.0, energy_usd_kwh=0.1, demand_usd_kw_month=10.0,
                                          peak_so_far_kw=0.0, in_block=True)
    assert cost == pytest.approx(50*0.1 + 50*10.0) and peak == 50.0
    cost, peak = bt.incremental_bill_cost(40.0, energy_usd_kwh=0.1, demand_usd_kw_month=10.0,
                                          peak_so_far_kw=50.0, in_block=True)
    assert cost == pytest.approx(4.0) and peak == 50.0          # below the month's peak: energy only
    cost, peak = bt.incremental_bill_cost(500.0, energy_usd_kwh=0.1, demand_usd_kw_month=10.0,
                                          peak_so_far_kw=50.0, in_block=False)
    assert cost == pytest.approx(50.0) and peak == 50.0         # outside the block: no capacity charge


def test_tariff_files_are_written_for_every_building(tmp_path):
    year, month, hour = _calendar()
    written = bt.write_bill_tariff_files(tmp_path, RATES, buildings=range(1, 18), year=year, month=month, hour=hour)
    assert sorted(written) == list(range(1, 18))
    frame = pd.read_csv(tmp_path/'bill_tariff_Building_5.csv')
    assert len(frame) == 8760 and list(frame.columns) == list(bt.COLUMNS)
    assert frame['energy_usd_kwh'].iloc[0] == pytest.approx(RATES[(5, 2023, 1)].energy_usd_kwh)
