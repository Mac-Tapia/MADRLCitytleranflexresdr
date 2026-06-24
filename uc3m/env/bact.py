"""
uc3m.env.bact — Building–Asset–Climate Tensor (BACT)
=====================================================
Codificación universal del contexto de cada edificio del Meta-Dec-POMDP UC3M
(Definición 4.1). El tensor BACT concatena tres bloques:

    BACT = [ KA activos | KC clima | KB edificio ]   →  dim = KA + KC + KB = 29

- KA = 14  → vector de activos (BESS, PV, EV, bomba de calor, ACS, ...).
- KC = 8   → vector de clima (lat, lon, altitud, T, HR, GHI, Köppen, trópico).
- KB = 7   → vector de edificio (tipo, área, COP, pisos, ocupación, 24 h, ...).

El BACT permite la transferibilidad zero/few-shot entre zonas climáticas
(Teor. 4.10): un mismo agente puede operar en cualquier ciudad describiendo su
contexto mediante este tensor.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ── Dimensiones del tensor BACT (Def. 4.1) ──────────────────────────────────
KA: int = 14   # activos energéticos por edificio
KC: int = 8    # variables de clima
KB: int = 7    # atributos del edificio
BACT_DIM: int = KA + KC + KB   # = 29


# ── Códigos de clasificación climática Köppen–Geiger ────────────────────────
# "Unknown" debe ser 0 y "Af" (tropical lluvioso, Iquitos) debe ser 1.
KOPPEN_CODES: dict[str, int] = {
    "Unknown": 0,
    "Af": 1,   # tropical lluvioso (sin estación seca)
    "Am": 2,   # tropical monzónico
    "Aw": 3,   # tropical de sabana
    "BWh": 4, "BWk": 5,   # desértico
    "BSh": 6, "BSk": 7,   # estepario
    "Csa": 8, "Csb": 9,   # mediterráneo
    "Cfa": 10, "Cfb": 11, "Cwa": 12,   # templado húmedo
    "Dfa": 13, "Dfb": 14,   # continental
    "ET": 15, "EF": 16,     # polar
}

# Grupos tropicales (primera letra "A") → señal de trópico en el vector clima.
_TROPICAL_CODES = {KOPPEN_CODES["Af"], KOPPEN_CODES["Am"], KOPPEN_CODES["Aw"]}


# ── Códigos de tipo de edificio ─────────────────────────────────────────────
# Las variantes de educación comparten código; "salud_24h" tiene código > 0.
BLDG_TYPE_CODES: dict[str, int] = {
    "office": 1,
    "office_critical": 2,
    "retail": 3,
    "hotel": 4,
    "comercial": 5,
    "mall": 5,
    "educacion": 6,
    "educacion_motolineal": 6,
    "educacion_tec": 6,
    "salud": 7,
    "healthcare": 7,
    "salud_24h": 8,
    "industrial": 9,
    "industrial_port": 10,
    "assembly": 11,
    "assembly_military": 12,
    "laboratory": 13,
}


def koppen_code(koppen: str) -> int:
    """Devuelve el código entero del grupo Köppen (0 si es desconocido)."""
    return KOPPEN_CODES.get(koppen, KOPPEN_CODES["Unknown"])


def bldg_type_code(bldg_type: str) -> int:
    """Devuelve el código entero del tipo de edificio (0 si es desconocido)."""
    if bldg_type is None:
        return 0
    return BLDG_TYPE_CODES.get(str(bldg_type).strip().lower(), 0)


# ── Vector de clima (KC = 8) ────────────────────────────────────────────────
@dataclass
class ClimateVector:
    """Descriptor climático de una ubicación (bloque KC del BACT)."""

    lat: float
    lon: float
    alt_m: float
    t_avg_c: float
    hr_avg_pct: float
    ghi_avg_wm2: float
    koppen: str = "Unknown"

    def to_array(self) -> np.ndarray:
        """Vector de clima de longitud KC=8: [lat, lon, alt, T, HR, GHI, code, trópico]."""
        code = koppen_code(self.koppen)
        is_tropical = 1.0 if code in _TROPICAL_CODES else 0.0
        arr = np.array(
            [
                self.lat,
                self.lon,
                self.alt_m,
                self.t_avg_c,
                self.hr_avg_pct,
                self.ghi_avg_wm2,
                float(code),
                is_tropical,
            ],
            dtype=np.float64,
        )
        return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)


# ── Clima de referencia: Iquitos, Perú (Köppen Af) ──────────────────────────
IQUITOS_CLIMATE = ClimateVector(
    lat=-3.7491,
    lon=-73.2538,
    alt_m=106.0,
    t_avg_c=26.5,
    hr_avg_pct=85.0,
    ghi_avg_wm2=520.0,
    koppen="Af",
)


# ── Codificador BACT (29-D por edificio) ────────────────────────────────────
# Orden de las 14 claves de activos esperadas en ``bldg_data``.
_ASSET_KEYS: tuple[str, ...] = (
    "cap_bess_kwh",     # capacidad BESS [kWh]
    "p_bess_kw",        # potencia BESS [kW]
    "dod",              # profundidad de descarga [0,1]
    "eta_rt",           # eficiencia round-trip [0,1]
    "pv_kwp",           # potencia PV instalada [kWp]
    "n_ev_chargers",    # número de cargadores EV
    "ev_charger_kw",    # potencia por cargador [kW]
    "has_dhw",          # tiene agua caliente sanitaria (0/1)
    "cop_design",       # COP de diseño de la bomba de calor
    "has_wind",         # tiene generación eólica (0/1)
    "has_h2",           # tiene almacenamiento de hidrógeno (0/1)
    "has_v2g",          # soporta V2G (0/1)
    "n_floors_served",  # pisos climatizados servidos por DERs
    "asset_reserved",   # reservado / extensión
)

# Orden de las 7 claves de edificio (bloque KB).
_BLDG_KEYS: tuple[str, ...] = (
    "area_m2",          # área techada [m²]
    "u_wall",           # transmitancia de muro [W/m²K]
    "n_floors",         # número de pisos
    "occupancy",        # ocupación nominal
    "is_24h",           # operación 24 h (0/1)
    "cop_building",     # COP medio del edificio
    "bldg_reserved",    # reservado / extensión
)


class BACTEncoder:
    """Construye el tensor BACT (29-D) de un edificio a partir de su metadato."""

    def __init__(self, climate: ClimateVector = IQUITOS_CLIMATE):
        self.climate = climate

    @staticmethod
    def _to_float(value) -> float:
        """Convierte a float seguro (bool→0/1, None→0, NaN/Inf→0)."""
        if value is None:
            return 0.0
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0
        return v if np.isfinite(v) else 0.0

    def encode(self, bldg_data: dict | None = None) -> np.ndarray:
        """Codifica un edificio en un vector BACT de longitud KA + KC + KB = 29."""
        data = bldg_data or {}

        # Bloque KA — activos energéticos (14)
        assets = np.array(
            [self._to_float(data.get(k, 0.0)) for k in _ASSET_KEYS],
            dtype=np.float64,
        )

        # Bloque KC — clima (8)
        climate = self.climate.to_array()

        # Bloque KB — edificio (7); la primera dimensión es el código de tipo
        bldg_vals = [float(bldg_type_code(data.get("bldg_type")))]
        bldg_vals += [self._to_float(data.get(k, 0.0)) for k in _BLDG_KEYS[: KB - 1]]
        building = np.array(bldg_vals, dtype=np.float64)

        vec = np.concatenate([assets, climate, building])
        assert vec.shape == (BACT_DIM,), f"BACT dim {vec.shape} != {BACT_DIM}"
        return np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
