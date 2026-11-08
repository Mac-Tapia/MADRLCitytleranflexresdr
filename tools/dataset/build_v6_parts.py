"""Pieces of the iquitos_v6 build that replace v5 steps (SPEC-016 T2, docs/plans/modulo3b_iquitos_v6.md).

- ``remove_washing_machines``: the washing machines leave the schema, the files and the actions; in v6 their
  energy is base load (D-V6-1).
- ``distill_v6``: the physical distillation (D-V6-14 to D-V6-20) replaces the residual one; each building's
  cooling power is fixed at capacity / design COP instead of being autosized from the modelled demand
  (FR-016.3).
- ``capped_block_flags``: the bill blocks where physics exceeded the bill, declared without blocking (D-V6-19).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

import distill_building_loads as dl


def remove_washing_machines(dataset_dir: Path, schema: dict) -> list:
    removed = []
    for name, building in schema['buildings'].items():
        if building.pop('washing_machines', None) is not None:
            removed.append(name)
        for key in ('inactive_actions', 'inactive_observations'):
            if isinstance(building.get(key), list):
                building[key] = [n for n in building[key] if 'washing_machine' not in n]
    for path in Path(dataset_dir).glob('Washing_Machine_*.csv'):
        path.unlink()
    for key in ('actions', 'observations'):
        if isinstance(schema.get(key), dict):
            for name in [n for n in schema[key] if 'washing_machine' in n]:
                schema[key].pop(name)
    return removed


def distill_v6(dataset_dir: Path, schema: dict, weather: pd.DataFrame, *, norms: Mapping,
               measurements: pd.DataFrame, buildings: Iterable[int], inventory=None) -> dict:
    results = {}
    for building in buildings:
        result = dl.calibrate_building_physical(building, schema, weather, norms=norms, dataset_dir=Path(dataset_dir),
                                                measurements=measurements, inventory=inventory)
        config = schema['buildings'][f'Building_{building}']
        cooling = config['cooling_device']
        cooling['autosize'] = False
        cooling.setdefault('attributes', {})['nominal_power'] = round(float(result.nominal_power_kw), 6)
        if result.thermal is not None:             # D-V6-53: the air conditioning is an action with 5R1C dynamics
            config['type'] = result.thermal['type']
            config['dynamics'] = result.thermal['dynamics']
        result.report['delta_%'] = monthly_closure_pct(dataset_dir, schema, building, weather, result.report,
                                                       inventory)
        results[building] = result
    if any(r.thermal is not None for r in results.values()):
        schema.setdefault('actions', {})['cooling_device'] = {'active': True}
        for name in THERMAL_OBSERVATIONS:
            schema.setdefault('observations', {})[name] = {'active': True, 'shared_in_central_agent': False}
    return results


# D-V6-53 / FR-016.10: what an agent needs to see to keep comfort (the indoor temperature is already observed).
THERMAL_OBSERVATIONS = ('indoor_dry_bulb_temperature_cooling_set_point', 'occupant_count')


def operating_hours(frame: pd.DataFrame, schedule):
    """D-V6-60: hours the function of the building runs: its occupied hours on the days its schedule works."""
    import numpy as np
    opening, closing = (int(h) for h in schedule['occupied_hours'])
    weekday, saturday, sunday = schedule['day_factors_weekday_saturday_sunday']
    day = frame['day_type'].to_numpy(dtype=int)
    factor = np.where(day <= 5, weekday, np.where(day == 6, saturday, sunday))
    clock = frame['hour'].to_numpy(dtype=int) % 24     # 0..23 in this dataset, as the schedule profiles
    return (clock >= opening) & (clock < closing) & (factor >= OPEN_DAY_FACTOR)


MIN_BASE_SHARE = 0.05   # D-V6-5: the base load never stops; same 5 % as the base shape of the distillation
OPEN_DAY_FACTOR = 0.5   # D-V6-60: a day counts as open when the schedule keeps at least half its weekday activity


def hold_temperature_by_schedule(dataset_dir: Path, schema: dict, weather: pd.DataFrame, *, buildings: Iterable[int],
                                 schedules, cooling_cop, max_set_point_c: float, natural_ach: float = 0.0,
                                 height: float = 3.0, peak_hours=(), fit_zone: bool = True, peak_caps=None) -> dict:
    """D-V6-60, as the CityLearn dataset citylearn_challenge_2023_phase_1: the temperature follows the set point
    because the cooling of the CSV is the load that holds it.

    The set point and the hours come from the function of the building. The conditioned zone is the area the billed
    cooling pays for, and each hour's electricity is kept: what cooling stops using moves to the base load of that
    hour, so bills and hourly peaks do not change, and any shortfall moves within the same block of the same month
    (the bill separates peak and off-peak). ``fit_zone=False`` keeps the zone already written in the schema: it
    settles the cooling after another step reshaped the base load. ``peak_caps(b)`` gives the hourly limit of the bill
    peak: the zone cannot need more electricity in one hour than the bill's peak allows."""
    import numpy as np
    from citylearn.v3 import thermal as th

    report = {}
    for building in buildings:
        building_schema = schema['buildings'][f'Building_{building}']
        dynamics = building_schema.get('dynamics')
        if not dynamics:
            continue
        schedule = schedules[int(building)]
        path = Path(dataset_dir)/f'Building_{building}.csv'
        frame = pd.read_csv(path)
        operating = operating_hours(frame, schedule)
        set_point = min(float(schedule['cooling_setpoint_c']), float(max_set_point_c))
        attributes = dict(dynamics['attributes'], set_point=set_point)
        points = np.where(operating, set_point, 99.0)    # no load is ever needed at 99 C: the equipment is off
        old_cooling = frame['cooling_demand'].to_numpy(dtype=float)
        target = float(old_cooling.sum())
        cop = np.asarray(cooling_cop(building), dtype=float)
        electric = frame['non_shiftable_load'].to_numpy(dtype=float) + old_cooling/cop
        base = frame['non_shiftable_load'].to_numpy(dtype=float)
        people = frame['occupant_count'].to_numpy(dtype=float)
        calendar_month = frame['month'].to_numpy(dtype=int)     # the year turns when the month falls (2024 has 8784 h)
        months = calendar_month + 100*np.concatenate(([0], np.cumsum(np.diff(calendar_month) < 0)))
        months = months*2 + np.isin(frame['hour'].to_numpy(dtype=int), list(peak_hours))    # month and bill block
        month_index = np.unique(months, return_inverse=True)[1]
        month_electric = np.bincount(month_index, weights=electric)
        cap = None if peak_caps is None else np.asarray(peak_caps(building), dtype=float)

        def ideal(scale, base_kwh):
            a = dict(attributes, floor_area_m2=attributes['floor_area_m2']*scale,
                     ventilation_m3_s=attributes['ventilation_m3_s']*scale,
                     natural_ventilation_m3_s=natural_ach*attributes['floor_area_m2']*scale*height/3600.0,
                     electric_gain_fraction=attributes['electric_gain_fraction']*scale)
            model = th.ISO13790Dynamics(**a)
            inputs = th.ThermalInputs(
                theta_e=weather['outdoor_dry_bulb_temperature'].to_numpy(dtype=float),
                rh_e=weather['outdoor_relative_humidity'].to_numpy(dtype=float),
                irradiance_w_m2=(weather['diffuse_solar_irradiance'] + weather['direct_solar_irradiance']).to_numpy(float),
                electric_gain_w=base_kwh*1000.0*model.electric_gain_fraction, occupants=people*scale,
                pressure_kpa=model.pressure_kpa)
            series = th.ideal_cooling_series(model.params, inputs, set_point=points, ventilation_m3_s=model.ventilation_m3_s,
                                             w_in=model.w_in, theta_m0=set_point,
                                             natural_ventilation_m3_s=model.natural_ventilation_m3_s)
            return (series['sensible_w'] + np.where(operating, series['latent_w'], 0.0))/1000.0, series['theta_air'], a

        def affordable(scale, base_kwh):
            # The area the bills pay for: no more cooling than billed in the year, nor than any month's electricity.
            load = ideal(scale, base_kwh)[0]
            used = np.bincount(month_index, weights=load/cop)
            within_peak = cap is None or bool(np.all(load/cop <= (1.0 - MIN_BASE_SHARE)*cap))
            return load.sum() <= target and within_peak and bool(np.all(used <= (1.0 - MIN_BASE_SHARE)*month_electric))

        def fit_scale(base_kwh):
            low, high = 1e-4, 1.0
            if affordable(high, base_kwh):
                return high
            for _ in range(18):
                middle = (low*high)**0.5
                low, high = (middle, high) if affordable(middle, base_kwh) else (low, middle)
            return low

        scale, cooling, new_base = 1.0, old_cooling, base
        for _ in range(2 if fit_zone else 0):             # the base load is an internal gain: settle it once
            scale = fit_scale(new_base)
            cooling = ideal(scale, new_base)[0]
            new_base = _move_within_month(electric - cooling/cop, months)
        for _ in range(6):                                # settle cooling and base so the set point is really held
            cooling, theta, final = ideal(scale, new_base)
            new_base = _move_within_month(electric - cooling/cop, months)
        frame['cooling_demand'] = cooling
        frame['non_shiftable_load'] = new_base
        frame['occupant_count'] = people*scale
        frame['indoor_relative_humidity'] = _indoor_humidity(theta, operating, weather, final, th)
        frame.to_csv(path, index=False, float_format='%.6f')
        dynamics['attributes'] = {key: (round(value, 6) if isinstance(value, float) else value) for key, value in final.items()}
        report[int(building)] = {
            'set_point_c': set_point, 'conditioned_area_m2': round(final['floor_area_m2'], 1), 'zone_scale': round(scale, 4),
            'operating_share': round(float(operating.mean()), 4),
            'cooling_annual_change_pct': round(100.0*(float(cooling.sum())/target - 1.0), 3) if target else 0.0,
            'electric_change_max_kwh': round(float(np.abs(frame['non_shiftable_load'].to_numpy() + cooling/cop - electric).max()), 3)}
    return report


