"""
UC3M — Universal CityLearn v3 Modified
=======================================
Framework MADRL universal para comunidades energéticas inteligentes.

Referencia:
  Capítulo IV — "Diseño e Implementación del Framework Universal
  CityLearn v3 Modificado (UC3M)"

Meta-Dec-POMDP 11-aria:
  M_UC3M = ⟨I, S, A, O, T, R, Z, γ, H, b₀, Λ⟩

Capacidades:
  - N arbitrario de edificios (sin límite)
  - Cualquier algoritmo MADRL vía AlgorithmFactory
  - Cualquier ubicación geográfica (30 zonas Köppen-Geiger)
  - 7 ejes de recompensa holísticos con pesos λ configurables
  - HPHI (Holistic Pareto Hypervolume Index) 7D normalizado
  - Transferibilidad zero/few-shot entre zonas climáticas (Teor. 4.10)
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__  = "UC3M Framework — MADRL Iquitos"
__license__ = "Apache 2.0"

from uc3m.env.uc3m_env   import UC3MEnv
from uc3m.reward.axes     import RewardAxes
from uc3m.reward.hphi     import HPHI
from uc3m.algorithms.factory import AlgorithmFactory
from uc3m.kpis.evaluator  import KPIEvaluator

__all__ = [
    "UC3MEnv",
    "RewardAxes",
    "HPHI",
    "AlgorithmFactory",
    "KPIEvaluator",
]
