"""Chargers and vehicles of iquitos_v6 from verified sources (SPEC-016 D-V6-6 and D-V6-21, FR-016.5).

Spaces = parking area / area per space (RNE A.010 dimensions with half the aisle); charging points =
1 per 10 spaces when there are more than 20 (EPBD 2024 art. 14(2)); EVs = share of the spaces
(declared assumption), and none where there is no charging point; charger power by vehicle class
(D.S. 036-2023-EM at 220 V). Heavy-vehicle buildings count their parking as light spaces and leave
the heavy fleet out of electrification, declared.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

MOTO_PREFIXES = ('Motos', 'Mixed_Motos', 'Bicycles_Motos')


def load_ev_rules(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def vehicle_class(vehicle_type: str) -> str:
    return 'moto' if str(vehicle_type).startswith(MOTO_PREFIXES) else 'car'


@dataclass(frozen=True)
class EvPlan:
    vehicle_class: str
    spaces: int
    chargers: int
    vehicles: int
    charger_kw: float
    daily_kwh_per_vehicle: float
    note: str = ''


def ev_plan(*, parking_m2: float, use_type: str, vehicle_type: str, rules: Mapping) -> EvPlan:
    if parking_m2 < 0:
        raise ValueError(f'parking area must be non-negative, got {parking_m2}')
    kind = vehicle_class(vehicle_type)
    use = 'private' if use_type in rules['private_use_types'] else 'public'
    spaces = int(parking_m2//rules['space_m2'][f'{kind}_{use}']['value'])
    points = rules['charging_points']
    chargers = spaces//points['per_spaces'] if spaces > points['minimum_spaces'] else 0
    vehicles = min(round(rules['ev_share']['value']*spaces), chargers) if chargers else 0
    note = 'heavy vehicles excluded from electrification; light spaces only' \
        if vehicle_type in rules['heavy_vehicle_types'] else ''
    return EvPlan(vehicle_class=kind, spaces=spaces, chargers=chargers, vehicles=vehicles,
                  charger_kw=rules['charger_kw'][kind]['value'],
                  daily_kwh_per_vehicle=rules['daily_energy_kwh'][kind]['value'], note=note)


def district_ev_plan(inventory: Mapping[int, object], rules: Mapping) -> dict[int, EvPlan]:
    return {bid: ev_plan(parking_m2=b.area_estacionamiento_m2, use_type=b.tipo_uso_citylearn,
                         vehicle_type=b.tipo_vehiculo_predominante, rules=rules)
            for bid, b in inventory.items()}
