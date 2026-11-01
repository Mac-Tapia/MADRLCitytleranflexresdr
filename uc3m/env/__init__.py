"""
uc3m.env — Capa de dominio del entorno UC3M
============================================
Expone el entorno Dec-POMDP universal (``UC3MEnv``) y el tensor de contexto
fijo por edificio (``BACT``). El dominio no importa CityLearn/torch a nivel de
módulo: ``bact`` solo usa numpy y ``UC3MEnv`` carga CityLearn de forma perezosa.
"""

from __future__ import annotations

from uc3m.env.bact import (
    BACT_DIM,
    KA,
    KB,
    KC,
    BACTEncoder,
    ClimateVector,
    IQUITOS_CLIMATE,
    BLDG_TYPE_CODES,
    KOPPEN_CODES,
    building_type_code,
)
from uc3m.env.uc3m_env import UC3MEnv

__all__ = [
    "UC3MEnv",
    "BACTEncoder",
    "ClimateVector",
    "IQUITOS_CLIMATE",
    "BACT_DIM",
    "KA",
    "KC",
    "KB",
    "BLDG_TYPE_CODES",
    "KOPPEN_CODES",
    "building_type_code",
]
