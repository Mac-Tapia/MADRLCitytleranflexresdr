"""Hashed evidence contracts for fail-closed training completion."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Tuple

from uc3m.domain.experiments import RunIdentity, RunStatus


HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_VERIFIED_KINDS = frozenset({"checkpoint", "kpi", "training_summary"})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(path: Path, expected_sha256: str) -> bool:
    path = Path(path)
    if not path.is_file() or not HEX_SHA256.fullmatch(expected_sha256.casefold()):
        return False
    return _sha256(path) == expected_sha256.casefold()


@dataclass(frozen=True)
class ArtifactRef:
    relative_path: str
    sha256: str
    size_bytes: int
    kind: str
    media_type: str
    producer: str

    def __post_init__(self) -> None:
        pure = PurePosixPath(self.relative_path.replace("\\", "/"))
        if pure.is_absolute() or ".." in pure.parts or str(pure) in {"", "."}:
            raise ValueError("artifact path must be relative and stay inside run root")
        if not HEX_SHA256.fullmatch(self.sha256.casefold()):
            raise ValueError("artifact sha256 must contain 64 hexadecimal characters")
        if self.size_bytes < 0:
            raise ValueError("artifact size must be non-negative")
        if not self.kind.strip() or not self.media_type.strip() or not self.producer.strip():
            raise ValueError("artifact kind, media_type, and producer are required")
        object.__setattr__(self, "relative_path", pure.as_posix())
        object.__setattr__(self, "sha256", self.sha256.casefold())

    @classmethod
    def from_file(
        cls,
        run_root: Path,
        path: Path,
        *,
        kind: str,
        media_type: str,
        producer: str,
    ) -> "ArtifactRef":
        root = Path(run_root).resolve()
        resolved = Path(path).resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError("artifact must be inside run root") from exc
        if not resolved.is_file():
            raise ValueError("artifact must be an existing file inside run root")
        return cls(
            relative_path=relative.as_posix(),
            sha256=_sha256(resolved),
            size_bytes=resolved.stat().st_size,
            kind=kind,
            media_type=media_type,
            producer=producer,
        )

    def as_dict(self) -> Dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "kind": self.kind,
            "media_type": self.media_type,
            "producer": self.producer,
        }


@dataclass(frozen=True)
class EvidenceManifest:
    identity: RunIdentity
    status: RunStatus
    completed_episodes: int
    target_episodes: int
    artifacts: Tuple[ArtifactRef, ...]

    def __post_init__(self) -> None:
        if self.completed_episodes < 0 or self.target_episodes <= 0:
            raise ValueError("episode counts must be non-negative with positive target")
        if self.completed_episodes > self.target_episodes:
            raise ValueError("completed episodes cannot exceed target")
        paths = [artifact.relative_path for artifact in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("artifact paths must be unique")
        if self.status is RunStatus.VERIFIED:
            kinds = {artifact.kind for artifact in self.artifacts}
            missing = REQUIRED_VERIFIED_KINDS - kinds
            if missing:
                raise ValueError(
                    "verified manifest missing required artifact kinds: "
                    + ", ".join(sorted(missing))
                )
            if self.completed_episodes != self.target_episodes:
                raise ValueError("verified manifest requires all target episodes")

    def verify_files(self, run_root: Path) -> bool:
        root = Path(run_root).resolve()
        for artifact in self.artifacts:
            path = (root / artifact.relative_path).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                return False
            if not path.is_file() or path.stat().st_size != artifact.size_bytes:
                return False
            if not verify_artifact(path, artifact.sha256):
                return False
        return bool(self.artifacts)

    def as_dict(self) -> Dict[str, object]:
        return {
            "run_id": self.identity.run_id,
            "experiment_fingerprint": self.identity.experiment_fingerprint,
            "status": self.status.value,
            "completed_episodes": self.completed_episodes,
            "target_episodes": self.target_episodes,
            "artifacts": [artifact.as_dict() for artifact in self.artifacts],
        }
