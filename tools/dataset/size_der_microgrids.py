"""Rooftop PV and BESS sizing per building with the MicroGrids LP (campaign v2).

Chain (owner decision 2026-11-01):
  1. pvlib ModelChain SAPM (tools/dataset/fix_solar_pvlib.py, Sandia module and
     inverter, observed-year NASA POWER weather of the build) gives the hourly AC
     energy of 1 kWp.
  2. MicroGrids' LP formulation (external/MicroGrids; upstream constraints plus
     the documented export term, docs/contributions/MicroGrids/CHANGES.md#exportacion-red)
     chooses PV kWp and BESS kWh at least net present cost for the building's
     hourly as-billed demand of the training year 2023 (no held-out year enters
     the design).
  3. external/prosumpy ``dispatch_max_sc`` replays the same series with the
     chosen sizes and records self-consumption, grid import and peak import.

Mapping of the on-grid supply to MicroGrids' generator (declared in
configs/dataset/der_economics.yaml): Generator_Efficiency = Low_Heating_Value = 1,
so the marginal cost per kWh is Diesel_Unitary_Cost = the building's 2023 energy
price [USD/kWh]; generator capex and O&M are zero; Generator_Nominal_Capacity is
bounded below by the observed hourly peak and lost load is forbidden.

Export (user decision 2026-11-01, overriding the earlier zero-export rule): every
building is grid-connected and nothing is wasted. Surplus PV is stored or injected
into the public grid (Allow_Curtailment = 0) and credited at the building's
purchase price (Export_Price = Diesel_Unitary_Cost): net billing, which does not
exist in Iquitos today and is a declared scenario. MicroGrids has a single
marginal cost, therefore neither time-of-use arbitrage nor storage of surplus PV
earns anything that export does not already earn: the LP has no economic reason
to install a battery.

Units: the LP is unit-homogeneous; this module feeds kW, kWh, USD/kW and USD/kWh
(one PV unit = 1 kWp, PV_Nominal_Capacity = 1, Inverter_Efficiency = 1 because the
pvlib series is already AC). The PV upper bound is the covered built area
(Area_Techada_m2), which is NOT the roof footprint and is used only as a bound.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Mapping

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MICROGRIDS_DIR = ROOT/'external/MicroGrids/MicroGrids'
PROSUMPY_DIR = ROOT/'external/prosumpy'
DEFAULT_SOLVER = 'appsi_highs'
ECONOMICS_PATH = ROOT/'configs/dataset/der_economics.yaml'
HOURS_2023 = 8760
MIN_BESS_KWH = 1.0  # below this the LP result is reported as no battery


def load_economics(path: Path = ECONOMICS_PATH) -> dict:
    import yaml
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def _v(entry):
    return entry['value']


# ── PV per kWp from pvlib ────────────────────────────────────────────────────

def pv_ac_w_per_kw(weather: pd.DataFrame, n_modules: int, module_params: dict) -> pd.Series:
    """Hourly AC output [W per kW DC] of a Sandia array of n_modules (fix_solar_pvlib chain)."""
    import fix_solar_pvlib as fs
    module_kwp = float(module_params['Vmpo']*module_params['Impo']/1000.0)
    pdc_kw = n_modules*module_kwp
    _, inverter, n_inverters = fs.select_sandia_inverter(pdc_kw)
    return fs.calc_solar_pvlib(weather_full=weather, n_modules=n_modules, modules_per_string=fs.MODULES_PER_STRING,
                               module_params=module_params, inverter_params=inverter, n_inverters=n_inverters,
                               bldg_id=0, pdc_kw=pdc_kw)


def roof_bound_kwp(area_m2: float, module_params: dict, usable_fraction: float = 1.0) -> float:
    """Upper bound: modules packed on area x usable_fraction (covered built area unless a roof survey exists)."""
    n = int(float(area_m2)*float(usable_fraction)//float(module_params['Area']))
    return n*float(module_params['Vmpo']*module_params['Impo']/1000.0)


def load_bound_kwp(annual_load_kwh: float, pv_kwh_per_kwp, max_ratio: float) -> float:
    """Upper bound: the capacity whose annual output is max_ratio of the building's annual load (SPEC-014)."""
    annual_per_kwp = float(np.sum(pv_kwh_per_kwp))
    if annual_per_kwp <= 0 or float(max_ratio) <= 0:
        raise ValueError('the load bound needs a positive PV yield and a positive ratio')
    return float(annual_load_kwh)*float(max_ratio)/annual_per_kwp


