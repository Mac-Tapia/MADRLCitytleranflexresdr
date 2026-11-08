"""Find training results: the attempts of a fresh campaign and the older run layout.

Fresh campaign (``discover_attempts``, ``audit_stage_evaluations``, ``build_seed_table``):
the campaign manifest is explicit, attempts come from its stage results and the trust
rule, and evaluations live in ``<attempt_root>/evaluation/<split>/``.

Older run layout (``discover_runs``, ``campaign_layout``):
``<results_root>/<run_id>/{evidence.json, experiment.json}`` and
``<results_root>/<run_id>/<E1|E1_s<seed>>/{data,figures,...}``. Algorithm,
scenario and seed live in experiment.json, not in the path. A fresh attempt has
neither file, so this reader does not see it.
"""
from __future__ import annotations

import hashlib
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


@dataclass(frozen=True)
class FreshAttempt:
    """One attempt of an explicit fresh campaign, with the verdict of the single trust rule."""
    campaign_id: str
    stage: str
    treatment_id: str
    algorithm: str
    scenario: str
    seed: int
    attempt_id: str
    attempt_root: Path
    accepted: bool
    reasons: Tuple[str, ...]


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def discover_attempts(manifest_path: Path, *, accepted_only: bool = True) -> List[FreshAttempt]:
    """Attempts recorded in the stage results of the campaign at ``manifest_path``.

    The campaign is always explicit: no folder is searched for the newest run. A
    treatment counts as accepted only through
    ``fresh_acceptance.treatment_trust_reasons``; the attempt listed is its
    complete attempt, or its last one when none completed.
    """
    from uc3m.application.dataset.provenance import contained_path
    from uc3m.application.training.attempt_trust import load_trust_contract, select_trusted_attempt

    if manifest_path is None:
        raise TypeError("discover_attempts needs the campaign manifest path")
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"no campaign manifest at {manifest_path}")
    manifest = _read_json(manifest_path)
    artifacts = manifest_path.parent
    campaign_id = manifest["campaign_id"]
    contract = load_trust_contract(artifacts, campaign_id)
    found: List[FreshAttempt] = []
    for stage in sorted(manifest.get("stages") or {}):
        result_path = contained_path(artifacts, f"stages/{stage}_result.json")
        if not result_path.is_file():
            continue
        result = _read_json(result_path)
        if result.get("campaign_id") != campaign_id or result.get("stage") != stage:
            raise ValueError(f"{result_path}: stage result of another campaign or stage")
        for treatment in result.get("treatments") or []:
            attempts = treatment.get("attempts") or []
            if not attempts:
                continue
            trusted, found_reasons = select_trusted_attempt(artifacts, campaign_id, treatment, contract=contract)
            chosen = trusted or attempts[-1]
            reasons = tuple(found_reasons)
            try:
                root = contained_path(artifacts, str(chosen["path"]))
                record = _read_json(root / "attempt.json")
                key = record["treatment"]
            except (ValueError, OSError, KeyError) as exc:
                reasons += (f"unreadable_attempt:{exc}",)
                root, record, key = artifacts / str(chosen.get("path", "")), {}, {}
            if key and (key.get("campaign_id") != campaign_id or key.get("stage") != stage):
                reasons += ("attempt_of_another_campaign_or_stage",)
            accepted = not reasons
            if accepted_only and not accepted:
                continue
            found.append(FreshAttempt(
                campaign_id, stage, str(record.get("treatment_id", treatment.get("treatment_id"))),
                str(key.get("algorithm", "")), str(key.get("scenario", "")), int(key.get("seed", -1)),
                str(record.get("attempt_id", chosen.get("attempt_id", ""))), root, accepted, reasons))
    return found


