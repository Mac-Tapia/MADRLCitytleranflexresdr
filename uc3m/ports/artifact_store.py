"""Port for auditable artifact persistence."""

from __future__ import annotations

from typing import Mapping, Protocol, runtime_checkable

from uc3m.domain.evidence import ArtifactRef


@runtime_checkable
class ArtifactStore(Protocol):
    def write_bytes(
        self,
        relative_path: str,
        payload: bytes,
        *,
        kind: str = "artifact",
        media_type: str = "application/octet-stream",
    ) -> ArtifactRef: ...

    def write_json(
        self,
        relative_path: str,
        payload: Mapping[str, object],
        *,
        kind: str = "manifest",
    ) -> ArtifactRef: ...

    def verify(self, artifact: ArtifactRef) -> bool: ...
