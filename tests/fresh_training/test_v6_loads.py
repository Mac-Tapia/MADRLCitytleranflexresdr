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
SPLIT = REPO/CAMPAIGN['dataset_root']/'splits/train_2023'


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
