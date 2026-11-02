"""T4: KPI from physical traces with checked units, on new analytical cases.

Every expected value below is derived by hand from the synthetic trace it is
asserted on; no value of any earlier campaign is used.
"""
import math
from pathlib import Path

import pytest

from uc3m.application.evaluation import kpi_contract as kc

REPO = Path(__file__).resolve().parents[2]
UNITS = {'net_power': 'kW', 'carbon_intensity': 'kgCO2/kWh', 'price': 'USD/kWh',
         'battery_throughput': 'kWh'}


def _hours(n, start='2023-01-01T00:00:00-05:00'):
    from datetime import datetime, timedelta
    t0 = datetime.fromisoformat(start)
    return tuple((t0 + timedelta(hours=i)).isoformat() for i in range(n))


def _trace(power_by_building, *, ci=0.5, price=0.2, currency='USD', provenance='tariff:synthetic',
           extra=None, units=None):
    n = len(next(iter(power_by_building.values())))
    series = {b: {'net_power': tuple(values)} for b, values in power_by_building.items()}
    for b, values in (extra or {}).items():
        series[b].update(values)
    return kc.PhysicalTrace(
        timestamps=_hours(n), seconds_per_step=3600, building_ids=tuple(power_by_building),
        series_by_building=series,
        district_series={'carbon_intensity': (ci,)*n, 'price': (price,)*n},
        units=units or UNITS, currency=currency, currency_provenance=provenance,
        exogenous_hash='0'*64)


@pytest.fixture(scope='module')
def catalog():
    return kc.load_kpi_catalog(REPO / 'configs' / 'evaluation' / 'kpis.yaml')


def _value(report, name):
    return report.values[name]


def test_total_delta_is_control_minus_baseline(catalog):
    control = _trace({'B1': [1.0]*24})
    baseline = _trace({'B1': [2.0]*24})
    report = kc.compute_fresh_kpis(control, baseline, catalog)
    cost = _value(report, 'energy_cost_total')
    assert cost['value'] == pytest.approx(24*1.0*0.2)
    assert cost['baseline'] == pytest.approx(24*2.0*0.2)
    assert cost['delta'] == pytest.approx(24*1.0*0.2 - 24*2.0*0.2)  # control - baseline < 0
    assert cost['gain'] == pytest.approx(0.5)  # (baseline - control) / |baseline|


def test_total_never_averages_daily_value(catalog):
    control = _trace({'B1': [1.0]*24 + [3.0]*24})
    report = kc.compute_fresh_kpis(control, control, catalog)
    assert _value(report, 'energy_cost_total')['value'] == pytest.approx((24*1 + 24*3)*0.2)
    with pytest.raises(ValueError):
        kc.KpiDefinition('bad_total', 'energy_cost', 'USD', 'minimize', 'district', 'total',
                         aggregation='daily_mean')


def test_district_peak_is_coincident_sum(catalog):
    b1 = [0.0]*24
    b2 = [0.0]*24
    b1[3], b2[15] = 10.0, 10.0  # individual peaks never coincide
    report = kc.compute_fresh_kpis(_trace({'B1': b1, 'B2': b2}), _trace({'B1': b1, 'B2': b2}), catalog)
    assert _value(report, 'district_daily_peak')['value'] == pytest.approx(10.0)  # not 20


def test_export_is_credited_at_purchase_price_and_displaces_co2(catalog):
    # Owner decision (2026-11-01): net billing; exported energy is credited at the
    # building purchase price and displaces thermal generation.
    importing = [2.0]*24
    exporting = [-2.0]*24  # district net is exactly zero every hour
    report = kc.compute_fresh_kpis(_trace({'B1': importing, 'B2': exporting}),
                                   _trace({'B1': importing, 'B2': exporting}), catalog)
    assert _value(report, 'energy_cost_total')['value'] == pytest.approx(0.0)
    assert _value(report, 'co2_total')['value'] == pytest.approx(0.0)
    assert _value(report, 'export_energy')['value'] == pytest.approx(48.0)
    exporter = kc.compute_fresh_kpis(_trace({'B2': exporting}), _trace({'B2': exporting}), catalog)
    assert _value(exporter, 'energy_cost_total')['value'] == pytest.approx(-24*2.0*0.2)
    assert _value(exporter, 'co2_total')['value'] == pytest.approx(-24*2.0*0.5)


def test_flexibility_uses_bidirectional_district_power(catalog):
    injecting = [-1.0]*12 + [-5.0]*12      # one daily injection peak of 5 kW
    report = kc.compute_fresh_kpis(_trace({'B1': injecting}), _trace({'B1': injecting}), catalog)
    assert _value(report, 'district_daily_peak')['value'] == pytest.approx(5.0)
    assert _value(report, 'district_ramping')['value'] == pytest.approx(4.0/23)
    assert _value(report, 'one_minus_load_factor')['value'] == pytest.approx(1 - 3.0/5.0)