def binding_pv_bound(pv_kwp_lp: float, roof_kwp: float, load_kwp: float):
    """Which bound limited the LP: 'area', 'load' or None. A tie is reported as the physical one."""
    if pv_kwp_lp < min(roof_kwp, load_kwp) - 1e-3:
        return None
    return 'area' if roof_kwp <= load_kwp else 'load'


def pv_to_load_gate(rows: Mapping, max_ratio: float) -> bool:
    """Every building at or under the limit. Missing values fail: an unmeasured ratio is not a pass."""
    ratios = [row.get('pv_to_load_ratio_2023') for row in rows.values()]
    return bool(ratios) and all(r is not None and r <= float(max_ratio) for r in ratios)


def fit_pv_modules(n_modules: int, annual_load_kwh: float, annual_pv_kwh, max_ratio: float) -> int:
    """The largest count up to n_modules whose real array output stays within max_ratio of the load.

    The LP bound uses a reference array's yield per kWp; each real array selects its own inverter, and
    small arrays yield more per kWp (B14 reached 1.165 in the first iquitos_v5 build). annual_pv_kwh(n)
    is the design-year output of the real n-module array. Never adds modules beyond the LP's choice.
    """
    limit = float(max_ratio)*float(annual_load_kwh)
    if limit <= 0:
        return 0
    n = int(n_modules)
    while n > 0 and annual_pv_kwh(n) > limit:
        n = min(int(n*limit/annual_pv_kwh(n)), n - 1)
    while n < int(n_modules) and annual_pv_kwh(n + 1) <= limit:
        n += 1
    return n


# ── MicroGrids LP ────────────────────────────────────────────────────────────

