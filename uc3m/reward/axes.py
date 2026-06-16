"""
7 Ejes de Recompensa Holísticos — UC3M §4.3
============================================
Operador de recompensa holístico escalarizado:

    R_i(t) = -Σ_{k=1}^{7} λ_k · r̃_i^{(k)}(t)

donde r̃^{(k)} = r^{(k)} / r^{(k),base} (normalizado a la RBC).

Ejes:
  1. CO₂      — emisiones de carbono evitadas
  2. Costo     — ahorro económico vs tarifa base
  3. Flexib.   — reducción de demanda punta + suavizado de red
  4. Confort   — temperatura interior dentro del rango de aceptabilidad
  5. Degra.    — mínima degradación electroquímica del BESS (Arrhenius-Peukert-SEI)
  6. Resilic.  — cobertura de carga durante corte de red (islanding)
  7. ACS       — eficiencia exergética del agua caliente sanitaria
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass


# ── Pesos por defecto (simplex Λ ≥ 0, Σλ_k = 1) ─────────────────────────────
DEFAULT_LAMBDAS = np.array([
    0.25,   # λ₁  CO₂
    0.25,   # λ₂  Costo
    0.20,   # λ₃  Flexibilidad
    0.10,   # λ₄  Confort térmico
    0.05,   # λ₅  Degradación BESS
    0.10,   # λ₆  Resiliencia
    0.05,   # λ₇  ACS
], dtype=np.float64)

assert abs(DEFAULT_LAMBDAS.sum() - 1.0) < 1e-9, "Σλ debe ser 1"

# ── Parámetros de normalización RBC (valores de referencia) ──────────────────
# Se calibran durante el primer episodio de RBC o se usan los de Iquitos aquí.
_EPS = 1e-8


@dataclass
class AxisValues:
    """Contenedor de los 7 valores de eje (por agente i, paso t)."""
    co2:         float = 0.0
    cost:        float = 0.0
    flexibility: float = 0.0
    comfort:     float = 0.0
    degradation: float = 0.0
    resilience:  float = 0.0
    acs:         float = 0.0

    def to_array(self) -> np.ndarray:
        return np.array([
            self.co2, self.cost, self.flexibility,
            self.comfort, self.degradation,
            self.resilience, self.acs,
        ], dtype=np.float64)


class RewardAxes:
    """
    Calcula los 7 ejes de recompensa para UN edificio por paso de tiempo.

    Uso:
        axes = RewardAxes(lambdas=[0.25,0.25,0.20,0.10,0.05,0.10,0.05])
        axes.set_baseline(co2_base=0.790, cost_base=0.38, ...)
        r_scalar, r_vec = axes.compute(building_state, env_state)
    """

    def __init__(
        self,
        lambdas: np.ndarray | list[float] | None = None,
        baseline: dict[str, float] | None = None,
    ):
        lam = np.array(lambdas, dtype=np.float64) if lambdas is not None else DEFAULT_LAMBDAS.copy()
        assert len(lam) == 7, "Se necesitan exactamente 7 pesos λ"
        lam = lam / (lam.sum() + _EPS)   # normalizar al simplex
        self.lambdas = lam

        # Valores de referencia RBC para normalización
        self._base: dict[str, float] = {
            "co2_kgperkwh":      0.790,    # ELECTRO ORIENTE diesel puro
            "cost_usd_per_kwh":  0.38,     # tarifa punta MT Iquitos OSINERGMIN
            "peak_kw":           1000.0,   # demanda punta comunidad (kW)
            "discomfort_c":      2.0,      # °C sobre setpoint en RBC
            "soh_loss_per_h":    1e-5,     # pérdida SoH/h en LFP
            "outage_load_kw":    100.0,    # carga sin cobertura en RBC
            "acs_cop_base":      0.85,     # COP calefón eléctrico resistivo
        }
        if baseline:
            self._base.update(baseline)

        # Acumuladores para estadísticas del episodio
        self._episode_sums: np.ndarray = np.zeros(7)
        self._step_count: int = 0

    def set_baseline(self, **kwargs: float) -> None:
        """Actualiza los valores de referencia RBC."""
        self._base.update(kwargs)

    def reset_episode(self) -> None:
        self._episode_sums[:] = 0.0
        self._step_count = 0

    # ── Eje 1 — CO₂ ──────────────────────────────────────────────────────────
    def _r_co2(
        self,
        net_consumption_kwh: float,
        carbon_intensity: float,
        pv_gen_kwh: float,
    ) -> float:
        """
        r₁ = -(E_net × CI) / (CI_base × E_ref)
        Donde CI varía con penetración solar (§4.3.1).
        Signo negativo: mayor consumo de red → mayor emisión → penalización.
        """
        emission = max(0.0, net_consumption_kwh) * carbon_intensity
        base_emission = self._base["co2_kgperkwh"] * (
            max(0.0, net_consumption_kwh) + pv_gen_kwh + _EPS
        )
        return -emission / (base_emission + _EPS)

    # ── Eje 2 — Costo económico ───────────────────────────────────────────────
    def _r_cost(
        self,
        net_consumption_kwh: float,
        price_usd_per_kwh: float,
        bess_charge_kwh: float,
        bess_discharge_kwh: float,
    ) -> float:
        """
        r₂ = -(E_net × P) / (P_base × E_ref)
        El BESS carga en fuera-punta y descarga en punta → arbitraje tarifario.
        """
        cost = max(0.0, net_consumption_kwh) * price_usd_per_kwh
        base_cost = self._base["cost_usd_per_kwh"] * (
            abs(net_consumption_kwh) + _EPS
        )
        return -cost / (base_cost + _EPS)

    # ── Eje 3 — Flexibilidad de red ───────────────────────────────────────────
    def _r_flexibility(
        self,
        net_consumption_kwh: float,
        net_consumption_prev_kwh: float | None,
        is_peak_hour: bool,
    ) -> float:
        """
        r₃ = L1_reduction + ramping_penalty
        L1_reduction: reducción de punta durante hora punta.
        Ramping: penaliza cambios bruscos en el consumo neto.
        """
        # Reducción de punta: positivo si consume menos que referencia en hora punta
        l1_term = 0.0
        if is_peak_hour:
            l1_term = -max(0.0, net_consumption_kwh) / (self._base["peak_kw"] / 24.0 + _EPS)

        # Ramping: penaliza variaciones bruscas
        ramp_term = 0.0
        if net_consumption_prev_kwh is not None:
            delta = abs(net_consumption_kwh - net_consumption_prev_kwh)
            ramp_term = -delta / (self._base["peak_kw"] / 24.0 + _EPS) * 0.1

        return l1_term + ramp_term

    # ── Eje 4 — Confort térmico ───────────────────────────────────────────────
    def _r_comfort(
        self,
        unmet_setpoint_diff: float,
        indoor_rh_pct: float | None = None,
    ) -> float:
        """
        r₄ = -|ΔT_unmet| / T_base — modelo adaptativo De Dear-Brager (§4.3.4)
        Banda de aceptabilidad adaptativa para Iquitos: T_neutral≈26°C,
        rango aceptable [23.5, 28.5]°C.
        Si indoor_rh_pct: penalización adicional por alta humedad (>70%).
        """
        comfort = -max(0.0, unmet_setpoint_diff) / (self._base["discomfort_c"] + _EPS)
        if indoor_rh_pct is not None and indoor_rh_pct > 70.0:
            comfort -= (indoor_rh_pct - 70.0) / 30.0 * 0.1   # penalización humedad
        return comfort

    # ── Eje 5 — Degradación BESS ─────────────────────────────────────────────
    def _r_degradation(
        self,
        soc: float,
        p_charge_kw: float,
        p_discharge_kw: float,
        t_cell_c: float = 30.0,
        capacity_kwh: float = 1.0,
    ) -> float:
        """
        r₅ = -ΔSoH_step / SoH_base
        Modelo Arrhenius-Peukert-SEI simplificado (§4.3.5):
          ΔSoH_Arrhenius ∝ exp(-Ea/(R·T))        — degradación calendárica
          ΔSoH_Peukert   ∝ (C_rate)^α × DoD      — ciclos de carga
          ΔSoH_SEI       ∝ sqrt(Q_throughput)     — crecimiento capa SEI
        """
        if capacity_kwh < _EPS:
            return 0.0

        T_K   = t_cell_c + 273.15
        Ea_R  = 4000.0         # Ea/R [K] — LFP (Wang et al. 2011)
        alpha = 1.15           # exponente Peukert

        # Degradación calendárica (temperatura)
        soh_cal = 1e-6 * np.exp(-Ea_R / T_K + Ea_R / (25 + 273.15))

        # Ciclos: C-rate normalizada
        c_rate = (abs(p_charge_kw) + abs(p_discharge_kw)) / (capacity_kwh + _EPS)
        dod_eff = abs(soc - 0.5) * 2.0   # profundidad efectiva del ciclo
        soh_cyc = 1e-6 * (c_rate ** alpha) * (dod_eff + _EPS)

        delta_soh = -(soh_cal + soh_cyc)
        return delta_soh / (self._base["soh_loss_per_h"] + _EPS)

    # ── Eje 6 — Resiliencia ───────────────────────────────────────────────────
    def _r_resilience(
        self,
        load_not_served_kwh: float,
        bess_soc: float,
        is_grid_outage: bool,
    ) -> float:
        """
        r₆ = bess_coverage_fraction durante cortes - penalización por carga no servida
        El BESS con SoC alto antes de un corte → mayor resiliencia.
        """
        if is_grid_outage:
            # Penalización por carga no servida
            penalty = -load_not_served_kwh / (self._base["outage_load_kw"] / 24.0 + _EPS)
            # Premio por SoC alto (preparación islanding)
            preparedness = bess_soc * 0.5
            return penalty + preparedness
        else:
            # Sin corte: recompensar SoC ≥ 0.3 como preparación
            return max(0.0, bess_soc - 0.3) * 0.1

    # ── Eje 7 — ACS (Agua Caliente Sanitaria) ────────────────────────────────
    def _r_acs(
        self,
        dhw_demand_kwh_th: float,
        dhw_elec_kwh: float,
        cop_acs: float | None = None,
    ) -> float:
        """
        r₇ = η_exergética_ACS = COP_ACS_actual / COP_ACS_base - 1
        Promueve el uso de bomba de calor ACS vs calefón resistivo.
        Para edificios sin ACS: r₇ = 0.
        """
        if dhw_demand_kwh_th < _EPS:
            return 0.0

        cop_actual = dhw_demand_kwh_th / (dhw_elec_kwh + _EPS)
        cop_actual = np.clip(cop_actual, 0.1, 5.0)
        base_cop   = self._base["acs_cop_base"]   # 0.85 calefón resistivo

        return (cop_actual - base_cop) / (base_cop + _EPS)

    # ── Computación integrada por paso ───────────────────────────────────────
    def compute(
        self,
        net_consumption_kwh:        float,
        net_consumption_prev_kwh:   float | None,
        carbon_intensity:           float,
        price_usd_per_kwh:          float,
        is_peak_hour:               bool,
        unmet_setpoint_diff:        float,
        bess_soc:                   float,
        bess_charge_kwh:            float,
        bess_discharge_kwh:         float,
        bess_capacity_kwh:          float,
        pv_gen_kwh:                 float,
        dhw_demand_kwh_th:          float   = 0.0,
        dhw_elec_kwh:               float   = 0.0,
        indoor_rh_pct:              float | None = None,
        t_cell_c:                   float   = 30.0,
        load_not_served_kwh:        float   = 0.0,
        is_grid_outage:             bool    = False,
        cop_acs:                    float | None = None,
    ) -> tuple[float, AxisValues]:
        """
        Retorna (r_escalar, AxisValues) para el paso actual.

        r_escalar = -Σ_k λ_k · r̃_k    (negativo: minimizamos costos)
        """
        r = AxisValues(
            co2         = self._r_co2(net_consumption_kwh, carbon_intensity, pv_gen_kwh),
            cost        = self._r_cost(net_consumption_kwh, price_usd_per_kwh,
                                       bess_charge_kwh, bess_discharge_kwh),
            flexibility = self._r_flexibility(net_consumption_kwh,
                                              net_consumption_prev_kwh, is_peak_hour),
            comfort     = self._r_comfort(unmet_setpoint_diff, indoor_rh_pct),
            degradation = self._r_degradation(bess_soc, bess_charge_kwh,
                                              bess_discharge_kwh, t_cell_c,
                                              bess_capacity_kwh),
            resilience  = self._r_resilience(load_not_served_kwh, bess_soc, is_grid_outage),
            acs         = self._r_acs(dhw_demand_kwh_th, dhw_elec_kwh, cop_acs),
        )

        r_vec   = r.to_array()
        # Clamping: [-10, 10] por eje para estabilidad numérica
        r_vec   = np.clip(r_vec, -10.0, 10.0)
        r_scalar = float(np.dot(self.lambdas, r_vec))

        # Acumular para estadísticas de episodio
        self._episode_sums += r_vec
        self._step_count   += 1

        return r_scalar, r

    def episode_means(self) -> np.ndarray:
        """Media de cada eje durante el episodio."""
        if self._step_count == 0:
            return np.zeros(7)
        return self._episode_sums / self._step_count

    def axis_names(self) -> list[str]:
        return ["CO2", "Costo", "Flexibilidad", "Confort", "Degradacion", "Resiliencia", "ACS"]

    @classmethod
    def from_config(cls, cfg: dict) -> "RewardAxes":
        """Crea desde sección 'reward' de un archivo YAML de config."""
        lambdas  = cfg.get("lambdas", DEFAULT_LAMBDAS.tolist())
        baseline = cfg.get("baseline", {})
        return cls(lambdas=lambdas, baseline=baseline)
