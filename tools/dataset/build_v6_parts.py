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
        cooling = schema['buildings'][f'Building_{building}']['cooling_device']
        cooling['autosize'] = False
        cooling.setdefault('attributes', {})['nominal_power'] = round(float(result.nominal_power_kw), 6)
        result.report['delta_%'] = monthly_closure_pct(dataset_dir, schema, building, weather, result.report,
                                                       inventory)
        results[building] = result
    return results


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


def redistill_peaks(dataset_dir: Path, *, buildings, targets, threshold: float, peak_hours, other_kw, years) -> list:
    """FR-016.8 and D-V6-47: reshape the base load of every measured month outside +/-threshold of its bill peak.

    implied peak = E / (load factor x hours); the target is the nearest threshold edge. Only the base load
    (non_shiftable_load) changes, mean-preserving inside each bill block, so the bills stay reproduced. Synthetic
    or flagged months and months without a load factor are left as they are. ``other_kw(b)`` gives the hourly
    electricity of the rest of the building (cooling, DHW) and ``years`` the year of every row.
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
            target = implied*(1.0 + threshold)*(1.0 - 1e-3)   # just inside the edge (6-decimal CSV rounding)
            new, status = pc.reshape_month(base[mask], other[mask], np.isin(hour[mask], list(peak_hours)),
                                           target_peak_kw=target)
            base[mask] = new
            changed |= status == 'resolved'
            rows.append({'building_id': int(building), 'year': t.year, 'month': t.month, 'ratio_before': ratio,
                         'target_peak_kw': target, 'status': status,
                         'ratio_after': float((base[mask] + other[mask]).max())/implied})
        if changed:
            frame['non_shiftable_load'] = base
            frame.to_csv(path, index=False, float_format='%.6f')
    return rows