def bill_peak_caps(targets, building, *, years, months, threshold: float, margin: float):
    """Hourly electricity limit of each measured month: the edge of its bill-implied peak; infinite elsewhere."""
    import numpy as np

    from uc3m.application.dataset import peak_contrast as pc
    caps = np.full(len(months), np.inf)
    for t in targets:
        if (t.building_id != building or t.provenance != 'measured' or not t.load_factor
                or not 0 < t.load_factor <= 1 or any(f in t.flags for f in pc.EXCLUDED_FLAGS)):
            continue
        mask = (years == t.year) & (months == t.month)
        if mask.any():
            caps[mask] = t.energy_kwh/(t.load_factor*int(mask.sum()))*(1.0 + threshold)*(1.0 - margin)
    return caps


def _move_within_month(base, months, floor_share: float = MIN_BASE_SHARE):
    """Hours below the floor take their shortfall from the rest of the month; the monthly energy stays."""
    import numpy as np
    out = np.array(base, dtype=float)
    for month in np.unique(months):
        where = months == month
        values = out[where]
        total = values.sum()
        if total <= 0.0:
            raise ValueError(f'month {month}: cooling exceeds all the billed electricity')
        floor = floor_share*total/len(values)
        lacking = values < floor
        if lacking.any():
            shortfall = (floor - values[lacking]).sum()
            values[lacking] = floor
            spare = values[~lacking] - floor
            values[~lacking] -= shortfall*spare/spare.sum()
            out[where] = values
    return out


