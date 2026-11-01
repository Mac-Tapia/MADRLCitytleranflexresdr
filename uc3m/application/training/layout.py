"""Canonical training paths, preserving the historical seed-zero layout."""

from pathlib import Path
from typing import Dict


def normalize_algorithm_dir(algorithm: str) -> str:
    return algorithm.strip().upper()


def normalize_scenario_dir(scenario: str, seed: int = 0) -> str:
    scenario = scenario.strip().upper()
    seed = int(seed)
    return scenario if seed == 0 else f"{scenario}_s{seed}"


def job_run_relative_parts(algorithm: str, scenario: str, seed: int = 0) -> Path:
    return Path(normalize_algorithm_dir(algorithm)) / normalize_scenario_dir(scenario, seed)


def resolve_job_run_dir(base: Path, algorithm: str, scenario: str, seed: int) -> Path:
    path = Path(base) / job_run_relative_parts(algorithm, scenario, seed)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_artifact_layout(output_dir: Path) -> Dict[str, Path]:
    output_dir = Path(output_dir)
    directories = {
        'run': output_dir,
        'data': output_dir / 'data',
        'checkpoints': output_dir / 'checkpoints',
        'figures': output_dir / 'figures',
        'tables': output_dir / 'figures' / 'tables',
    }
    for path in directories.values():
        path.mkdir(parents=True, exist_ok=True)
    return directories
