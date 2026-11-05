"""Post-training pipeline of a fresh campaign: status, freeze, evaluate, analyze, deliver.

    python -m uc3m.application.pipeline status   --manifest outputs/campaigns/<alias>/campaign_manifest.json
    python -m uc3m.application.pipeline freeze   --manifest ... --config configs/experiments/iquitos.yaml
    python -m uc3m.application.pipeline evaluate --manifest ... --stage confirm --split validation_2024 --workers 4
    python -m uc3m.application.pipeline analyze  --manifest ... --stage confirm --split validation_2024
    python -m uc3m.application.pipeline deliver  --manifest ... --destination outputs/deliveries/<name>

Composition only: acceptance is ``fresh_acceptance.treatment_trust_reasons`` (through
the results catalog), evaluation is ``frozen_evaluation.evaluate_frozen``, selection is
``fresh_tuning.select_hyperparameters``, statistics are ``fresh_analysis.analyze_campaign``
and the delivery is ``report_fresh_campaign.build_fresh_delivery``. Nothing here trains:
the only training path is ``uc3m.application.training.cli``. No result is overwritten.
Frozen evaluations of different attempts are independent (each writes inside its own
attempt), so they run in parallel worker processes. The last stdout line is JSON; exit
code 0 means done, 2 means refused with a reason.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
import uuid
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SPLIT = 'validation_2024'


def _validate_stage_split(stage, split):
    if stage not in ('pilot', 'hpo', 'confirm', 'sensitivity') or split not in (
            'train_2023', 'validation_2024', 'test_2025'):
        raise ValueError('unknown stage or split')


def _read(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _campaign_root(manifest_path: Path, project_root: Path) -> Path:
    """The frozen dataset folder (split manifest, splits, normalizer) the campaign recorded."""
    from uc3m.application.dataset.provenance import contained_path
    record = _read(manifest_path)['inputs']['split_manifest']
    return contained_path(project_root, record['path']).parent


def stage_status(manifest_path: Path) -> List[Dict[str, object]]:
    """Every listed attempt of the campaign with the verdict of the single trust rule."""
    from uc3m.application.evaluation.results_catalog import discover_attempts
    return [{'stage': a.stage, 'treatment_id': a.treatment_id, 'algorithm': a.algorithm, 'scenario': a.scenario,
             'seed': a.seed, 'attempt_id': a.attempt_id, 'attempt_root': str(a.attempt_root),
             'accepted': a.accepted, 'reasons': list(a.reasons)}
            for a in discover_attempts(manifest_path, accepted_only=False)]


def default_evaluate(attempt_root, split_id, campaign_root, **kwargs):
    """Module-level (picklable) wrapper: each worker process imports the evaluator and builds
    its own CityLearn adapters (this module is a composition root, like training/cli.py)."""
    from uc3m.adapters.citylearn.frozen_adapters import citylearn_frozen_adapters
    from uc3m.application.evaluation.frozen_evaluation import evaluate_frozen
    return evaluate_frozen(attempt_root, split_id, campaign_root, adapters=citylearn_frozen_adapters(), **kwargs)


def _evaluate_one(evaluate: Callable, attempt_root: str, split: str, campaign_root: str) -> Optional[str]:
    try:
        evaluate(Path(attempt_root), split, Path(campaign_root))
    except Exception as exc:  # noqa: BLE001 - every refusal is reported, never hidden
        return f'{type(exc).__name__}: {exc}'
    return None


def evaluate_stage(manifest_path: Path, *, project_root: Path = PROJECT_ROOT, stage: str = 'confirm',
                   split: str = VALIDATION_SPLIT, evaluate: Callable = default_evaluate,
                   workers: int = 1) -> Dict[str, object]:
    """Frozen evaluation of every accepted attempt of ``stage`` on ``split``; existing ones are kept."""
    from uc3m.application.evaluation.results_catalog import discover_attempts, read_evaluation_report
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError('workers must be a positive integer')
    _validate_stage_split(stage, split)
    campaign_root = _campaign_root(Path(manifest_path), Path(project_root))
    pending, existing = [], []
    for attempt in discover_attempts(manifest_path):
        if attempt.stage != stage:
            continue
        if read_evaluation_report(attempt, split, require_full_split=(stage == 'hpo' or split == 'test_2025')) is not None:
            existing.append(attempt.treatment_id)
        else:
            pending.append(attempt)
    jobs = [(evaluate, str(a.attempt_root), split, str(campaign_root)) for a in pending]
    if workers == 1 or len(jobs) <= 1:
        errors = [_evaluate_one(*job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
            errors = list(pool.map(_evaluate_one, *zip(*jobs)))
    evaluated = [a.treatment_id for a, error in zip(pending, errors) if error is None]
    failed = [{'attempt': str(a.attempt_root), 'treatment_id': a.treatment_id, 'reason': error}
              for a, error in zip(pending, errors) if error is not None]
    return {'stage': stage, 'split': split, 'evaluated': evaluated, 'existing': existing, 'failed': failed}


def _validation_rows(manifest_path: Path, campaign_id: str) -> Dict[str, List[dict]]:
    """One validation row per listed HPO treatment; unaccepted or unevaluated ones stay infeasible."""
    from uc3m.application.evaluation.results_catalog import discover_attempts, read_evaluation_report
    from uc3m.application.training.fresh_tuning import VALIDATION_SPLIT as SELECTION_SPLIT, validation_row
    rows: Dict[str, List[dict]] = {}
    for attempt in discover_attempts(manifest_path, accepted_only=False):
        if attempt.stage != 'hpo':
            continue
        treatment = _read(attempt.attempt_root/'resolved_treatment.json')
        completion = _read(attempt.attempt_root/'completion.json') if attempt.accepted else {}
        folder = attempt.attempt_root/'evaluation'/SELECTION_SPLIT
        report, digest = {}, ''
        measurement = read_evaluation_report(attempt, SELECTION_SPLIT, require_full_split=True) if attempt.accepted else None
        if measurement is not None:
            report, _ = measurement
            digest = hashlib.sha256((folder/'evaluation_manifest.json').read_bytes()).hexdigest()
        rows.setdefault(attempt.algorithm, []).append(validation_row(
            treatment, completion, report, evaluation_manifest_sha256=digest, split=SELECTION_SPLIT,
            campaign_id=campaign_id))
    return rows


def freeze_hpo(manifest_path: Path, config_path: Path, project_root: Path = PROJECT_ROOT) -> Dict[str, object]:
    """Select and freeze one configuration per algorithm on validation; any blocked algorithm blocks all."""
    from uc3m.application.training.fresh_campaign import build_dag, load_campaign_config, write_configuration_freezes
    from uc3m.application.training.fresh_tuning import SelectionBlocked, protocol_from_dag, select_hyperparameters
    manifest_path = Path(manifest_path)
    campaign_id = _read(manifest_path)['campaign_id']
    config = load_campaign_config(Path(config_path), Path(project_root))
    if config['campaign_id'] != campaign_id:
        raise PermissionError(f"config {config['campaign_id']} is not the campaign {campaign_id}")
    protocol = protocol_from_dag(build_dag(config, Path(project_root)), campaign_id)
    rows = _validation_rows(manifest_path, campaign_id)
    freezes, blocked = [], {}
    for algorithm in sorted(protocol.expected):
        try:
            freezes.append(select_hyperparameters(rows.get(algorithm, []), protocol))
        except (SelectionBlocked, ValueError) as refused:
            blocked[algorithm] = str(refused)
    if blocked:
        return {'status': 'refused', 'reason': 'hpo_selection_blocked', 'blocked': blocked}
    written = write_configuration_freezes(manifest_path, freezes)
    from uc3m.application.evaluation.test_access import write_test_unlock
    write_test_unlock(manifest_path)
    return {'status': 'ok', 'frozen': {f.algorithm: f.freeze_hash() for f in freezes}, 'manifest': written}


def analyze_stage(manifest_path: Path, *, stage: str = 'confirm', split: str = VALIDATION_SPLIT,
                  protocol=None) -> Path:
    """Seed table and scientific report of ``stage`` on ``split``, hashed in analysis_manifest.json."""
    from uc3m.application.training.lock import run_lock
    from uc3m.application.dataset.provenance import contained_path
    _validate_stage_split(stage, split)
    with run_lock(contained_path(Path(manifest_path).parent, '.analysis.lock')):
        return _analyze_stage(manifest_path, stage=stage, split=split, protocol=protocol)


def _analyze_stage(manifest_path, *, stage, split, protocol):
    from uc3m.application.evaluation.fresh_analysis import analyze_campaign
    from uc3m.application.evaluation.analysis_acceptance import protocol_for_stage
    from uc3m.application.evaluation.results_catalog import build_seed_table
    from uc3m.application.training.persistence import write_json_atomic
    manifest_path = Path(manifest_path)
    folder = manifest_path.parent/'analysis'/f'{stage}_{split}'
    if folder.exists():
        raise FileExistsError(f'{folder} exists; an analysis is never overwritten')
    table = build_seed_table(manifest_path, stage=stage, split=split,
                             require_full_split=(stage == 'confirm' and split == 'test_2025'))
    protocol = protocol or protocol_for_stage(manifest_path, stage, split)
    report = analyze_campaign(table, protocol)
    staging = folder.with_name(folder.name + '.partial_' + uuid.uuid4().hex)
    staging.mkdir(parents=True)
    manifest = _read(manifest_path)
    complete = report.decisions.get('scientifically_complete') is True
    scientific = complete and stage == 'confirm' and split == 'test_2025'
    payloads = {'seed_table.json': {'campaign_id': manifest['campaign_id'], 'stage': stage, 'split': split,
                                    'rows': [dict(r) for r in table.rows]},
                'scientific_report.json': {**report.as_dict(), 'campaign_id': manifest['campaign_id'],
                                           'status': ('scientifically_complete' if scientific else
                                                      'analysis_complete' if complete else 'incomplete')}}
    digests = {}
    for name, payload in payloads.items():
        path = staging/name
        path.write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')
        digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (staging/'analysis_manifest.json').write_text(json.dumps(
        {'campaign_id': manifest['campaign_id'], 'spec_hash': manifest['spec_hash'],
         'stage': stage, 'split': split, 'protocol': dataclasses.asdict(protocol), 'files': digests},
        indent=2), encoding='utf-8')
    manifest.setdefault('analyses', {})[f'{stage}:{split}'] = {
        'path': (folder/'analysis_manifest.json').relative_to(manifest_path.parent).as_posix(),
        'sha256': hashlib.sha256((staging/'analysis_manifest.json').read_bytes()).hexdigest()}
    # Register before publication: a cut leaves a missing, rejected reference;
    # a fresh staging can be produced without overwriting a published analysis.
    write_json_atomic(manifest_path, manifest)
    staging.rename(folder)
    return folder


def deliver(manifest_path: Path, destination: Path, *, stage: str = 'confirm',
            split: str = VALIDATION_SPLIT, gate_report: Optional[Path] = None,
            analysis_manifest: Optional[Path] = None) -> Dict[str, object]:
    from uc3m.application.evaluation.fresh_delivery import build_fresh_delivery
    _validate_stage_split(stage, split)
    from uc3m.application.evaluation.results_catalog import build_seed_table
    rows = [dict(r) for r in build_seed_table(manifest_path, stage=stage, split=split).rows]
    if analysis_manifest is None:
        record = (_read(manifest_path).get('analyses') or {}).get(f'{stage}:{split}')
        if record:
            from uc3m.application.dataset.provenance import contained_path
            analysis_manifest = contained_path(manifest_path.parent, record['path'])
    return build_fresh_delivery(Path(manifest_path), Path(destination), seed_rows=rows,
                                gate_report=gate_report, analysis_manifest=analysis_manifest)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('command', choices=('status', 'freeze', 'evaluate', 'analyze', 'deliver'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--stage', default='confirm')
    parser.add_argument('--split', default=VALIDATION_SPLIT)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--gate-report', type=Path)
    parser.add_argument('--analysis-manifest', type=Path)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--project-root', type=Path, default=PROJECT_ROOT)
    return parser


def _run(args) -> Dict[str, object]:
    if not args.manifest.is_file():
        raise FileNotFoundError(f'no campaign manifest at {args.manifest}')
    if args.command == 'status':
        return {'status': 'ok', 'treatments': stage_status(args.manifest)}
    if args.command == 'freeze':
        if args.config is None:
            raise ValueError('freeze needs --config')
        return freeze_hpo(args.manifest, args.config, args.project_root)
    if args.command == 'evaluate':
        result = evaluate_stage(args.manifest, project_root=args.project_root, stage=args.stage,
                                split=args.split, workers=args.workers)
        return {'status': 'ok' if not result['failed'] else 'incomplete', **result}
    if args.command == 'analyze':
        folder = analyze_stage(args.manifest, stage=args.stage, split=args.split)
        report = _read(folder/'scientific_report.json')
        return {'status': 'ok', 'analysis': str(folder), 'decisions': report.get('decisions')}
    if args.destination is None:
        raise ValueError('deliver needs --destination')
    delivery = deliver(args.manifest, args.destination, stage=args.stage, split=args.split,
                       gate_report=args.gate_report, analysis_manifest=args.analysis_manifest)
    return {'status': 'refused' if delivery['state'] == 'rejected' else 'ok', 'delivery': delivery}


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = _run(args)
    except (FileNotFoundError, FileExistsError, PermissionError, ValueError, KeyError) as refused:
        report = {'status': 'refused', 'reason': f'{type(refused).__name__}: {refused}'}
    print(json.dumps(report, default=str))
    return 0 if report['status'] == 'ok' else 2


if __name__ == '__main__':
    sys.exit(main())
