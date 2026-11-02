"""Official tariff, demand charge and existing-area PV of campaign iquitos_v3.

User decisions (2026-11-01): the price is Osinergmin's monthly tariff sheet for the
Iquitos sector (block tariff + demand); BESS is sized by MicroGrids with an hourly
price and a monthly peak-block demand charge; PV is bounded by the existing covered
area x 0.63 ("area techada usada como techo disponible"); export stays net billing
at the energy charge. Unit tests use synthetic inputs; integration tests read
data/campaigns/iquitos_v3 and fail (never skip) when it is absent.
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))
CAMPAIGN = REPO/'data/campaigns/iquitos_v3'
DATASET = CAMPAIGN/'dataset'

CELLS = ['TARIFA MT2', 'TARIFA CON DOBLE MEDICION', 'Cargo Fijo Mensual', 'S//mes', '15.13',
         'Cargo por Energ&iacute;a Activa en Punta', 'ctm. S//kW.h', '41.76',
         'Cargo por Energ&iacute;a Activa Fuera de Punta', 'ctm. S//kW.h', '41.76',
         'Cargo por Potencia Activa de Generaci&oacute;n en HP', 'S//kW-mes', '33.28',
         'Cargo por Potencia Activa de Distribuci&oacute;n en HP', 'S//kW-mes', '18.80',
         'TARIFA MT3', 'Cargo Fijo Mensual', 'S//mes', '13.17',
         'Cargo por Energ&iacute;a Activa en Punta', 'ctm. S//kW.h', '41.76',
         'Cargo por Energ&iacute;a Activa Fuera de Punta', 'ctm. S//kW.h', '41.76',
         'Cargo por Potencia Activa de generaci&oacute;n para Usuarios:', 'Presentes en Punta', 'S//kW-mes', '30.10',
         'Presentes Fuera de Punta', 'S//kW-mes', '19.10',
         'Cargo por Potencia Activa de redes de distribuci&oacute;n para Usuarios:', 'Presentes en Punta',
         'S//kW-mes', '20.28', 'Presentes Fuera de Punta', 'S//kW-mes', '20.24']
SHEET = '<html><body><table><tr><td>' + '</td><td>'.join(CELLS) + '</td></tr></table></body></html>'


def _json(path):
    assert path.is_file(), f'{path.relative_to(REPO)} missing: build iquitos_v3 first'
    return json.loads(path.read_text(encoding='utf-8'))


# ── unit ─────────────────────────────────────────────────────────────────────

def test_sheet_parser_reads_charges_without_retyping():
    import osinergmin_pliegos as op
    html = SHEET.replace('\n', ' ').replace('> ', '>\n').replace(' Cargo', '\nCargo').replace(' Presentes', '\nPresentes')
    html = html.replace(' S//', '\nS//').replace('S//mes ', 'S//mes\n').replace('S//kW.h ', 'S//kW.h\n')
    html = html.replace('S//kW-mes ', 'S//kW-mes\n').replace(' TARIFA', '\nTARIFA')
    charges = op.parse_sheet(html)
    assert charges['MT2']['energy_peak_ctm_kwh'] == 41.76 and charges['MT2']['gen_hp_pen_kw'] == 33.28
    assert charges['MT3']['gen_present_peak_pen_kw'] == 30.10 and charges['MT3']['dist_present_offpeak_pen_kw'] == 20.24


def test_sheet_in_force_and_day_weighting():
    import osinergmin_pliegos as op
    sheets = {date(2022, 12, 4): {'MT2': {'energy_peak_ctm_kwh': 40.0}},
              date(2023, 1, 4): {'MT2': {'energy_peak_ctm_kwh': 46.2}}}
    assert op.sheet_for_month(sheets, 2023, 1) == date(2022, 12, 4)
    coverage = op.month_coverage(sheets, 2023, 1)
    assert coverage == {'2022-12-04': pytest.approx(3/31), '2023-01-04': pytest.approx(28/31)}
    weighted = op.weighted_charges(sheets, 2023, 1, 'MT2')
    assert weighted['energy_peak_ctm_kwh'] == pytest.approx(40.0*3/31 + 46.2*28/31)


def test_bill_reconstruction_components():
    import osinergmin_pliegos as op
    sheets = {date(2023, 1, 1): {'MT3': {'fixed_pen_month': 10.0, 'energy_peak_ctm_kwh': 40.0,
                                         'energy_offpeak_ctm_kwh': 40.0, 'gen_present_peak_pen_kw': 30.0,
                                         'gen_present_offpeak_pen_kw': 20.0, 'dist_present_peak_pen_kw': 20.0,
                                         'dist_present_offpeak_pen_kw': 21.0, 'reactive_ctm_kvarh': 4.0}}}
    bill = op.reconstruct_bill(tariff='MT3', year=2023, month=4, peak_kwh=3000.0, offpeak_kwh=7000.0,
                               reactive_kvarh=4000.0, load_factor=0.5, sheets=sheets)
    pmax = 10000.0/(0.5*720)
    assert bill['pmax_kw'] == pytest.approx(pmax)
    assert bill['present_in_peak'] is True  # (3000/150)/27.8 = 0.72 >= 0.5
    assert bill['subtotal_without_igv_pen'] == pytest.approx(10.0 + 4000.0 + pmax*50.0 + 1000.0*0.04)
    assert bill['total_with_igv_pen'] == pytest.approx(bill['subtotal_without_igv_pen']*1.18)


def test_microgrids_demand_charge_makes_peak_block_cost_visible(tmp_path):
    import numpy as np
    import pandas as pd
    import size_der_microgrids as sd
    economics = sd.load_economics()
    index = pd.date_range('2023-01-01', periods=24*14, freq='h')
    hour = index.hour.to_numpy()
    demand = 10.0 + 20.0*((hour >= 18) & (hour <= 22))
    tariff = {'energy_price': np.full(len(index), 0.1), 'period_month': index.month.to_numpy(),
              'peak_period': ((hour >= 18) & (hour <= 22)).astype(int), 'demand_charge': {1: 13.0}}
    result = sd.solve_microgrids(demand, np.zeros(len(index)), 0.1, 0.0, economics, tmp_path/'run', tariff=tariff)
    assert result['termination_condition'] == 'optimal'
    assert result['monthly_peak_block_max_kw'][1] == pytest.approx(30.0, abs=1e-6)
    assert result['demand_charge_year_usd'] == pytest.approx(13.0*30.0, rel=1e-6)
    assert result['grid_energy_cost_year_usd'] == pytest.approx(0.1*demand.sum(), rel=1e-6)


# ── built dataset (integration) ──────────────────────────────────────────────

def test_every_month_has_a_cited_osinergmin_sheet():
    provenance = _json(CAMPAIGN/'provenance.json')
    cited = [q for q in provenance['quantities'] if q['name'] == 'tariff_sheet']
    assert len(cited) >= 36
    for q in cited:
        assert q['origin'] == 'cited' and q['source'].startswith('https://www.osinergmin.gob.pe/')
        assert q['valid_from'] and q['obtained_at'] and (REPO/q['raw_file']).is_file()
    sources = [s for s in provenance['sources'] if s['source_type'] == 'official_tariff_sheet']
    assert len(sources) == len(cited)
    coverage = _json(CAMPAIGN/'audit/tariff_bill_validation.json')['sheet_in_force_on_day_1']
    assert len(coverage) == 36
    assert _json(CAMPAIGN/'dataset_acceptance.json')['gates']['tariff_history_complete'] is True


def test_citylearn_price_is_the_sheet_energy_charge_of_each_building():
    import osinergmin_pliegos as op
    provenance = _json(CAMPAIGN/'provenance.json')
    fx = {int(k): v for k, v in provenance['pen_per_usd'].items()}
    sheets = {date.fromisoformat(Path(q['raw_file']).stem.split('_')[-1]):
              op.parse_sheet((REPO/q['raw_file']).read_bytes())
              for q in provenance['quantities'] if q['name'] == 'tariff_sheet'}
    schema = _json(DATASET/'schema.json')
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    for b in (2, 6, 11, 17):
        assert schema['buildings'][f'Building_{b}']['pricing'] == f'pricing_{b}.csv'
        with open(DATASET/f'pricing_{b}.csv', newline='', encoding='utf-8') as stream:
            prices = [float(r['electricity_pricing']) for r in csv.DictReader(stream)]
        label = sizing['buildings'][str(b)]['price_source']['tariff_by_month_2023']['06']['tariff']
        charges = op.weighted_charges(sheets, 2023, 6, label)
        expected = charges.get('energy_ctm_kwh', charges.get('energy_peak_ctm_kwh'))/100.0/fx[2023]
        june = prices[(31+28+31+30+31)*24:(31+28+31+30+31+30)*24]
        assert set(round(p, 9) for p in june) == {round(expected, 9)}, b


def test_bills_are_recomputed_and_errors_reported_per_building_and_month():
    report = _json(CAMPAIGN/'audit/tariff_bill_validation.json')
    assert report['rows'] and set(report['summary']) == {str(b) for b in range(2, 18)}
    for row in report['rows']:
        for key in ('error_with_igv', 'error_without_igv', 'pmax_kw', 'tariff', 'present_in_peak'):
            assert key in row
    names = {q['name'] for q in _json(CAMPAIGN/'provenance.json')['quantities']}
    assert {'tariff_bill_validation', 'tariff_peak_block_hours', 'tariff_present_in_peak_rule'} <= names


def test_bess_sized_with_demand_charge_and_verified():
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    shaving = _json(CAMPAIGN/'audit/bess_peak_shaving_check.json')
    assert 'tarifa-horaria-demanda' in sizing['formulation']
    for b in range(1, 18):
        row = sizing['buildings'][str(b)]
        assert row['termination_condition'] == 'optimal'
        assert len(row['demand_charge_usd_kw_month_2023']) == 12 and row['lp']['demand_charge_year_usd'] >= 0
        assert set(row['prosumpy']['peak_import_kw']) == {'no_der', 'pv_only', 'pv_bess'}
        if row['bess_kwh'] > 0:
            assert str(b) in shaving['buildings']
    assert shaving['status'] == ('checked' if any(r['bess_kwh'] > 0 for r in sizing['buildings'].values())
                                 else 'no_bess_sized')


def test_pv_bound_is_existing_area_times_base_rule():
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    module = sizing['module']
    with open(REPO/'CityLearn/data/buildingcsv/building.csv', newline='', encoding='utf-8') as stream:
        areas = {int(r['ID_Edificio'].split('_')[1]): float(r['Area_Techada_m2']) for r in csv.DictReader(stream)}
    for b in range(1, 18):
        row = sizing['buildings'][str(b)]
        expected = int(areas[b]*0.63//module['Area'])*module['Vmpo']*module['Impo']/1000.0
        assert row['roof_bound_kwp'] == pytest.approx(expected) and row['usable_area_fraction'] == 0.63
        assert row['pv_kwp'] <= row['roof_bound_kwp'] + 1e-6
    rule = [q for q in _json(CAMPAIGN/'provenance.json')['quantities'] if q['name'] == 'pv_usable_area_rule']
    assert rule and rule[0]['origin'] == 'user_decision' and 'techada usada como techo disponible' in rule[0]['reason']


def test_supervision_hypotheses_exclusions_and_sector_are_recorded():
    report = _json(CAMPAIGN/'audit/tariff_bill_validation.json')
    hypotheses = report['hypotheses']
    for key in ('baseline_sheet_with_igv', 'a_no_igv', 'b_capacity_half_of_E_over_LF_h',
                'c_capacity_on_mean_of_two_highest_of_six_months', 'd_charges_outside_the_sheet', 'e_sector'):
        assert key in hypotheses, key
    assert report['months_used'] + len(report['excluded']) == report['months_total']
    assert all(e['excluded_reason'] for e in report['excluded'])
    assert all(r['excluded_reason'] for r in report['rows']
               if {'partial_month_suspect', 'printed_total_implausible'} & set(r['flags'])
               or not 0.2 < 1 + r['error_with_igv'] < 5)
    labels = {(v['DDLSE'], v['LBSector'], v['LBInter']) for v in report['sheet_labels'].values()}
    assert labels == {('IQUITOS', '2', 'AISL')} and len(report['sheet_labels']) >= 36
    assert 'matches' in report['definitions_search_in_sheets']


def test_unverified_demand_charge_is_never_presented_as_verified():
    report = _json(CAMPAIGN/'audit/tariff_bill_validation.json')
    status = report['capacity_component']['status']
    assert status in {'validated', 'unverified'}
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    for b, row in sizing['buildings'].items():
        assert row['demand_charge_status'] == status, b
        assert row['without_demand_charge']['termination_condition'] == 'optimal', b
    entry = next(q for q in _json(CAMPAIGN/'provenance.json')['quantities'] if q['name'] == 'demand_charge_validation')
    assert entry['value'] == status
    for name in ('tariff_peak_block_hours', 'tariff_present_in_peak_rule'):
        rule = next(q for q in _json(CAMPAIGN/'provenance.json')['quantities'] if q['name'] == name)
        assert rule['origin'] == 'assumption' and 'not defined' in rule['reason']
