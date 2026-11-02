"""Synthetic local trust-boundary probes; no external models or services."""
import json
from pathlib import Path
import tempfile

from uc3m.application.dataset.provenance import audit_raw_sources
from uc3m.application.thesis.evidence_registry import EvidenceRegistry
from uc3m.application.training.fresh_campaign import attempt_completion
from uc3m.application.evaluation.results_catalog import discover_runs


def main():
    results = {}
    with tempfile.TemporaryDirectory(prefix='madrl_boundary_audit_') as temporary:
        base = Path(temporary)
        root = base/'declared_project'
        root.mkdir()
        own_file = base/'synthetic_outside_declared_root.csv'
        own_file.write_text('synthetic\n1\n', encoding='utf-8')
        try:
            manifest = audit_raw_sources([{'path': str(own_file), 'source_type': 'measured_billing'}], root=root)
            results['absolute_raw_source'] = {'accepted': True, 'source_is_inside_declared_root': False,
                'source_count': len(manifest.sources), 'platform': 'Windows',
                'note': 'Both files belong to this temporary probe; no actual outside source was accessed.'}
        except ValueError as exc:
            results['absolute_raw_source'] = {'accepted': False, 'error': type(exc).__name__}

        registry = EvidenceRegistry()
        registry.register('AUDIT_ONLY', str(root/'does_not_exist.json'), 'Synthetic missing evidence', accepted=True)
        results['evidence_registry'] = {'summary': registry.summary(), 'artifact_exists': False}

        results['attempt_metadata'] = attempt_completion({
            'campaign_id': 'OTHER_SYNTHETIC_CAMPAIGN', 'attempt_id': 'other',
            'verified': True, 'exit_code': 0, 'salvage': None, 'env_steps': 50*8760,
            'successful_optimizer_updates_by_owner': {'actor': 0},
            'checkpoint_files': ['synthetic_missing_checkpoint.pt']}, target_episodes=50, episode_time_steps=8760)

        attempt = root/'outputs/campaigns/alias/pilot/HAPPO/E1/seed_901/try_01'
        attempt.mkdir(parents=True)
        (attempt/'learning_evidence.json').write_text(json.dumps({'campaign_id': 'AUDIT_ONLY', 'verified': True}), encoding='utf-8')
        (attempt/'completion.json').write_text(json.dumps({'training_complete': True}), encoding='utf-8')
        results['fresh_catalog'] = {'fresh_attempt_files': ['learning_evidence.json', 'completion.json'],
                                    'discovered_runs': len(discover_runs(root/'outputs/campaigns')),
                                    'note': 'New native runs are not in the legacy evidence.json/experiment.json contract.'}

    (Path(__file__).parent/'security_probes.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