def _indoor_humidity(theta, operating, weather, attributes, th):
    """Relative humidity of the air at its temperature: design humidity ratio with the equipment on, outdoor air off."""
    import numpy as np
    pressure = attributes['pressure_kpa']
    w_in = th.humidity_ratio(attributes['set_point'], attributes['indoor_rh_pct'], pressure)
    outdoor = weather['outdoor_dry_bulb_temperature'].to_numpy(dtype=float)
    humidity = weather['outdoor_relative_humidity'].to_numpy(dtype=float)
    out = np.zeros(len(theta))
    for h in range(len(theta)):
        w = w_in if operating[h] else th.humidity_ratio(outdoor[h], humidity[h], pressure)
        out[h] = 100.0*w/th.humidity_ratio(theta[h], 100.0, pressure)
    return np.clip(out, 0.0, 100.0)


def indoor_temperature_gate(dataset_dir: Path, schema: dict, *, buildings: Iterable[int], schedules, low_c: float,
                            high_c: float, outdoor_c=None, off_hours_excess_c: float = None) -> dict:
    """D-V6-60 and D-V6-61: inside the owner's range in the operating hours of each function, never below it, and
    with the equipment off no hotter than the outdoor air plus a margin."""
    import numpy as np
    rows = {}
    for building in buildings:
        frame = pd.read_csv(Path(dataset_dir)/f'Building_{building}.csv')
        theta = frame['indoor_dry_bulb_temperature'].to_numpy(dtype=float)
        operating = operating_hours(frame, schedules[int(building)])
        excess = float((theta - np.asarray(outdoor_c, dtype=float))[~operating].max()) if outdoor_c is not None and (~operating).any() else None
        rows[int(building)] = {'operating_min_c': float(theta[operating].min()), 'operating_max_c': float(theta[operating].max()),
                               'overall_min_c': float(theta.min()), 'overall_max_c': float(theta.max()),
                               'off_hours_excess_over_outdoor_c': excess}
    tolerance = 0.05     # rounding of the CSV and the one-step mass update of the 5R1C
    passed = all(row['operating_max_c'] <= high_c + tolerance and row['overall_min_c'] >= low_c - tolerance
                 and (off_hours_excess_c is None or row['off_hours_excess_over_outdoor_c'] is None
                      or row['off_hours_excess_over_outdoor_c'] <= off_hours_excess_c)
                 for row in rows.values())
    return {'low_c': low_c, 'high_c': high_c, 'off_hours_excess_c': off_hours_excess_c, 'passed': passed, 'buildings': rows}


