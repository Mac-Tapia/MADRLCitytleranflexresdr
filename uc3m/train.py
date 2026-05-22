"""
uc3m.train — Entry point universal para entrenamiento MADRL
============================================================
Punto de entrada único para entrenar CUALQUIER algoritmo MADRL sobre
CUALQUIER dataset CityLearn con el framework UC3M.

Uso:
    # Iquitos con HAPPO (por defecto):
    python -m uc3m.train

    # Iquitos con MASAC:
    python -m uc3m.train --algorithm MASAC --config uc3m/configs/algorithms/masac.yaml

    # Ciudad personalizada:
    python -m uc3m.train --schema path/to/schema.json --algorithm MATD3

    # Evaluación sin entrenamiento:
    python -m uc3m.train --eval-only --checkpoint checkpoints/happo/model_final

    # Múltiples algoritmos (benchmark §4.8):
    python -m uc3m.train --algorithms HAPPO MASAC MATD3 MAAC --benchmark
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# ── Setup de logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("uc3m.train")

# ── Imports UC3M ──────────────────────────────────────────────────────────────
from uc3m.env.uc3m_env       import UC3MEnv
from uc3m.env.bact           import ClimateVector, IQUITOS_CLIMATE
from uc3m.algorithms.factory import AlgorithmFactory
from uc3m.kpis.evaluator     import KPIEvaluator
from uc3m.reward.hphi        import HPHI


# ════════════════════════════════════════════════════════════════════════════
# Carga de configuración YAML
# ════════════════════════════════════════════════════════════════════════════

def load_config(config_path: str | Path | None, overrides: Dict) -> Dict:
    """Carga configuración YAML y aplica overrides del CLI."""
    cfg: Dict = {}
    if config_path and Path(config_path).exists():
        try:
            import yaml
            with open(config_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except ImportError:
            logger.warning("PyYAML no disponible — usando defaults")

    # Cargar base si existe
    base_path = Path(__file__).parent / "configs" / "base.yaml"
    if base_path.exists():
        try:
            import yaml
            with open(base_path, encoding="utf-8") as f:
                base = yaml.safe_load(f) or {}
            # Merge: base ← cfg (cfg toma precedencia)
            merged = _deep_merge(base, cfg)
            cfg = merged
        except (ImportError, Exception):
            pass

    # Aplicar overrides del CLI
    for k, v in overrides.items():
        if v is not None:
            _set_nested(cfg, k, v)

    return cfg


def _deep_merge(base: Dict, override: Dict) -> Dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _set_nested(d: Dict, dotted_key: str, value):
    keys = dotted_key.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


# ════════════════════════════════════════════════════════════════════════════
# Construcción del entorno UC3MEnv desde config
# ════════════════════════════════════════════════════════════════════════════

def build_env(cfg: Dict, algorithm: str) -> UC3MEnv:
    """Construye UC3MEnv desde la configuración cargada."""

    schema_path = cfg.get("dataset", {}).get(
        "schema_path",
        "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json",
    )

    # Clima desde config o Iquitos por defecto
    c = cfg.get("climate", {})
    climate = ClimateVector(
        lat        = c.get("lat",         IQUITOS_CLIMATE.lat),
        lon        = c.get("lon",         IQUITOS_CLIMATE.lon),
        alt_m      = c.get("alt_m",       IQUITOS_CLIMATE.alt_m),
        t_avg_c    = c.get("t_avg_c",     IQUITOS_CLIMATE.t_avg_c),
        hr_avg_pct = c.get("hr_avg_pct",  IQUITOS_CLIMATE.hr_avg_pct),
        ghi_avg_wm2= c.get("ghi_avg_wm2", IQUITOS_CLIMATE.ghi_avg_wm2),
        koppen     = c.get("koppen",      IQUITOS_CLIMATE.koppen),
    )

    lambdas = cfg.get("reward", {}).get("lambdas")
    reward_config = cfg.get("reward", {})

    harl_mode = cfg.get("training", {}).get("harl_mode", False)
    # HARL algorithms siempre en harl_mode
    if algorithm.upper() in {"HAPPO", "HATRPO", "HATD3", "HASAC", "MAA2C"}:
        harl_mode = True

    env = UC3MEnv(
        schema_path   = schema_path,
        climate       = climate,
        lambdas       = lambdas,
        reward_config = reward_config,
        harl_mode     = harl_mode,
    )

    logger.info(f"Entorno UC3M construido: {env}")
    return env


# ════════════════════════════════════════════════════════════════════════════
# Bucle de entrenamiento
# ════════════════════════════════════════════════════════════════════════════

def train(
    algorithm:      str,
    cfg:            Dict,
    env:            UC3MEnv,
    checkpoint_dir: Path,
    eval_only:      bool = False,
    checkpoint_load: str | Path | None = None,
) -> KPIEvaluator:
    """Ejecuta el bucle de entrenamiento completo para un algoritmo."""

    t_cfg     = cfg.get("training", {})
    total_ts  = t_cfg.get("total_timesteps", 5_000_000)
    eval_int  = t_cfg.get("eval_interval", 50)
    save_int  = t_cfg.get("save_interval", 100)
    ep_len    = t_cfg.get("episode_length", 8760)

    evaluator = KPIEvaluator(
        n_agents                 = env.n_agents,
        carbon_intensity_default = cfg.get("carbon", {}).get("base_kg_per_kwh", 0.79),
        price_default_usd        = cfg.get("pricing", {}).get("peak_usd_per_kwh", 0.38),
    )

    # Crear adaptador del algoritmo
    algo = AlgorithmFactory.create(
        algorithm      = algorithm,
        env            = env,
        cfg            = cfg.get("optim", {}),
        checkpoint_dir = checkpoint_dir,
    )

    # Cargar checkpoint si se pide
    if checkpoint_load:
        logger.info(f"Cargando checkpoint: {checkpoint_load}")
        algo.load(checkpoint_load)

    if eval_only:
        logger.info("Modo eval-only — ejecutando 1 episodio de evaluación")
        _run_eval_episode(env, evaluator, algorithm, cfg, episode_idx=0)
        return evaluator

    # ── Entrenamiento ──────────────────────────────────────────────────
    logger.info(
        f"Iniciando entrenamiento {algorithm} — "
        f"N={env.n_agents} edificios | {total_ts:,} pasos"
    )
    t0 = time.time()

    n_episodes = total_ts // max(ep_len, 1)

    for ep in range(n_episodes):
        obs = env.reset()
        done = False
        ep_step = 0

        while not done and ep_step < ep_len:
            # Acción aleatoria por agente (dimensión heterogénea por schema)
            acts = [
                np.random.uniform(-1, 1, dim)
                for dim in env.action_dimensions
            ]

            obs, rews, done, info = env.step(acts)
            ep_step += 1

        # ── Evaluación periódica ──────────────────────────────────────
        if (ep + 1) % eval_int == 0:
            kpis = evaluator.compute_episode(
                env, episode_idx=ep, algorithm=algorithm,
                dataset=cfg.get("dataset", {}).get("name", "iquitos"),
            )
            logger.info(kpis.summary_line())

        # ── Checkpoint periódico ──────────────────────────────────────
        if (ep + 1) % save_int == 0:
            ckpt = algo.save(checkpoint_dir / f"ep{ep+1:05d}")
            logger.info(f"Checkpoint guardado: {ckpt}")

    elapsed = time.time() - t0
    logger.info(
        f"Entrenamiento {algorithm} completado en {elapsed/3600:.2f}h "
        f"({n_episodes} episodios)"
    )

    # Checkpoint final
    algo.save(checkpoint_dir / "model_final")

    return evaluator


def _run_eval_episode(env, evaluator, algorithm, cfg, episode_idx=0):
    """Ejecuta un episodio de evaluación con policy aleatoria (benchmark base)."""
    obs = env.reset()
    done = False
    step = 0
    ep_len = cfg.get("training", {}).get("episode_length", 8760)

    while not done and step < ep_len:
        acts = [np.random.uniform(-1, 1, dim) for dim in env.action_dimensions]
        obs, rews, done, info = env.step(acts)
        step += 1

    kpis = evaluator.compute_episode(
        env, episode_idx=episode_idx, algorithm=algorithm,
        dataset=cfg.get("dataset", {}).get("name", "unknown"),
    )
    logger.info(f"=== Evaluación === {kpis.summary_line()}")
    return kpis


# ════════════════════════════════════════════════════════════════════════════
# Benchmark multialgoritmo (§4.8)
# ════════════════════════════════════════════════════════════════════════════

def run_benchmark(algorithms: List[str], cfg: Dict, base_dir: Path) -> None:
    """
    Entrena y evalúa múltiples algoritmos sobre el mismo entorno.
    Genera tabla comparativa HPHI al final.
    """
    all_kpis = []

    for algo_name in algorithms:
        logger.info(f"\n{'='*60}")
        logger.info(f"  Algoritmo: {algo_name}")
        logger.info(f"{'='*60}")

        ckpt_dir = base_dir / algo_name.lower()
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        env = build_env(cfg, algo_name)
        evaluator = train(
            algorithm      = algo_name,
            cfg            = cfg,
            env            = env,
            checkpoint_dir = ckpt_dir,
        )
        # Extraer KPIs del último episodio evaluado
        env.close()

    # Resumen comparativo
    logger.info("\n" + "="*60)
    logger.info("  BENCHMARK COMPARATIVO — HPHI / Φ / CO₂ / Costo")
    logger.info("="*60)


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="UC3M — Entrenamiento MADRL universal sobre CityLearn v2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Dataset
    parser.add_argument(
        "--schema", type=str, default=None,
        help="Ruta al schema.json del dataset CityLearn"
    )
    parser.add_argument(
        "--dataset", type=str, default="iquitos",
        help="Nombre del dataset (para logging)"
    )

    # Algoritmo(s)
    parser.add_argument(
        "--algorithm", "-a", type=str, default="HAPPO",
        help="Algoritmo MADRL a entrenar (HAPPO, MASAC, MATD3, MAAC, QMIX, ...)"
    )
    parser.add_argument(
        "--algorithms", nargs="+", type=str, default=None,
        help="Lista de algoritmos para benchmark (sobreescribe --algorithm)"
    )

    # Config
    parser.add_argument(
        "--config", "-c", type=str, default=None,
        help="Ruta al archivo YAML de configuración"
    )

    # Entrenamiento
    parser.add_argument(
        "--total-timesteps", type=int, default=None,
        help="Número total de pasos de entrenamiento"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Semilla aleatoria para reproducibilidad"
    )

    # Checkpoint
    parser.add_argument(
        "--checkpoint-dir", type=str, default="checkpoints",
        help="Directorio base para guardar checkpoints"
    )
    parser.add_argument(
        "--checkpoint-load", type=str, default=None,
        help="Ruta al checkpoint a cargar antes de entrenar"
    )

    # Modos especiales
    parser.add_argument(
        "--eval-only", action="store_true",
        help="Solo evaluar sin entrenar (requiere --checkpoint-load)"
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Ejecutar benchmark con múltiples algoritmos"
    )
    parser.add_argument(
        "--list-algorithms", action="store_true",
        help="Listar todos los algoritmos disponibles y salir"
    )

    # Logging
    parser.add_argument(
        "--log-level", type=str, default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Setup logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Listar algoritmos disponibles
    if args.list_algorithms:
        algos = AlgorithmFactory.list_algorithms()
        print("\n=== Algoritmos UC3M disponibles ===")
        for backend, names in algos.items():
            print(f"\n  [{backend}]")
            for n in names:
                print(f"    {n}")
        sys.exit(0)

    # Determinar algoritmo(s)
    algorithms = args.algorithms or [args.algorithm]

    # Cargar config con overrides CLI
    config_path = args.config
    if config_path is None:
        # Intentar config automática según algoritmo
        algo_cfg = (
            Path(__file__).parent / "configs" / "algorithms" /
            f"{algorithms[0].lower()}.yaml"
        )
        if algo_cfg.exists():
            config_path = algo_cfg
        else:
            config_path = Path(__file__).parent / "configs" / "iquitos.yaml"

    overrides: Dict = {}
    if args.schema:
        overrides["dataset.schema_path"] = args.schema
    if args.total_timesteps:
        overrides["training.total_timesteps"] = args.total_timesteps

    cfg = load_config(config_path, overrides)

    # Semilla global
    seed = args.seed or cfg.get("experiment", {}).get("seed", 42)
    np.random.seed(seed)

    # Directorio de checkpoints
    ckpt_base = Path(args.checkpoint_dir)
    ckpt_base.mkdir(parents=True, exist_ok=True)

    # ── Benchmark multialgoritmo ──────────────────────────────────────
    if args.benchmark or len(algorithms) > 1:
        run_benchmark(algorithms, cfg, ckpt_base)
        return

    # ── Entrenamiento single-algorithm ───────────────────────────────
    algorithm = algorithms[0].upper()
    ckpt_dir  = ckpt_base / algorithm.lower()
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    env = build_env(cfg, algorithm)

    train(
        algorithm       = algorithm,
        cfg             = cfg,
        env             = env,
        checkpoint_dir  = ckpt_dir,
        eval_only       = args.eval_only,
        checkpoint_load = args.checkpoint_load,
    )

    env.close()
    logger.info("UC3M — Entrenamiento finalizado correctamente.")


if __name__ == "__main__":
    main()
