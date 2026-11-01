"""
BACT — Building-Aware Context Tensor (UC3M, Cap. IV)
====================================================
Contexto fijo por edificio que el dominio UC3M antepone a cada observación
local de CityLearn. El tensor es invariante en el tiempo (describe activos,
clima y geometría del edificio) y permite transferibilidad entre zonas
climáticas.

Definición 4.1 — Dimensiones del BACT:

    BACT_dim = KA + KC + KB = 14 + 8 + 7 = 29

  - KA = 14  activos / DERs (BESS, PV, EV, ratios derivados)
  - KC = 8   contexto climático-geográfico (lat, lon, alt, T, HR, GHI, Köppen)
  - KB = 7   descriptores físicos del edificio (tipo, área, ACS, COP, ...)

Este módulo es deliberadamente "puro": solo depende de numpy, no de CityLearn
ni de torch, para que el dominio sea importable y testeable sin esas
dependencias (principio hexagonal — el dominio no conoce la infraestructura).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

import numpy as np

# ── Dimensiones del BACT (Definición 4.1) ──────────────────────────────────────
KA: int = 14   # activos / DERs
KC: int = 8    # clima + geografía
KB: int = 7    # físico del edificio

BACT_DIM: int = KA + KC + KB   # 29

_EPS = 1e-8


# ── Codificación Köppen-Geiger ──────────────────────────────────────────────────
class _DefaultZeroDict(dict):
    """dict que devuelve 0 para claves desconocidas sin mutarse."""

    def __missing__(self, key):  # noqa: D401
        return 0


# Grupos principales Köppen → código entero. "Unknown"/ausente → 0.
KOPPEN_CODES: Dict[str, int] = _DefaultZeroDict({
    "Af": 1,   # tropical lluvioso (Iquitos)
    "Am": 2,   # tropical monzónico
    "Aw": 3,   # tropical sabana
    "BWh": 4, "BSh": 5,            # árido cálido
    "Csa": 6, "Csb": 7,           # mediterráneo
    "Cfa": 8, "Cfb": 9,           # templado húmedo
    "Cwa": 10, "Cwb": 11,         # templado seco invierno
    "Dfa": 12, "Dfb": 13,         # continental húmedo
    "ET": 14, "EF": 15,           # polar
})

# Grupo principal (primera letra) → banda climática 1..5.
_KOPPEN_MAIN_GROUP: Dict[str, int] = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


# ── Códigos de tipo de edificio (institucional/comercial Iquitos) ────────────────
# Las variantes de un mismo uso comparten código (educación, salud, ...).
BLDG_TYPE_CODES: Dict[str, int] = {
    "office": 1,
    "office_critical": 1,
    "retail": 2,
    "commercial_mall": 2,
    "assembly": 3,
    "assembly_military": 3,
    "educacion": 4,
    "educacion_motolineal": 4,
    "educacion_tec": 4,
    "education": 4,
    "salud": 5,
    "salud_24h": 5,
    "healthcare": 5,
    "healthcare_hospital": 5,
    "hotel": 6,
    "multifamily_hotel": 6,
    "industrial": 7,
    "industrial_port": 7,
    "laboratory": 8,
    "airport": 9,
}


@dataclass
class ClimateVector:
    """Contexto climático-geográfico de una ubicación (KC = 8 dimensiones).

    Es universal: cualquier ciudad/zona Köppen se describe con esta misma
    estructura, lo que habilita transferibilidad entre datasets CityLearn.
    """

    lat: float
    lon: float
    alt_m: float
    t_avg_c: float
    hr_avg_pct: float
    ghi_avg_wm2: float
    koppen: str = "Af"

    def to_array(self) -> np.ndarray:
        """Vector de longitud KC=8. Posiciones 0 y 1 son lat y lon."""
        main_group = _KOPPEN_MAIN_GROUP.get(
            (self.koppen[:1].upper() if self.koppen else ""), 0
        )
        arr = np.array(
            [
                float(self.lat),
                float(self.lon),
                float(self.alt_m),
                float(self.t_avg_c),
                float(self.hr_avg_pct),
                float(self.ghi_avg_wm2),
                float(KOPPEN_CODES[self.koppen] if self.koppen else 0),
                float(main_group),
            ],
            dtype=np.float64,
        )
        return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)


# ── Clima de referencia: Iquitos, Perú (Köppen Af, selva amazónica) ──────────────
IQUITOS_CLIMATE = ClimateVector(
    lat=-3.7491,
    lon=-73.2538,
    alt_m=106,
    t_avg_c=26.5,
    hr_avg_pct=85.0,
    ghi_avg_wm2=520.0,
    koppen="Af",
)


def building_type_code(name_or_type: str | None) -> int:
    """Mapea un nombre/tipo de edificio (case-insensitive) a su código."""
    if not name_or_type:
        return 0
    key = str(name_or_type).strip().lower()
    return BLDG_TYPE_CODES.get(key, 0)


class BACTEncoder:
    """Codifica el contexto fijo de un edificio en un vector BACT de 29D.

    El orden es ``[activos(KA) | clima(KC) | físico(KB)]``. Todos los valores
    se sanean (sin NaN/Inf) para no contaminar la observación del agente.
    """

    def __init__(self, climate: ClimateVector = IQUITOS_CLIMATE):
        self.climate = climate

    # — activos / DERs (KA = 14) —
    def _assets(self, b: Mapping[str, object]) -> np.ndarray:
        cap = float(b.get("cap_bess_kwh", 0.0) or 0.0)
        p = float(b.get("p_bess_kw", 0.0) or 0.0)
        dod = float(b.get("dod", 0.0) or 0.0)
        eta = float(b.get("eta_rt", 0.0) or 0.0)
        pv = float(b.get("pv_kwp", 0.0) or 0.0)
        n_ev = float(b.get("n_ev_chargers", 0.0) or 0.0)
        ev_kw = float(b.get("ev_charger_kw", 0.0) or 0.0)

        c_rate = p / (cap + _EPS)
        ev_total_kw = n_ev * ev_kw
        usable_kwh = cap * dod
        pv_to_bess = pv / (p + _EPS)
        energy_to_pv = cap / (pv + _EPS)
        rt_loss = max(0.0, 1.0 - eta)
        has_v2g = 1.0 if float(b.get("has_v2g", 0.0) or 0.0) > 0 else 0.0

        return np.array(
            [cap, p, dod, eta, pv, n_ev, ev_kw,
             c_rate, ev_total_kw, usable_kwh, pv_to_bess,
             energy_to_pv, rt_loss, has_v2g],
            dtype=np.float64,
        )

    # — físico del edificio (KB = 7) —
    def _building(self, b: Mapping[str, object]) -> np.ndarray:
        type_code = building_type_code(b.get("bldg_type"))
        area = float(b.get("area_m2", 0.0) or 0.0)
        has_dhw = 1.0 if bool(b.get("has_dhw", False)) else 0.0
        cop = float(b.get("cop_design", 0.0) or 0.0)

        return np.array(
            [float(type_code), area, has_dhw, cop,
             float(np.log1p(max(area, 0.0))),
             1.0 if type_code > 0 else 0.0,
             1.0],
            dtype=np.float64,
        )

    def encode(self, building_data: Mapping[str, object]) -> np.ndarray:
        """Devuelve el vector BACT de longitud ``BACT_DIM`` (29)."""
        assets = self._assets(building_data)
        climate = self.climate.to_array()
        building = self._building(building_data)
        vec = np.concatenate([assets, climate, building])
        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
        assert vec.shape == (BACT_DIM,), f"BACT debe ser {BACT_DIM}D, es {vec.shape}"
        return vec.astype(np.float64)


__all__ = [
    "KA", "KC", "KB", "BACT_DIM",
    "KOPPEN_CODES", "BLDG_TYPE_CODES",
    "ClimateVector", "IQUITOS_CLIMATE",
    "BACTEncoder", "building_type_code",
]
