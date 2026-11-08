"""Air-conditioning capacity of iquitos_v6 from the inventory and EM.030 (SPEC-016 D-V6-16, FR-016.3).

Peruvian norms give no AC capacity: EM.050 has no figures. Capacity = splits x 18 000 BTU/h plus,
for a building with a large system, the outdoor-air load of EM.030 art. 6 (Vbz = Rp*Pz + Ra*Az)
and the occupant gain. Health buildings ventilate with the air changes of MINSA NTS 110 Table 6.
The bill calibration (D-V6-14) checks the result.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import yaml

W_PER_BTU_H = 0.29307107


def load_hvac_norms(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def station_pressure_kpa(elevation_m: float) -> float:
    """Standard atmosphere pressure at an elevation (ASHRAE Fundamentals ch. 1, eq. 3)."""
    return 101.325*(1 - 2.25577e-5*float(elevation_m))**5.2559


def _saturation_pressure_kpa(t_c: float) -> float:
    """Magnus form of Alduchov and Eskridge (1996), valid for -40 to 50 C."""
    return 0.61094*math.exp(17.625*t_c/(t_c + 243.04))


def moist_air_enthalpy_kj_per_kg(t_c: float, rh_pct: float, pressure_kpa: float) -> float:
    """Enthalpy of moist air per kg of dry air (ASHRAE Fundamentals ch. 1, eqs. 22 and 32)."""
    vapour = float(rh_pct)/100*_saturation_pressure_kpa(float(t_c))
    humidity_ratio = 0.621945*vapour/(float(pressure_kpa) - vapour)
    return 1.006*t_c + humidity_ratio*(2501 + 1.86*t_c)


def outdoor_design_enthalpy(t_c: Sequence[float], rh_pct: Sequence[float], pressure_kpa: float,
                            percentile: float) -> float:
    hourly = [moist_air_enthalpy_kj_per_kg(t, rh, pressure_kpa) for t, rh in zip(t_c, rh_pct)]
    return float(np.percentile(hourly, percentile))


@dataclass(frozen=True)
class CapacityEstimate:
    kw_thermal: float
    w_per_m2: float
    components: Mapping[str, float] = field(default_factory=dict)
    source: Mapping[str, str] = field(default_factory=dict)


def hvac_capacity_kw(*, area_m2: float, use_type: str, split_units: int, has_large_system: bool, norms: Mapping,
                     outdoor_enthalpy: float, indoor_enthalpy: float) -> CapacityEstimate:
    if area_m2 <= 0 or split_units < 0:
        raise ValueError(f'area must be positive and splits non-negative (area={area_m2}, splits={split_units})')
    rows = norms['use_types']
    if use_type not in rows:
        raise ValueError(f'no norm row for use type {use_type!r}')
    row = rows[use_type]
    split_kw = split_units*norms['split_unit']['btu_per_h']*W_PER_BTU_H/1000
    people = outdoor_l_s = ventilation_kw = occupants_kw = 0.0
    if has_large_system:
        occupied = area_m2*norms['occupied_fraction']['value']
        people = row['rd']/100*occupied
        if 'air_changes_per_hour' in row:
            outdoor_l_s = row['air_changes_per_hour']*occupied*norms['ceiling_height_m']['value']*1000/3600
        else:
            outdoor_l_s = row['rp']*people + row['ra']*occupied
        delta_h = max(float(outdoor_enthalpy) - float(indoor_enthalpy), 0.0)
        ventilation_kw = norms['air_density_kg_m3']['value']*outdoor_l_s/1000*delta_h
        occupants_kw = people*norms['occupant_gain_w']['value']/1000
    total = split_kw + ventilation_kw + occupants_kw
    return CapacityEstimate(
        kw_thermal=total, w_per_m2=total*1000/area_m2,
        components={'split_kw': split_kw, 'people': people, 'outdoor_air_l_s': outdoor_l_s,
                    'ventilation_kw': ventilation_kw, 'occupants_kw': occupants_kw},
        source={'split': f"{norms['split_unit']['btu_per_h']} BTU/h per split ({norms['split_unit']['origin']})",
                'ventilation': row['source'] if has_large_system else 'no large system'})



def zone_occupancy(*, area_m2: float, use_type: str, norms: Mapping) -> tuple:
    """(design occupants, outdoor-air flow in m3/s) of a building from the same norm rows as its capacity
    (EM.030 art. 6 Vbz = Rp*Pz + Ra*Az, or the NTS 110 air changes), for any AC system (SPEC-016 D-V6-53)."""
    row = norms['use_types'][use_type]
    occupied = float(area_m2)*norms['occupied_fraction']['value']
    people = row['rd']/100*occupied
    if 'air_changes_per_hour' in row:
        flow_l_s = row['air_changes_per_hour']*occupied*norms['ceiling_height_m']['value']*1000/3600
    else:
        flow_l_s = row['rp']*people + row['ra']*occupied
    return people, flow_l_s/1000.0


def district_capacity(inventory: Mapping[int, object], norms: Mapping, *, outdoor_enthalpy: float,
                      indoor_enthalpy: float) -> dict[int, CapacityEstimate]:
    return {bid: hvac_capacity_kw(area_m2=b.area_techada_m2, use_type=b.tipo_uso_citylearn,
                                  split_units=b.split_units, has_large_system=b.has_large_refrigeration,
                                  norms=norms, outdoor_enthalpy=outdoor_enthalpy, indoor_enthalpy=indoor_enthalpy)
            for bid, b in inventory.items()}
