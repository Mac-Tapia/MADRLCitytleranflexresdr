"""Contract tests for jury observations manifest J-01 through J-17."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'data' / 'audits' / 'jury_observations_manifest.json'

VALID_TYPES = {'documental', 'analytical', 'experimental'}
VALID_STATUSES = {'pending', 'partial', 'resolved', 'pending_experiment', 'pending_documental'}


def test_all_17_observations_formalized():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    observations = manifest['observations']
    assert len(observations) == 17
    ids = {obs['id'] for obs in observations}
    expected_ids = {f'J-{i:02d}' for i in range(1, 18)}
    assert ids == expected_ids


def test_observation_structure_valid():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    for obs in manifest['observations']:
        assert 'id' in obs
        assert 'description' in obs
        assert obs['type'] in VALID_TYPES, f"{obs['id']} has invalid type: {obs['type']}"
        assert obs['status'] in VALID_STATUSES, f"{obs['id']} has invalid status: {obs['status']}"
        assert 'correction' in obs
        assert 'evidence_path' in obs


def test_experimental_observations_not_marked_resolved_without_campaign():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    experimental = [o for o in manifest['observations'] if o['type'] == 'experimental']
    for obs in experimental:
        if obs['status'] == 'resolved':
            assert obs.get('campaign_evidence'), (
                f"{obs['id']} is experimental and resolved but has no campaign_evidence"
            )


def test_evidence_registry_importable():
    from uc3m.application.thesis.evidence_registry import EvidenceRegistry
    registry = EvidenceRegistry()
    assert callable(getattr(registry, 'register', None))
    assert callable(getattr(registry, 'get_references', None))
