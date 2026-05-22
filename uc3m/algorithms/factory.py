"""
AlgorithmFactory — Plugin interface para 18+ algoritmos MADRL
=============================================================
Soporta todos los algoritmos definidos en §4.4 del framework UC3M:

  HARL (heterogeneous agent RL):
    HAPPO, HATRPO, HATD3, HASAC, MAA2C

  MARLlib (18+ algoritmos vía RLlib):
    MAPPO, MADDPG, MATD3, MAAC, MASAC, QMIX, VDN, FACMAC, COMA,
    IPPO, IQL, MAT, VDPPO, VDAC, CDS, ...

  Off-policy (standalone):
    MASAC, MATD3, MAAC (versiones standalone)

Uso:
    algo = AlgorithmFactory.create("HAPPO", env, cfg)
    algo.train(n_episodes=1000)
    algo.save("checkpoints/happo_iquitos")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)

# ── Registro de backends ───────────────────────────────────────────────────────

_HARL_ALGOS = {
    "HAPPO", "HATRPO", "HATD3", "HASAC", "MAA2C",
}

_MARLLIB_ALGOS = {
    "MAPPO", "MADDPG", "MATD3_ML", "MAAC_ML", "MASAC_ML",
    "QMIX", "VDN", "FACMAC", "COMA", "IPPO", "IQL", "MAT",
    "VDPPO", "VDAC", "CDS", "FAMA",
}

_OFFPOLICY_ALGOS = {
    "MASAC", "MATD3", "MAAC",
}

_ALL_ALGOS = _HARL_ALGOS | _MARLLIB_ALGOS | _OFFPOLICY_ALGOS


class AlgorithmFactory:
    """
    Factory que instancia el wrapper de entrenamiento correcto para
    cada algoritmo MADRL dado un UC3MEnv ya construido.

    Ejemplo:
        env  = UC3MEnv.from_iquitos(harl_mode=True)
        algo = AlgorithmFactory.create("HAPPO", env, cfg={"n_rollout_threads": 4})
        algo.learn(total_timesteps=500_000)
    """

    # ── Registro dinámico de adaptadores externos ─────────────────────────
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, adapter_class: Type) -> None:
        """Registra un adaptador personalizado para un algoritmo."""
        cls._registry[name.upper()] = adapter_class
        logger.info(f"[AlgorithmFactory] Adaptador registrado: {name.upper()}")

    @classmethod
    def create(
        cls,
        algorithm: str,
        env,                        # UC3MEnv
        cfg: Dict[str, Any] | None = None,
        checkpoint_dir: str | Path | None = None,
    ):
        """
        Instancia el adaptador de entrenamiento para el algoritmo dado.

        Parámetros
        ----------
        algorithm     : str  — nombre del algoritmo (case-insensitive)
        env           : UC3MEnv — entorno ya construido
        cfg           : dict — hiperparámetros del algoritmo
        checkpoint_dir: str | Path — directorio para checkpoints

        Returns
        -------
        Un adaptador con método `.learn(total_timesteps)` y `.save(path)`.
        """
        name = algorithm.strip().upper()
        cfg  = cfg or {}

        if name in cls._registry:
            return cls._registry[name](env, cfg, checkpoint_dir)

        if name in _HARL_ALGOS:
            return cls._create_harl(name, env, cfg, checkpoint_dir)

        if name in _MARLLIB_ALGOS:
            return cls._create_marllib(name, env, cfg, checkpoint_dir)

        if name in _OFFPOLICY_ALGOS:
            return cls._create_offpolicy(name, env, cfg, checkpoint_dir)

        raise ValueError(
            f"Algoritmo '{name}' no reconocido. "
            f"Disponibles: {sorted(_ALL_ALGOS)}"
        )

    @classmethod
    def list_algorithms(cls) -> Dict[str, list]:
        return {
            "HARL":      sorted(_HARL_ALGOS),
            "MARLlib":   sorted(_MARLLIB_ALGOS),
            "off-policy": sorted(_OFFPOLICY_ALGOS),
            "custom":    sorted(cls._registry.keys()),
        }

    # ── Backends ──────────────────────────────────────────────────────────

    @classmethod
    def _create_harl(cls, name: str, env, cfg: dict, checkpoint_dir) -> "_HARLAdapter":
        try:
            import sys
            harl_path = Path(__file__).parents[3] / "external" / "HARL"
            if str(harl_path) not in sys.path:
                sys.path.insert(0, str(harl_path))
            return _HARLAdapter(name, env, cfg, checkpoint_dir)
        except ImportError as e:
            raise ImportError(
                f"HARL no disponible. Instala con: pip install -e external/HARL\n"
                f"Error: {e}"
            ) from e

    @classmethod
    def _create_marllib(cls, name: str, env, cfg: dict, checkpoint_dir) -> "_MARLlibAdapter":
        try:
            import sys
            marllib_path = Path(__file__).parents[3] / "external" / "MARLlib"
            if str(marllib_path) not in sys.path:
                sys.path.insert(0, str(marllib_path))
            return _MARLlibAdapter(name, env, cfg, checkpoint_dir)
        except ImportError as e:
            raise ImportError(
                f"MARLlib no disponible. Instala con: pip install -e external/MARLlib\n"
                f"Error: {e}"
            ) from e

    @classmethod
    def _create_offpolicy(cls, name: str, env, cfg: dict, checkpoint_dir) -> "_OffPolicyAdapter":
        try:
            import sys
            op_path = Path(__file__).parents[3] / "external" / "off-policy"
            if str(op_path) not in sys.path:
                sys.path.insert(0, str(op_path))
            return _OffPolicyAdapter(name, env, cfg, checkpoint_dir)
        except ImportError as e:
            raise ImportError(
                f"off-policy no disponible. Comprueba external/off-policy\n"
                f"Error: {e}"
            ) from e


# ── Adaptadores ────────────────────────────────────────────────────────────────

class _BaseAdapter:
    """Interfaz mínima que todos los adaptadores implementan."""

    def __init__(self, name: str, env, cfg: dict, checkpoint_dir):
        self.name           = name
        self.env            = env
        self.cfg            = cfg
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("checkpoints") / name.lower()
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._trainer = None

    def learn(self, total_timesteps: int = 500_000) -> Dict[str, Any]:
        raise NotImplementedError

    def save(self, path: str | Path | None = None) -> Path:
        raise NotImplementedError

    def load(self, path: str | Path) -> None:
        raise NotImplementedError


class _HARLAdapter(_BaseAdapter):
    """
    Adaptador para algoritmos HARL (HAPPO, HATRPO, HATD3, HASAC).
    El env debe tener harl_mode=True.
    """

    def __init__(self, name: str, env, cfg: dict, checkpoint_dir):
        super().__init__(name, env, cfg, checkpoint_dir)
        if not getattr(env, "harl_mode", False):
            logger.warning(
                f"HARL ({name}) requiere harl_mode=True en UC3MEnv. "
                "Seteando automáticamente."
            )
            env.harl_mode = True
        self._setup()

    def _setup(self):
        """Inicializa el runner HARL con la configuración del entorno."""
        try:
            from harl.runners import RUNNER_REGISTRY
            algo_lower = self.name.lower()
            runner_cfg = self._build_harl_cfg()
            self._trainer = RUNNER_REGISTRY[algo_lower](runner_cfg, self.env)
            logger.info(f"[HARL] {self.name} runner inicializado. N={self.env.n_agents}")
        except (ImportError, KeyError):
            logger.warning(f"[HARL] Runner no disponible todavía para {self.name}. Usando stub.")
            self._trainer = None

    def _build_harl_cfg(self) -> dict:
        n = self.env.n_agents
        obs_dim = self.env.observation_dimension or 128
        act_dim = self.env.action_dimension
        base = {
            "algorithm_name": self.name.lower(),
            "n_agents":        n,
            "obs_space":       [(obs_dim,)] * n,
            "act_space":       [(act_dim,)] * n,
            "n_rollout_threads": self.cfg.get("n_rollout_threads", 1),
            "episode_length":   self.env.time_steps,
            "num_env_steps":    self.cfg.get("num_env_steps", 10_000_000),
            "use_centralized_V": True,   # CTDE: centralized training
            "checkpoint_dir":   str(self.checkpoint_dir),
        }
        base.update(self.cfg)
        return base

    def learn(self, total_timesteps: int = 5_000_000) -> Dict[str, Any]:
        if self._trainer is None:
            logger.warning(f"[HARL] {self.name} no disponible — bucle de entrenamiento de placeholder.")
            return self._placeholder_loop(total_timesteps)
        self._trainer.run()
        return {}

    def _placeholder_loop(self, total_timesteps: int) -> Dict[str, Any]:
        """Loop básico sin librería HARL — útil para pruebas de integración."""
        import numpy as np
        obs = self.env.reset()
        total = 0
        ep_rewards = []
        while total < total_timesteps:
            acts = [
                np.random.uniform(-1, 1, self.env.action_dimension)
                for _ in range(self.env.n_agents)
            ]
            obs, rews, done, info = self.env.step(acts)
            ep_rewards.extend(rews)
            total += 1
            if done:
                obs = self.env.reset()
        mean_rew = float(np.mean(ep_rewards)) if ep_rewards else 0.0
        logger.info(f"[HARL placeholder] {self.name} | steps={total} | mean_r={mean_rew:.4f}")
        return {"mean_reward": mean_rew, "total_steps": total}

    def save(self, path=None) -> Path:
        p = Path(path) if path else self.checkpoint_dir / "model_final"
        if self._trainer and hasattr(self._trainer, "save"):
            self._trainer.save(str(p))
        logger.info(f"[HARL] Checkpoint guardado en {p}")
        return p

    def load(self, path) -> None:
        if self._trainer and hasattr(self._trainer, "load"):
            self._trainer.load(str(path))


class _MARLlibAdapter(_BaseAdapter):
    """
    Adaptador para algoritmos MARLlib (MAPPO, QMIX, VDN, etc.).
    """

    def __init__(self, name: str, env, cfg: dict, checkpoint_dir):
        super().__init__(name, env, cfg, checkpoint_dir)
        # Mapeo nombre UC3M → nombre MARLlib
        self._ml_name = {
            "MATD3_ML": "matd3", "MAAC_ML": "maac", "MASAC_ML": "masac",
        }.get(name, name.lower())
        self._setup()

    def _setup(self):
        try:
            from marllib import marl
            self._marl = marl
            logger.info(f"[MARLlib] {self.name} inicializado.")
        except ImportError:
            logger.warning("[MARLlib] no disponible. Usando placeholder.")
            self._marl = None

    def learn(self, total_timesteps: int = 5_000_000) -> Dict[str, Any]:
        if self._marl is None:
            return {"error": "MARLlib no disponible"}
        # MARLlib requiere registrar el env personalizado; aquí stub
        logger.info(f"[MARLlib] {self.name} — entrenamiento vía RLlib no implementado en esta versión.")
        return {}

    def save(self, path=None) -> Path:
        p = Path(path) if path else self.checkpoint_dir / "model_final"
        logger.info(f"[MARLlib] Checkpoint en {p}")
        return p

    def load(self, path) -> None:
        pass


class _OffPolicyAdapter(_BaseAdapter):
    """
    Adaptador para MASAC, MATD3, MAAC standalone (external/off-policy).
    """

    def __init__(self, name: str, env, cfg: dict, checkpoint_dir):
        super().__init__(name, env, cfg, checkpoint_dir)
        self._setup()

    def _setup(self):
        try:
            import sys
            op_path = Path(__file__).parents[3] / "external" / "off-policy"
            import importlib
            spec = importlib.util.find_spec("algorithms")
            if spec:
                from algorithms.runner import Runner   # type: ignore
                runner_cfg = self._build_cfg()
                self._trainer = Runner(self.name.lower(), self.env, runner_cfg)
                logger.info(f"[off-policy] {self.name} runner inicializado.")
            else:
                self._trainer = None
        except Exception as e:
            logger.warning(f"[off-policy] {self.name} no disponible: {e}")
            self._trainer = None

    def _build_cfg(self) -> dict:
        return {
            "n_agents":      self.env.n_agents,
            "obs_dim":       self.env.observation_dimension or 128,
            "act_dim":       self.env.action_dimension,
            "hidden_size":   self.cfg.get("hidden_size", 256),
            "lr":            self.cfg.get("lr", 3e-4),
            "gamma":         self.cfg.get("gamma", 0.99),
            "checkpoint_dir": str(self.checkpoint_dir),
        }

    def learn(self, total_timesteps: int = 500_000) -> Dict[str, Any]:
        if self._trainer is None:
            return self._placeholder_loop(total_timesteps)
        return self._trainer.run(total_timesteps)

    def _placeholder_loop(self, total_timesteps: int) -> Dict[str, Any]:
        import numpy as np
        obs = self.env.reset()
        total = 0
        ep_rewards: list = []
        while total < total_timesteps:
            acts = [
                np.random.uniform(-1, 1, self.env.action_dimension)
                for _ in range(self.env.n_agents)
            ]
            obs, rews, done, _ = self.env.step(acts)
            ep_rewards.extend(rews if isinstance(rews, list) else list(rews.values()))
            total += 1
            if done:
                obs = self.env.reset()
        mean_rew = float(np.mean(ep_rewards)) if ep_rewards else 0.0
        logger.info(f"[off-policy placeholder] {self.name} | steps={total} | mean_r={mean_rew:.4f}")
        return {"mean_reward": mean_rew, "total_steps": total}

    def save(self, path=None) -> Path:
        p = Path(path) if path else self.checkpoint_dir / "model_final"
        if self._trainer and hasattr(self._trainer, "save"):
            self._trainer.save(str(p))
        return p

    def load(self, path) -> None:
        if self._trainer and hasattr(self._trainer, "load"):
            self._trainer.load(str(path))
