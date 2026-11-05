"""SPEC-014: the PV bound by load, the blocking integrity gate and what the audit really checks."""
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import audit_citylearn_csv_integrity as integrity  # noqa: E402
import size_der_microgrids as sd  # noqa: E402

BUILDER = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')
ROWS = 3


def test_load_bound_is_the_capacity_that_produces_the_allowed_share_of_the_annual_load():
    assert sd.load_bound_kwp(1500.0, [1000.0, 500.0], 1.0) == pytest.approx(1.0)
    assert sd.load_bound_kwp(1500.0, [1000.0, 500.0], 0.5) == pytest.approx(0.5)


@pytest.mark.parametrize('load, per_kwp, ratio', [(100.0, [0.0], 1.0), (100.0, [1.0], 0.0), (100.0, [1.0], -1.0)])
def test_load_bound_refuses_inputs_that_would_silently_remove_the_limit(load, per_kwp, ratio):
    with pytest.raises(ValueError):
        sd.load_bound_kwp(load, per_kwp, ratio)


def test_a_building_without_load_gets_no_pv():
    assert sd.load_bound_kwp(0.0, [1000.0], 1.0) == 0.0


def test_the_limit_is_a_single_declared_design_value():
    entry = sd.load_economics()['pv']['max_pv_to_load_ratio']
    assert entry['value'] == 1.0 and entry['status'] == 'design_rule' and entry['source']


@pytest.mark.parametrize('lp, roof, load, expected', [
    (10.0, 10.0, 50.0, 'area'), (10.0, 50.0, 10.0, 'load'), (5.0, 10.0, 50.0, None), (10.0, 10.0, 10.0, 'area')])
def test_the_report_names_which_bound_limited_the_capacity(lp, roof, load, expected):
    assert sd.binding_pv_bound(lp, roof, load) == expected


def _rows(*ratios):
    return {str(i): {'pv_to_load_ratio_2023': ratio} for i, ratio in enumerate(ratios)}


def test_the_gate_passes_only_when_every_building_respects_the_limit():
    assert sd.pv_to_load_gate(_rows(0.2, 1.0), 1.0) is True
    assert sd.pv_to_load_gate(_rows(0.2, 1.5), 1.0) is False


def test_the_gate_fails_closed_on_missing_values():
    assert sd.pv_to_load_gate({}, 1.0) is False
    assert sd.pv_to_load_gate(_rows(None), 1.0) is False


def test_the_gate_allows_only_the_measured_inverter_difference():
    # kWp comes from a reference array; the real array picks another inverter, within this margin.
    assert sd.pv_to_load_gate(_rows(1.0 + sd.PV_RATIO_MARGIN), 1.0) is True
    assert sd.pv_to_load_gate(_rows(1.0 + 2*sd.PV_RATIO_MARGIN), 1.0) is False


def test_the_builder_applies_the_bound_and_both_gates():
    assert 'sd.load_bound_kwp(' in BUILDER
    assert "'pv_to_load_bounded': sd.pv_to_load_gate(" in BUILDER
    assert "'csv_integrity':" in BUILDER
    # Every LP receives the combined bound; a roof-only solve would bypass the limit.
    assert 'sd.solve_microgrids(load, per_kwp, price, roof,' not in BUILDER


def _dataset(tmp_path, monkeypatch, *, price=0.1, pricing_files=('pricing_1.csv',), reference='pricing_1.csv',
             departure=(-1, 61, 60)):
    monkeypatch.setattr(integrity, 'EXPECTED_ROWS', ROWS)
    building = dict.fromkeys(integrity.BUILDING_COLUMNS, [0, 0, 0])
    pd.DataFrame(building).to_csv(tmp_path/'Building_1.csv', index=False)
    pd.DataFrame({f'w{i}': [0, 0, 0] for i in range(integrity.WEATHER_COLUMNS)}).to_csv(tmp_path/'weather.csv', index=False)
    pd.DataFrame({'carbon_intensity': [0.5]*ROWS}).to_csv(tmp_path/'carbon_intensity.csv', index=False)
    for name in pricing_files:
        pd.DataFrame({column: [price]*ROWS for column in integrity.PRICING_COLUMNS}).to_csv(tmp_path/name, index=False)
    pd.DataFrame({'electric_vehicle_charger_state': [3, 1, 1], 'electric_vehicle_id': ['a', 'a', 'a'],
                  'electric_vehicle_departure_time': list(departure), 'electric_vehicle_required_soc_departure': [-0.1, 90, 90],
                  'electric_vehicle_estimated_arrival_time': [-1, -1, -1],
                  'electric_vehicle_estimated_soc_arrival': [50, -0.1, -0.1]}).to_csv(tmp_path/'charger_1_1.csv', index=False)
    config = {'energy_simulation': 'Building_1.csv', 'chargers': {'c': {'charger_simulation': 'charger_1_1.csv'}}}
    if reference:
        config['pricing'] = reference
    (tmp_path/'schema.json').write_text(json.dumps({'buildings': {'Building_1': config}}), encoding='utf-8')
    return tmp_path


def _issues(report, text):
    return [issue for issue in report['issues'] if text in issue]


def test_a_per_building_tariff_needs_no_shared_pricing_file(tmp_path, monkeypatch):
    report = integrity.audit(_dataset(tmp_path, monkeypatch))
    assert report['status'] == 'ok', report['issues']
    assert 'pricing_1.csv' in report['files'] and 'pricing.csv' not in report['files']


def test_a_negative_tariff_is_detected(tmp_path, monkeypatch):
    report = integrity.audit(_dataset(tmp_path, monkeypatch, price=-0.1))
    assert report['status'] == 'failed' and _issues(report, 'valores negativos')


def test_a_missing_tariff_is_detected(tmp_path, monkeypatch):
    report = integrity.audit(_dataset(tmp_path, monkeypatch, pricing_files=()))
    assert report['status'] == 'failed' and _issues(report, 'pricing_1.csv')


def test_an_incomplete_tariff_is_detected(tmp_path, monkeypatch):
    dataset = _dataset(tmp_path, monkeypatch)
    pd.read_csv(dataset/'pricing_1.csv').head(2).to_csv(dataset/'pricing_1.csv', index=False)
    report = integrity.audit(dataset)
    assert report['status'] == 'failed' and _issues(report, 'filas')


def test_a_schema_without_building_tariffs_still_needs_the_shared_file(tmp_path, monkeypatch):
    report = integrity.audit(_dataset(tmp_path, monkeypatch, pricing_files=(), reference=None))
    assert report['status'] == 'failed' and _issues(report, 'pricing.csv')


def test_a_weekend_stay_is_a_valid_departure_countdown(tmp_path, monkeypatch):
    # The pilot's motorcycles stay from Friday to Monday: 61 hours left is real, not an error.
    report = integrity.audit(_dataset(tmp_path, monkeypatch, departure=(-1, 61, 60)))
    assert not _issues(report, 'electric_vehicle_departure_time')


def test_a_countdown_longer_than_a_week_is_rejected(tmp_path, monkeypatch):
    report = integrity.audit(_dataset(tmp_path, monkeypatch, departure=(-1, 169, 168)))
    assert _issues(report, 'electric_vehicle_departure_time')
