"""
KPIEvaluator — indicadores auxiliares de simulación y proxies de recompensa
=============================================================
Calcula los KPIs de evaluación del framework UC3M al final de cada episodio
o experimento completo.

KPIs agrupados en 7 dimensiones (§4.7.3):
  1. Energéticos      — ahorro energía, autosuficiencia, autoconsumo
  2. Económicos       — ahorro coste, LCOE, arbitraje tarifario
  3. Ambientales      — CO₂ evitado, índice renovable
  4. Confort          — horas de discomfort, ASHRAE-55, humedad
  5. Resiliencia      — cobertura de cortes, tiempo de islanding
  6. Degradación BESS — SoH loss, ciclos equivalentes, throughput
  7. Holísticos HPHI  — HPHI 7D, Sparsity, ε-coverage, Φ global

Usado por:
  - Bucle de entrenamiento de cada algoritmo (logging por episodio)
  - Pipeline de evaluación final (comparación entre algoritmos)
  - Dashboard W&B / MLflow
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Dict

from uc3m.reward.hphi import HPHI, compute_global_score

_EPS = 1e-8


@dataclass
class EpisodeKPIs:
    """KPIs calculados al final de un episodio de simulación."""

    # ── Dimensión 1 — Energéticos ──────────────────────────────────────
    energy_saved_kwh:         float | None = None  # requires a supplied matched baseline
    self_sufficiency:         float | None = None
    self_consumption:         float | None = None
    peak_reduction_kw:        float | None = None
    load_factor:              float | None = None

    # ── Dimensión 2 — Económicos ───────────────────────────────────────
    cost_saved_usd:           float | None = None
    cost_total_usd:           float | None = None
    arbitrage_gain_usd:       float | None = None  # needs a paired arbitrage experiment

    # ── Dimensión 3 — Ambientales ──────────────────────────────────────
    co2_avoided_kg:           float | None = None
    co2_total_kg:             float | None = None
    renewable_fraction:       float | None = None

    # ── Dimensión 4 — Confort ──────────────────────────────────────────
    discomfort_hours:         float | None = None  # hourly unmet setpoint, no ASHRAE certification
    avg_unmet_setpoint:       float | None = None
    avg_indoor_rh:            float | None = None

    # ── Dimensión 5 — Resiliencia ──────────────────────────────────────
    resilience_score:         float | None = None
    islanding_hours:          float | None = None
    load_not_served_kwh:      float | None = None

    # ── Dimensión 6 — Degradación BESS ────────────────────────────────
    soh_loss_pct:             float | None = None
    equivalent_cycles:        float | None = None
    throughput_kwh:           float | None = None

    # ── Dimensión 7 — Holísticos ───────────────────────────────────────
    hphi:                     float = 0.0   # HPHI 7D normalizado [0,1]
    sparsity:                 float = 0.0   # dispersión frontera Pareto
    epsilon_coverage:         float | None = None
    global_score:             float = 0.0   # reward proxy, not a calibrated physical 7D score
    pareto_front_size:        int   = 0     # |F| puntos no dominados

    # ── Metadatos ──────────────────────────────────────────────────────
    algorithm:    str = ""
    n_agents:     int = 0
    episode:      int = 0
    time_steps:   int = 0
    dataset:      str = ""
    metric_status: dict = field(default_factory=dict)
    scientific_eligible: bool = False

    def to_dict(self) -> dict:
        """Payload with None and provenance; use metric_values for scalar logging."""
        d = {}
        for k, v in self.__dict__.items():
            d[k] = float(v) if isinstance(v, (int, float, np.floating)) and not isinstance(v, bool) else v
        return d

    def summary_line(self) -> str:
        def fmt(value, digits):
            return 'N/A' if value is None else f'{value:.{digits}f}'
        return (
            f"[Ep {self.episode:>4}] "
            f"HPHI={self.hphi:.4f}  Φ={self.global_score:.4f}  "
            f"CO₂↓={fmt(self.co2_avoided_kg, 1)}kg  "
            f"Cost↓={fmt(self.cost_saved_usd, 2)}USD  "
            f"Peak↓={fmt(self.peak_reduction_kw, 1)}kW  "
            f"SoH↓={fmt(self.soh_loss_pct, 4)}%  "
            f"PF={self.pareto_front_size}"
        )

    def metric_values(self) -> Dict[str, float]:
        """Available scalars for log_metrics; provenance stays in to_dict."""
        metadata = {'n_agents', 'episode', 'time_steps', 'scientific_eligible'}
        return {k: float(v) for k, v in self.__dict__.items()
                if k not in metadata and isinstance(v, (int, float, np.floating))
                and not isinstance(v, bool) and np.isfinite(v)}


class KPIEvaluator:
    """
    Calcula indicadores disponibles; ausencias son None y modelos requieren opt-in.

    Uso típico:
        evaluator = KPIEvaluator(n_agents=17, baseline_kwh_per_step=..., ...)
        # Al final del episodio:
        kpis = evaluator.compute_episode(env, episode_idx=ep)
        # Logging:
        print(kpis.summary_line())
        mlflow.log_metrics(kpis.metric_values())
    """

    def __init__(
        self,
        n_agents: int,
        baseline_consumption_kwh: float | None = None,
        baseline_cost_usd: float | None = None,
        baseline_co2_kg: float | None = None,
        reference_pareto_front: np.ndarray | None = None,
        hphi_calculator: HPHI | None = None,
        carbon_intensity_default: float = 0.79,
        price_default_usd: float = 0.32,
        *,
        price_currency: str | None = None,
        baseline_peak_kw: float | None = None,
        allow_modeled_estimates: bool = False,
    ):
        if type(n_agents) is not int or n_agents < 1:
            raise ValueError('n_agents must be a positive integer')
        for value in (baseline_consumption_kwh, baseline_cost_usd, baseline_co2_kg,
                      baseline_peak_kw, price_default_usd, carbon_intensity_default):
            if value is not None and not np.isfinite(value):
                raise ValueError('baselines and modeled rates must be finite')
        self.n_agents    = n_agents
        self._hphi       = hphi_calculator if hphi_calculator is not None else HPHI()
        self._ref_pareto = reference_pareto_front

        # Valores de baseline (RBC) para normalización
        self._baseline_kwh  = baseline_consumption_kwh
        self._baseline_cost = baseline_cost_usd
        self._baseline_co2  = baseline_co2_kg
        self._ci_default    = carbon_intensity_default
        self._price_default = price_default_usd
        self._price_currency = price_currency
        self._baseline_peak = baseline_peak_kw
        self._allow_modeled = allow_modeled_estimates
        self._modeled_metrics = set()

        # Acumuladores intra-episodio
        self._episode: int = 0

    # ═══════════════════════════════════════════════════════════════════════
    # API principal
    # ═══════════════════════════════════════════════════════════════════════

    def compute_episode(
        self,
        env,                           # UC3MEnv
        episode_idx: int = 0,
        algorithm: str = "",
        dataset: str = "iquitos",
    ) -> EpisodeKPIs:
        """
        Calcula todos los KPIs del episodio a partir del estado del UC3MEnv.

        Parámetros
        ----------
        env          : UC3MEnv ya ejecutado (un episodio completo)
        episode_idx  : número de episodio
        algorithm    : nombre del algoritmo (para logging)
        dataset      : nombre del dataset (para trazabilidad)
        """
        self._episode = episode_idx
        self._modeled_metrics = set()

        # ── 1. Extraer medias de ejes de recompensa ───────────────────────
        axis_means = env.episode_axis_means()   # (N, 7)
        axis_means = np.asarray(axis_means, dtype=float)
        if axis_means.shape != (self.n_agents, 7) or not np.isfinite(axis_means).all():
            raise ValueError('reward proxy metrics require one finite seven-axis row per agent')
        mean_across_agents = axis_means.mean(axis=0)   # (7,)

        # ── 2. HPHI y métricas Pareto ─────────────────────────────────────
        for i in range(len(axis_means)):
            self._hphi.add_point(axis_means[i])

        hphi_val    = self._hphi.compute()
        sparsity    = self._hphi.sparsity()
        eps_cov     = (
            self._hphi.epsilon_coverage(self._ref_pareto)
            if self._ref_pareto is not None else 0.0
        )
        pf_size     = len(self._hphi.pareto_front())
        global_phi  = compute_global_score(
            np.clip(mean_across_agents + 1.0, _EPS, None)   # shift a [0,1] aproximado
        )

        # ── 3. KPIs energéticos (desde CityLearn buildings) ──────────────
        e_kpis = self._energy_kpis(env)

        # ── 4. KPIs económicos ────────────────────────────────────────────
        eco_kpis = self._economic_kpis(env)

        # ── 5. KPIs ambientales ───────────────────────────────────────────
        env_kpis = self._environmental_kpis(env)

        # ── 6. KPIs de confort ────────────────────────────────────────────
        com_kpis = self._comfort_kpis(env)

        # ── 7. KPIs de resiliencia ────────────────────────────────────────
        res_kpis = self._resilience_kpis(env)

        # ── 8. KPIs de degradación BESS ───────────────────────────────────
        deg_kpis = self._degradation_kpis(env)

        result = EpisodeKPIs(
            # Energéticos
            energy_saved_kwh   = e_kpis["saved_kwh"],
            self_sufficiency   = e_kpis["self_sufficiency"],
            self_consumption   = e_kpis["self_consumption"],
            peak_reduction_kw  = e_kpis["peak_reduction_kw"],
            load_factor        = e_kpis["load_factor"],
            # Económicos
            cost_saved_usd     = eco_kpis["saved_usd"],
            cost_total_usd     = eco_kpis["total_usd"],
            arbitrage_gain_usd = eco_kpis["arbitrage_usd"],
            # Ambientales
            co2_avoided_kg     = env_kpis["avoided_kg"],
            co2_total_kg       = env_kpis["total_kg"],
            renewable_fraction = env_kpis["renewable_frac"],
            # Confort
            discomfort_hours   = com_kpis["discomfort_h"],
            avg_unmet_setpoint = com_kpis["avg_unmet"],
            avg_indoor_rh      = com_kpis["avg_rh"],
            # Resiliencia
            resilience_score   = res_kpis["score"],
            islanding_hours    = res_kpis["islanding_h"],
            load_not_served_kwh= res_kpis["not_served_kwh"],
            # Degradación
            soh_loss_pct       = deg_kpis["soh_loss_pct"],
            equivalent_cycles  = deg_kpis["equiv_cycles"],
            throughput_kwh     = deg_kpis["throughput_kwh"],
            # Holísticos
            hphi               = hphi_val,
            sparsity           = sparsity,
            epsilon_coverage   = eps_cov,
            global_score       = global_phi,
            pareto_front_size  = pf_size,
            # Metadatos
            algorithm          = algorithm,
            n_agents           = self.n_agents,
            episode            = episode_idx,
            time_steps         = int(getattr(env.citylearn, 'time_step', env.time_steps)),
            dataset            = dataset,
        )
        metadata = {'algorithm', 'n_agents', 'episode', 'time_steps', 'dataset', 'metric_status', 'scientific_eligible'}
        result.metric_status = {name: ('unavailable' if value is None else 'simulation')
                                for name, value in result.__dict__.items() if name not in metadata}
        for name in ('hphi', 'global_score', 'sparsity', 'pareto_front_size'):
            result.metric_status[name] = 'reward_proxy'
        if self._ref_pareto is None:
            result.epsilon_coverage = None
            result.metric_status['epsilon_coverage'] = 'unavailable'
        for name in ('energy_saved_kwh', 'cost_saved_usd', 'co2_avoided_kg', 'peak_reduction_kw'):
            if getattr(result, name) is not None:
                result.metric_status[name] = 'comparison_supplied_baseline'
        for name in self._modeled_metrics:
            result.metric_status[name] = 'modeled'
        return result

    def reset_pareto(self) -> None:
        """Limpia la frontera Pareto acumulada (entre experimentos)."""
        self._hphi.clear()

    # ═══════════════════════════════════════════════════════════════════════
    # KPIs por categoría (helpers internos)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _series(env, obj, name):
        """Read only completed intervals, refusing missing/nonfinite signals."""
        value = getattr(obj, name, None)
        if value is None:
            return None
        arr = np.asarray(value, dtype=float).reshape(-1)
        count = int(getattr(env.citylearn, 'time_step', env.time_steps))
        if count <= 0 or arr.size < count:
            return None
        arr = arr[:count]
        return arr if np.all(np.isfinite(arr)) else None

    def _energy_kpis(self, env):
        nets, pvs, loads, discharges = [], [], [], []
        for building in env.citylearn.buildings:
            net = self._series(env, building, 'net_electricity_consumption')
            if net is None:
                raise ValueError('energy KPIs require completed finite net consumption')
            nets.append(net)
            pv = self._series(env, building, 'solar_generation')
            pvs.append(None if pv is None else np.abs(pv))
            load = self._series(env, building, 'net_electricity_consumption_without_storage_and_pv')
            if load is None:
                load = self._series(env, building, 'energy_consumption')
            loads.append(load)
            storage = getattr(building, 'electrical_storage', None)
            ec = self._series(env, storage, 'electricity_consumption') if storage else np.zeros_like(net)
            discharges.append(None if ec is None else np.maximum(-ec, 0))
        district = np.sum(nets, axis=0)
        total_net = float(district.sum())
        peak = float(np.max(np.maximum(district, 0)))
        valid = all(v is not None for v in pvs+loads+discharges)
        ss, sc = None, None
        if valid:
            pv = np.sum(pvs, axis=0)
            load = np.sum(loads, axis=0)
            discharge = np.sum(discharges, axis=0)
            if float(load.sum()) > 0:
                ss = float(np.clip(np.minimum(pv+discharge, load).sum()/load.sum(), 0, 1))
            if float(pv.sum()) > 0:
                sc = float(np.clip(np.minimum(pv, load).sum()/pv.sum(), 0, 1))
        return {'saved_kwh': None if self._baseline_kwh is None else self._baseline_kwh-total_net,
                'self_sufficiency': ss, 'self_consumption': sc,
                'peak_reduction_kw': None if self._baseline_peak is None else self._baseline_peak-peak,
                'load_factor': None if peak == 0 else float(np.maximum(district, 0).mean()/peak)}

    def _settlement(self, env, attr, container, fallback, metric, *, currency_ok=True):
        total, modeled = 0., False
        for building in env.citylearn.buildings:
            net = self._series(env, building, 'net_electricity_consumption')
            rates = self._series(env, getattr(building, container, None), attr) if currency_ok else None
            if net is None:
                return None
            if rates is None:
                if not self._allow_modeled:
                    return None
                rates = np.full_like(net, fallback)
                modeled = True
            if len(rates) != len(net):
                return None
            total += float(np.sum(net*rates))  # signed net settlement, matching canonical physical convention
        if modeled:
            self._modeled_metrics.add(metric)
        return total

    def _economic_kpis(self, env):
        total = self._settlement(env, 'electricity_pricing', 'pricing', self._price_default,
                                 'cost_total_usd', currency_ok=self._price_currency == 'USD')
        saved = None if total is None or self._baseline_cost is None else self._baseline_cost-total
        if saved is not None and 'cost_total_usd' in self._modeled_metrics:
            self._modeled_metrics.add('cost_saved_usd')
        return {'saved_usd': saved, 'total_usd': total, 'arbitrage_usd': None}

    def _environmental_kpis(self, env):
        total = self._settlement(env, 'carbon_intensity', 'carbon_intensity', self._ci_default, 'co2_total_kg')
        avoided = None if total is None or self._baseline_co2 is None else self._baseline_co2-total
        if avoided is not None and 'co2_total_kg' in self._modeled_metrics:
            self._modeled_metrics.add('co2_avoided_kg')
        pvs = [self._series(env, b, 'solar_generation') for b in env.citylearn.buildings]
        nets = [self._series(env, b, 'net_electricity_consumption') for b in env.citylearn.buildings]
        renewable = None
        if all(v is not None for v in pvs+nets):
            pv = sum(float(np.abs(v).sum()) for v in pvs)
            imports = sum(float(np.maximum(v, 0).sum()) for v in nets)
            renewable = pv/(imports+pv) if imports+pv > 0 else None
        return {'avoided_kg': avoided, 'total_kg': total, 'renewable_frac': renewable}

    def _comfort_kpis(self, env):
        unmet = [self._series(env, b, 'average_unmet_cooling_setpoint_difference')
                 for b in env.citylearn.buildings]
        rhs = [self._series(env, b, 'indoor_relative_humidity') for b in env.citylearn.buildings]
        valid_unmet = all(v is not None for v in unmet)
        return {'discomfort_h': (sum(float(np.count_nonzero(v > 0)) for v in unmet)/self.n_agents
                                 if valid_unmet else None),
                'avg_unmet': (float(np.mean([np.maximum(v, 0).mean() for v in unmet]))
                              if valid_unmet else None),
                'avg_rh': float(np.mean([v.mean() for v in rhs])) if all(v is not None for v in rhs) else None}

    def _resilience_kpis(self, env):
        # A storage SoC proxy cannot establish service delivered during outages.
        return {'score': None, 'islanding_h': None, 'not_served_kwh': None}

    def _degradation_kpis(self, env):
        throughput, capacity, available = 0., 0., True
        for building in env.citylearn.buildings:
            storage = getattr(building, 'electrical_storage', None)
            if storage is None:
                continue
            ec = self._series(env, storage, 'electricity_consumption')
            cap = getattr(storage, 'capacity', None)
            if ec is None or cap is None or not np.isfinite(cap) or cap <= 0:
                available = False
                continue
            throughput += float(np.abs(ec).sum())
            capacity += float(cap)
        cycles = throughput/(2*capacity) if available and capacity > 0 else None
        loss = cycles*0.0003 if cycles is not None and self._allow_modeled else None
        if loss is not None:
            self._modeled_metrics.add('soh_loss_pct')
        return {'soh_loss_pct': loss, 'equiv_cycles': cycles,
                'throughput_kwh': throughput if available else None}

    @staticmethod
    def compare(kpis_list: list[EpisodeKPIs]) -> Dict[str, dict]:
        """
        Genera tabla comparativa entre resultados de distintos algoritmos.
        kpis_list: lista de EpisodeKPIs (uno por algoritmo / run).
        """
        result = {}
        for k in kpis_list:
            result[k.algorithm or f"run_{k.episode}"] = {
                "HPHI":          k.hphi,
                "Global_Phi":    k.global_score,
                "CO2_avoided_kg":k.co2_avoided_kg,
                "Cost_saved_USD":k.cost_saved_usd,
                "Peak_red_kW":   k.peak_reduction_kw,
                "SoH_loss_%":    k.soh_loss_pct,
                "Resilience":    k.resilience_score,
                "PF_size":       float(k.pareto_front_size),
                "metric_status": dict(k.metric_status),
                "scientific_eligible": k.scientific_eligible,
            }
        return result
