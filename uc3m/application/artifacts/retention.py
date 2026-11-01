"""Artifact retention classes parsed from governance/artifact_retention_policy.yaml.

The caller parses the YAML; this module validates the resulting mapping so the
application layer stays stdlib-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Any, Mapping, Tuple

from uc3m.domain.evidence import ArtifactRef


class BackupVerificationError(ValueError):
    """Raised whenever a backup or restore cannot be proven byte-identical."""


def _strings(value: Any, label: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return tuple(value)


def _flag(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return value


@dataclass(frozen=True)
class ArtifactClass:
    name: str
    kinds: Tuple[str, ...]
    path_globs: Tuple[str, ...]
    git_versioned: bool
    gitignore_rules: Tuple[str, ...]
    backup: bool
    discard_after_promotion: bool
    retention: Mapping[str, str]

    def matches_path(self, relative_path: str) -> bool:
        return any(fnmatchcase(relative_path, pattern) for pattern in self.path_globs)


@dataclass(frozen=True)
class RetentionPolicy:
    schema_version: str
    run_manifests: Tuple[str, ...]
    classes: Tuple[ArtifactClass, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RetentionPolicy":
        if not isinstance(payload, Mapping) or payload.get("schema_version") != "1.0":
            raise ValueError("retention policy requires schema_version '1.0'")
        raw_classes = payload.get("classes")
        if not isinstance(raw_classes, Mapping) or not raw_classes:
            raise ValueError("retention policy requires a non-empty 'classes' mapping")
        classes = []
        for name, raw in raw_classes.items():
            if not isinstance(raw, Mapping):
                raise ValueError(f"class {name} must be a mapping")
            retention = raw.get("retention")
            if not isinstance(retention, Mapping) or not {"active", "promoted"} <= set(retention):
                raise ValueError(f"class {name} retention requires active and promoted")
            item = ArtifactClass(
                name=str(name),
                kinds=_strings(raw.get("kinds"), f"{name}.kinds"),
                path_globs=_strings(raw.get("path_globs"), f"{name}.path_globs"),
                git_versioned=_flag(raw.get("git_versioned"), f"{name}.git_versioned"),
                gitignore_rules=_strings(raw.get("gitignore_rules"), f"{name}.gitignore_rules"),
                backup=_flag(raw.get("backup"), f"{name}.backup"),
                discard_after_promotion=_flag(raw.get("discard_after_promotion"),
                                              f"{name}.discard_after_promotion"),
                retention={str(k): str(v) for k, v in retention.items()},
            )
            # Evidence-bearing artifacts may only leave the working copy when a
            # verified backup still holds them; otherwise their hash is lost.
            if item.kinds and item.discard_after_promotion and not item.backup:
                raise ValueError(f"class {name}: discard_after_promotion requires backup")
            classes.append(item)
        fallbacks: dict = {}
        for item in classes:
            if not item.path_globs:
                for kind in item.kinds:
                    if kind in fallbacks:
                        raise ValueError(f"kind {kind} has two classes without path_globs")
                    fallbacks[kind] = item.name
        return cls(
            schema_version="1.0",
            run_manifests=_strings(payload.get("run_manifests"), "run_manifests"),
            classes=tuple(classes),
        )

    def classify(self, artifact: ArtifactRef) -> ArtifactClass:
        candidates = [item for item in self.classes if artifact.kind in item.kinds]
        by_path = [item for item in candidates if item.matches_path(artifact.relative_path)]
        if len(by_path) > 1:
            raise BackupVerificationError(
                f"ambiguous retention class for {artifact.relative_path}: "
                + ", ".join(item.name for item in by_path))
        if by_path:
            return by_path[0]
        fallback = [item for item in candidates if not item.path_globs]
        if not fallback:
            raise BackupVerificationError(
                f"no retention class for kind {artifact.kind!r} ({artifact.relative_path})")
        return fallback[0]
