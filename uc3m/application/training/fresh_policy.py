"""Read policy of the fresh campaign: declared roots by role, nothing implicit.

Every input of a fresh campaign is checked here before it is opened. Retired
historical roots, prior-run roots, other campaigns, "latest" pointers and any
junction or symlink on the way fail closed. Attempts are created exclusively
and always start at episode zero.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Optional, Tuple

import yaml

from uc3m.application.training.persistence import write_json_atomic
from uc3m.application.training.layout import storage_label, treatment_path
from uc3m.application.training.lock import run_lock
from uc3m.domain.campaigns import AttemptIdentity, CampaignSpec, TreatmentKey, canonical_hash

LAYOUT_PATH = 'governance/repository_layout.yaml'
ROLES = ('raw', 'dataset', 'split', 'artifact', 'checkpoint', 'config')


class FreshInputError(ValueError):
    code = 'fresh_input_rejected'


class RetiredHistoricalInput(FreshInputError):
    code = 'retired_historical_input'


class ForeignCampaignInput(FreshInputError):
    code = 'foreign_campaign_input'


class UntrustedCheckpoint(FreshInputError):
    code = 'untrusted_checkpoint'


class CampaignRootExists(FileExistsError):
    code = 'campaign_root_exists'


@dataclass(frozen=True)
class CampaignRoots:
    campaign_id: str
    dataset: Path
    artifacts: Path
    spec_hash: str = ''
    storage_alias: str = ''


def load_layout(project_root: Path) -> Mapping[str, object]:
    path = Path(project_root)/LAYOUT_PATH
    payload = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError(f'{LAYOUT_PATH} must be a schema_version 1 mapping')
    return payload


def _roots_for(spec: CampaignSpec, project_root: Path, layout) -> CampaignRoots:
    root = Path(os.path.abspath(project_root))
    fresh = layout['fresh_roots']
    alias = storage_label(spec.storage_alias)
    return CampaignRoots(spec.campaign_id,
                         root/fresh['dataset'].format(storage_alias=alias),
                         root/fresh['artifacts'].format(storage_alias=alias), spec.spec_hash(), alias)


def _check_root_path(path: Path) -> None:
    for parent in (path, *path.parents):
        if _is_link(parent):
            raise ForeignCampaignInput(f'campaign path passes through a link: {parent}')


def _campaign_claim(roots: CampaignRoots, path: Path):
    _check_root_path(path)
    payload = json.loads((path/'campaign.json').read_text(encoding='utf-8'))
    if (payload.get('campaign_id') != roots.campaign_id or
            payload.get('spec_hash') != roots.spec_hash or
            payload.get('storage_alias') != roots.storage_alias):
        raise ForeignCampaignInput('campaign alias belongs to a different identity')
    return payload


def create_campaign_roots(spec: CampaignSpec, project_root: Path) -> CampaignRoots:
    """Claim both roots of a new campaign; an existing one means a new ID is needed."""
    roots = _roots_for(spec, project_root, load_layout(project_root))
    existing = [str(path) for path in (roots.dataset, roots.artifacts) if os.path.lexists(path)]
    if existing:
        raise CampaignRootExists(f'campaign roots already exist, choose a new campaign_id: {existing}')
    for path in (roots.dataset, roots.artifacts):
        _check_root_path(path)
    for path in (roots.dataset, roots.artifacts):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.mkdir(exist_ok=False)
        write_json_atomic(path/'campaign.json', {
            'schema_version': 1, 'campaign_id': spec.campaign_id,
            'storage_alias': roots.storage_alias, 'spec_hash': roots.spec_hash,
            'spec': spec.as_dict(), 'status': 'planned',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'scientific_acceptance': False})
    return roots


def open_campaign_roots(spec: CampaignSpec, project_root: Path) -> CampaignRoots:
    roots = _roots_for(spec, project_root, load_layout(project_root))
    for path in (roots.dataset, roots.artifacts):
        if not path.is_dir() or _is_link(path):
            raise ForeignCampaignInput(f'campaign root missing or linked: {path}')
        _campaign_claim(roots, path)
    return roots


def _is_link(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    reparse = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & reparse)


def _under(relative: str, prefix: str) -> bool:
    prefix = prefix.strip('/')
    return relative == prefix or relative.startswith(prefix + '/')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def assert_campaign_input(path: Path, role: str, manifest: CampaignSpec, *, project_root: Path,
                          expected_sha256: Optional[str] = None) -> Path:
    """Return the resolved input path, or fail before the file is ever opened."""
    if role not in ROLES:
        raise ForeignCampaignInput(f'unknown input role: {role}')
    root = Path(os.path.abspath(project_root))
    candidate = Path(os.path.abspath(path))
    try:
        relative = candidate.relative_to(root).as_posix()
    except ValueError as exc:
        raise ForeignCampaignInput(f'input outside the project root: {candidate}') from exc
    layout = load_layout(root)
    for target_id, retired in layout.get('retired_historical_roots', {}).items():
        if _under(relative, retired):
            raise RetiredHistoricalInput(f'{relative} belongs to retired historical root {target_id}')
    for forbidden in layout.get('forbidden_input_roots', ()):
        if _under(relative, forbidden):
            raise ForeignCampaignInput(f'{relative} is a prior-run or prior-dataset root')
    if candidate.name in layout.get('forbidden_pointer_names', ()) or 'latest' in candidate.name.casefold():
        raise ForeignCampaignInput(f'{relative} is a pointer, not a declared input')
    current = root
    for part in Path(relative).parts:
        current = current/part
        if _is_link(current):
            raise ForeignCampaignInput(f'{relative} passes through a link at {current.relative_to(root)}')
    roots = _roots_for(manifest, root, layout)
    for declared in (roots.dataset, roots.artifacts):
        if declared.exists():
            _campaign_claim(roots, declared)
    if role == 'raw':
        allowed = [root/p.format(storage_alias=storage_label(manifest.storage_alias))
                   for p in layout['approved_raw_roots']]
    elif role in {'dataset', 'split'}:
        allowed = [roots.dataset]
    elif role in {'artifact', 'checkpoint'}:
        allowed = [roots.artifacts]
    else:
        allowed = [root/'configs']
    resolved = candidate.resolve()
    if resolved != candidate or not any(_under(resolved.as_posix(), base.resolve().as_posix())
                                         for base in allowed):
        raise ForeignCampaignInput(f'{relative} is not inside the declared {role} root of '
                                   f'{manifest.campaign_id}')
    if role == 'checkpoint':
        if not expected_sha256:
            raise UntrustedCheckpoint('a checkpoint is only loaded against its recorded hash')
        if not resolved.is_file() or _sha256(resolved) != expected_sha256:
            raise UntrustedCheckpoint(f'{relative} does not match its recorded hash')
    return resolved


def _existing_attempts(base: Path) -> Tuple[str, ...]:
    if not base.is_dir():
        return ()
    for entry in base.iterdir():
        if entry.name.startswith('try_') and (_is_link(entry) or not entry.is_dir()
                                              or not entry.name[4:].isdigit()):
            raise ValueError(f'attempt path occupied by another role: {entry}')
    return tuple(sorted((p.name for p in base.iterdir()
                         if p.is_dir() and p.name.startswith('try_') and p.name[4:].isdigit()),
                        key=lambda name: int(name[4:])))


def attempt_base(roots: CampaignRoots, key: TreatmentKey) -> Path:
    if key.campaign_id != roots.campaign_id:
        raise ForeignCampaignInput('treatment belongs to another campaign')
    claim = _campaign_claim(roots, roots.artifacts)
    if claim.get('frozen_at') or claim.get('status') in {
            'training_complete', 'evaluation_complete', 'scientific_acceptance'}:
        raise ValueError('frozen campaign cannot acquire or rename treatments')
    with run_lock(roots.artifacts/'.names.lock'):
        registry_path = roots.artifacts/'treatments.json'
        registry = json.loads(registry_path.read_text(encoding='utf-8')) if registry_path.exists() else {'treatments': []}
        seen_paths = set()
        for row in registry['treatments']:
            recorded = TreatmentKey(**row['treatment'])
            expected = treatment_path(roots.artifacts, recorded.stage, recorded.algorithm,
                                      recorded.scenario, recorded.seed, 1, row['candidate']).parent
            relative = expected.relative_to(roots.artifacts).as_posix()
            if (row['path'] != relative or row['path'] in seen_paths or
                    recorded.campaign_id != roots.campaign_id or
                    row['fingerprint'] != recorded.fingerprint() or
                    row['treatment_id'] != recorded.treatment_id):
                raise ValueError('invalid treatment registry path or identity')
            seen_paths.add(relative)
            _check_root_path(expected)
        fingerprint = key.fingerprint()
        for row in registry['treatments']:
            if row['fingerprint'] == fingerprint:
                base = roots.artifacts/row['path']
                _check_root_path(base)
                return base
        candidate = None
        group = [row for row in registry['treatments'] if row['treatment']['stage'] == key.stage
                 and row['treatment']['algorithm'] == key.algorithm and row['treatment']['scenario'] == key.scenario]
        if key.stage in {'hpo', 'sensitivity'}:
            identity = key.as_dict()
            identity.pop('seed')
            candidate_hash = canonical_hash(identity)
            same = [row for row in group if row.get('candidate_hash') == candidate_hash]
            prefix = 'config' if key.stage == 'hpo' else 'weight'
            candidate = same[0]['candidate'] if same else f'{prefix}_{len({r["candidate"] for r in group})+1:02d}'
        else:
            candidate_hash = None
            if any(row['treatment']['seed'] == key.seed for row in group):
                raise ValueError('treatment storage conflict: scientific identity changed')
        base = treatment_path(roots.artifacts, key.stage, key.algorithm, key.scenario,
                              key.seed, 1, candidate).parent
        _check_root_path(base)
        registry['treatments'].append({'fingerprint': fingerprint, 'treatment_id': key.treatment_id,
                                      'treatment': key.as_dict(), 'candidate': candidate,
                                      'candidate_hash': candidate_hash,
                                      'path': base.relative_to(roots.artifacts).as_posix()})
        write_json_atomic(registry_path, registry)
        return base


def create_attempt(campaign: CampaignRoots, key: TreatmentKey) -> Tuple[AttemptIdentity, Path]:
    """A new, empty attempt; earlier attempts stay untouched and are never resumed."""
    base = attempt_base(campaign, key)
    base.mkdir(parents=True, exist_ok=True)
    if _is_link(base):
        raise ForeignCampaignInput(f'attempt root is a link: {base}')
    while True:
        existing = _existing_attempts(base)
        number = (int(existing[-1][4:]) + 1) if existing else 1
        if number >= 1000:
            raise ValueError('attempt identity capacity exhausted')
        attempt_id = f'a{number:03d}'
        attempt_root = base/f'try_{number:02d}'
        try:
            attempt_root.mkdir(exist_ok=False)
        except FileExistsError:
            if _is_link(attempt_root) or not attempt_root.is_dir():
                raise ValueError(f'attempt path occupied by another role: {attempt_root}')
            continue  # a concurrent creator claimed this number first
        break
    identity = AttemptIdentity(key.treatment_id, attempt_id, key.seed)
    write_json_atomic(attempt_root/'attempt.json', {
        **identity.as_dict(), 'treatment': key.as_dict(),
        'previous_attempts': list(existing), 'resume': False,
        'created_at': datetime.now(timezone.utc).isoformat()})
    return identity, attempt_root


def read_attempt(attempt_root: Path) -> Mapping[str, object]:
    payload = json.loads((Path(attempt_root)/'attempt.json').read_text(encoding='utf-8'))
    AttemptIdentity(payload['treatment_id'], payload['attempt_id'], payload['seed'],
                    payload['initial_episode'], payload['fresh_start'])
    return payload
