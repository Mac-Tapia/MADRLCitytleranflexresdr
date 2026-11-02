"""
HPHI — Holistic Pareto Hypervolume Index  (Definición 4.6)
===========================================================
Métrica 7-D normalizada para evaluación multiobjetivo (extensión arquitectónica;
el experimento principal conserva tres ejes):

    HPHI(F) = HV(F; z_nadir) / Π_{k=1}^{7}(z_k^ideal - z_k^nadir)  ∈ [0, 1]

Todos los ejes se maximizan: z_nadir es el peor valor admitido y z_ideal el
mejor. La referencia es fija (se declara al construir y no la mueven los puntos
ni reset); comparar algoritmos exige la misma referencia. HV es el hipervolumen
exacto de ``uc3m.domain.pareto.hypervolume`` (sin muestreo). Un punto peor que
el nadir en algún eje no aporta volumen; un eje mejor que el ideal se acota al
ideal y el punto se cuenta en ``Saturated_points``, sin ocultarlo.

HPHI = 1 → algún punto alcanza el ideal en todos los ejes.
HPHI = 0 → ningún punto domina estrictamente al nadir.

Complementado por:
  - Sparsity: dispersión sobre la frontera
  - ε-cobertura: proximidad a frontera de referencia
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from uc3m.domain.pareto import hypervolume

_EPS = 1e-12


class HPHI:
    """
    Calcula el HPHI 7-D para una colección de soluciones Pareto.

    Uso típico:
        hphi_calc = HPHI()
        # Al final de cada episodio / barrido de λ:
        hphi_calc.add_point(axis_means)      # np.ndarray(7,)
        score = hphi_calc.compute()          # float ∈ [0,1]
    """

    def __init__(
        self,
        n_obj: int = 7,
        nadir: np.ndarray | None = None,
        ideal: np.ndarray | None = None,
    ):
        self.n_obj = n_obj
        # Por defecto: recompensa mínima por eje -10 (nadir) y 0 (ideal).
        nadir_array = np.asarray(nadir if nadir is not None else np.full(n_obj, -10.0), dtype=np.float64)
        ideal_array = np.asarray(ideal if ideal is not None else np.zeros(n_obj), dtype=np.float64)
        if nadir_array.shape != (n_obj,) or ideal_array.shape != (n_obj,):
            raise ValueError(f"nadir e ideal deben tener {n_obj} valores")
        if not (np.all(np.isfinite(nadir_array)) and np.all(np.isfinite(ideal_array))):
            raise ValueError("nadir e ideal deben ser finitos")
        if np.any(ideal_array - nadir_array <= _EPS):
            raise ValueError("el ideal debe ser estrictamente mejor que el nadir en cada eje")
        self._nadir = nadir_array
        self._ideal = ideal_array
        self._frontier: list[np.ndarray] = []

    @property
    def nadir(self) -> np.ndarray:
        return self._nadir.copy()

    @property
    def ideal(self) -> np.ndarray:
        return self._ideal.copy()

    def add_point(self, axis_values: np.ndarray | Sequence[float]) -> None:
        """Añade un punto a la aproximación de la frontera; la referencia no cambia."""
        p = np.asarray(axis_values, dtype=np.float64)
        if p.shape != (self.n_obj,):
            raise ValueError(f"Se esperan {self.n_obj} valores, se recibieron {p.size}")
        if not np.all(np.isfinite(p)):
            raise ValueError("los valores por eje deben ser finitos")
        self._frontier.append(p.copy())

    def clear(self) -> None:
        """Limpia la frontera acumulada (nuevo experimento); conserva la referencia."""
        self._frontier.clear()

    def update(self, axis_values: np.ndarray | Sequence[float]) -> None:
        """Alias estable para callers antiguos que usaban update()."""
        self.add_point(axis_values)

    def reset(self) -> None:
        """Alias estable para callers antiguos que usaban reset()."""
        self.clear()

    def compute_accumulated(self) -> float:
        """Alias estable para callers antiguos que usaban compute_accumulated()."""
        return self.compute()

    def pareto_front(self) -> np.ndarray:
        """Filtra la frontera de Pareto no dominada de los puntos acumulados (maximización)."""
        if not self._frontier:
            return np.empty((0, self.n_obj))
        pts = np.stack(self._frontier, axis=0)
        is_dominated = np.zeros(len(pts), dtype=bool)
        for i, p in enumerate(pts):
            for j, q in enumerate(pts):
                if i != j and np.all(q >= p) and np.any(q > p):
                    is_dominated[i] = True
                    break
        return pts[~is_dominated]

    def saturated_points(self) -> int:
        """Puntos con algún eje mejor que el ideal declarado."""
        return int(sum(bool(np.any(p > self._ideal)) for p in self._frontier))

    def compute(self) -> float:
        """
        Calcula HPHI ∈ [0, 1]:
            HPHI = HV(F; z_nadir) / Π_k(z_k^ideal - z_k^nadir)
        """
        pf = self.pareto_front()
        if len(pf) == 0:
            return 0.0
        capped = np.minimum(pf, self._ideal)
        inside = capped[np.all(capped >= self._nadir, axis=1)]
        if len(inside) == 0:
            return 0.0
        normalized = (inside - self._nadir) / (self._ideal - self._nadir)
        return float(
            hypervolume(
                normalized.tolist(),
                reference=[0.0] * self.n_obj,
                maximize=[True] * self.n_obj,
            )
        )

    # ── Métricas auxiliares (§4.7.3) ─────────────────────────────────────────
    def sparsity(self) -> float:
        """
        Sp(F) = 1/(|F|-1) · Σ_j ||f_j - f_{j+1}||²
        Mide la dispersión sobre la frontera Pareto.
        """
        pf = self.pareto_front()
        if len(pf) < 2:
            return 0.0
        # Ordenar por primera dimensión para el cálculo
        pf_sorted = pf[np.argsort(pf[:, 0])]
        diffs = np.diff(pf_sorted, axis=0)
        return float(np.mean(np.sum(diffs ** 2, axis=1)))

    def epsilon_coverage(
        self,
        reference_front: np.ndarray,
        epsilon: float = 0.1,
    ) -> float:
        """
        C_ε(F, F*) = |{f ∈ F* : ∃f' ∈ F, ||f-f'|| ≤ ε}| / |F*|
        """
        pf = self.pareto_front()
        if len(pf) == 0 or len(reference_front) == 0:
            return 0.0
        covered = 0
        for f_star in reference_front:
            dists = np.linalg.norm(pf - f_star, axis=1)
            if dists.min() <= epsilon:
                covered += 1
        return covered / len(reference_front)

    def summary(self) -> dict[str, float]:
        """Resumen de métricas HPHI + sparsity para logging."""
        pf = self.pareto_front()
        summary = {
            "HPHI":     self.compute(),
            "Sparsity": self.sparsity(),
            "PF_size":  float(len(pf)),
            "Saturated_points": float(self.saturated_points()),
        }
        if self.n_obj == 7:
            for index, name in enumerate(
                ("CO2", "Costo", "Flex", "Confort", "Degra", "Resilic", "ACS")
            ):
                summary[f"Ideal_{name}"] = float(self._ideal[index])
        return summary


def compute_global_score(axis_means: np.ndarray) -> float:
    """
    Score global Φ = (Π_{k=1}^{7} J̃_k)^{1/7}
    Media geométrica de los KPIs normalizados (§4.8.4).
    Requiere J̃_k ∈ [0, 1] (normalizado a la línea base RBC).
    """
    j = np.clip(axis_means, _EPS, None)
    return float(np.prod(j) ** (1.0 / len(j)))
