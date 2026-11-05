"""Read back an explicit native micro campaign after its explicit software gate.

Never discovers a newest run, deserializes weights, trains, or promotes a model.
Observed interactions include internal native evaluation where recorded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from uc3m.application.evaluation.results_catalog import discover_attempts  # noqa: E402
from uc3m.application.training.attempt_trust import read_trusted_attempt  # noqa: E402
from uc3m.application.training.integrity import verify_campaign_inputs  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--gate', type=Path, required=True)
    args = parser.parse_args()
    manifest_path, gate_path = args.manifest.resolve(), args.gate.resolve()
    for path in (manifest_path, gate_path):
        path.relative_to(ROOT)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    gate = json.loads(gate_path.read_text(encoding='utf-8-sig'))
    assert gate['software_acceptance'] is True and gate['source_state_stable'] is True
    assert all(manifest['identity'][key] == gate[gate_key] for key, gate_key in (
        ('source_sha256', 'source_sha256'), ('test_source_sha256', 'test_source_sha256'),
        ('source_git_head', 'git_head')))
    integrity = verify_campaign_inputs(manifest_path, ROOT)
    assert integrity.accepted, integrity.reasons
    attempts = discover_attempts(manifest_path)
    assert len(attempts) == 4 and {a.algorithm for a in attempts} == {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
    rows = []
    for attempt in attempts:
        context = read_trusted_attempt(attempt.attempt_root, algorithm=attempt.algorithm)
        resolved, evidence = context.resolved, context.evidence
        assert resolved['episodes'] == 2 and resolved['episode_time_steps'] == 168
        assert attempt.stage == 'pilot' and attempt.scenario == 'E1' and attempt.seed == 901
        updates = evidence['successful_optimizer_updates_by_owner']
        rows.append({'algorithm': attempt.algorithm,
            'attempt_root': attempt.attempt_root.relative_to(ROOT).as_posix(),
            'target_episodes': 2, 'target_steps_per_episode': 168,
            'observed_interactions': evidence['env_steps'],
            'observed_completed_episodes': evidence['completed_episodes'],
            'native_reported_training_steps': evidence.get('native_reported_training_steps'),
            'optimizer_owners': len(updates), 'minimum_successful_updates_per_owner': min(updates.values()),
            'checkpoint_files': evidence['checkpoint_files'],
            'checkpoint_bundle_hash': evidence['checkpoint_bundle_hash'],
            'learning_evidence_sha256': sha(attempt.attempt_root/'learning_evidence.json'),
            'strict_readback_accepted': True})
    report = {'scope': 'four bounded native learners; not annual or scientific acceptance',
        'manifest': manifest_path.relative_to(ROOT).as_posix(), 'manifest_sha256': sha(manifest_path),
        'software_gate': gate_path.relative_to(ROOT).as_posix(), 'gate_sha256': sha(gate_path),
        'input_integrity': integrity.as_dict(), 'attempts': rows,
        'scientific_acceptance': False, 'operational_acceptance': False}
    target = ROOT/'data/maintenance/integracion/c20261101i01/I15/native_micro_summary.json'
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
