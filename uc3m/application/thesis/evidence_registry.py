"""Registry of accepted evidence for thesis tables and figures.

Only ``register_verified_evidence`` accepts evidence: it rechecks the content
hash and the owning campaign. Editorial references (plain ``register`` or a jury
manifest, whatever its status) stay unaccepted; an ``accepted=True`` argument
never verifies a file. Accepted references are read back against their hash
whenever they are requested, so a changed or deleted artifact stops counting.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EvidenceRef:
    observation_id: str
    artifact_path: str
    description: str
    accepted: bool = False
    sha256: Optional[str] = None
    campaign_id: Optional[str] = None
    phase: Optional[str] = None

    def still_verified(self) -> bool:
        if not (self.accepted and self.sha256):
            return False
        path = Path(self.artifact_path)
        try:
            return (not path.is_symlink() and path.is_file()
                    and hashlib.sha256(path.read_bytes()).hexdigest() == self.sha256)
        except OSError:
            return False


class EvidenceRegistry:
    def __init__(self):
        self._entries: Dict[str, EvidenceRef] = {}

    def register(self, observation_id: str, artifact_path: str,
                 description: str, accepted: bool = False) -> EvidenceRef:
        """Editorial reference; acceptance only comes from register_verified_evidence."""
        if accepted:
            raise ValueError('accepted=True does not verify a file; use register_verified_evidence')
        ref = EvidenceRef(observation_id, artifact_path, description, False)
        self._entries[observation_id] = ref
        return ref

    def register_verified_evidence(self, path, expected_hash: str, campaign_id: str, phase: str, *,
                                   observation_id: Optional[str] = None) -> EvidenceRef:
        """Accept an artifact of a fresh campaign only after rechecking its content hash."""
        path = Path(path)
        if not campaign_id.startswith('fresh_'):
            raise PermissionError(f'{campaign_id}: only fresh campaigns register new evidence')
        if path.is_symlink() or not path.is_file():
            raise PermissionError(f'{path}: evidence must be a regular file')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise PermissionError(f'{path}: content does not match the expected hash')
        if path.suffix == '.json':
            payload = json.loads(path.read_text(encoding='utf-8'))
            owner = payload.get('campaign_id') if isinstance(payload, dict) else None
            if owner is not None and owner != campaign_id:
                raise PermissionError(f'{path}: evidence belongs to {owner}, not {campaign_id}')
        key = observation_id or f'{campaign_id}:{phase}:{path.name}'
        ref = EvidenceRef(key, str(path), f'{phase} evidence sha256={expected_hash}', True,
                          expected_hash, campaign_id, phase)
        self._entries[key] = ref
        return ref

    def get_references(self, *, accepted_only: bool = False) -> List[EvidenceRef]:
        entries = list(self._entries.values())
        if accepted_only:
            entries = [e for e in entries if e.still_verified()]
        return entries

    def load_from_manifest(self, manifest_path: Path) -> None:
        """Jury observations are editorial references: a 'resolved' status is not verified evidence."""
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        for obs in data['observations']:
            self.register(
                observation_id=obs['id'],
                artifact_path=obs.get('evidence_path', ''),
                description=obs['description'],
            )

    def summary(self) -> dict:
        total = len(self._entries)
        accepted = sum(1 for e in self._entries.values() if e.still_verified())
        return {'total': total, 'accepted': accepted, 'pending': total - accepted}