def test_baseline_zero_is_undefined(catalog):
    control = _trace({'B1': [1.0]*24})
    baseline = _trace({'B1': [0.0]*24})
    cost = _value(kc.compute_fresh_kpis(control, baseline, catalog), 'energy_cost_total')
    assert cost['gain'] is None and cost['availability'] == 'undefined'
    assert cost['cause'] == 'baseline_zero'


def test_missing_not_zero(catalog):
    control = _trace({'B1': [1.0]*24})
    report = kc.compute_fresh_kpis(control, control, catalog)
    throughput = _value(report, 'battery_throughput')
    assert throughput['value'] is None and throughput['availability'] == 'unavailable'
    assert throughput['cause'] == 'missing_series:battery_throughput'
    no_price = kc.PhysicalTrace(control.timestamps, 3600, ('B1',), control.series_by_building,
                                {'carbon_intensity': (0.5,)*24}, UNITS, 'USD', 'tariff:synthetic', '0'*64)
    broken = kc.compute_fresh_kpis(no_price, no_price, catalog)
    assert _value(broken, 'energy_cost_total')['availability'] == 'unavailable'
    result = kc.validate_kpi_report(broken, catalog)
    assert not result.passed and any('energy_cost_total' in r for r in result.reasons)


@pytest.mark.parametrize('bad', [True, float('nan'), float('inf'), None])
def test_rejects_bool_nan_inf(bad):
    with pytest.raises(ValueError):
        _trace({'B1': [1.0]*23 + [bad]})


def test_throughput_is_not_unconditional_benefit(catalog):
    throughput = {'B1': {'battery_throughput': (1.0,)*24}}
    report = kc.compute_fresh_kpis(_trace({'B1': [1.0]*24}, extra=throughput),
                                   _trace({'B1': [1.0]*24}, extra={'B1': {'battery_throughput': (2.0,)*24}}),
                                   catalog)
    entry = _value(report, 'battery_throughput')
    assert entry['sense'] == 'exposure' and entry['gain'] is None
    assert entry['value'] == pytest.approx(24.0) and entry['delta'] == pytest.approx(-24.0)
    assert 'battery_throughput' not in catalog.primary_endpoints


def test_currency_provenance_required(catalog):
    with pytest.raises(ValueError):
        _trace({'B1': [1.0]*24}, provenance='')
    with pytest.raises(ValueError):  # relabelling another currency as USD is refused
        kc.compute_fresh_kpis(_trace({'B1': [1.0]*24}, currency='PEN',
                                     units={**UNITS, 'price': 'PEN/kWh'}),
                              _trace({'B1': [1.0]*24}), catalog)
    with pytest.raises(ValueError):
        _trace({'B1': [1.0]*24}, units={**UNITS, 'price': 'EUR/kWh'})


def test_no_estimated_savings_as_measured_kpi(catalog):
    with pytest.raises(ValueError):
        kc.KpiDefinition('estimated_saving', 'energy_cost', 'USD', 'minimize', 'district', 'total',
                         provenance='estimated', primary=True)
    report = kc.compute_fresh_kpis(_trace({'B1': [1.0]*24}), _trace({'B1': [2.0]*24}), catalog)
    assert all(entry['provenance'] == 'trace' for entry in report.values.values())
    tampered = kc.KpiReport(report.context, {**report.values, 'energy_cost_total': {
        **report.values['energy_cost_total'], 'provenance': 'estimated'}}, report.trace_hash,
        report.baseline_trace_hash, report.balance_checks)
    assert not kc.validate_kpi_report(tampered, catalog).passed


def test_flexibility_primaries_and_axis_gain(catalog):
    control = _trace({'B1': [2.0, 4.0]*12})
    baseline = _trace({'B1': [2.0, 6.0]*12})
    report = kc.compute_fresh_kpis(control, baseline, catalog)
    assert _value(report, 'district_daily_peak')['value'] == pytest.approx(4.0)
    assert _value(report, 'district_ramping')['value'] == pytest.approx(2.0)  # kW/h, 23 steps of 2
    assert _value(report, 'one_minus_load_factor')['value'] == pytest.approx(1 - 3.0/4.0)
    gains = [_value(report, n)['gain'] for n in ('district_daily_peak', 'district_ramping',
                                                 'one_minus_load_factor')]
    assert report.axis_gains['flexibility'] == pytest.approx(sum(gains)/3)
    assert report.axis_gains['co2_emissions'] == pytest.approx(_value(report, 'co2_total')['gain'])
    assert kc.validate_kpi_report(report, catalog).passed
    balance = report.balance_checks['energy']
    assert balance['passed'] and math.isclose(balance['import_minus_export_kwh'], balance['net_kwh'])
