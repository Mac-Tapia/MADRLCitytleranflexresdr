"""D01/S10: baseline comparison of two campaigns; physics summary and sealed test split."""
import importlib.util
from pathlib import Path
import sys

import pytest

from uc3m.application.evaluation.bill_cost import BillRate
from uc3m.application.evaluation.kpi_contract import PhysicalTrace

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("d01_compare", REPO / "tools/dataset/compare_campaign_baselines.py")
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)


@pytest.fixture(autouse=True)
def official_rates(monkeypatch):
    rates = {(1, 2024, 1): BillRate("MT3", 0.1, 10.0, 1.0), (2, 2024, 1): BillRate("MT3", 0.2, 20.0, 1.0)}
    monkeypatch.setattr(tool, "load_rates", lambda: rates)


def _trace(a, b, price_a=(0.1, 0.1, 0.1), price_b=(0.2, 0.2, 0.2), carbon=(0.5, 0.5, 0.5)):
    series = {"Building_1": {"net_power": list(a), "price": list(price_a), "battery_throughput": [0.0] * 3},
              "Building_2": {"net_power": list(b), "price": list(price_b), "battery_throughput": [1.0] * 3}}
    units = {"net_power": "kW", "carbon_intensity": "kgCO2/kWh", "price": "USD/kWh", "battery_throughput": "kWh"}
    stamps = ("2024-01-01T00:00:00", "2024-01-01T01:00:00", "2024-01-01T02:00:00")
    return PhysicalTrace(stamps, 3600, ("Building_1", "Building_2"), series, {"carbon_intensity": list(carbon)}, units, "USD", "test", "h")


def test_export_is_credited_per_building_at_its_own_price_and_district_peak_is_signed_sum():
    summary = tool.summarize_trace(_trace((1.0, -1.0, 2.0), (2.0, 0.0, -1.0)))
    assert summary["import_mwh"] == pytest.approx(5.0 / 1000)
    assert summary["export_mwh"] == pytest.approx(2.0 / 1000)
    # A: (1 - 1 + 2) * 0.1; B: (2 + 0 - 1) * 0.2. A single district price could not give this.
    assert summary["cost_usd"] == pytest.approx(0.4)
    assert summary["co2_kg"] == pytest.approx(3.0 * 0.5)
    assert summary["district_peak_kw"] == pytest.approx(3.0)
    assert summary["battery_throughput_kwh"] == pytest.approx(3.0)
    # These hours are outside the 18:00-23:00 block: energy and fixed charge only.
    assert summary["bill_energy_usd"] == pytest.approx(0.4)
    assert summary["bill_demand_usd"] == 0.0
    assert summary["bill_total_usd"] == pytest.approx(0.4 + 2.0)


def test_a_building_without_official_rate_is_refused_not_billed_at_zero(monkeypatch):
    monkeypatch.setattr(tool, "load_rates", lambda: {})
    with pytest.raises(ValueError):
        tool.summarize_trace(_trace((1.0, 1.0, 1.0), (1.0, 1.0, 1.0)))


def test_flat_price_and_constant_carbon_make_cost_and_co2_exactly_proportional():
    hourly = tool.hourly_cost_co2(_trace((1.0, 3.0, 2.0), (2.0, 6.0, 4.0)))
    assert tool.pearson(*hourly) == pytest.approx(1.0)


def test_varying_carbon_breaks_the_proportionality():
    hourly = tool.hourly_cost_co2(_trace((1.0, 3.0, 2.0), (2.0, 6.0, 4.0), carbon=(0.9, 0.1, 0.5)))
    assert tool.pearson(*hourly) < 0.9


def test_constant_series_has_no_defined_correlation():
    assert tool.pearson([1.0, 1.0], [1.0, 2.0]) is None


def test_delta_reports_whether_cost_and_co2_move_together():
    base = dict(cost_usd=100.0, co2_kg=50.0, district_peak_kw=10.0, net_mwh=1.0,
                bill_total_usd=200.0, bill_demand_usd=50.0)
    control = dict(cost_usd=101.0, co2_kg=51.0, district_peak_kw=9.0, net_mwh=1.1,
                   bill_total_usd=190.0, bill_demand_usd=40.0)
    delta = tool.paired_delta(control, base)
    assert delta["cost_usd"] == pytest.approx(1.0)
    assert delta["peak_percent"] == pytest.approx(-10.0)
    assert delta["cost_and_co2_same_direction"] is True
    assert delta["bill_and_co2_same_direction"] is False


def test_percent_keeps_the_direction_when_the_base_is_negative():
    # A net-exporting district earns money and credits CO2: going from -100 to -90 is a loss.
    base = dict(cost_usd=-100.0, co2_kg=-50.0, district_peak_kw=10.0, net_mwh=-1.0,
                bill_total_usd=-100.0, bill_demand_usd=0.0)
    worse = dict(cost_usd=-90.0, co2_kg=-45.0, district_peak_kw=10.0, net_mwh=-0.9,
                 bill_total_usd=-90.0, bill_demand_usd=0.0)
    delta = tool.paired_delta(worse, base)
    assert delta["cost_percent"] == pytest.approx(10.0)
    assert delta["co2_percent"] == pytest.approx(10.0)
    assert delta["bill_percent"] == pytest.approx(10.0)


def test_price_seen_counts_what_the_trace_used():
    seen = tool.price_seen(_trace((1.0, 1.0, 1.0), (1.0, 1.0, 1.0), price_b=(0.2, 0.3, 0.2)))
    assert seen["distinct_price_series"] == 2
    assert seen["max_values_per_building_price"] == 2
    assert (seen["price_min"], seen["price_max"]) == (0.1, 0.3)
    assert seen["carbon_values"] == 1


def test_comparison_uses_the_declared_scenario_catalog():
    assert tool.SCENARIO_CATALOG == REPO / "configs/scenarios.yaml"
    assert tool.SCENARIO_CATALOG.is_file()


def test_test_split_stays_sealed(tmp_path):
    with pytest.raises(SystemExit) as error:
        tool.main(["--campaigns", "iquitos_v1", "iquitos_v4", "--split", "test_2025",
                   "--output", str(tmp_path / "out.json")])
    assert error.value.code == 2
    assert not (tmp_path / "out.json").exists()