def read_evaluation_report(attempt: FreshAttempt, split: str, *, require_full_split=False):
    """Read one candidate's physical evidence; candidate IDs are not seed replicas."""
    from uc3m.application.dataset.provenance import contained_path
    if split not in ('train_2023', 'validation_2024', 'test_2025'):
        raise ValueError('unknown evaluation split')
    folder = contained_path(attempt.attempt_root, f"evaluation/{split}")
    report_path = contained_path(folder, 'kpi_report.json')
    if not report_path.is_file():
        return None
    evaluation = _read_json(contained_path(folder, 'evaluation_manifest.json'))
    recorded = (evaluation.get('files') or {}).get('kpi_report.json')
    digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
    if digest != recorded:
        raise ValueError(f"{report_path}: sha256 differs from evaluation_manifest.json")
    report = _read_json(report_path)
    expected = {"campaign_id": attempt.campaign_id, "treatment_id": attempt.treatment_id,
                "algorithm": attempt.algorithm, "scenario": attempt.scenario,
                "seed": attempt.seed, "split": split}
    context = report.get("context") or {}
    mismatched = sorted(k for k, v in expected.items() if context.get(k) != v)
    if mismatched:
        raise ValueError(f"{report_path}: report context does not match the attempt ({mismatched})")
    if require_full_split or evaluation.get('schema_version') == 2:
        runs_path = contained_path(folder, 'frozen_runs.json')
        if (evaluation.get('schema_version') != 2 or evaluation.get('split') != split
                or not runs_path.is_file()
                or hashlib.sha256(runs_path.read_bytes()).hexdigest() != evaluation['files'].get('frozen_runs.json')):
            raise ValueError('physical evaluation evidence missing or changed; full split unverified')
        runs = _read_json(runs_path)
        expected_rows = {'train_2023': 8760, 'validation_2024': 8784, 'test_2025': 8760}[split]
        if evaluation.get('expected_full_split_rows') != expected_rows:
            raise ValueError('physical split horizon differs from v1 protocol')
        control, baseline = runs['control'], runs['baseline']
        if (control['trace_hash'] != report['trace_hash']
                or baseline['trace_hash'] != report['baseline_trace_hash']
                or control['split'] != split or baseline['split'] != split
                or control['completed_steps'] != baseline['completed_steps']
                or control['training_updates'] != 0 or baseline['training_updates'] != 0):
            raise ValueError('physical frozen run differs from the KPI report')
        if require_full_split and (type(control['completed_steps']) is not int
                                   or control['completed_steps'] != expected_rows):
            raise ValueError('scientific evaluation requires the full physical split horizon')
    return report, digest


EVALUATION_UNVERIFIED = 'evaluation_unverified'


@dataclass(frozen=True)
class AttemptAudit:
    """Whether one attempt of a stage counts in its seed table on a split, and why not."""
    treatment_id: str
    algorithm: str
    scenario: str
    seed: int
    attempt_id: str
    included: bool
    reasons: Tuple[str, ...]

    @property
    def evaluation_unverified(self) -> bool:
        return any(reason.startswith(EVALUATION_UNVERIFIED) for reason in self.reasons)

    def as_dict(self) -> Dict[str, object]:
        return {'treatment_id': self.treatment_id, 'algorithm': self.algorithm, 'scenario': self.scenario,
                'seed': self.seed, 'attempt_id': self.attempt_id, 'included': self.included,
                'reasons': list(self.reasons)}


def _of_candidate(attempt, candidate: Optional[str]) -> bool:
    """Sensitivity variants share scenario and seed: the variant is a segment of the treatment id."""
    return candidate is None or candidate in attempt.treatment_id.split('/')


def audit_stage_evaluations(manifest_path: Path, *, stage: str, split: str, require_full_split: bool = False,
                            candidate: Optional[str] = None) -> List[AttemptAudit]:
    """Every listed attempt of ``stage`` with the verdict on it for ``split``; it never stops at the first.

    An attempt counts only if the trust rule accepts it and its evaluation verifies with
    ``read_evaluation_report``, the same reader ``build_seed_table`` uses.
    """
    audit = []
    for attempt in discover_attempts(manifest_path, accepted_only=False):
        if attempt.stage != stage or not _of_candidate(attempt, candidate):
            continue
        reasons = list(attempt.reasons)
        if attempt.accepted:
            try:
                if read_evaluation_report(attempt, split, require_full_split=require_full_split) is None:
                    reasons.append(f'evaluation_missing:{split}')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                reasons.append(f'{EVALUATION_UNVERIFIED}:{split}:{exc}')
        audit.append(AttemptAudit(attempt.treatment_id, attempt.algorithm, attempt.scenario, attempt.seed,
                                  attempt.attempt_id, not reasons, tuple(reasons)))
    return audit


def build_seed_table(manifest_path: Path, *, stage: str = "confirm", split: str = "validation_2024",
                     require_full_split: bool = False, candidate: Optional[str] = None):
    """Seed rows from the hash-verified KPI reports of the accepted attempts of one stage.

    Layout: ``<attempt_root>/evaluation/<split>/kpi_report.json`` with its sha256 in
    ``evaluation_manifest.json`` (``{"files": {"kpi_report.json": "<sha256>"}}``) in
    the same folder. An attempt without a report is a missing measurement (no row);
    a changed report or a report whose context is not this attempt is refused.
    """
    from uc3m.application.evaluation.fresh_analysis import SeedTable, rows_from_kpi_report
    if stage not in ('pilot', 'hpo', 'confirm', 'sensitivity') or split not in (
            'train_2023', 'validation_2024', 'test_2025'):
        raise ValueError('unknown stage or split')

    rows = []
    for attempt in discover_attempts(manifest_path):
        if attempt.stage != stage or not _of_candidate(attempt, candidate):
            continue
        measurement = read_evaluation_report(attempt, split, require_full_split=require_full_split)
        if measurement is not None:
            report, digest = measurement
            rows.extend(rows_from_kpi_report(report, report_sha256=digest))
    return SeedTable.from_rows(rows)


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
