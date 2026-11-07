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