def write_indoor_temperature(dataset_dir: Path, schema: dict, weather: pd.DataFrame, *, buildings: Iterable[int],
                             band_c: float, comfort_limit_c: float = None) -> dict:
    """D-V6-53: indoor temperature without control = the 5R1C model of the schema under the delivered cooling of
    the final CSV (after the peak re-distillation), the same equations CityLearn runs. Returns the share of
    occupied hours within the comfort band of every building."""
    import numpy as np
    from citylearn.v3 import thermal as th

    report = {}
    for building in buildings:
        dynamics = schema['buildings'][f'Building_{building}'].get('dynamics')
        if not dynamics:
            continue
        a = dynamics['attributes']
        model = th.ISO13790Dynamics(**a)
        path = Path(dataset_dir)/f'Building_{building}.csv'
        frame = pd.read_csv(path)
        inputs = th.ThermalInputs(
            theta_e=weather['outdoor_dry_bulb_temperature'].to_numpy(dtype=float),
            rh_e=weather['outdoor_relative_humidity'].to_numpy(dtype=float),
            irradiance_w_m2=(weather['diffuse_solar_irradiance'] + weather['direct_solar_irradiance']).to_numpy(float),
            electric_gain_w=frame['non_shiftable_load'].to_numpy(dtype=float)*1000.0*model.electric_gain_fraction,
            occupants=frame['occupant_count'].to_numpy(dtype=float), pressure_kpa=model.pressure_kpa)
        theta = th.simulate_delivered(model.params, inputs, frame['cooling_demand'].to_numpy(dtype=float),
                                      ventilation_m3_s=model.ventilation_m3_s, w_in=model.w_in,
                                      theta_m0=model.set_point,
                                      natural_ventilation_m3_s=model.natural_ventilation_m3_s)
        frame['indoor_dry_bulb_temperature'] = theta
        occupied = inputs.occupants > 0
        # D-V6-54 (owner, 2026-11-08): comfort no worse than today. The hourly set point the reward and the
        # CityLearn comfort KPIs read is max(design set point, temperature as billed - band), so the comfort limit
        # (set point + band) is max(24 + band, the building's temperature with its billed cooling).
        # D-V6-60: with a limit, the comfort band of the reward ends there, whatever the set point of the function.
        reference = model.set_point if comfort_limit_c is None else min(model.set_point, float(comfort_limit_c) - band_c)
        frame['indoor_dry_bulb_temperature_cooling_set_point'] = np.where(
            occupied, np.maximum(reference, theta - band_c), reference)
        frame.to_csv(path, index=False, float_format='%.6f')
        report[int(building)] = {
            'comfort_reference': 'max(24 C + band, temperature as billed) (D-V6-54)',
            'occupied_hours': int(occupied.sum()),
            'within_band_share': float(np.mean(theta[occupied] <= model.set_point + band_c)) if occupied.any() else 1.0,
            'max_occupied_c': float(theta[occupied].max()) if occupied.any() else None}
    return report


