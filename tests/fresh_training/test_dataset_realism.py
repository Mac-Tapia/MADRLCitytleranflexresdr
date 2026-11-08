"""Realism contract of the active Iquitos campaign dataset.

Owner criteria (2026-11-01): every dataset calculation is realistic and traceable;
Iquitos has no charging stations and no mass EV fleet (only a 2-motorcycle pilot at
B01); rooftop PV and BESS are sized by the MicroGrids LP on pvlib AC per kWp; every
building is grid-connected, nothing is curtailed and export is credited at the
building's purchase price (user decision, net billing scenario); one building type
per building across modules; heat pumps frozen at
the calibration values; controlled machines inside the bills; constant carbon
factor; the bills close against what CityLearn actually simulates.

Superseded since then: the B01 pilot by the fleet of SPEC-016 (D-V6-27 to D-V6-35, D-V6-45; bound by
test_write_ev_v6.py) and the controlled machines by base load (D-V6-1).

Unit tests use tmp_path; integration tests read the active dataset (configs/experiments/iquitos.yaml) and fail
(never skip) when it is absent.
"""
import csv
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))
CAMPAIGN = REPO/yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))['dataset_root']
DATASET = CAMPAIGN/'dataset'
REGISTRY = yaml.safe_load((REPO/'configs/dataset/building_types.yaml').read_text(encoding='utf-8'))
EV_PILOT = yaml.safe_load((REPO/'configs/dataset/ev_pilot.yaml').read_text(encoding='utf-8'))
ORIGINS = {'measured', 'model', 'cited', 'assumption', 'design_rule', 'derived', 'user_decision'}


def _json(path):
    assert path.is_file(), f'{path.relative_to(REPO)} missing: build the active dataset first'
    return json.loads(path.read_text(encoding='utf-8'))


def _schema():
    return _json(DATASET/'schema.json')


def _csv_column(path, column):
    with open(path, newline='', encoding='utf-8') as stream:
        return [row[column] for row in csv.DictReader(stream)]


# ── registry and configuration (unit) ───────────────────────────────────────

def test_registry_declares_required_types():
    types = {int(b): row['canonical_type'] for b, row in REGISTRY['buildings'].items()}
    assert set(types) == set(range(1, 18))
    assert types[16] == 'industrial_shipyard' and types[17] == 'laboratory_24h'
    assert types[2] == 'municipal_office' and types[9] == 'emergency_operations_office_24h'
    assert types[8] == 'police_school'
    for row in REGISTRY['buildings'].values():
        assert row['schedule'] in REGISTRY['schedules'] and row['justification']
    assert REGISTRY['schedules']['laboratory_24h']['occupied_hours'] == [0, 24]
    assert REGISTRY['schedules']['office_24h']['occupied_hours'] == [0, 24]


def test_der_economics_declares_source_and_status():
    economics = yaml.safe_load((REPO/'configs/dataset/der_economics.yaml').read_text(encoding='utf-8'))
    allowed = {'repository_example', 'design_rule', 'assumption_pending_user_verification'}
    for group in ('pv', 'bess', 'project'):
        for name, entry in economics[group].items():
            assert entry['status'] in allowed, (group, name)
            assert entry.get('source'), (group, name)
    assert economics['export']['price_ratio_to_purchase'] == 1.0
    assert economics['export']['curtailment_allowed'] is False and economics['export']['origin'] == 'user_decision'


def test_tou_blocks_scaled_to_printed_total(tmp_path):
    from uc3m.application.dataset import construction as cn
    path = tmp_path/'B_04.csv'
    path.write_text('E;Mes;Año;EnergiaActivaHoraPunta;EnergiaActivaFueraPunta;EnergiaReactiva;FactorCarga;'
                    'totalEnergiaActiva;TotalFacturado;Tarifa\n'
                    'X;ene;2023;100,0;400,0;0;0,5;600,0;10,0;MT3\n'
                    'X;feb;2023;100,0;400,0;0;0,5;505,0;10,0;MT3\n'
                    'X;mar;2023;100,0;400,0;0;0,5;50,0;10,0;MT3\n', encoding='utf-8')
    jan, feb, mar = cn.parse_billing_csv(path, 4, scale_tou_to_printed_total=True)
    assert jan.energy_kwh == pytest.approx(600.0) and jan.peak_kwh == pytest.approx(120.0)
    assert 'tou_scaled_to_printed_total' in jan.flags and 'total_mismatch' in jan.flags
    assert feb.energy_kwh == pytest.approx(500.0) and 'tou_scaled_to_printed_total' not in feb.flags  # within 2 %
    # A printed total outside 0.5..2 x the registers is a transcription error: registers kept, flagged.
    assert mar.energy_kwh == pytest.approx(500.0) and 'printed_total_implausible' in mar.flags
    legacy = cn.parse_billing_csv(path, 4)
    assert legacy[0].energy_kwh == pytest.approx(500.0)  # the earlier campaign rule is unchanged


