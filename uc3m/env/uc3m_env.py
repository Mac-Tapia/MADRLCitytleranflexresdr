"""
UC3MEnv — Fachada universal Dec-POMDP sobre CityLearn v3 (enfoque híbrido)
==========================================================================
``UC3MEnv`` NO reimplementa la física: es una **fachada (adapter)** delgada
sobre la capa operativa ``CityLearn/citylearn/v3`` (``make_citylearn_v3_env``,
un PettingZoo ParallelEnv). Así existe una sola implementación del entorno y se
conserva la API documentada del framework UC3M.

Responsabilidades de la fachada:
  1. Anteponer el tensor de contexto fijo BACT (29D) a cada observación local.
  2. Exponer una API estable e independiente del backend
     (``n_agents``, ``action_dimensions``, ``reset``, ``step``, ...).
  3. Soportar dos convenciones de E/S:
       - ``harl_mode=False`` → dicts ``{agent_id: array}`` (estilo PettingZoo).
       - ``harl_mode=True``  → listas ordenadas por agente (estilo HARL).

La importación de CityLearn es **perezosa** (dentro de ``__init__``) para que el
dominio se pueda importar y testear sin CityLearn/torch instalados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import numpy as np

from uc3m.env.bact import BACT_DIM, BACTEncoder, ClimateVector, IQUITOS_CLIMATE
from uc3m.reward.axes import RewardAxes

Observation = Union[Dict[str, np.ndarray], List[np.ndarray]]
Reward = Union[Dict[str, float], List[float]]


def _first_space_dimension(space: Any) -> int:
    """Return the leading dimension of a non-scalar Gymnasium space."""
    shape = getattr(space, "shape", None)
    if not shape:
        raise ValueError(f"Expected a non-scalar space, got shape={shape!r}")
    return int(shape[0])


class UC3MEnv:
    """Entorno Dec-POMDP universal para N edificios arbitrarios."""

    def __init__(
        self,
        schema_path: str | Path,
        climate: ClimateVector = IQUITOS_CLIMATE,
        *,
        lambdas: Optional[Sequence[float]] = None,
        reward_config: Optional[Mapping[str, Any]] = None,
        harl_mode: bool = False,
        scenario: str = "E1",
        seed: Optional[int] = None,
        episode_time_steps: Optional[int] = None,
        normalize_observations: bool = False,
        madrl_algorithm: Optional[str] = None,
    ) -> None:
        self.schema_path = str(schema_path)
        self.climate = climate
        self.lambdas = lambdas
        self.reward_config = dict(reward_config or {})
        self.harl_mode = bool(harl_mode)
        self.scenario = scenario
        self._seed = seed

        # — Construcción perezosa del backend CityLearn v3 —
        from citylearn.v3.environment import make_citylearn_v3_env

        self._dec = make_citylearn_v3_env(
            schema_path=self.schema_path,
            scenario=scenario,
            seed=seed,
            episode_time_steps=episode_time_steps,
            normalize_observations=normalize_observations,
            madrl_algorithm=madrl_algorithm,
        )

        self.agent_ids: List[str] = list(self._dec.possible_agents)
        self._action_dims: List[int] = [
            _first_space_dimension(self._dec.action_space(a)) for a in self.agent_ids
        ]
        self._cl_obs_dims: List[int] = [
            _first_space_dimension(self._dec.observation_space(a)) for a in self.agent_ids
        ]
        # Observación expuesta = BACT (29) + observación local de CityLearn.
        self._obs_dims: List[int] = [BACT_DIM + d for d in self._cl_obs_dims]

        self._bact: Dict[str, np.ndarray] = self._build_bact_vectors()
        self._last_obs: Dict[str, np.ndarray] = {}
        self._prev_net_kwh: List[float] = [0.0] * self.n_agents

        reward_cfg = dict(self.reward_config)
        if lambdas is not None:
            reward_cfg.setdefault("lambdas", list(lambdas))
        self._reward_axes: List[RewardAxes] = [
            RewardAxes.from_config(reward_cfg) for _ in range(self.n_agents)
        ]

    def episode_axis_means(self) -> np.ndarray:
        """Medias de los 7 ejes de recompensa por agente, shape ``(N, 7)``."""
        if not self._reward_axes:
            return np.zeros((self.n_agents, 7), dtype=np.float64)
        return np.stack([ax.episode_means() for ax in self._reward_axes], axis=0)

    # ── Propiedades de introspección ────────────────────────────────────────
    @property
    def n_agents(self) -> int:
        return len(self.agent_ids)

    @property
    def n_buildings(self) -> int:
        return self.n_agents

    @property
    def action_dimensions(self) -> List[int]:
        return list(self._action_dims)

    @property
    def action_dimension(self) -> int:
        return max(self._action_dims) if self._action_dims else 0

    @property
    def observation_dimensions(self) -> List[int]:
        return list(self._obs_dims)

    @property
    def observation_dimension(self) -> int:
        return max(self._obs_dims) if self._obs_dims else 0

    @property
    def time_steps(self) -> int:
        core = self.citylearn
        return int(getattr(core, "time_steps", 0) or 0)

    @property
    def citylearn(self):
        """Entorno CityLearn v2 interno (con ``.buildings``)."""
        return getattr(self._dec.env, "unwrapped", self._dec.env)

    # ── API Dec-POMDP ───────────────────────────────────────────────────────
    def reset(self, seed: Optional[int] = None, options: Optional[Mapping] = None) -> Observation:
        obs_dict, _info = self._dec.reset(seed=seed if seed is not None else self._seed, options=options)
        self.last_terminations = {a: False for a in self.agent_ids}
        self.last_truncations = {a: False for a in self.agent_ids}
        self._last_obs = {
            a: self._augment(a, obs_dict[a]) for a in self.agent_ids if a in obs_dict
        }
        self._prev_net_kwh = [0.0] * self.n_agents
        for ax in self._reward_axes:
            ax.reset_episode()
        return self._format_obs(self._last_obs)

    def step(self, actions: Union[Mapping[str, Any], Sequence[Any]]):
        action_dict = self._actions_to_dict(actions)
        obs_dict, reward_dict, terminations, truncations, infos = self._dec.step(action_dict)
        self.last_terminations = dict(terminations)
        self.last_truncations = dict(truncations)

        augmented = {
            a: self._augment(a, obs_dict[a]) for a in self.agent_ids if a in obs_dict
        }
        if augmented:
            self._last_obs = augmented

        self._update_reward_axes()

        done = bool(
            (terminations and any(bool(v) for v in terminations.values()))
            or (truncations and any(bool(v) for v in truncations.values()))
        )

        obs_out = self._format_obs(self._last_obs)
        rew_out = self._format_rewards(reward_dict)
        info_out = self._format_info(infos)
        return obs_out, rew_out, done, info_out

    def state(self) -> np.ndarray:
        """Estado global CTDE = concatenación de observaciones locales."""
        return self._dec.state()

    def close(self) -> None:
        try:
            self._dec.close()
        except Exception:  # pylint: disable=broad-exception-caught  # pragma: no cover
            pass

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (
            f"UC3MEnv(N={self.n_agents}, obs_dim={self.observation_dimension}, "
            f"act_dim={self.action_dimension}, harl_mode={self.harl_mode}, "
            f"scenario={self.scenario})"
        )

    # ── Internos ────────────────────────────────────────────────────────────
    def _augment(self, agent: str, obs: Any) -> np.ndarray:
        """Antepone el BACT del agente a su observación local de CityLearn."""
        local = np.nan_to_num(
            np.asarray(obs, dtype=np.float64).reshape(-1),
            nan=0.0, posinf=0.0, neginf=0.0,
        )
        bact = self._bact.get(agent, np.zeros(BACT_DIM, dtype=np.float64))
        return np.concatenate([bact, local])

    def _format_obs(self, obs_dict: Dict[str, np.ndarray]) -> Observation:
        if self.harl_mode:
            return [obs_dict[a] for a in self.agent_ids if a in obs_dict]
        return dict(obs_dict)

    def _format_rewards(self, reward_dict: Mapping[str, float]) -> Reward:
        if self.harl_mode:
            return [float(reward_dict.get(a, 0.0)) for a in self.agent_ids]
        return {a: float(reward_dict.get(a, 0.0)) for a in self.agent_ids}

    def _format_info(self, infos: Mapping[str, Any]) -> Any:
        if self.harl_mode:
            return [infos.get(a, {}) for a in self.agent_ids]
        return dict(infos)

    def _actions_to_dict(self, actions: Union[Mapping[str, Any], Sequence[Any]]) -> Dict[str, np.ndarray]:
        if isinstance(actions, Mapping):
            return {a: np.asarray(actions[a], dtype=np.float32) for a in self.agent_ids}
        # Secuencia ordenada por agente (estilo HARL / lista posicional).
        seq = list(actions)
        if len(seq) != self.n_agents:
            raise ValueError(
                f"Se esperaban {self.n_agents} acciones, se recibieron {len(seq)}."
            )
        return {a: np.asarray(seq[i], dtype=np.float32) for i, a in enumerate(self.agent_ids)}

    def _build_bact_vectors(self) -> Dict[str, np.ndarray]:
        encoder = BACTEncoder(self.climate)
        buildings = list(getattr(self.citylearn, "buildings", []) or [])
        out: Dict[str, np.ndarray] = {}
        for i, agent in enumerate(self.agent_ids):
            building = buildings[i] if i < len(buildings) else None
            out[agent] = encoder.encode(self._building_to_data(building))
        return out

    @staticmethod
    def _building_to_data(building: Any) -> Dict[str, object]:
        """Extrae descriptores estáticos de un edificio CityLearn (con fallbacks)."""
        def _attr(obj: Any, *names: str, default: float = 0.0) -> float:
            for name in names:
                cur = obj
                ok = True
                for part in name.split("."):
                    cur = getattr(cur, part, None)
                    if cur is None:
                        ok = False
                        break
                if ok and cur is not None:
                    try:
                        return float(cur)
                    except (TypeError, ValueError):
                        continue
            return float(default)

        if building is None:
            return {}

        chargers = getattr(building, "electric_vehicle_chargers", None) or []
        try:
            n_ev = float(len(chargers))
        except TypeError:
            n_ev = 0.0
        ev_kw = 0.0
        if chargers:
            ev_kw = _attr(chargers[0], "nominal_power", "max_charging_power", default=0.0)

        name = getattr(building, "name", "") or ""
        return {
            "bldg_type": name,
            "area_m2": _attr(building, "floor_area", "net_floor_area"),
            "cap_bess_kwh": _attr(building, "electrical_storage.capacity",
                                  "electrical_storage.capacity_history"),
            "p_bess_kw": _attr(building, "electrical_storage.nominal_power"),
            "dod": _attr(building, "electrical_storage.depth_of_discharge", default=0.8),
            "eta_rt": _attr(building, "electrical_storage.efficiency", default=0.9),
            "pv_kwp": _attr(building, "pv.nominal_power"),
            "n_ev_chargers": n_ev,
            "ev_charger_kw": ev_kw,
            "has_dhw": _attr(building, "dhw_storage.capacity") > 0,
            "cop_design": _attr(building, "cooling_device.efficiency", default=2.8),
        }

    def _update_reward_axes(self) -> None:
        """Acumula medias de ejes de recompensa UC3M por edificio tras cada paso."""
        buildings = list(getattr(self.citylearn, "buildings", []) or [])
        for i, axes in enumerate(self._reward_axes):
            building = buildings[i] if i < len(buildings) else None
            metrics = self._building_step_metrics(building, i)
            axes.compute(**metrics)
            self._prev_net_kwh[i] = metrics["net_consumption_kwh"]

    @staticmethod
    def _latest_scalar(series: Any, default: float = 0.0) -> float:
        if series is None:
            return float(default)
        # Objetos CityLearn (CarbonIntensity, Pricing, ...) con serie interna.
        for attr in ("carbon_intensity", "electricity_pricing", "value", "values"):
            if hasattr(series, attr):
                inner = getattr(series, attr)
                if inner is not series:
                    return UC3MEnv._latest_scalar(inner, default=default)
        arr = np.asarray(series, dtype=np.float64).reshape(-1)
        if arr.size == 0:
            return float(default)
        val = float(arr[-1])
        return val if np.isfinite(val) else float(default)

    def _at_time_step(self, building: Any, series: Any, default: float = 0.0) -> float:
        """Valor escalar en ``building.time_step`` si la serie es indexable."""
        if series is None:
            return float(default)
        step = int(getattr(building, "time_step", 0) or 0)
        for attr in ("carbon_intensity", "electricity_pricing"):
            if hasattr(series, attr):
                arr = np.asarray(getattr(series, attr), dtype=np.float64).reshape(-1)
                if arr.size == 0:
                    return float(default)
                idx = min(max(step, 0), arr.size - 1)
                val = float(arr[idx])
                return val if np.isfinite(val) else float(default)
        return self._latest_scalar(series, default=default)

    def _building_step_metrics(self, building: Any, index: int) -> Dict[str, Any]:
        """Extrae señales mínimas del edificio CityLearn para ``RewardAxes.compute``."""
        if building is None:
            net = 0.0
            return {
                "net_consumption_kwh": net,
                "net_consumption_prev_kwh": self._prev_net_kwh[index],
                "carbon_intensity": 0.79,
                "price_usd_per_kwh": 0.26,
                "is_peak_hour": False,
                "unmet_setpoint_diff": 0.0,
                "bess_soc": 0.5,
                "bess_charge_kwh": 0.0,
                "bess_discharge_kwh": 0.0,
                "bess_capacity_kwh": 1.0,
                "pv_gen_kwh": 0.0,
            }

        net = self._latest_scalar(getattr(building, "net_electricity_consumption", None))
        pv = self._latest_scalar(getattr(building, "solar_generation", None))
        bess = getattr(building, "electrical_storage", None)
        bess_soc = self._latest_scalar(getattr(bess, "soc", None), default=0.5) if bess else 0.5
        bess_cap = self._latest_scalar(getattr(bess, "capacity", None), default=1.0) if bess else 1.0
        bess_ec = self._latest_scalar(getattr(bess, "electricity_consumption", None)) if bess else 0.0
        bess_charge = max(0.0, bess_ec)
        bess_discharge = max(0.0, -bess_ec)

        return {
            "net_consumption_kwh": net,
            "net_consumption_prev_kwh": self._prev_net_kwh[index],
            "carbon_intensity": self._at_time_step(
                building, getattr(building, "carbon_intensity", None), default=0.79
            ),
            "price_usd_per_kwh": self._at_time_step(
                building, getattr(building, "pricing", None), default=0.26
            ),
            "is_peak_hour": False,
            "unmet_setpoint_diff": self._latest_scalar(
                getattr(building, "indoor_dry_bulb_temperature_set_point_delta", None)
            ),
            "bess_soc": bess_soc,
            "bess_charge_kwh": bess_charge,
            "bess_discharge_kwh": bess_discharge,
            "bess_capacity_kwh": max(bess_cap, 1e-6),
            "pv_gen_kwh": pv,
        }


__all__ = ["UC3MEnv"]
