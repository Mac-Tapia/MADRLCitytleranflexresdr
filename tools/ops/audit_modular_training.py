"""Report actual native-smoke evidence without implying a trained best model."""
import argparse
import json
from pathlib import Path

from uc3m.application.training.persistence import write_json_atomic
from uc3m.application.training.runner import read_manifest
from uc3m.application.training.layout import iter_evidence_paths, normalize_scenario_dir
from uc3m.adapters.algorithms.evidence import checkpoint_bundle, finite_kpis


def audit(output_root):
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
            'four_algorithm_smoke_verified': algorithms >= {'HAPPO', 'MASAC', 'MATD3', 'MAAC'},
            'scientific_acceptance': False,
            'full_plan_complete': False,
            'pending': ['full_horizon_multiseed_campaign', 'optimizer_rng_replay_resume_parity',
                        'full_report_extraction', 'open_source_provenance_gate',
                        'best_model_selection_and_delivery']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, default=Path('outputs/modular_smoke'))
    parser.add_argument('--output', type=Path, default=Path('data/audits/modular_training_acceptance.json'))
    args = parser.parse_args()
    report = audit(args.runs)
    write_json_atomic(args.output, report)
    print(json.dumps(report))
    return 0 if report['four_algorithm_smoke_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
