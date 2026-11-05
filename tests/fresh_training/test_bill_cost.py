"""Evaluated cost = bill with capacity charge (owner decision D02, 2026-11-04; SPEC-013).

Unit tests use analytic traces. The artifact tests read the versioned bill tariff table
and data/campaigns/iquitos_v4 and fail (never skip) when they are absent.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

from uc3m.application.evaluation.bill_cost import BillRate, bill_components, bill_measures, load_bill_tariffs
from uc3m.application.evaluation.kpi_contract import PhysicalTrace, compute_fresh_kpis, load_kpi_catalog, validate_kpi_report

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))
CATALOG = REPO/'configs/evaluation/kpis.yaml'
TABLE = REPO/'data/tariffs/osinergmin/bill_tariffs.csv'
V4 = REPO/'data/campaigns/iquitos_v4'
UNITS = {'net_power': 'kW', 'carbon_intensity': 'kgCO2/kWh', 'price': 'USD/kWh', 'battery_throughput': 'kWh'}
RATES = {(1, 2024, 1): BillRate('MT3', 0.10, 10.0, 5.0), (1, 2024, 2): BillRate('MT3', 0.20, 20.0, 5.0)}


def stamps(start_day='2024-01-31', hours=48):
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(f'{start_day}T00:00:00-05:00')
    return tuple((start + timedelta(hours=h)).isoformat() for h in range(hours))


def trace(power, name='Building_1', price=0.5):
    n = len(power)
    return PhysicalTrace(stamps(hours=n), 3600, (name,),
                         {name: {'net_power': tuple(power), 'battery_throughput': (0.0,)*n, 'price': (price,)*n}},
                         {'carbon_intensity': (0.5,)*n, 'price': (price,)*n}, UNITS, 'USD', 'test', 'hash')


def profile(day_one, day_two):
    """Two days, one hour in each month: {hour: kW} over a 1 kW base."""
    return [day_one.get(h, 1.0) for h in range(24)] + [day_two.get(h, 1.0) for h in range(24)]


def test_energy_demand_and_fixed_by_month():
    parts = bill_components(trace(profile({18: 7.0, 12: 30.0}, {22: 3.0})), RATES)
    energy_one = (22*1.0 + 7.0 + 30.0)*0.10
    energy_two = (23*1.0 + 3.0)*0.20
    assert parts['energy_usd'] == pytest.approx(energy_one + energy_two)
    assert parts['demand_usd'] == pytest.approx(7.0*10.0 + 3.0*20.0)  # the 30 kW at 12:00 is outside the block
    assert parts['fixed_usd'] == pytest.approx(10.0)
    assert parts['total_usd'] == pytest.approx(parts['energy_usd'] + parts['demand_usd'] + parts['fixed_usd'])


def test_peak_block_is_18_to_22_inclusive():
    outside = bill_components(trace(profile({17: 50.0, 23: 50.0}, {})), RATES)['demand_usd']
    assert outside == pytest.approx(1.0*10.0 + 1.0*20.0)


def test_export_is_credited_but_never_a_negative_demand():
    parts = bill_components(trace([-5.0]*48), RATES)
    assert parts['demand_usd'] == 0.0
    assert parts['energy_usd'] == pytest.approx(-5.0*24*0.10 - 5.0*24*0.20)


def test_bill_ignores_the_price_the_simulator_flattened():
    cheap, dear = trace([2.0]*48, price=0.01), trace([2.0]*48, price=0.99)
    assert bill_components(cheap, RATES) == bill_components(dear, RATES)


@pytest.mark.parametrize('name, rates', [('Building_2', RATES), ('District', RATES),
                                         ('Building_1', {(1, 2024, 1): RATES[(1, 2024, 1)]})])
def test_missing_rate_is_unavailable_not_zero(name, rates):
    assert bill_components(trace([1.0]*48, name=name), rates) is None


def test_table_rejects_duplicates_and_bad_values(tmp_path):
    head = 'building,year,month,tariff,basis,energy_usd_kwh,demand_usd_kw_month,fixed_usd_month\n'
    row = '1,2024,1,MT3,bill,0.1,10,5\n'
    path = tmp_path/'t.csv'
    path.write_text(head + row, encoding='utf-8')
    assert load_bill_tariffs(path) == {(1, 2024, 1): BillRate('MT3', 0.1, 10.0, 5.0)}
    path.write_text(head + row + row, encoding='utf-8')
    with pytest.raises(ValueError):
        load_bill_tariffs(path)
    path.write_text(head + '1,2024,1,MT3,bill,nan,10,5\n', encoding='utf-8')
    with pytest.raises(ValueError):
        load_bill_tariffs(path)
    path.write_text(head + '1,2024,1,MT3,bill,0.1,-1,5\n', encoding='utf-8')
    with pytest.raises(ValueError):
        load_bill_tariffs(path)


def _report(control, base, extra):
    return compute_fresh_kpis(control, base, load_kpi_catalog(CATALOG), extra_measures=extra)


def test_cost_axis_is_the_bill():
    catalog = load_kpi_catalog(CATALOG)
    assert catalog.axes['energy_cost'] == ('bill_cost_total',)
    by_name = catalog.by_name()
    assert by_name['bill_cost_total'].primary and not by_name['energy_cost_total'].primary


def test_shaving_the_peak_block_gains_on_the_bill_with_same_energy():
    flat = trace([1.0]*48, price=0.1)
    peaky = trace(profile({18: 7.0, 10: 1.0 - 6.0}, {}), price=0.1)
    # Both consume the same energy in January; the control has no peak in the block.
    report = _report(flat, peaky, bill_measures(RATES))
    assert report.values['bill_cost_total']['value'] < report.values['bill_cost_total']['baseline']
    assert report.values['energy_cost_total']['delta'] == pytest.approx(0.0, abs=1e-9)
    assert report.axis_gains['energy_cost'] > 0


def test_without_the_table_the_primary_endpoint_fails_closed():
    report = _report(trace([1.0]*48), trace([1.0]*48), None)
    entry = report.values['bill_cost_total']
    assert entry['value'] is None and entry['cause'] == 'requires_injected_bill_tariffs'
    assert report.axis_gains['energy_cost'] is None
    assert any('bill_cost_total' in reason for reason in validate_kpi_report(report, load_kpi_catalog(CATALOG)).reasons)


def test_peak_billing_indicator_comes_from_the_bill():
    import yaml
    rows = {row['name']: row for row in yaml.safe_load(CATALOG.read_text(encoding='utf-8'))['thesis_indicators']}
    assert rows['peak_billing']['value_from'] == 'trace:bill_demand_charge'
    assert rows['peak_billing']['definition_status'] == 'defined'


# ── versioned table ──────────────────────────────────────────────────────────

def test_table_covers_every_building_and_month():
    rates = load_bill_tariffs(TABLE)
    assert len(rates) == 17*36
    assert {key[0] for key in rates} == set(range(1, 18)) and {key[1] for key in rates} == {2023, 2024, 2025}


def test_table_agrees_with_what_sized_the_dataset():
    rates = load_bill_tariffs(TABLE)
    sizing = json.loads((V4/'audit/der_sizing_microgrids.json').read_text(encoding='utf-8'))['buildings']
    for building, row in sizing.items():
        for month, value in row['demand_charge_usd_kw_month_2023'].items():
            assert rates[(int(building), 2023, int(month))].demand_usd_kw_month == pytest.approx(value, abs=1e-8)


def test_table_energy_agrees_with_the_dataset_price_files():
    rates = load_bill_tariffs(TABLE)
    for building in range(1, 18):
        with open(V4/f'dataset/pricing_{building}.csv', newline='', encoding='utf-8') as handle:
            prices = [float(row['electricity_pricing']) for row in csv.DictReader(handle)]
        # Rows are hourly from 2023-01-01; 744 h = January, 2023 has 8760 h.
        assert rates[(building, 2023, 1)].energy_usd_kwh == pytest.approx(prices[0], abs=1e-8)
        assert rates[(building, 2024, 1)].energy_usd_kwh == pytest.approx(prices[8760], abs=1e-8)


# ── baseline comparison ──────────────────────────────────────────────────────

def test_baseline_summary_reports_the_bill(monkeypatch):
    import compare_campaign_baselines as tool
    monkeypatch.setattr(tool, 'load_rates', lambda: RATES)
    summary = tool.summarize_trace(trace(profile({18: 7.0}, {})))
    assert summary['bill_demand_usd'] == pytest.approx(7.0*10.0 + 1.0*20.0)
    assert summary['bill_total_usd'] == pytest.approx(summary['bill_energy_usd'] + summary['bill_demand_usd'] + 10.0)


def test_paired_delta_reports_the_bill():
    import compare_campaign_baselines as tool
    base = {'cost_usd': -10.0, 'co2_kg': -10.0, 'net_mwh': 0.0, 'district_peak_kw': 5.0, 'bill_total_usd': -100.0,
            'bill_demand_usd': 40.0}
    control = dict(base, bill_total_usd=-110.0, bill_demand_usd=30.0)
    delta = tool.paired_delta(control, base)
    assert delta['bill_usd'] == pytest.approx(-10.0) and delta['bill_percent'] == pytest.approx(-10.0)
    assert delta['bill_demand_usd'] == pytest.approx(-10.0)