def _write_inputs(workdir: Path, demand_kwh: np.ndarray, pv_kwh_per_kwp: np.ndarray, price: float,
                  economics: Mapping, capex_scale: float, tariff: Mapping = None) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    periods = np.arange(1, len(demand_kwh) + 1)
    # MicroGrids reads Demand.xls / PV_Energy.xls with pandas (engine from file content).
    pd.DataFrame({1: demand_kwh}, index=periods).to_excel(workdir/'Demand.xls', engine='openpyxl')
    pd.DataFrame({1: pv_kwh_per_kwp}, index=periods).to_excel(workdir/'PV_Energy.xls', engine='openpyxl')
    pv, bess, project = economics['pv'], economics['bess'], economics['project']
    grid = economics['grid_supply_mapping']
    params = {
        'Periods': len(demand_kwh), 'Years': int(_v(project['project_years'])), 'StartDate': "'01/01/2023 00:00:00'",
        'PlotTime': 1, 'PlotDay': "'01/01/2023 00:00:00'", 'PlotScenario': 1, 'Delta_Time': 1.0,
        'PV_invesment_Cost': 1000.0*float(_v(pv['capex_usd_per_wp']))*capex_scale,  # USD per kWp
        'Battery_Invesment_Cost': 1000.0*float(_v(bess['capex_usd_per_wh']))*capex_scale,  # USD per kWh
        'Generator_Invesment_Cost': float(grid['generator_invesment_cost_usd_per_w']),
        'Maintenance_Operation_Cost_PV': float(_v(pv['om_fraction_of_capex_per_year'])),
        'Maintenance_Operation_Cost_Battery': float(_v(bess['om_fraction_of_capex_per_year'])),
        'Maintenance_Operation_Cost_Generator': float(grid['maintenance_operation_cost_generator']),
        'Diesel_Unitary_Cost': 0.0 if tariff else float(price), 'Discount_Rate': float(_v(project['discount_rate'])),
        'Interest_Rate_Loan': float(_v(project['loan_interest_rate'])),
        'Lost_Load_Probability': float(grid['lost_load_probability']),
        'Discharge_Battery_Efficiency': float(_v(bess['discharge_efficiency'])),
        'Charge_Battery_Efficiency': float(_v(bess['charge_efficiency'])),
        'Deep_of_Discharge': float(_v(bess['minimum_soc_fraction'])), 'Inverter_Efficiency': 1.0,
        'Generator_Efficiency': 1.0, 'Low_Heating_Value': 1.0,
        'Value_Of_Lost_Load': float(grid['value_of_lost_load_usd_per_wh']),
        'Porcentage_Funded': float(_v(project['fraction_funded_by_loan'])),
        'Maximun_Battery_Discharge_Time': float(_v(bess['max_discharge_time_h'])),
        'Maximun_Battery_Charge_Time': float(_v(bess['max_charge_time_h'])),
        'PV_Nominal_Capacity': 1.0, 'Battery_Reposition_Time': float(_v(bess['replacement_year'])),
        'Scenarios': 1,
        'Export_Price': 0.0 if tariff else float(price)*float(economics['export']['price_ratio_to_purchase']),
        'Allow_Curtailment': 0 if not economics['export']['curtailment_allowed'] else 1}
    if tariff:
        params['Months'] = int(max(tariff['period_month']))
    lines = [f'param: {name} := {value};\n' for name, value in params.items()]
    lines.append('param: Scenario_Weight :=\n1   1;\n')
    if tariff:
        # Hourly tariff (fork change docs/contributions/MicroGrids/CHANGES.md#tarifa-horaria-demanda).
        ratio = float(economics['export']['price_ratio_to_purchase'])
        prices = list(tariff['energy_price'])
        lines.append('param Grid_Energy_Price :=\n' + '\n'.join(f'1 {t} {v!r}' for t, v in enumerate(prices, 1)) + ';\n')
        lines.append('param Export_Price_Hourly :=\n'
                     + '\n'.join(f'1 {t} {ratio*v!r}' for t, v in enumerate(prices, 1)) + ';\n')
        lines.append('param Period_Month :=\n'
                     + '\n'.join(f'{t} {int(v)}' for t, v in enumerate(tariff['period_month'], 1)) + ';\n')
        lines.append('param Peak_Period :=\n'
                     + '\n'.join(f'{t} {int(v)}' for t, v in enumerate(tariff['peak_period'], 1)) + ';\n')
        lines.append('param Demand_Charge :=\n'
                     + '\n'.join(f'{m} {v!r}' for m, v in sorted(tariff['demand_charge'].items())) + ';\n')
    path = workdir/'data.dat'
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path


def _microgrids_modules(workdir: Path):
    os.environ['MICROGRIDS_DATA_DIR'] = str(workdir)
    if str(MICROGRIDS_DIR) not in sys.path:
        sys.path.insert(0, str(MICROGRIDS_DIR))
    import Initialize
    importlib.reload(Initialize)  # module-level Demand/PV tables follow MICROGRIDS_DATA_DIR
    import Model_Creation
    import Constraints
    return Model_Creation, Constraints