def test_carbon_factor_is_constant_and_derived():
    import generate_iquitos_dataset as gen
    value, derivation = gen.constant_carbon_intensity(REPO/'configs/dataset/grid_emissions.yaml')
    assert value == pytest.approx(74100*3.6e-6/0.40)
    assert derivation['origin'] == 'model' and derivation['inputs']
    frame = gen.SupportFilesGenerator().build_constant_carbon_intensity(10, value)
    assert frame['carbon_intensity'].nunique() == 1


def test_citylearn_cooling_cop_matches_heat_pump():
    import numpy as np
    from citylearn.energy_model import HeatPump
    import distill_building_loads as dl
    t_out = np.array([20.0, 26.5, 34.0])
    pump = HeatPump(nominal_power=10.0, efficiency=0.21, target_cooling_temperature=8.5)
    assert dl.citylearn_cooling_cop(t_out, 0.21, 8.5) == pytest.approx(pump.get_cop(t_out, heating=False))


def test_depot_sessions_are_overnight_and_respect_year_boundaries():
    import dimension_ev_chargers as ev
    frame = ev.generate_depot_charger_csv(EV_PILOT['pilot'], vehicle_index=1)
    state = frame['electric_vehicle_charger_state'].to_numpy()
    assert len(state) == 26304 and set(state) <= {1, 2, 3}
    hours = frame.index.hour
    starts = [i for i in range(1, len(state)) if state[i] == 1 and state[i-1] != 1]
    assert starts and all(hours[i] == 18 for i in starts)
    for boundary in (8760, 17544):  # no session crosses a split boundary
        assert state[boundary - 1] != 1 or frame['electric_vehicle_departure_time'].iloc[boundary - 1] == 0
        assert state[boundary] != 1
    ends = [i for i in range(len(state) - 1) if state[i] == 1 and state[i+1] != 1]
    assert all(hours[i] in (7, 23) for i in ends)
    ids = set(frame['electric_vehicle_id']) - {'NONE'}
    assert len(ids) == 1  # one dedicated vehicle per socket


# ── built dataset (integration) ──────────────────────────────────────────────
# Every realism gate holds in the active dataset (configs/experiments/iquitos.yaml).

def test_pv_within_roof_bound():
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    schema = _schema()
    for b in range(1, 18):
        row = sizing['buildings'][str(b)]
        kwp = schema['buildings'][f'Building_{b}']['pv']['attributes']['nominal_power']
        assert kwp == pytest.approx(row['pv_kwp'], abs=1e-6)
        assert kwp <= row['roof_bound_kwp'] + 1e-6, b
        solar = [float(v) for v in _csv_column(DATASET/f'Building_{b}.csv', 'solar_generation')[:8760]]
        assert sum(solar)*kwp/1000.0 == pytest.approx(row['annual_pv_kwh_2023'], rel=1e-3, abs=1.0)


def test_microgrids_optimal_and_prosumpy_check_recorded():
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    assert sizing['solver'] == 'appsi_highs'
    for b in range(1, 18):
        row = sizing['buildings'][str(b)]
        assert row['termination_condition'] == 'optimal', b
        check = row['prosumpy']
        for key in ('self_consumption_pct', 'grid_import_kwh', 'peak_import_kw'):
            assert set(check[key]) == {'no_der', 'pv_only', 'pv_bess'}, (b, key)
        battery = _schema()['buildings'][f'Building_{b}'].get('electrical_storage')
        if row['bess_kwh'] > 0:
            assert battery['attributes']['capacity'] == pytest.approx(row['bess_kwh'])
    assert sizing['sensitivity']['capex_relative_change'] == [-0.3, 0.3]
    assert 'material_change' in sizing['sensitivity']


def test_export_credited_at_purchase_price_without_curtailment():
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    for b in range(1, 18):
        row = sizing['buildings'][str(b)]
        assert row['lp']['curtailed_kwh'] == pytest.approx(0.0, abs=1e-6), b
        assert row['lp']['export_price_usd_per_kwh'] == pytest.approx(row['price_usd_per_kwh']), b
        assert row['lp']['lost_load_kwh'] == pytest.approx(0.0, abs=1e-6), b
    # Local peer trading is a different mechanism: the community market stays off.
    assert _schema()['community_market']['enabled'] is False
    rules = [e for e in _json(CAMPAIGN/'provenance.json')['quantities'] if e['name'] == 'export_credit_rule']
    assert rules and rules[0]['origin'] == 'user_decision' and 'Iquitos' in rules[0]['reason']


def test_every_provenance_quantity_has_an_origin_class():
    provenance = _json(CAMPAIGN/'provenance.json')
    quantities = provenance['quantities']
    assert len(quantities) >= 30
    for entry in quantities:
        assert entry['origin'] in ORIGINS, entry
        assert entry.get('name') and 'value' in entry, entry
        if entry['origin'] == 'assumption':
            assert entry['assumption'] is True and entry.get('reason'), entry
        if entry['origin'] in {'measured', 'cited'}:
            assert entry.get('source'), entry
    names = {e['name'] for e in quantities}
    for required in ('pv_kwp', 'bess_kwh', 'carbon_intensity', 'ev_battery_kwh', 'cooling_efficiency',
                     'controlled_machine_cycle_kwh', 'pv_capex_usd_per_wp', 'monthly_energy_targets'):
        assert required in names, required


