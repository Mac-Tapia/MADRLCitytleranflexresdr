"""
uc3m.env — Capa de entorno Meta-Dec-POMDP UC3M sobre CityLearn
==============================================================
Expone:
  - ``UC3MEnv``       : entorno multi-agente CityLearn v3 (Dec-POMDP, CTDE).
  - ``ClimateVector`` : descriptor climático (bloque KC del BACT).
  - ``BACTEncoder``   : codificador del tensor Building–Asset–Climate (29-D).
  - ``IQUITOS_CLIMATE``: clima de referencia de Iquitos (Köppen Af).
  - ``KA``, ``KC``, ``KB`` : dimensiones del tensor BACT (14 + 8 + 7 = 29).
"""

from __future__ import annotations

from uc3m.env.bact import (
    BACT_DIM,
    BACTEncoder,
    BLDG_TYPE_CODES,
    ClimateVector,
    IQUITOS_CLIMATE,
    KA,
    KB,
    KC,
    KOPPEN_CODES,
)
from uc3m.env.uc3m_env import UC3MEnv

__all__ = [
    "UC3MEnv",
    "ClimateVector",
    "BACTEncoder",
    "IQUITOS_CLIMATE",
    "BLDG_TYPE_CODES",
    "KOPPEN_CODES",
    "KA",
    "KC",
    "KB",
    "BACT_DIM",
]