def solve_microgrids(demand_kwh: np.ndarray, pv_kwh_per_kwp: np.ndarray, price: float, roof_kwp: float,
                     economics: Mapping, workdir: Path, capex_scale: float = 1.0,
                     tariff: Mapping = None) -> Dict[str, object]:
    """MicroGrids LP (Model_Creation + Constraints, as Model_Resolution attaches them).

    ``tariff`` (campaign v3): hourly energy price [USD/kWh], also the net-billing export
    credit; billing month and peak-block flag per hour; and the monthly demand charge
    [USD/kW-month] on the maximum grid import inside the peak block.
    """
    from pyomo.environ import AbstractModel, Constraint, Objective, SolverFactory, minimize, value
    from pyomo.opt import TerminationCondition
    demand_kwh = np.asarray(demand_kwh, dtype=float)
    data = _write_inputs(Path(workdir), demand_kwh, np.asarray(pv_kwh_per_kwp, dtype=float), price, economics,
                         capex_scale, tariff)
    mc, c = _microgrids_modules(Path(workdir))
    model = AbstractModel()
    mc.Model_Creation(model)
    model.ObjectiveFuntion = Objective(rule=c.Net_Present_Cost, sense=minimize)
    model.EnergyBalance = Constraint(model.scenario, model.periods, rule=c.Energy_balance)
    model.MaximunLostLoad = Constraint(model.scenario, rule=c.Maximun_Lost_Load)
    model.ScenarioLostLoadCost = Constraint(model.scenario, rule=c.Scenario_Lost_Load_Cost)
    model.SolarEnergy = Constraint(model.scenario, model.periods, rule=c.Solar_Energy)
    model.StateOfCharge = Constraint(model.scenario, model.periods, rule=c.State_of_Charge)
    model.MaximunCharge = Constraint(model.scenario, model.periods, rule=c.Maximun_Charge)
    model.MinimunCharge = Constraint(model.scenario, model.periods, rule=c.Minimun_Charge)
    model.MaxPowerBatteryCharge = Constraint(rule=c.Max_Power_Battery_Charge)
    model.MaxPowerBatteryDischarge = Constraint(rule=c.Max_Power_Battery_Discharge)
    model.MaxBatIn = Constraint(model.scenario, model.periods, rule=c.Max_Bat_in)
    model.Maxbatout = Constraint(model.scenario, model.periods, rule=c.Max_Bat_out)
    model.MaximunDieselEnergy = Constraint(model.scenario, model.periods, rule=c.Maximun_Diesel_Energy)
    model.DieselComsuption = Constraint(model.scenario, model.periods, rule=c.Diesel_Comsuption)
    model.DieselCostTotal = Constraint(model.scenario, rule=c.Diesel_Cost_Total)
    model.FinancialCost = Constraint(rule=c.Financial_Cost)
    model.ScenarioNetPresentCost = Constraint(model.scenario, rule=c.Scenario_Net_Present_Cost)
    model.InitialInversion = Constraint(rule=c.Initial_Inversion)
    model.OperationMaintenanceCost = Constraint(rule=c.Operation_Maintenance_Cost)
    model.TotalFinalcialCost = Constraint(rule=c.Total_Finalcial_Cost)
    model.BatteryRepositionCost = Constraint(rule=c.Battery_Reposition_Cost)
    model.ScenarioExportRevenue = Constraint(model.scenario, rule=c.Scenario_Export_Revenue)
    model.NoCurtailment = Constraint(model.scenario, model.periods, rule=c.No_Curtailment)
    model.PeakDemandBound = Constraint(model.scenario, model.periods, rule=c.Peak_Demand_Bound)
    model.ScenarioGridCost = Constraint(model.scenario, rule=c.Scenario_Grid_Cost)
    instance = model.create_instance(str(data))
    instance.PV_Units.setub(float(roof_kwp))  # covered-area bound, not a roof survey
    instance.Generator_Nominal_Capacity.setlb(float(demand_kwh.max()))  # grid covers the observed peak
    solver_name = os.environ.get('MICROGRIDS_SOLVER', DEFAULT_SOLVER)
    started = time.perf_counter()
    results = SolverFactory(solver_name).solve(instance)
    elapsed = time.perf_counter() - started
    condition = results.solver.termination_condition
    out = {'solver': solver_name, 'termination_condition': str(condition), 'solve_seconds': round(elapsed, 2),
           'capex_scale': capex_scale}
    if condition != TerminationCondition.optimal:
        return out
    periods = list(instance.periods)
    series = lambda var: np.array([value(var[1, t]) for t in periods])  # noqa: E731
    pv = series(instance.Total_Energy_PV)
    curtailed = series(instance.Energy_Curtailment)
    grid = series(instance.Generator_Energy)
    lost = series(instance.Lost_Load)
    export = series(instance.Energy_Export)
    out.update({'pv_kwp': float(value(instance.PV_Units)), 'bess_kwh': float(value(instance.Battery_Nominal_Capacity)),
                'bess_max_discharge_kw': float(value(instance.Maximun_Discharge_Power)),
                'npc_usd': float(value(instance.ObjectiveFuntion)),
                'pv_kwh': float(pv.sum()), 'curtailed_kwh': float(curtailed.sum()), 'grid_kwh': float(grid.sum()),
                'lost_load_kwh': float(lost.sum()), 'grid_peak_kw': float(grid.max()),
                'export_kwh': float(export.sum()), 'export_price_usd_per_kwh': float(value(instance.Export_Price)),
                'export_revenue_npv_usd': float(value(instance.Scenario_Export_Revenue[1])),
                'export_revenue_year_usd': float(export.sum()*value(instance.Export_Price)),
                'battery_out_kwh': float(series(instance.Energy_Battery_Flow_Out).sum()),
                'battery_in_kwh': float(series(instance.Energy_Battery_Flow_In).sum())})
    if tariff:
        prices = np.asarray(tariff['energy_price'], dtype=float)
        ratio = float(economics['export']['price_ratio_to_purchase'])
        peaks = {int(m): float(value(instance.Peak_Demand[1, m])) for m in instance.months}
        out.update({'export_price_usd_per_kwh': float(prices.mean())*ratio,
                    'export_revenue_year_usd': float((export*prices).sum())*ratio,
                    'grid_energy_cost_year_usd': float((grid*prices).sum()),
                    'demand_charge_year_usd': float(sum(tariff['demand_charge'][m]*peaks[m] for m in peaks)),
                    'monthly_peak_block_max_kw': peaks,
                    'battery_net_out_kwh_series': (series(instance.Energy_Battery_Flow_Out)
                                                   - series(instance.Energy_Battery_Flow_In)).tolist()})
    return out


