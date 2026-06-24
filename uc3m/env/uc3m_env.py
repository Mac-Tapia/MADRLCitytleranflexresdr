"""
uc3m.env.uc3m_env — Entorno Meta-Dec-POMDP UC3M sobre CityLearn
================================================================
``UC3MEnv`` envuelve un ``citylearn.citylearn.CityLearnEnv`` y le añade la capa
experimental CityLearn v3 del framework UC3M:

- Observaciones aumentadas con el tensor BACT (29-D) por edificio (contexto
  activo–clima–edificio para transferibilidad geográfica, Teor. 4.10).
- Recompensa holística de 7 ejes (``uc3m.reward.axes.RewardAxes``) escalarizada
  por agente, calculada en cada paso a partir del estado físico de CityLearn.
- Dos modos de interfaz:
    * ``harl_mode=False`` (por defecto) → ``reset``/``step`` usan ``dict`` indexado
      por ``agent_id`` (compatible con backends off-policy estilo PettingZoo).
    * ``harl_mode=True`` → ``reset``/``step`` usan ``list`` ordenada por edificio
      (compatible con los runners HARL: HAPPO/HATRPO/HATD3/HASAC/MAA2C).

El entorno expone observación/acción heterogéneas: cada edificio tiene un número
distinto de cargadores EV / DERs, por lo que las dimensiones varían por agente.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Union

import numpy as np

from uc3m.env.bact import BACT_DIM, BACTEncoder, ClimateVector, IQUITOS_CLIMATE
from uc3m.reward.axes import RewardAxes

logger = logging.getLogger(__name__)

# Horas punta TOU por defecto (OSINERGMIN MT3/MT4 Iquitos: 18:00–22:59).
_DEFAULT_PEAK_HOURS = (18, 19, 20, 21, 22)


def _last(x, default: float = 0.0) -> float:
    """Último valor finito de un array/escalar de CityLearn (o ``default``)."""
    if x is None:
        return default
    try:
        a = np.asarray(x, dtype=float).ravel()
    except (TypeError, ValueError):
        return default
    if a.size == 0:
        return default
    v = a[-1]
    return float(v) if np.isfinite(v) else default


class UC3MEnv:
    """Entorno multi-agente CityLearn v3 (Dec-POMDP, CTDE) del framework UC3M."""

    def __init__(
        self,
        schema_path: str,
        climate: ClimateVector = IQUITOS_CLIMATE,
        lambdas=None,
        reward_config: dict | None = None,
        harl_mode: bool = False,
    ):
        # Import perezoso: evita cargar CityLearn al sólo importar el paquete uc3m.
        from citylearn.citylearn import CityLearnEnv

        self.schema_path = str(schema_path)
        self.climate = climate
        self.harl_mode = bool(harl_mode)
        self.reward_config = reward_config or {}

        self._cl = CityLearnEnv(schema=self.schema_path, central_agent=False)

        self.n_buildings = len(self._cl.buildings)
        self.n_agents = self.n_buildings
        self.agent_ids = [getattr(b, "name", f"Building_{i + 1}")
                          for i, b in enumerate(self._cl.buildings)]

        # Dimensiones de acción por agente (heterogéneas).
        self.action_dimensions = [int(s.shape[0]) for s in self._cl.action_space]
        self.action_dimension = max(self.action_dimensions) if self.action_dimensions else 1

        # Dimensiones de observación = BACT (29) + observación cruda de CityLearn.
        raw_obs_dims = [int(s.shape[0]) for s in self._cl.observation_space]
        self._raw_obs_dims = raw_obs_dims
        self.observation_dimension = (max(raw_obs_dims) + BACT_DIM) if raw_obs_dims else BACT_DIM

        # Tensor BACT por edificio (contexto fijo durante el episodio).
        self._encoder = BACTEncoder(climate=self.climate)
        self._bact = [self._encoder.encode(self._building_metadata(b))
                      for b in self._cl.buildings]

        # Operador de recompensa holístico de 7 ejes, uno por agente.
        lam = lambdas if lambdas is not None else self.reward_config.get("lambdas")
        baseline = self.reward_config.get("baseline")
        self._axes = [RewardAxes(lambdas=lam, baseline=baseline)
                      for _ in range(self.n_agents)]

        # Parámetros de precio/carbono para los ejes de recompensa.
        base = self.reward_config.get("baseline", {}) if self.reward_config else {}
        self._ci = float(base.get("co2_kgperkwh", 0.79))
        self._price_peak = float(base.get("cost_usd_per_kwh", 0.38))
        self._price_offpeak = float(base.get("offpeak_usd_per_kwh", 0.26))
        self._peak_hours = set(self.reward_config.get("peak_hours", _DEFAULT_PEAK_HOURS))

        self._prev_net: List[float | None] = [None] * self.n_agents
        self._started = False

    # ════════════════════════════════════════════════════════════════════════
    # Propiedades
    # ════════════════════════════════════════════════════════════════════════

    @property
    def citylearn(self):
        """Entorno CityLearn interno (acceso a ``.buildings`` para KPIs)."""
        return self._cl

    @property
    def time_steps(self) -> int:
        """Número de pasos por episodio del dataset CityLearn."""
        return int(getattr(self._cl, "time_steps", 0) or 0)

    # ════════════════════════════════════════════════════════════════════════
    # API del entorno
    # ════════════════════════════════════════════════════════════════════════

    def reset(self) -> Union[Dict[str, np.ndarray], List[np.ndarray]]:
        """Reinicia el episodio y devuelve la observación inicial aumentada."""
        out = self._cl.reset()
        obs_list = out[0] if isinstance(out, tuple) else out
        for ax in self._axes:
            ax.reset_episode()
        self._prev_net = [None] * self.n_agents
        self._started = True
        return self._format_obs(obs_list)

    def step(self, actions):
        """Avanza un paso. Acepta ``dict`` (por agent_id) o ``list`` de acciones."""
        act_list = self._to_action_list(actions)
        out = self._cl.step(act_list)

        # CityLearn (gymnasium): (obs, reward, terminated, truncated, info)
        if len(out) == 5:
            obs_list, _cl_reward, terminated, truncated, info = out
        else:  # compatibilidad con (obs, reward, done, info)
            obs_list, _cl_reward, terminated, info = out
            truncated = False

        done = self._as_done(terminated) or self._as_done(truncated)

        rewards = self._compute_rewards()
        obs = self._format_obs(obs_list)

        if self.harl_mode:
            return obs, rewards, done, info
        rewards_dict = {aid: r for aid, r in zip(self.agent_ids, rewards)}
        return obs, rewards_dict, done, info

    def close(self) -> None:
        """Libera el entorno CityLearn interno."""
        try:
            if hasattr(self._cl, "close"):
                self._cl.close()
        except Exception:  # noqa: BLE001 — cierre best-effort
            pass

    def episode_axis_means(self) -> np.ndarray:
        """Media de los 7 ejes de recompensa por agente: matriz (N, 7)."""
        if not self._axes:
            return np.zeros((0, 7))
        return np.stack([ax.episode_means() for ax in self._axes], axis=0)

    # ════════════════════════════════════════════════════════════════════════
    # Helpers internos
    # ════════════════════════════════════════════════════════════════════════

    def _format_obs(self, obs_list):
        """Antepone el BACT a cada observación y saneada NaN/Inf."""
        formatted: List[np.ndarray] = []
        for i in range(self.n_agents):
            raw = np.asarray(obs_list[i], dtype=np.float64).ravel() if i < len(obs_list) \
                else np.zeros(self._raw_obs_dims[i], dtype=np.float64)
            full = np.concatenate([self._bact[i], raw])
            full = np.nan_to_num(full, nan=0.0, posinf=0.0, neginf=0.0)
            formatted.append(full)
        if self.harl_mode:
            return formatted
        return {aid: vec for aid, vec in zip(self.agent_ids, formatted)}

    def _to_action_list(self, actions) -> List[np.ndarray]:
        """Normaliza acciones (dict o secuencia) a lista ordenada por edificio."""
        if isinstance(actions, dict):
            seq = [actions[aid] for aid in self.agent_ids]
        else:
            seq = list(actions)
        return [np.asarray(a, dtype=np.float64).ravel() for a in seq]

    @staticmethod
    def _as_done(flag) -> bool:
        """Interpreta terminated/truncated como bool (escalar o lista)."""
        if isinstance(flag, (list, tuple, np.ndarray)):
            return bool(np.any(np.asarray(flag)))
        return bool(flag)

    def _compute_rewards(self) -> List[float]:
        """Calcula la recompensa holística escalarizada por agente."""
        hour = int(getattr(self._cl, "time_step", 0)) % 24
        is_peak = hour in self._peak_hours
        price = self._price_peak if is_peak else self._price_offpeak

        rewards: List[float] = []
        for i, bldg in enumerate(self._cl.buildings):
            net = _last(getattr(bldg, "net_electricity_consumption", None), 0.0)
            pv = abs(_last(getattr(bldg, "solar_generation", None), 0.0))
            unmet = _last(getattr(bldg, "average_unmet_cooling_setpoint_difference", None), 0.0)

            storage = getattr(bldg, "electrical_storage", None)
            soc = _last(getattr(storage, "soc", None), 0.5) if storage is not None else 0.5
            cap = float(getattr(storage, "capacity", 0.0) or 0.0) if storage is not None else 0.0
            stor_flow = _last(getattr(storage, "electricity_consumption", None), 0.0) \
                if storage is not None else 0.0
            charge = max(0.0, stor_flow)
            discharge = max(0.0, -stor_flow)

            r_scalar, _axisvals = self._axes[i].compute(
                net_consumption_kwh=net,
                net_consumption_prev_kwh=self._prev_net[i],
                carbon_intensity=self._ci,
                price_usd_per_kwh=price,
                is_peak_hour=is_peak,
                unmet_setpoint_diff=unmet,
                bess_soc=soc,
                bess_charge_kwh=charge,
                bess_discharge_kwh=discharge,
                bess_capacity_kwh=cap,
                pv_gen_kwh=pv,
            )
            self._prev_net[i] = net
            rewards.append(float(r_scalar) if np.isfinite(r_scalar) else 0.0)
        return rewards

    def _building_metadata(self, building) -> dict:
        """Extrae metadatos del edificio (best-effort) para el BACT."""
        data: dict = {}
        storage = getattr(building, "electrical_storage", None)
        if storage is not None:
            data["cap_bess_kwh"] = float(getattr(storage, "capacity", 0.0) or 0.0)
            nominal = getattr(storage, "nominal_power", None)
            if nominal is not None:
                try:
                    data["p_bess_kw"] = float(nominal)
                except (TypeError, ValueError):
                    pass
        pv = getattr(building, "pv", None)
        if pv is not None:
            data["pv_kwp"] = float(getattr(pv, "nominal_power", 0.0) or 0.0)
        return data

    def __repr__(self) -> str:
        return (
            f"UC3MEnv(buildings={self.n_buildings}, harl_mode={self.harl_mode}, "
            f"obs_dim={self.observation_dimension}, act_dim={self.action_dimension}, "
            f"schema='{self.schema_path}')"
        )