def monthly_closure_pct(dataset_dir: Path, schema: dict, building: int, weather: pd.DataFrame,
                        report: pd.DataFrame, inventory=None) -> pd.Series:
    """Generated electricity of each month, read back from the written CSV, against its bill [%]."""
    frame = dl.build_month_year_index(pd.read_csv(Path(dataset_dir)/f'Building_{building}.csv'))
    t_out = weather['outdoor_dry_bulb_temperature'].to_numpy(dtype=float)
    cop = dl.citylearn_cooling_cop(t_out, *dl.physical_cop_params(schema, building))
    _, cop_dhw = dl.get_cop_params(schema, building, dl.DEFAULT_INVENTORY if inventory is None else inventory)
    electric = frame['non_shiftable_load'] + frame['cooling_demand']/cop
    if 'dhw_demand' in frame:
        electric = electric + frame['dhw_demand']/cop_dhw
    generated = electric.groupby([frame['_year'], frame['_month']]).sum()
    deltas = []
    for row in report.itertuples(index=False):
        billed = row.E_peak_medido_kWh + row.E_offpeak_medido_kWh
        deltas.append(100.0*(generated.loc[(row.year, row.mes)] - billed)/billed)
    return pd.Series(deltas, index=report.index)


def capped_block_flags(results: Mapping) -> list:
    return [{'building_id': int(b), 'year': year, 'month': month, 'block': block,
             'flag': 'cooling_capped_by_bill',
             'note': 'physical cooling exceeded the bill block; capped and declared (D-V6-19)'}
            for b, result in results.items() for year, month, block in result.capped_blocks]


def size_v6_bess(load_kwh_h, pv_kwh_h, ev_kwh_h, peak_block_h, *, model, shift_fraction: float,
                 ev_charging_power_kw: float):
    """D-V6-7 and D-V6-30: dual-function BESS of one building from its hourly load, PV and EV charging.

    Surplus = PV above load; block import = load + EV - PV in the peak block; size_bess takes the larger of the
    surplus-plus-EV energy and the shifted peak energy, and the largest of surplus, EV and shaved power.
    """
    import numpy as np

    from uc3m.application.dataset import bess_sizing as bs
    load, pv, ev = (np.asarray(x, dtype=float) for x in (load_kwh_h, pv_kwh_h, ev_kwh_h))
    return bs.size_bess(surplus_kwh_h=np.clip(pv - load, 0.0, None), ev_kwh_h=np.clip(ev, 0.0, None),
                        ev_charging_power_kw=float(ev_charging_power_kw), model=model,
                        block_import_kwh_h=np.clip(load + ev - pv, 0.0, None),
                        peak_block_h=np.asarray(peak_block_h, dtype=bool), shift_fraction=float(shift_fraction))


