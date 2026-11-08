"""SPEC-016 FR-016.1/FR-016.2 (D-V6-14 to D-V6-19): physical cooling inside the distillation of iquitos_v6.

Each measured block (peak and off-peak, D-V6-15) is closed exactly: cooling from capacity x part load /
COP, cut to the ceiling of the block, and the base as the rest, always positive. DHW stays modelled
inside the base, which it never exceeds. The iquitos_v5 residual distillation is left unchanged.
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import distill_building_loads as dl  # noqa: E402
from uc3m.application.dataset import hvac_capacity as hc  # noqa: E402

SPLIT = REPO/yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))['dataset_root']/'splits/train_2023'
BUILDINGS = (4, 5, 11)  # retail without capping, hotel with DHW, hospital capped in every month


@pytest.fixture(scope='module')
def distilled(tmp_path_factory):
    out = tmp_path_factory.mktemp('v6_distill')
    for name in ['schema.json', 'weather.csv'] + [f'Building_{b}.csv' for b in BUILDINGS]:
        shutil.copyfile(SPLIT/name, out/name)
    dl.configure_building_types(yaml.safe_load((REPO/'configs/dataset/building_types.yaml').read_text(encoding='utf-8')))
    norms = hc.load_hvac_norms(REPO/'configs/dataset/hvac_norms.yaml')
    weather = pd.read_csv(out/'weather.csv')
    original = {b: pd.read_csv(out/f'Building_{b}.csv') for b in BUILDINGS}
    results = {b: dl.calibrate_building_physical(b, dl.load_schema(out), weather, norms=norms, dataset_dir=out,
                                                 measurements=dl._DEFAULT_MEASUREMENTS)
               for b in BUILDINGS}
    return out, original, results


def _electric(out, schema, b):
    frame = pd.read_csv(out/f'Building_{b}.csv')
    cop = dl.citylearn_cooling_cop(pd.read_csv(out/'weather.csv')['outdoor_dry_bulb_temperature'].to_numpy(),
                                   *dl.physical_cop_params(schema, b))
    _, cop_dhw = dl.get_cop_params(schema, b, dl.DEFAULT_INVENTORY)
    return frame, frame['cooling_demand']/cop, frame['dhw_demand']/cop_dhw


@pytest.mark.parametrize('building', BUILDINGS)
def test_every_measured_block_is_closed_exactly(distilled, building):
    out, _, results = distilled
    frame, cooling, dhw = _electric(out, dl.load_schema(out), building)
    total = frame['non_shiftable_load'] + cooling + dhw
    peak = frame['hour'].isin(dl.PEAK_HOURS)
    bills = dl._DEFAULT_MEASUREMENTS.query('building_id == @building and year == 2023')
    for m in bills.itertuples():
        month = frame['month'] == m.month
        # the CSV is written with 6 decimals (%.6f): at most ~1e-3 kWh of rounding per block
        assert total[month & peak].sum() == pytest.approx(m.energia_punta_kwh, abs=1e-3)
        assert total[month & ~peak].sum() == pytest.approx(m.energia_fuera_punta_kwh, abs=1e-3)
    assert len(results[building].report) == len(bills)


@pytest.mark.parametrize('building', BUILDINGS)
def test_base_load_is_positive_every_hour_and_dhw_never_exceeds_it(distilled, building):
    out, _, _ = distilled
    frame, _, dhw = _electric(out, dl.load_schema(out), building)
    assert (frame['non_shiftable_load'] > 0).all()
    assert (dhw <= 0.5*(frame['non_shiftable_load'] + dhw) + 1e-5).all()  # 6-decimal CSV rounding


def test_capped_hospital_is_declared_and_uncapped_retail_keeps_its_physics(distilled):
    _, _, results = distilled
    assert len(results[11].capped_blocks) > 0
    assert any('capacity overestimated' in note for note in results[11].declarations)
    assert results[4].capped_blocks == [] and results[4].declarations == []


def test_hotel_dhw_is_kept_modelled(distilled):
    out, original, _ = distilled
    assert pd.read_csv(out/'Building_5.csv')['dhw_demand'].sum() > 0 and original[5]['dhw_demand'].sum() > 0


def test_capacity_and_cop_are_recorded_for_the_schema(distilled):
    _, _, results = distilled
    for result in results.values():
        assert result.capacity.kw_thermal > 0 and result.nominal_power_kw > 0
        assert result.nominal_power_kw == pytest.approx(result.capacity.kw_thermal/result.design_cop)


def test_bill_reader_drops_empty_rows_and_records_the_reported_total_discrepancy():
    measured = dl._DEFAULT_RAW_MEASUREMENTS
    assert len(measured[measured['building_id'] == 4]) <= 37                # B_04.csv has ~1e6 empty rows
    b11 = measured[(measured['building_id'] == 11) & (measured['reported_total_delta_kwh'].abs() > 1.0)]
    assert len(b11) > 0 and np.isfinite(b11['reported_total_delta_pct']).all()
