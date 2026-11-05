"""Provenance of the raw sources a fresh dataset is built from.

Each source declares what it is. A measurement is a measurement only if its
type says so and nothing in the project generated it; project-generated bills,
modeled assumptions and reanalysis are kept with their real status. Training
artifacts and anything under prior-run roots are never a source.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Mapping, Optional, Sequence, Tuple

# source_type -> (measured, approved_role)
SOURCE_TYPES: Mapping[str, Tuple[bool, str]] = {
    'measured_billing': (True, 'measured_input'),
    'measured_report_table': (True, 'measured_input'),  # compiled consumption table in a study report
    'official_statistic': (True, 'official_statistic'),
    'official_tariff_sheet': (False, 'cited_official_tariff'),  # regulator's published tariff (Osinergmin)
    'building_inventory': (False, 'declared_inventory'),
    'weather_reanalysis': (False, 'observational_reanalysis_input'),
    'modeled_assumption': (False, 'modeled_assumption'),
    'project_generated_billing': (False, 'excluded_modeled_input'),
}
FORBIDDEN_PREFIXES = ('outputs/', 'data/dataset_audit/', 'data/audits/',
                      'CityLearn/data/datasets/', '.cache/')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _is_link(path: Path) -> bool:
    info = os.lstat(path)
    reparse = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & reparse)


def contained_path(root: Path, relative: str) -> Path:
    """Resolve ``relative`` inside ``root``; refuse drives, UNC, parents and linked ancestors.

    Containment is decided on every component from the root to the target, so a
    regular file under a junction or symlink is refused like the link itself.
    """
    text = str(relative)
    windows = PureWindowsPath(text)
    if not text or windows.drive or windows.root or text.startswith(('/', '\\')) or Path(text).is_absolute():
        raise ValueError(f'{text}: absolute, drive or UNC path is not a project-relative path')
    parts = text.replace('\\', '/').split('/')
    if '..' in parts:
        raise ValueError(f'{text}: parent traversal is not allowed')
    # Refuse Windows aliases on every platform: ADS, device names and trailing dots/spaces.
    for part in (p for p in parts if p not in ('', '.')):
        if ':' in part or '\x00' in part or part.endswith((' ', '.')) or PureWindowsPath(part).is_reserved():
            raise ValueError(f'{text}: ambiguous Windows path component')
    base = Path(os.path.abspath(root))
    for ancestor in (*reversed(base.parents), base):
        if os.path.lexists(ancestor) and _is_link(ancestor):
            raise ValueError(f'{text}: root reached through a link or junction ({ancestor.name})')
    current = base
    for part in (p for p in parts if p not in ('', '.')):
        current = current/part
        if os.path.lexists(current) and _is_link(current):
            raise ValueError(f'{text}: reached through a link or junction ({current.name})')
    resolved = current.resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        raise ValueError(f'{text}: resolves outside the project root') from None
    return resolved


@dataclass(frozen=True)
class RawSource:
    path: str
    sha256: str
    bytes: int
    source_uri: str
    obtained_at: str
    source_type: str
    measured: bool
    available_at: str
    license_or_access_note: str
    approved_role: str
    generated_by: Optional[str] = None
    notes: str = ''

    def as_dict(self):
        return dict(self.__dict__)


@dataclass(frozen=True)
class RawSourceManifest:
    sources: Tuple[RawSource, ...]
    manifest_hash: str

    def as_dict(self):
        return {'schema_version': 1, 'sources': [s.as_dict() for s in self.sources],
                'manifest_hash': self.manifest_hash}

    def by_path(self) -> Mapping[str, RawSource]:
        return {s.path: s for s in self.sources}


def audit_raw_sources(entries: Sequence[Mapping[str, object]], *, root: Path) -> RawSourceManifest:
    """Hash and classify declared sources; refuse anything that is not a source."""
    root = Path(os.path.abspath(root))
    sources = []
    for entry in entries:
        relative = str(entry['path']).replace('\\', '/')
        source_type = str(entry['source_type'])
        if source_type not in SOURCE_TYPES:
            raise ValueError(f'{relative}: source type {source_type} is not a raw source')
        path = contained_path(root, str(entry['path']))
        canonical_parts = tuple(part.casefold() for part in path.relative_to(root.resolve()).parts)
        forbidden_parts = [tuple(p.casefold() for p in prefix.strip('/').split('/'))
                           for prefix in FORBIDDEN_PREFIXES]
        if any(canonical_parts[:len(prefix)] == prefix for prefix in forbidden_parts):
            raise ValueError(f'{relative}: prior-run, prior-dataset or cache paths are not raw sources')
        measured, role = SOURCE_TYPES[source_type]
        generated_by = entry.get('generated_by')
        if measured and generated_by:
            raise ValueError(f'{relative}: generated by {generated_by}, so it cannot be a measurement')
        if not path.is_file():
            raise ValueError(f'{relative}: missing or linked source file')
        sources.append(RawSource(relative, sha256_file(path), path.stat().st_size,
                                 str(entry.get('source_uri', '')), str(entry.get('obtained_at', '')),
                                 source_type, measured, str(entry.get('available_at', '')),
                                 str(entry.get('license_or_access_note', '')), role,
                                 generated_by or None, str(entry.get('notes', ''))))
    sources.sort(key=lambda s: s.path)
    body = json.dumps([s.as_dict() for s in sources], sort_keys=True, separators=(',', ':'))
    return RawSourceManifest(tuple(sources), hashlib.sha256(body.encode('utf-8')).hexdigest())