def bess_attributes(size) -> dict:
    """CityLearn Battery attributes of a sized BESS, with the catalog model's own parameters."""
    return {'capacity': float(size.capacity_kwh), 'nominal_power': float(size.nominal_power_kw),
            'efficiency': float(size.model.efficiency), 'depth_of_discharge': float(size.model.depth_of_discharge),
            'loss_coefficient': float(size.model.loss_coefficient), 'initial_soc': 0.0,
            'capacity_loss_coefficient': 1e-5}


def redistill_peaks(dataset_dir: Path, *, buildings, targets, threshold: float, peak_hours, other_kw, years,
                    cooling_cop=None, edge_margin: float = 1e-3) -> list:
    """FR-016.8 and D-V6-47: reshape the base load of every measured month outside +/-threshold of its bill peak.

    implied peak = E / (load factor x hours); the target is the nearest threshold edge. Only the base load
    (non_shiftable_load) changes, mean-preserving inside each bill block, so the bills stay reproduced. Synthetic
    or flagged months and months without a load factor are left as they are. ``other_kw(b)`` gives the hourly
    electricity of the rest of the building (cooling, DHW) and ``years`` the year of every row.

    D-V6-55 (owner, 2026-11-08): when the base alone cannot reach the target and ``cooling_cop(b)`` gives the hourly
    COP, base and cooling electricity are reshaped together inside each block (same factor per hour on both), so
    the block energy and the bill stay exact; the cooling of those months changes shape and is declared.
    """
    import numpy as np

    from uc3m.application.dataset import peak_contrast as pc
    rows = []
    years = np.asarray(years)
    for building in buildings:
        path = Path(dataset_dir)/f'Building_{building}.csv'
        frame = pd.read_csv(path)
        base = frame['non_shiftable_load'].to_numpy(dtype=float).copy()
        other = np.asarray(other_kw(building), dtype=float)[:len(base)]
        cop = None if cooling_cop is None else np.asarray(cooling_cop(building), dtype=float)[:len(base)]
        cooling = None if cop is None else frame['cooling_demand'].to_numpy(dtype=float)/cop
        month, hour = frame['month'].to_numpy(dtype=int), frame['hour'].to_numpy(dtype=int)
        changed = False
        for t in targets:
            if (t.building_id != building or t.provenance != 'measured' or not t.load_factor
                    or not 0 < t.load_factor <= 1 or any(f in t.flags for f in pc.EXCLUDED_FLAGS)):
                continue
            mask = (years[:len(base)] == t.year) & (month == t.month)
            if not mask.any():
                continue
            implied = t.energy_kwh/(t.load_factor*int(mask.sum()))
            ratio = float((base[mask] + other[mask]).max())/implied
            if ratio <= 1.0 + threshold + 1e-9:      # D-V6-48: only peaks above the bill's are corrected
                continue
            target = implied*(1.0 + threshold)*(1.0 - edge_margin)   # just inside the edge (6-decimal CSV rounding)
            block = np.isin(hour[mask], list(peak_hours))
            new, status = pc.reshape_month(base[mask], other[mask], block, target_peak_kw=target)
            base[mask] = new
            if status == 'unresolved' and cooling is not None:
                joint = base[mask] + cooling[mask]
                joint_new, status = pc.reshape_month(joint, other[mask] - cooling[mask], block, target_peak_kw=target)
                if status == 'resolved':
                    factor = np.divide(joint_new, joint, out=np.ones_like(joint), where=joint > 0)
                    previous = cooling[mask].copy()
                    base[mask] = base[mask]*factor
                    cooling[mask] = previous*factor
                    other[mask] = other[mask] + cooling[mask] - previous
                    status = 'resolved_with_cooling'
            changed |= status in ('resolved', 'resolved_with_cooling')
            rows.append({'building_id': int(building), 'year': t.year, 'month': t.month, 'ratio_before': ratio,
                         'target_peak_kw': target, 'status': status,
                         'ratio_after': float((base[mask] + other[mask]).max())/implied})
        if changed:
            frame['non_shiftable_load'] = base
            if cooling is not None:
                frame['cooling_demand'] = cooling*cop
            frame.to_csv(path, index=False, float_format='%.6f')
    return rows
