"""Atomic filesystem artifact store with SHA-256 readback verification."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Mapping

from uc3m.domain.evidence import ArtifactRef, verify_artifact


class LocalArtifactStore:
    def __init__(self, root: Path, *, producer: str) -> None:
        if not producer.strip():
            raise ValueError("producer must not be empty")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.producer = producer

    def _target(self, relative_path: str) -> Path:
        pure = PurePosixPath(str(relative_path).replace("\\", "/"))
        if pure.is_absolute() or ".." in pure.parts or str(pure) in {"", "."}:
            raise ValueError("artifact path must be relative to the store root")
        target = (self.root / Path(*pure.parts)).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("artifact path must be relative to the store root") from exc
        return target

    def _replace(self, source: Path, destination: Path) -> None:
        os.replace(source, destination)

    def write_bytes(
        self,
        relative_path: str,
        payload: bytes,
        *,
        kind: str = "artifact",
        media_type: str = "application/octet-stream",
    ) -> ArtifactRef:
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        target = self._target(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self._replace(temporary, target)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

        artifact = ArtifactRef.from_file(
            self.root,
            target,
            kind=kind,
            media_type=media_type,
            producer=self.producer,
        )
        if not self.verify(artifact):
            raise OSError(f"artifact readback verification failed: {relative_path}")
        return artifact

    def write_json(
        self,
        relative_path: str,
        payload: Mapping[str, object],
        *,
        kind: str = "manifest",
    ) -> ArtifactRef:
        serialized = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        return self.write_bytes(
            relative_path,
            serialized,
            kind=kind,
            media_type="application/json",
        )

    def verify(self, artifact: ArtifactRef) -> bool:
        target = self._target(artifact.relative_path)
        return (
            target.is_file()
            and target.stat().st_size == artifact.size_bytes
            and verify_artifact(target, artifact.sha256)
        )
