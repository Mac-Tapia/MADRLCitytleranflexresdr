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
        results[building] = result
    return results


def capped_block_flags(results: Mapping) -> list:
    return [{'building_id': int(b), 'year': year, 'month': month, 'block': block,
             'flag': 'cooling_capped_by_bill',
             'note': 'physical cooling exceeded the bill block; capped and declared (D-V6-19)'}
            for b, result in results.items() for year, month, block in result.capped_blocks]
