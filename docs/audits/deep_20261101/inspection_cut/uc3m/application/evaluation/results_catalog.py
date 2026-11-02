"""Find training results in the modular layout written by the Colab campaign.

Layout: ``<results_root>/<run_id>/{evidence.json, experiment.json}`` and
``<results_root>/<run_id>/<E1|E1_s<seed>>/{data,figures,...}``. Algorithm,
scenario and seed live in experiment.json, not in the path, so evaluation tools
resolve directories here instead of hard-coding a campaign folder.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from uc3m.application.training.layout import normalize_scenario_dir, iter_evidence_paths

RESULTS_ROOT_ENV = "MADRL_RESULTS_ROOT"
DEFAULT_RESULTS_ROOT = Path(__file__).resolve().parents[3] / "outputs" / "campaign"


class AmbiguousCampaign(ValueError):
    """More than one verified run claims the same algorithm, scenario and seed."""


@dataclass(frozen=True)
class CampaignRun:
    run_id: str
    algorithm: str
    scenario: str
    seed: int
    status: str
    completed_episodes: int
    target_episodes: int
    scenario_dir: Path


def resolve_results_root(results_root: Optional[Path] = None) -> Path:
    """Explicit argument, then MADRL_RESULTS_ROOT, then outputs/campaign."""
    if results_root is not None:
        return Path(results_root)
    from_env = os.environ.get(RESULTS_ROOT_ENV)
    return Path(from_env) if from_env else DEFAULT_RESULTS_ROOT


def discover_runs(results_root: Path, *, verified_only: bool = True) -> List[CampaignRun]:
    runs = []
    for evidence_path in sorted(iter_evidence_paths(results_root)):
        run_dir = evidence_path.parent
        experiment_path = run_dir / "experiment.json"
        if not experiment_path.is_file():
            continue
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
        if verified_only and evidence.get("status") != "verified":
            continue
        scenario = str(experiment["scenario_id"]).upper()
        seed = int(experiment["seed"])
        runs.append(
            CampaignRun(
                run_id=str(evidence.get("run_id", run_dir.name)),
                algorithm=str(experiment["algorithm"]).upper(),
                scenario=scenario,
                seed=seed,
                status=str(evidence.get("status")),
                completed_episodes=int(evidence.get("completed_episodes", 0)),
                target_episodes=int(evidence.get("target_episodes", 0)),
                scenario_dir=run_dir / normalize_scenario_dir(scenario, seed),
            )
        )
    return sorted(runs, key=lambda run: (run.algorithm, run.scenario, run.seed, run.run_id))


def campaign_layout(results_root: Path, *, seed: int = 0) -> Dict[Tuple[str, str], Path]:
    """(ALGORITHM, SCENARIO) -> scenario directory of the single verified run for ``seed``."""
    layout: Dict[Tuple[str, str], Path] = {}
    for run in discover_runs(results_root):
        if run.seed != seed:
            continue
        key = (run.algorithm, run.scenario)
        if key in layout:
            raise AmbiguousCampaign(
                f"{run.algorithm} {run.scenario} seed {seed} has more than one verified run; "
                "keep one campaign per results root"
            )
        layout[key] = run.scenario_dir
    return layout