def test_one_building_type_per_building_across_modules():
    # The modules that still record a type: the distillation report and the EV audit no longer carry one,
    # and the controlled machines left the dataset (D-V6-1).
    expected = {str(b): row['canonical_type'] for b, row in REGISTRY['buildings'].items()}
    seen = {}
    for b, row in _json(CAMPAIGN/'audit/der_sizing_microgrids.json')['buildings'].items():
        seen.setdefault(('der', b), set()).add(row['building_type'])
    for b, row in _json(DATASET/'building_metadata.json')['building_types'].items():
        seen.setdefault(('generator', b), set()).add(row)
    assert {module for module, _ in seen} == {'der', 'generator'}
    assert {b for _, b in seen} == set(expected)
    for (module, b), values in seen.items():
        assert values == {expected[b]}, (module, b, values)


def test_heat_pump_parameters_in_schema_equal_the_declared_and_the_frozen_ones():
    schema = _schema()
    declared = {e['scope']: e['value'] for e in _json(CAMPAIGN/'provenance.json')['quantities']
                if e['name'] == 'cooling_efficiency'}
    for b in range(1, 18):
        device = schema['buildings'][f'Building_{b}']['cooling_device']['attributes']
        assert device['efficiency'] == pytest.approx(declared[f'B{b:02d}']), b
    split = _json(CAMPAIGN/'split_manifest.json')['fixed_device_sizes']
    assert set(split) == {f'Building_{b}' for b in range(1, 18)}
    for key, devices in split.items():
        attributes = schema['buildings'][key]['cooling_device']['attributes']
        assert devices['cooling_device']['efficiency'] == pytest.approx(attributes['efficiency'])
        assert devices['cooling_device']['target_cooling_temperature'] == pytest.approx(
            attributes['target_cooling_temperature'])


def test_controlled_machines_left_and_the_distillation_closes_on_the_bills():
    # D-V6-1: their energy is base load, so the measured blocks close without a machine term.
    assert not any('washing_machines' in building for building in _schema()['buildings'].values())
    assert not list(DATASET.glob('Washing_Machine_*.csv'))
    with open(CAMPAIGN/'audit/distillation_report.csv', newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert {row['building_id'] for row in rows} == {str(b) for b in range(1, 18)}
    for row in rows:
        assert abs(float(row['delta_%'])) < 1e-3, (row['building_id'], row['year'], row['mes'])


def test_carbon_intensity_is_one_constant():
    values = {float(v) for v in _csv_column(DATASET/'carbon_intensity.csv', 'carbon_intensity')}
    assert len(values) == 1 and values.pop() == pytest.approx(74100*3.6e-6/0.40, rel=1e-6)


def test_bills_close_against_citylearn_no_control_simulation():
    report = _json(CAMPAIGN/'audit/citylearn_balance.json')
    assert report['split'] == 'train_2023' and report['tolerance_relative'] <= 0.01
    assert set(report['buildings']) == {str(b) for b in range(1, 18)}
    for b, row in report['buildings'].items():
        assert len(row['months']) == 12 and row['passed'], (b, row['max_relative_error'])
    assert 'peak_check' in report and len(report['peak_check']) == 17


def test_acceptance_records_realism_gates():
    acceptance = _json(CAMPAIGN/'dataset_acceptance.json')
    assert acceptance['dataset_verified'] is True
    for gate in ('hourly_balance', 'citylearn_balance', 'microgrids_optimal', 'ev_fleet_written'):
        assert acceptance['gates'][gate] is True, gate


def test_export_step_is_credited_at_the_hourly_purchase_price():
    """No-control CityLearn step with PV surplus: net cost = -export x that hour's price (net billing)."""
    schema = _schema()
    assert schema['community_market']['enabled'] is False and 'grid_export_price' not in schema['community_market']
    assert schema['community_market']['export_settlement'] == 'net_billing_at_hourly_purchase_price'
    from citylearn.citylearn import CityLearnEnv
    env = CityLearnEnv(str(CAMPAIGN/'splits/train_2023/schema.json'))
    env.reset()
    assert env.community_market_enabled is False
    building = next(b for b in env.buildings if b.name == 'Building_2')  # municipal office, roof PV >> load
    zero = [[0.0]*len(names) for names in env.action_names]
    for _ in range(48):
        env.step(zero)
        t = env.time_step - 1
        net = float(building.net_electricity_consumption[t])
        if net < 0:
            price = float(building.pricing.electricity_pricing[t])
            # CityLearn stores the cost series as float32 (relative precision ~6e-8).
            assert float(building.net_electricity_consumption_cost[t]) == pytest.approx(net*price, rel=1e-6)
            assert net*price < 0
            break
    else:
        pytest.fail('no exporting step for Building_2 in the first 48 h')
    rules = [e for e in _json(CAMPAIGN/'provenance.json')['quantities'] if e['name'] == 'export_settlement_citylearn']
    assert rules and rules[0]['origin'] == 'user_decision'
