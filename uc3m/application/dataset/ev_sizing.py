"""Chargers and vehicles of iquitos_v6 from verified sources (SPEC-016 D-V6-6 and D-V6-21, FR-016.5).

Spaces = parking area / area per space (RNE A.010 dimensions with half the aisle); charging points =
1 per 10 spaces when there are more than 20 (EPBD 2024 art. 14(2)); EVs = share of the spaces
(declared assumption), and none where there is no charging point. Heavy-vehicle buildings count their
parking as light spaces and leave the heavy fleet out of electrification, declared.

D-V6-23 and D-V6-26: three classes, electric motorcycles, mototaxis and V2G pickups, in every building;
the classes named by the predominant inventory type share 80 % of the EVs and the others 20 %, with
largest-remainder rounding. Only the pickups discharge to the building.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

CLASSES = ('moto', 'mototaxi', 'pickup')


def load_ev_rules(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def named_classes(vehicle_type: str, rules: Mapping) -> list[str]:
    """Classes named by the predominant type, in order (D-V6-24); the token map is site configuration."""
    tokens = rules['vehicle_type_tokens']
    named: list[str] = []
    for token in str(vehicle_type).split('_'):
        kind = tokens.get(token)
        if kind and kind not in named:
            named.append(kind)
    return named


def space_class(vehicle_type: str, rules: Mapping) -> str:
    """Parking space of the first named class: a motorcycle space, or a car space for pickups."""
    named = named_classes(vehicle_type, rules)
    return 'moto' if named and named[0] in ('moto', 'mototaxi') else 'car'


def fleet_split(vehicle_type: str, vehicles: int, rules: Mapping) -> dict[str, int]:
    share = rules['fleet_split']['named_share']
    named = named_classes(vehicle_type, rules) or ['pickup']
    others = [c for c in CLASSES if c not in named]
    weights = {c: share/len(named) if c in named else (1 - share)/len(others) for c in CLASSES}
    raw = {c: weights[c]*vehicles for c in CLASSES}
    counts = {c: int(raw[c]) for c in CLASSES}
    for kind in sorted(CLASSES, key=lambda c: -(raw[c] - counts[c]))[:vehicles - sum(counts.values())]:
        counts[kind] += 1
    return counts


@dataclass(frozen=True)
class EvPlan:
    space_class: str
    spaces: int
    chargers: int
    vehicles: int
    fleet: Mapping[str, int]
    note: str = ''


def ev_plan(*, parking_m2: float, use_type: str, vehicle_type: str, rules: Mapping) -> EvPlan:
    if parking_m2 < 0:
        raise ValueError(f'parking area must be non-negative, got {parking_m2}')
    kind = space_class(vehicle_type, rules)
    use = 'private' if use_type in rules['private_use_types'] else 'public'
    spaces = int(parking_m2//rules['space_m2'][f'{kind}_{use}']['value'])
    points = rules['charging_points']
    chargers = spaces//points['per_spaces'] if spaces > points['minimum_spaces'] else 0
    vehicles = min(round(rules['ev_share']['value']*spaces), chargers) if chargers else 0
    note = 'heavy vehicles excluded from electrification; light spaces only' \
        if vehicle_type in rules['heavy_vehicle_types'] else ''
    return EvPlan(space_class=kind, spaces=spaces, chargers=chargers, vehicles=vehicles,
                  fleet=fleet_split(vehicle_type, vehicles, rules), note=note)


def coincidence_cap_kw(installed_kw: float, use_type: str, rules: Mapping) -> float:
    """Combined charging power allowed in a building (D-V6-27 FC, D.S. 036-2023-EM art. 13.3.1)."""
    table = rules['demand_factor']
    if use_type not in table['use_types']:
        raise ValueError(f'no demand-factor row for use type {use_type!r}')
    first, upper = float(table['use_types'][use_type]), float(table['upper_threshold_kw'])
    power = max(float(installed_kw), 0.0)
    return (min(power, first) + table['middle_factor']*max(min(power, upper) - first, 0.0)
            + table['upper_factor']*max(power - upper, 0.0))


def district_ev_plan(inventory: Mapping[int, object], rules: Mapping) -> dict[int, EvPlan]:
    return {bid: ev_plan(parking_m2=b.area_estacionamiento_m2, use_type=b.tipo_uso_citylearn,
                         vehicle_type=b.tipo_vehiculo_predominante, rules=rules)
            for bid, b in inventory.items()}