# ── prosumpy verification ────────────────────────────────────────────────────

def prosumpy_check(demand_kwh: np.ndarray, pv_kwh: np.ndarray, bess_kwh: float, economics: Mapping) -> dict:
    """dispatch_max_sc on the same series: no DER, PV only and PV + BESS."""
    if str(PROSUMPY_DIR) not in sys.path:
        sys.path.insert(0, str(PROSUMPY_DIR))
    from prosumpy.dispatch import dispatch_max_sc
    bess = economics['bess']
    index = pd.RangeIndex(len(demand_kwh))
    demand = pd.Series(np.asarray(demand_kwh, dtype=float), index=index)
    cases = {'no_der': (np.zeros(len(demand)), 0.0), 'pv_only': (np.asarray(pv_kwh, dtype=float), 0.0),
             'pv_bess': (np.asarray(pv_kwh, dtype=float), float(bess_kwh))}
    out = {'self_consumption_pct': {}, 'grid_import_kwh': {}, 'peak_import_kw': {}, 'exported_kwh': {}}
    for name, (pv, capacity) in cases.items():
        param = {'timestep': 1.0, 'BatteryCapacity': capacity*(1.0 - float(_v(bess['minimum_soc_fraction']))),
                 'BatteryEfficiency': float(_v(bess['charge_efficiency']))*float(_v(bess['discharge_efficiency'])),
                 'InverterEfficiency': 1.0,
                 'MaxPower': capacity/float(_v(bess['max_discharge_time_h'])) if capacity else 0.0}
        result = dispatch_max_sc(pd.Series(pv, index=index), demand, param, return_series=False)
        grid = np.asarray(result['grid2load'], dtype=float)
        to_load = np.asarray(result['inv2load'], dtype=float)
        total_pv = float(pv.sum())
        out['self_consumption_pct'][name] = round(100.0*float(to_load.sum())/total_pv, 4) if total_pv > 0 else 0.0
        out['grid_import_kwh'][name] = round(float(grid.sum()), 3)
        out['peak_import_kw'][name] = round(float(grid.max()), 3)
        out['exported_kwh'][name] = round(float(np.asarray(result['inv2grid'], dtype=float).sum()), 3)
    return out


