"""Phase 2 training evidence of the configured fresh campaign, without implying a best model.

The four-algorithm evidence comes from the accepted pilot attempts of the campaign
named in ``configs/experiments/iquitos.yaml`` (the single trust rule of
``results_catalog.discover_attempts``). The retired ``outputs/modular_smoke`` runs
are not read. The pending list is computed from the campaign stages and the
foundation manifests, never written by hand.

Each run writes its own report under ``outputs/quality_reports/``; the tracked
``data/audits/modular_training_acceptance.json`` keeps the historical smoke record
and is not overwritten.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from uc3m.application.training.persistence import write_json_atomic
from uc3m.application.training.runner import read_manifest
from uc3m.application.training.layout import iter_evidence_paths, normalize_scenario_dir
from uc3m.adapters.algorithms.evidence import checkpoint_bundle, finite_kpis

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path('configs/experiments/iquitos.yaml')
ALGORITHMS = frozenset({'HAPPO', 'MASAC', 'MATD3', 'MAAC'})
LATER_STAGES = ('hpo', 'confirm', 'sensitivity')


def audit(output_root):
    """Native-smoke evidence of a runner output root (kept for the runner integration test)."""
    rows = []
    for path in sorted(iter_evidence_paths(output_root)):
        known_run_id = path.parent.name
        try:
            manifest = read_manifest(path)
            known_run_id = manifest.identity.run_id
            spec = json.loads((path.parent/'experiment.json').read_text(encoding='utf-8'))
            algorithm = spec['algorithm']
            native = path.parent/normalize_scenario_dir(spec['scenario_id'], spec['seed'])
            # Smoke uses canonical 17-building dataset, not a universal agent count.
            checkpoints = checkpoint_bundle(native/'checkpoints', algorithm, 17)
            result = json.loads((native/'results.json').read_text(encoding='utf-8'))
            valid = (manifest.status.value == 'verified' and manifest.verify_files(path.parent)
                     and bool(checkpoints)
                     and finite_kpis(result.get('citylearn_v3_report', {}).get('all_values')))
            rows.append({'run_id': manifest.identity.run_id, 'algorithm': algorithm,
                         'status': 'verified_smoke' if valid else 'not_verified',
                         'checkpoint_files': len(checkpoints),
                         'episode_time_steps': spec['episode_time_steps']})
        except (OSError, ValueError, TypeError, KeyError):
            rows.append({'run_id': known_run_id, 'status': 'incomplete_or_invalid'})
    algorithms = {row.get('algorithm') for row in rows if row['status'] == 'verified_smoke'}
    return {'schema_version': 1, 'runs': rows,
            'four_algorithm_smoke_verified': algorithms >= ALGORITHMS}


def campaign_manifest_path(project_root: Path, config_path: Path) -> Path:
    config = yaml.safe_load((project_root/config_path).read_text(encoding='utf-8'))
    return project_root/'outputs/campaigns'/config['storage_alias']/'campaign_manifest.json'


def _foundation_ready(project_root: Path) -> bool:
    from uc3m.governance import validate_foundation_manifests
    return bool(validate_foundation_manifests(project_root).get('ready'))


def audit_campaign(manifest_path: Path, *, project_root: Path = ROOT) -> dict:
    """Pilot coverage, stage coverage and computed pending items of one fresh campaign."""
    from uc3m.application.evaluation.results_catalog import discover_attempts

    manifest_path = Path(manifest_path)
    pending = []
    if not _foundation_ready(project_root):
        pending.append('open_source_provenance_gate')
    if not manifest_path.is_file():
        return {'schema_version': 2, 'campaign_id': None, 'manifest': str(manifest_path),
                'status': 'campaign_not_prepared', 'runs': [], 'stages': {},
                'four_algorithm_smoke_verified': False, 'scientific_acceptance': False,
                'full_plan_complete': False,
                'pending': ['campaign_prepare', 'pilot_four_algorithms', *pending,
                            *(f'stage_{stage}' for stage in LATER_STAGES), 'scientific_acceptance']}
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    attempts = discover_attempts(manifest_path, accepted_only=False)
    planned = {stage: int(info.get('treatments', 0)) for stage, info in (manifest.get('stages') or {}).items()}
    stages = {}
    for stage, count in planned.items():
        accepted = {a.planned_treatment_id for a in attempts if a.stage == stage and a.accepted}
        stages[stage] = {'planned_treatments': count, 'accepted_treatments': len(accepted)}
    runs = [{'stage': a.stage, 'treatment_id': a.planned_treatment_id, 'algorithm': a.algorithm,
             'attempt_id': a.attempt_id, 'status': 'accepted' if a.accepted else 'rejected',
             'reasons': list(a.reasons)}
            for a in attempts if a.stage == 'pilot']
    pilot_algorithms = {row['algorithm'] for row in runs if row['status'] == 'accepted'}
    four = pilot_algorithms >= ALGORITHMS
    if not four:
        pending.insert(0, 'pilot_four_algorithms')
    for stage in LATER_STAGES:
        info = stages.get(stage)
        if info is None or info['accepted_treatments'] < info['planned_treatments']:
            pending.append(f'stage_{stage}')
    # Scientific acceptance is verified only by fresh_acceptance with the clean gate
    # report and the analysis manifest; this audit never asserts it.
    pending.append('scientific_acceptance')
    return {'schema_version': 2, 'campaign_id': manifest.get('campaign_id'),
            'manifest': manifest_path.relative_to(project_root).as_posix()
            if manifest_path.is_relative_to(project_root) else str(manifest_path),
            'status': 'pilot_verified' if four else 'pilot_pending',
            'runs': runs, 'stages': stages,
            'four_algorithm_smoke_verified': four,
            'scientific_acceptance': False, 'full_plan_complete': False,
            'pending': pending}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--manifest', type=Path, default=None,
                        help='campaign manifest; by default the one of --config')
    parser.add_argument('--output', type=Path, default=None,
                        help='report path; by default outputs/quality_reports/modular_training_<UTC>.json')
    args = parser.parse_args(argv)
    manifest = args.manifest or campaign_manifest_path(ROOT, args.config)
    report = audit_campaign(manifest)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = args.output or ROOT/'outputs/quality_reports'/f'modular_training_{stamp}.json'
    write_json_atomic(output, report)
    print(json.dumps(report))
    return 0 if report['four_algorithm_smoke_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
