"""SPEC-016 T2 of docs/plans/modulo3b_iquitos_v6.md: v6 loads in the builder.

The washing machines leave the schema, the files and the actions (their energy is base load in v6, D-V6-1);
the physical distillation (D-V6-14 to D-V6-20) replaces the residual one and fixes each building's cooling
power at its capacity / design COP, with the capped blocks declared. CityLearn v3 loads the result.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import build_v6_parts as v6  # noqa: E402
import distill_building_loads as dl  # noqa: E402
from uc3m.application.dataset import hvac_capacity as hc  # noqa: E402

CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SPLIT = REPO/'data/campaigns/iquitos_v5/splits/train_2023'   # a v5 split: it still has washing machines


@pytest.fixture(scope='module')
def dataset(tmp_path_factory):
    out = tmp_path_factory.mktemp('v6') / 'train_2023'
    shutil.copytree(SPLIT, out)
    return out


def test_washing_machines_leave_schema_files_and_actions(dataset):
    schema = json.loads((dataset/'schema.json').read_text(encoding='utf-8'))
    assert any('washing_machines' in b for b in schema['buildings'].values())     # v5 has them
    removed = v6.remove_washing_machines(dataset, schema)
    assert removed and not any('washing_machines' in b for b in schema['buildings'].values())
    assert not list(dataset.glob('Washing_Machine_*.csv'))
    (dataset/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    from citylearn.v3.environment import make_citylearn_v3_env
    env = make_citylearn_v3_env(schema_path=dataset/'schema.json', scenario='E1', seed=0, episode_time_steps=24)
    try:
        names = [n for b in env.env.buildings for n in b.active_actions]
        assert names and not any('washing_machine' in n for n in names)
        env.reset()
        _, rewards, _, _, _ = env.step({a: np.zeros(env.action_space(a).shape, dtype=np.float32)
                                        for a in env.possible_agents})
        assert all(np.isfinite(float(r)) for r in rewards.values())
    finally:
        env.close()


def test_physical_distillation_fixes_the_cooling_power_and_declares_capped_blocks(dataset):
    schema = json.loads((dataset/'schema.json').read_text(encoding='utf-8'))
    dl.configure_building_types(yaml.safe_load((REPO/'configs/dataset/building_types.yaml').read_text(encoding='utf-8')))
    norms = hc.load_hvac_norms(REPO/'configs/dataset/hvac_norms.yaml')
    weather = pd.read_csv(dataset/'weather.csv')
    results = v6.distill_v6(dataset, schema, weather, norms=norms, measurements=dl._DEFAULT_MEASUREMENTS,
                            buildings=(4, 11))
    for b in (4, 11):
        cooling = schema['buildings'][f'Building_{b}']['cooling_device']
        assert cooling['autosize'] is False
        assert cooling['attributes']['nominal_power'] == pytest.approx(results[b].nominal_power_kw, rel=1e-6)
    assert results[11].capped_blocks and not results[4].capped_blocks             # hospital capped, retail not
    flags = v6.capped_block_flags(results)
    assert {f['building_id'] for f in flags} == {11} and all(f['flag'] == 'cooling_capped_by_bill' for f in flags)


def test_the_report_carries_the_monthly_closure_against_the_bill(dataset):
    # write_outputs reads delta_% (v5 contract): generated electricity of each month vs its bill, from the CSV.
    schema = json.loads((dataset/'schema.json').read_text(encoding='utf-8'))
    norms = hc.load_hvac_norms(REPO/'configs/dataset/hvac_norms.yaml')
    results = v6.distill_v6(dataset, schema, pd.read_csv(dataset/'weather.csv'), norms=norms,
                            measurements=dl._DEFAULT_MEASUREMENTS, buildings=(4,))
    report = results[4].report
    assert 'delta_%' in report.columns and len(report) == 12
    assert report['delta_%'].abs().max() < 1e-3


def test_the_v6_bess_is_sized_for_surplus_vehicles_and_the_peak_block():
    # D-V6-7 and D-V6-30: one battery stores the PV surplus and the EV energy the PV does not cover, and shaves
    # shift_fraction of the largest peak-block import shifting it to off-peak (size_bess, catalog model).
    from uc3m.application.dataset import bess_sizing as bs
    model = bs.select_catalog_model(bs.load_battery_catalog(REPO/'CityLearn/data/misc/battery_choices.yaml'))
    hours = np.arange(24*7)
    load = np.full(len(hours), 20.0)
    pv = np.where((hours % 24 >= 9) & (hours % 24 < 15), 35.0, 0.0)
    ev = np.where(hours % 24 == 10, 7.04, 0.0)
    block = np.isin(hours % 24, [18, 19, 20, 21, 22])
    size = v6.size_v6_bess(load, pv, ev, block, model=model, shift_fraction=0.2, ev_charging_power_kw=7.04)
    expected = bs.size_bess(surplus_kwh_h=np.clip(pv - load, 0, None), ev_kwh_h=ev, ev_charging_power_kw=7.04,
                            model=model, block_import_kwh_h=np.clip(load + ev - pv, 0, None), peak_block_h=block,
                            shift_fraction=0.2)
    assert size == expected and size.capacity_kwh > 0 and size.shaved_kw == pytest.approx(0.2*20.0)
    attributes = v6.bess_attributes(size)
    assert attributes['capacity'] == size.capacity_kwh and attributes['nominal_power'] == size.nominal_power_kw
    assert attributes['efficiency'] == model.efficiency and attributes['depth_of_discharge'] == model.depth_of_discharge


def test_redistillation_rewrites_only_the_base_of_months_outside_the_threshold(tmp_path):
    # FR-016.8 and D-V6-47: months whose generated peak is outside +/-threshold of the bill-implied peak get their
    # base reshaped to the threshold edge; block energies stay; months inside are untouched.
    from uc3m.application.dataset import construction as cn
    hours = 24*59                                                    # January and February 2023
    t = np.arange(hours)
    month = np.where(t < 744, 1, 2)
    base = 10.0 + 8.0*np.sin(2*np.pi*(t % 24)/24)
    pd.DataFrame({'month': month, 'hour': t % 24, 'day_type': 1, 'non_shiftable_load': base,
                  'cooling_demand': 0.0, 'dhw_demand': 0.0}).to_csv(tmp_path/'Building_3.csv', index=False)
    other = np.ones(hours)
    peak = float((base + other).max())
    energy_jan, energy_feb = float((base + other)[month == 1].sum()), float((base + other)[month == 2].sum())
    targets = [cn.MonthlyRecord(3, 2023, 1, energy_jan, 0.2*energy_jan, 0.8*energy_jan, 'measured', 'billing', 'measured',
                                ('x',), (), energy_jan/(744*peak/1.6), 1.0),                 # implied peak/1.6, LF 0.93
               cn.MonthlyRecord(3, 2023, 2, energy_feb, 0.2*energy_feb, 0.8*energy_feb, 'measured', 'billing', 'measured',
                                ('x',), (), energy_feb/(672*peak), 1.0)]                    # inside
    rows = v6.redistill_peaks(tmp_path, buildings=(3,), targets=targets, threshold=0.5, peak_hours={18, 19, 20, 21, 22},
                              other_kw=lambda b: other, years=np.full(hours, 2023))
    new = pd.read_csv(tmp_path/'Building_3.csv')['non_shiftable_load'].to_numpy()
    jan_implied = peak/1.6
    assert [(r['month'], r['status']) for r in rows] == [(1, 'resolved')]
    # just inside the edge, so the 6-decimal CSV does not push it out (trial4 left 31 months at 1.5000001)
    assert float((new + other)[month == 1].max()) == pytest.approx(1.5*(1 - 1e-3)*jan_implied, rel=1e-6)
    assert np.allclose(new[month == 2], base[month == 2])
    assert new[month == 1].sum() == pytest.approx(base[month == 1].sum())


def test_redistillation_leaves_low_peaks_alone(tmp_path):
    # D-V6-48: a generated peak below the bill's (15-minute maximum demand vs hourly data) is not reshaped.
    from uc3m.application.dataset import construction as cn
    hours = 744
    t = np.arange(hours)
    base = 10.0 + 8.0*np.sin(2*np.pi*(t % 24)/24)
    pd.DataFrame({'month': 1, 'hour': t % 24, 'day_type': 1, 'non_shiftable_load': base,
                  'cooling_demand': 0.0, 'dhw_demand': 0.0}).to_csv(tmp_path/'Building_3.csv', index=False)
    energy = float((base + 1.0).sum())
    peak = float((base + 1.0).max())
    target = [cn.MonthlyRecord(3, 2023, 1, energy, 0.2*energy, 0.8*energy, 'measured', 'billing', 'measured',
                               ('x',), (), energy/(hours*peak*3.0), 1.0)]                  # bill peak 3x higher
    rows = v6.redistill_peaks(tmp_path, buildings=(3,), targets=target, threshold=0.5, peak_hours={18, 19, 20, 21, 22},
                              other_kw=lambda b: np.ones(hours), years=np.full(hours, 2023))
    assert rows == [] and np.allclose(pd.read_csv(tmp_path/'Building_3.csv')['non_shiftable_load'], base)


def test_redistillation_reshapes_cooling_too_when_the_base_alone_cannot(tmp_path):
    # D-V6-55: a cooling-driven peak that flattening the base cannot bring under the edge is flattened together with
    # the base inside each bill block (same factor per hour); every block keeps its energy, so the bill holds.
    from uc3m.application.dataset import construction as cn
    hours = 744
    t = np.arange(hours)
    hour = t % 24
    base = np.full(hours, 2.0)
    cooling_e = np.where((hour >= 12) & (hour < 15), 30.0, 0.5)          # a sharp afternoon cooling peak
    cop = np.full(hours, 3.0)
    pd.DataFrame({'month': 1, 'hour': hour, 'day_type': 1, 'non_shiftable_load': base,
                  'cooling_demand': cooling_e*cop, 'dhw_demand': 0.0}).to_csv(tmp_path/'Building_9.csv', index=False)
    total = base + cooling_e
    energy, peak = float(total.sum()), float(total.max())
    target = [cn.MonthlyRecord(9, 2023, 1, energy, 0.2*energy, 0.8*energy, 'measured', 'billing', 'measured',
                               ('x',), (), energy/(hours*peak/2.0), 1.0)]                # implied peak = half
    rows = v6.redistill_peaks(tmp_path, buildings=(9,), targets=target, threshold=0.5, peak_hours={18, 19, 20, 21, 22},
                              other_kw=lambda b: cooling_e, years=np.full(hours, 2023), cooling_cop=lambda b: cop)
    assert [r['status'] for r in rows] == ['resolved_with_cooling']
    out = pd.read_csv(tmp_path/'Building_9.csv')
    new_total = out['non_shiftable_load'].to_numpy() + out['cooling_demand'].to_numpy()/cop
    assert float(new_total.max()) == pytest.approx(1.5*(1 - 1e-3)*peak/2.0, rel=1e-5)
    block = np.isin(hour, [18, 19, 20, 21, 22])
    for part in (block, ~block):
        assert new_total[part].sum() == pytest.approx(total[part].sum(), rel=1e-6)
    assert (out['cooling_demand'] >= 0).all() and (out['non_shiftable_load'] > 0).all()


def test_indoor_temperature_and_comfort_reference_no_worse_than_today(tmp_path):
    # D-V6-53/54: the uncontrolled indoor temperature is the 5R1C response to the billed cooling, and the hourly set
    # point is max(24, that temperature - band), so the comfort limit is max(26 C, the temperature as billed).
    hours = 72
    t = np.arange(hours)
    occupied = ((t % 24 >= 8) & (t % 24 < 18)).astype(float)
    pd.DataFrame({'month': 1, 'hour': t % 24, 'day_type': 1, 'non_shiftable_load': 20.0, 'cooling_demand': 15.0*occupied,
                  'dhw_demand': 0.0, 'occupant_count': 40.0*occupied,
                  'indoor_dry_bulb_temperature': 24.0}).to_csv(tmp_path/'Building_1.csv', index=False)
    weather = pd.DataFrame({'outdoor_dry_bulb_temperature': 31.0, 'outdoor_relative_humidity': 70.0,
                            'diffuse_solar_irradiance': 100.0*occupied, 'direct_solar_irradiance': 400.0*occupied})
    schema = {'buildings': {'Building_1': {'dynamics': {'type': 'citylearn.v3.thermal.ISO13790Dynamics', 'attributes': {
        'floor_area_m2': 800.0, 'envelope_w_m2k': 2.0, 'solar_aperture_fraction': 0.05, 'ventilation_m3_s': 0.3,
        'mass_class': 'medium', 'set_point': 24.0, 'pressure_kpa': 100.0, 'electric_gain_fraction': 0.5}}}}}
    report = v6.write_indoor_temperature(tmp_path, schema, weather, buildings=(1,), band_c=2.0)
    out = pd.read_csv(tmp_path/'Building_1.csv')
    theta, set_point = out['indoor_dry_bulb_temperature'].to_numpy(), out['indoor_dry_bulb_temperature_cooling_set_point'].to_numpy()
    busy = occupied > 0
    assert np.allclose(set_point[busy] + 2.0, np.maximum(26.0, theta[busy]), atol=1e-5)
    assert np.allclose(set_point[~busy], 24.0)
    assert report[1]['comfort_reference'].startswith('max(24 C + band')