def round_pv(pv_kwp_lp: float, module_params: dict, roof_kwp: float) -> tuple[int, float]:
    module_kwp = float(module_params['Vmpo']*module_params['Impo']/1000.0)
    n = int(round(pv_kwp_lp/module_kwp))
    if n > 0 and n*module_kwp > roof_kwp + 1e-9:
        # Search the original multiplication predicate. Dividing the roof by
        # module_kwp can lose panel counts above 2**53, where adjacent counts
        # may produce the same floating-point power. Zero is the same fallback
        # as in the old decrement loop when no positive count fits.
        lower, upper = 0, n
        while lower + 1 < upper:
            middle = (lower + upper)//2
            if middle*module_kwp <= roof_kwp + 1e-9:
                lower = middle
            else:
                upper = middle
        n = lower
    return n, n*module_kwp


def round_bess(bess_kwh_lp: float) -> float:
    return 0.0 if bess_kwh_lp < MIN_BESS_KWH else round(bess_kwh_lp, 1)


def bess_design_rule(block_peak_kw: float, block_hours: int, economics: Mapping, rule: Mapping) -> dict:
    """Declared peak-shaving size (configs/dataset/bess_design_rule.yaml), not an LP optimum."""
    bess = economics['bess']
    shaved = float(rule['shave_fraction_of_peak_block']['value'])*max(0.0, float(block_peak_kw))
    window = float(rule['soc_ceiling']['value']) - float(_v(bess['minimum_soc_fraction']))
    usable = float(_v(bess['discharge_efficiency']))*window
    capacity = round_bess(shaved*int(block_hours)/usable)
    if not capacity:
        return {'shaved_kw': 0.0, 'capacity_kwh': 0.0, 'nominal_power_kw': 0.0}
    return {'shaved_kw': shaved, 'capacity_kwh': capacity,
            'nominal_power_kw': round(capacity/float(_v(bess['max_discharge_time_h'])), 3)}


def bess_rule_curves(efficiency: float, rule: Mapping) -> dict:
    """Schema attributes that stop CityLearn from drawing the battery curves from the env seed."""
    return {'capacity_power_curve': [list(point) for point in rule['capacity_power_curve']['value']],
            'power_efficiency_curve': [[float(x), float(factor)*float(efficiency)]
                                       for x, factor in rule['power_efficiency_factors']['value']]}


def sensitivity(base: Mapping[int, Mapping], scaled: Mapping[float, Mapping[int, Mapping]], threshold: float) -> dict:
    rows, material = {}, False
    for b, row in base.items():
        entry = {'base': {'pv_kwp': row['pv_kwp'], 'bess_kwh': row['bess_kwh']}}
        for scale, results in scaled.items():
            other = results[b]
            entry[f'capex_x{scale:.2f}'] = {'pv_kwp': other.get('pv_kwp'), 'bess_kwh': other.get('bess_kwh'),
                                            'termination_condition': other['termination_condition']}
            for key in ('pv_kwp', 'bess_kwh'):
                a, o = row[key], other.get(key)
                if o is None:
                    continue
                scale_ref = max(abs(a), 1.0)
                if abs(o - a)/scale_ref > threshold:
                    material = True
                    entry.setdefault('material', []).append(f'{key} x{scale:.2f}: {a:.1f} -> {o:.1f}')
        rows[str(b)] = entry
    return {'buildings': rows, 'material_change': material}


def write_json(path: Path, payload) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


__all__ = ['load_economics', 'pv_ac_w_per_kw', 'roof_bound_kwp', 'load_bound_kwp', 'binding_pv_bound',
           'pv_to_load_gate', 'fit_pv_modules', 'solve_microgrids', 'prosumpy_check', 'round_pv', 'round_bess', 'sensitivity', 'write_json']
