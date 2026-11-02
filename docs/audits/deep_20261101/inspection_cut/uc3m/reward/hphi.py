"""
HPHI — Holistic Pareto Hypervolume Index  (Definición 4.6)
===========================================================
Métrica original 7-D normalizada para evaluación multiobjetivo:

    HPHI(F) = HV(F; z_nadir) / Π_{k=1}^{7}(z_k^nadir - z_k^ideal)  ∈ [0, 1]

donde HV es el hipervolumen Lebesgue 7-D (Zitzler & Thiele, 1999).

HPHI = 1 → frontera Pareto perfecta (alcanza el ideal en todos los ejes).
HPHI = 0 → política trivial.

Complementado por:
  - Sparsity: dispersión sobre la frontera
  - ε-cobertura: proximidad a frontera de referencia
"""

from __future__ import annotations

import numpy as np
from typing import Sequence

_EPS = 1e-12


def _hypervolume_2d(points: np.ndarray, ref: np.ndarray) -> float:
    """Hipervolumen 2D exacto (contribución incremental ordenada por eje 0)."""
    pts = points[np.all(points < ref, axis=1)]  # filtrar puntos dominados por ref
    if len(pts) == 0:
        return 0.0
    pts_sorted = pts[np.argsort(pts[:, 0])]
    hv = 0.0
    prev_y = ref[1]
    for p in pts_sorted:
        hv += (ref[0] - p[0]) * (prev_y - p[1])
        prev_y = min(prev_y, p[1])
    return hv


def _hypervolume_nd(points: np.ndarray, ref: np.ndarray) -> float:
    """
    Hipervolumen N-D via algoritmo WFG simplificado (no escalable, OK para
    frontera pequeña de laboratorio).  Para |F| > 500, usar pymoo HV.
    """
    try:
        from pymoo.indicators.hv import HV  # type: ignore[import-not-found]
        ind = HV(ref_point=ref)
        return float(ind(points))
    except ImportError:
        pass

    # Fallback: Monte Carlo 7-D (aprox. suficiente para N_points < 200)
    n_pts, n_dim = points.shape
    # Calcular bounding box
    lower = points.min(axis=0)
    upper = ref.copy()
    if np.any(upper <= lower):
        return 0.0
    vol_box = float(np.prod(np.maximum(upper - lower, _EPS)))
    n_samples = 50_000
    rng = np.random.default_rng(42)
    samples = rng.uniform(lower, upper, size=(n_samples, n_dim))

    # Punto dominado si ∃ p ∈ points tal que p ≤ sample en todos los ejes
    dominated = np.zeros(n_samples, dtype=bool)
    for p in points:
        dominated |= np.all(samples >= p, axis=1)
    hv = vol_box * dominated.mean()
    return float(hv)


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
        # Nadir: peores valores observados (maximizando penalizaciones)
        # Por defecto: recompensa mínima posible por eje (clamped a -10)
        self._nadir = nadir if nadir is not None else np.full(n_obj, -10.0)
        # Ideal: mejores valores posibles por eje
        self._ideal = ideal if ideal is not None else np.zeros(n_obj)

        self._frontier: list[np.ndarray] = []

    def add_point(self, axis_values: np.ndarray | Sequence[float]) -> None:
        """Añade un punto a la aproximación de la frontera de Pareto."""
        p = np.asarray(axis_values, dtype=np.float64)
        assert len(p) == self.n_obj, f"Se esperan {self.n_obj} valores, se recibieron {len(p)}"
        # Actualizar nadir e ideal dinámicamente
        self._nadir = np.minimum(self._nadir, p)
        self._ideal = np.maximum(self._ideal, p)
        self._frontier.append(p.copy())

    def clear(self) -> None:
        """Limpia la frontera acumulada (nuevo experimento)."""
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
        """Filtra la frontera de Pareto no dominada de los puntos acumulados."""
        if not self._frontier:
            return np.empty((0, self.n_obj))
        pts = np.stack(self._frontier, axis=0)
        # Eliminar puntos dominados
        is_dominated = np.zeros(len(pts), dtype=bool)
        for i, p in enumerate(pts):
            for j, q in enumerate(pts):
                if i != j and np.all(q >= p) and np.any(q > p):
                    is_dominated[i] = True
                    break
        return pts[~is_dominated]

    def compute(self) -> float:
        """
        Calcula HPHI ∈ [0, 1]:
            HPHI = HV(F; z_nadir) / Π_k(z_k^nadir - z_k^ideal)
        """
        pf = self.pareto_front()
        if len(pf) == 0:
            return 0.0

        nadir = self._nadir.copy()
        ideal = self._ideal.copy()

        # Asegurar que nadir ≠ ideal
        denom_vec = nadir - ideal
        if np.any(np.abs(denom_vec) < _EPS):
            denom_vec = np.where(np.abs(denom_vec) < _EPS, 1.0, denom_vec)

        # Normalizar puntos a [0, 1] (ideal=1, nadir=0 tras negación)
        # HV usa nadir como punto de referencia (peor)
        ref = nadir + 1e-6  # ligeramente peor que nadir para incluir todos

        if self.n_obj == 2:
            hv = _hypervolume_2d(pf, ref)
        else:
            hv = _hypervolume_nd(pf, ref)

        denom = float(np.prod(np.abs(denom_vec) + _EPS))
        return float(np.clip(hv / (denom + _EPS), 0.0, 1.0))

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
        return {
            "HPHI":     self.compute(),
            "Sparsity": self.sparsity(),
            "PF_size":  float(len(pf)),
            "Ideal_CO2":        float(self._ideal[0]),
            "Ideal_Costo":      float(self._ideal[1]),
            "Ideal_Flex":       float(self._ideal[2]),
            "Ideal_Confort":    float(self._ideal[3]),
            "Ideal_Degra":      float(self._ideal[4]),
            "Ideal_Resilic":    float(self._ideal[5]),
            "Ideal_ACS":        float(self._ideal[6]),
        }


def compute_global_score(axis_means: np.ndarray) -> float:
    """
    Score global Φ = (Π_{k=1}^{7} J̃_k)^{1/7}
    Media geométrica de los KPIs normalizados (§4.8.4).
    Requiere J̃_k ∈ [0, 1] (normalizado a la línea base RBC).
    """
    j = np.clip(axis_means, _EPS, None)
    return float(np.prod(j) ** (1.0 / len(j)))
