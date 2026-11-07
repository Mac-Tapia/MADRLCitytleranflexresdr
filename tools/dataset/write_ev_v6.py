"""Chargers and EVs of the FIFO queue into a CityLearn schema (SPEC-016 T1, docs/plans/modulo3b_iquitos_v6.md).

For each building it runs the queue (uc3m.application.dataset.ev_queue.building_charging), writes one
ChargerSimulation CSV per charger, replaces the building's ``chargers`` in the schema and adds every EV to
``electric_vehicles_def``. Parameters come only from configs/dataset/ev_v6.yaml:
- mode, connector, standard and direction of each class (D-V6-33);
- charge power of the class, discharge only for pickups through V2L (D-V6-32);
- battery and charger efficiencies, depth of discharge, minimum current and voltage (D-V6-34);
- power modulated by the agent between the minimum and the maximum (D-V6-35).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from uc3m.application.dataset import ev_queue as q  # noqa: E402


def _value(entry):
    return entry['value'] if isinstance(entry, Mapping) else entry


def min_charging_power_kw(max_kw: float, rules: Mapping) -> float:
    """D-V6-34: supply voltage x minimum current when the class maximum reaches it, else 0."""
    common = rules['battery_and_charger']
    floor = float(_value(common['supply_voltage_v']))*float(_value(common['min_current_a']))/1000.0
    return round(floor, 6) if max_kw >= floor else 0.0


def charger_entry(name: str, kind: str, csv_name: str, rules: Mapping) -> dict:
    params, common = rules['classes'][kind], rules['battery_and_charger']
    charging = params['charging']
    max_kw = float(_value(params['charge_kw']))
    discharge = float(_value(params['discharge_kw']))
    return {
        'type': 'citylearn.electric_vehicle_charger.Charger',
        'charger_simulation': csv_name,
        'autosize': False,
        'hardware': {'vehicle_class': kind, 'charging_mode': f"{charging['standard'].replace(' ', '_')}_Mode_{charging['mode']}_AC",
                     'standard': charging['standard'], 'current': charging['current'],
                     'connector': charging['connector'], 'category': charging['category'],
                     'direction': charging['direction'], 'voltage_v': float(_value(common['supply_voltage_v'])),
                     'phases': 1, 'source': 'configs/dataset/ev_v6.yaml (D-V6-32 to D-V6-35)'},
        'attributes': {'nominal_power': max_kw, 'efficiency': float(_value(common['charger_efficiency'])),
                       'max_charging_power': max_kw, 'min_charging_power': min_charging_power_kw(max_kw, rules),
                       'max_discharging_power': discharge, 'min_discharging_power': 0.0},
    }


def ev_entry(kind: str, rules: Mapping) -> dict:
    params, common = rules['classes'][kind], rules['battery_and_charger']
    spec = q.vehicle_class(kind, rules)
    return {'include': True, 'vehicle_class': kind,
            'battery': {'type': 'citylearn.energy_model.Battery', 'autosize': False,
                        'attributes': {'capacity': float(_value(params['battery_kwh'])),
                                       'nominal_power': float(_value(params['charge_kw'])),
                                       'initial_soc': 1.0,   # full before its first trip (P-V6-15, D-V6-41)
                                       'depth_of_discharge': float(_value(common['battery_depth_of_discharge'])),
                                       'efficiency': float(_value(common['battery_efficiency'])),
                                       'capacity_loss_coefficient': float(_value(common['capacity_loss_coefficient'])),
                                       # P-V6-22: flat curves (no taper near full), the assumption of the queue's
                                       # charging time; without them CityLearn draws random curves.
                                       'capacity_power_curve': [[0.0, 1.0], [1.0, 1.0]],
                                       'power_efficiency_curve': [[0.0, float(_value(common['battery_efficiency']))],
                                                                  [1.0, float(_value(common['battery_efficiency']))]]}}}


def write_ev_fleet(dataset_dir: Path, schema: dict, *, plans: Mapping, registry: Mapping, rules: Mapping,
                   inventory: Mapping, days: Sequence, keep_others: bool = False) -> dict:
    """Write the chargers and EVs of ``plans`` into ``dataset_dir`` and ``schema``; return the report per building.

    ``keep_others`` keeps the EVs already declared (for buildings not in ``plans``); otherwise the fleet of
    ``plans`` replaces every EV of the schema.
    """
    dataset_dir = Path(dataset_dir)
    evs = dict(schema.get('electric_vehicles_def') or {}) if keep_others else {}
    report = {}
    for building, plan in plans.items():
        schedule = registry['schedules'][registry['buildings'][building]['schedule']]
        charging = q.building_charging(building, plan, schedule=schedule, rules=rules, days=days,
                                       use_type=inventory[building].tipo_uso_citylearn)
        chargers = {}
        for name, kind, table in charging.chargers:
            csv_name = f'charger_{name}.csv'   # the integrity audit reads charger_*.csv
            pd.DataFrame({c: table[c] for c in q.CHARGER_COLUMNS + (q.TRIP_COLUMN,)}).to_csv(dataset_dir/csv_name,
                                                                                         index=False)
            chargers[name] = charger_entry(name, kind, csv_name, rules)
            unit, socket = name.rsplit('_unit_', 1)[1].split('_socket_')
            chargers[name]['hardware'].update({'physical_charger_id': f'B{building:02d}_{kind}_unit_{unit}',
                                               'socket_count_per_physical_unit':
                                                   int(_value(rules['charging_unit']['sockets_per_unit'])),
                                               'outlet_index': int(socket)})
        schema['buildings'][f'Building_{building}']['chargers'] = chargers
        for ev, kind in charging.vehicle_class.items():
            evs[ev] = ev_entry(kind, rules)
        report[building] = {'chargers': len(chargers), 'vehicles': len(charging.vehicles),
                            'class_chargers': {k: sum(1 for _, c, _ in charging.chargers if c == k) for k in plan.fleet},
                            'epbd_points': charging.epbd_points, 'required_sockets': dict(charging.required_sockets),
                            'physical_chargers': dict(charging.physical_chargers), 'fleet': dict(plan.fleet),
                            'load_factor': dict(charging.load_factor), 'unserved': dict(charging.unserved),
                            'depleted': dict(charging.depleted), 'mean_wait_h': dict(charging.mean_wait_h),
                            'installed_kw': charging.installed_kw,
                            'coincidence_cap_kw': charging.coincidence_cap_kw}
    schema['electric_vehicles_def'] = evs
    schema['electric_vehicle_arrival_soc'] = 'endogenous'   # D-V6-41: read by CityLearn/citylearn/internal/runtime.py
    schema['electric_vehicle_discharge_limit'] = 'building_demand'   # D-V6-28: V2B, never exported (v3 layer)
    return report
