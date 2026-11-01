"""Registry of accepted evidence for thesis tables and figures."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class EvidenceRef:
    observation_id: str
    artifact_path: str
    description: str
    accepted: bool = False


class EvidenceRegistry:
    def __init__(self):
        self._entries: Dict[str, EvidenceRef] = {}

    def register(self, observation_id: str, artifact_path: str,
                 description: str, accepted: bool = False) -> EvidenceRef:
        ref = EvidenceRef(observation_id, artifact_path, description, accepted)
        self._entries[observation_id] = ref
        return ref

    def get_references(self, *, accepted_only: bool = False) -> List[EvidenceRef]:
        entries = list(self._entries.values())
        if accepted_only:
            entries = [e for e in entries if e.accepted]
        return entries

    def load_from_manifest(self, manifest_path: Path) -> None:
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
        for obs in data['observations']:
            self.register(
                observation_id=obs['id'],
                artifact_path=obs.get('evidence_path', ''),
                description=obs['description'],
                accepted=obs['status'] == 'resolved',
            )

    def summary(self) -> dict:
        total = len(self._entries)
        accepted = sum(1 for e in self._entries.values() if e.accepted)
        return {'total': total, 'accepted': accepted, 'pending': total - accepted}
