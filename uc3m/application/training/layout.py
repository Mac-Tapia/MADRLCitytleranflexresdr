"""Canonical training paths, preserving the historical seed-zero layout."""

from pathlib import Path
from typing import Dict, Optional
import re
import os
import stat


def storage_label(value: str) -> str:
    """A label is metadata, never a truncated scientific fingerprint."""
    if (not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,23}', value)
            or re.search(r'\d{6,}|[0-9a-f]{12,}', value)
            or value in {'con', 'prn', 'aux', 'nul'}
            or re.fullmatch(r'(com|lpt)[1-9]', value)):
        raise ValueError('invalid short storage label')
    return value


def campaign_path(spec, naming_registry: Path) -> Path:
    """Resolve an explicitly declared campaign alias below its configured root."""
    return Path(naming_registry)/storage_label(spec.storage_alias)


def treatment_path(campaign_manifest: Path, phase: str, algorithm: str,
                   scenario: str, seed: int, attempt: int,
                   candidate: Optional[str] = None) -> Path:
    if phase not in {'pilot', 'hpo', 'confirm', 'sensitivity'}:
        raise ValueError('unknown treatment phase')
    algorithm, scenario = algorithm.lower(), scenario.lower()
    if algorithm not in {'happo', 'masac', 'matd3', 'maac'} or scenario not in {'e1', 'e2', 'e3'}:
        raise ValueError('unknown treatment algorithm/scenario')
    if (type(seed) is not int or not 0 <= seed < 100000 or
            type(attempt) is not int or not 1 <= attempt < 10000):
        raise ValueError('seed/attempt needs an explicit short-path policy')
    path = Path(campaign_manifest)/phase/algorithm/scenario
    if phase in {'hpo', 'sensitivity'} and candidate is None:
        raise ValueError('candidate label required')
    if candidate is not None:
        path /= storage_label(candidate)
    return path/f'seed_{seed}'/f'try_{attempt:02d}'


def normalize_algorithm_dir(algorithm: str) -> str:
    return algorithm.strip().upper()


def experiment_path(output_root: Path, spec) -> Path:
    """Short storage path for the existing single-experiment CLI.

    Scientific RunIdentity stays in evidence.json. A fresh campaign passes its
    registered treatment/attempt directory explicitly to ExperimentRunner.
    """
    return treatment_path(output_root, 'pilot', spec.algorithm,
                          spec.scenario.scenario_id, spec.seed, 1)


def iter_evidence_paths(output_root: Path):
    """Discover old and short layouts inside the explicit root, without links."""
    output_root = Path(output_root)
    if not output_root.is_dir():
        return

    def linked(path):
        info = path.lstat()
        return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)

    if linked(output_root):
        raise ValueError('linked result root')
    for folder, dirs, files in os.walk(output_root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '__pycache__'} and not linked(Path(folder)/d))
        path = Path(folder)/'evidence.json'
        if 'evidence.json' in files and not linked(path):
            yield path


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
