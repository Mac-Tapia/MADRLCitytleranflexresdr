"""Incremental, cut-safe persistence of finished attempts on a declared Drive folder.

Only local filesystem behavior is established by unit tests. A real Colab/Drive
mount and disconnect requires separate runtime acceptance. Copies in progress
are journaled; a complete copy is published only after its digest verifies.
Untrusted or interrupted staging folders are retained for diagnosis, never
silently deleted or promoted. Conflicts make the CLI return 2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Dict, List

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.attempt_evidence import _is_link
from uc3m.application.training.lock import run_lock
from uc3m.application.training.persistence import write_json_atomic

MANIFEST = 'drive_sync_manifest.json'
CAMPAIGN_FILES = ('campaign_manifest.json', 'campaign.json', 'treatments.json', 'configuration_freezes.json',
                  'test_unlock.json')


def _walk_files(root: Path, *, exclude_root=()):
    if _is_link(root):
        raise ValueError('linked artifact root')
    def fail(error):
        raise error
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        base = Path(directory)
        kept = []
        for name in sorted(dirs):
            if base == root and name in exclude_root:
                continue
            if any(marker in name for marker in ('.partial_', '.restoring_')):
                continue
            if _is_link(base/name):
                raise ValueError(f'linked artifact directory: {base/name}')
            kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = base/name
            if _is_link(path):
                raise ValueError(f'linked artifact file: {path}')
            yield path


def directory_digest(path: Path, *, training_only=False) -> str:
    """The existing name/NUL/bytes/NUL identity, with bounded checkpoint memory."""
    digest = hashlib.sha256()
    for file in sorted(_walk_files(Path(path), exclude_root=('evaluation',) if training_only else ())):
        digest.update(file.relative_to(path).as_posix().encode('utf-8') + b'\0')
        with file.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                digest.update(block)
        digest.update(b'\0')
    return digest.hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _read(path):
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'expected mapping: {path}')
    return value


def finished_attempts(artifacts: Path) -> List[Path]:
    return sorted(p.parent for p in _walk_files(Path(artifacts))
                  if p.name == 'attempt.json' and (p.parent/'completion.json').is_file())


def _read_manifest(drive: Path) -> Dict[str, object]:
    path = contained_path(drive, MANIFEST)
    state = _read(path) if path.is_file() else {}
    for key in ('attempts', 'files', 'pending_files', 'pending_attempts', 'attempt_scopes', 'post_files'):
        state.setdefault(key, {})
        if not isinstance(state[key], dict):
            raise ValueError(f'invalid Drive manifest {key}')
    return state


def _write_manifest(drive: Path, manifest) -> None:
    write_json_atomic(contained_path(drive, MANIFEST), manifest)


def _is_stage_log(relative: str) -> bool:
    """Stage files rewritten on every launch: a local copy newer than Drive is expected, never a conflict."""
    folder, _, name = relative.rpartition('/')
    return folder == 'stages' and name.endswith(('_gpu_memory.json', '_result.json', 'owner_authorizations.jsonl'))


def _campaign_files(root: Path) -> List[Path]:
    files = [contained_path(root, name) for name in CAMPAIGN_FILES if (root/name).is_file()]
    if (root/'stages').is_dir():
        files += sorted(_walk_files(root/'stages'))
    return files


def _unique_staging(target: Path, role: str) -> Path:
    return target.with_name(target.name + '.' + role + '_' + uuid.uuid4().hex)


def _postprocessing_files(root, manifest):
    for attempt in finished_attempts(root):
        evaluation = contained_path(attempt, 'evaluation')
        if evaluation.is_dir():
            yield from _walk_files(evaluation)
    for record in (manifest.get('analyses') or {}).values():
        entry = contained_path(root, record['path'])
        if not entry.is_file() or _file_digest(entry) != record['sha256']:
            raise ValueError('registered analysis manifest missing or changed')
        yield from _walk_files(entry.parent)


def _copy_training(source, target):
    # A model snapshot is immutable; evaluations are appended separately.
    return shutil.copytree(source, target, ignore=lambda path, names:
        ['evaluation'] if Path(path) == source and 'evaluation' in names else [])


def _snapshot_digest(path, manifest, relative):
    return directory_digest(path, training_only=manifest['attempt_scopes'].get(relative) == 'training_v1')


def sync_finished_attempts(artifacts: Path, drive: Path) -> Dict[str, object]:
    artifacts, drive = Path(artifacts), Path(drive)
    drive.mkdir(parents=True, exist_ok=True)
    with run_lock(contained_path(drive, '.sync.lock')):
        return _sync(artifacts, drive)


def _sync(artifacts, drive):
    manifest = _read_manifest(drive)
    report = {'copied': [], 'already_synced': [], 'conflicts': [], 'files': [], 'recovered': []}
    local_path = contained_path(artifacts, 'campaign_manifest.json')
    local = _read(local_path) if local_path.is_file() else {}
    remote = _read(contained_path(drive, 'campaign_manifest.json')) if (drive/'campaign_manifest.json').is_file() else {}
    if (remote and (remote.get('campaign_id') != local.get('campaign_id')
                   or remote.get('spec_hash') != local.get('spec_hash'))):
        report['conflicts'].append('campaign_manifest.json')
        return report
    if manifest.get('campaign_id') not in (None, local.get('campaign_id')):
        report['conflicts'].append(MANIFEST)
        return report
    manifest['campaign_id'] = local.get('campaign_id')
    # Restore needs the bound plan before it can judge any copied native model.
    for file in _campaign_files(artifacts):
        relative = file.relative_to(artifacts).as_posix()
        target = contained_path(drive, relative)
        digest = _file_digest(file)
        if not target.is_file() or _file_digest(target) != digest:
            target.parent.mkdir(parents=True, exist_ok=True)
            staging = _unique_staging(target, 'partial')
            shutil.copy2(file, staging)
            if _file_digest(staging) != digest:
                report['conflicts'].append(relative)
                continue
            # Write-ahead: a cut after the replace leaves bytes the manifest can still recognize.
            manifest['pending_files'][relative] = digest
            _write_manifest(drive, manifest)
            staging.replace(target)
        manifest['files'][relative] = digest
        manifest['pending_files'].pop(relative, None)
        _write_manifest(drive, manifest)
        report['files'].append(relative)
    for attempt in finished_attempts(artifacts):
        relative = attempt.relative_to(artifacts).as_posix()
        digest = directory_digest(attempt, training_only=True)
        target = contained_path(drive, relative)
        if target.exists():
            recorded = manifest['attempts'].get(relative)
            scope = manifest['attempt_scopes'].get(relative)
            # Migrate a legacy full-directory digest only after re-reading its
            # original remote snapshot, never by trusting the new local copy.
            legacy_ok = scope is None and (recorded is None or directory_digest(target) == recorded)
            if (directory_digest(target, training_only=True) != digest
                    or (scope == 'training_v1' and recorded != digest)
                    or (scope not in (None, 'training_v1')) or (scope is None and not legacy_ok)):
                report['conflicts'].append(relative)
                continue
            if relative not in manifest['attempts']:
                report['recovered'].append(relative)
            report['already_synced'].append(relative)
        else:
            staging = _unique_staging(target, 'partial')
            manifest['pending_attempts'][relative] = {
                'sha256': digest, 'scope': 'training_v1', 'staging': staging.relative_to(drive).as_posix()}
            _write_manifest(drive, manifest)  # write-ahead: survives a cut after the following rename
            _copy_training(attempt, staging)
            if directory_digest(staging, training_only=True) != digest:
                report['conflicts'].append(relative)
                continue
            staging.rename(target)
            report['copied'].append(relative)
        manifest['attempts'][relative] = digest
        manifest['attempt_scopes'][relative] = 'training_v1'
        manifest['pending_attempts'].pop(relative, None)
        _write_manifest(drive, manifest)
    for file in _postprocessing_files(artifacts, local):
        relative = file.relative_to(artifacts).as_posix()
        target, digest = contained_path(drive, relative), _file_digest(file)
        if target.exists() and (not target.is_file() or _file_digest(target) != digest):
            report['conflicts'].append(relative)
            continue
        if manifest['post_files'].get(relative, digest) != digest:
            report['conflicts'].append(relative)
            continue
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            staging = _unique_staging(target, 'partial')
            shutil.copy2(file, staging)
            if _file_digest(staging) != digest:
                report['conflicts'].append(relative)
                continue
            staging.rename(target)
        manifest['post_files'][relative] = digest
        _write_manifest(drive, manifest)
    _write_manifest(drive, manifest)
    return report


def _trust_reasons(artifacts: Path, campaign_id: str, attempt: Path) -> List[str]:
    from uc3m.application.training.attempt_trust import treatment_trust_reasons
    resolved = _read(attempt/'resolved_treatment.json')
    record = _read(attempt/'attempt.json')
    treatment = {'treatment_id': resolved.get('treatment_id'),
                 'attempts': [{'attempt_id': record.get('attempt_id'),
                               'path': attempt.relative_to(artifacts).as_posix(), 'training_complete': True}]}
    return treatment_trust_reasons(artifacts, campaign_id, treatment)


def _recover_pending(drive, manifest, report):
    for relative, pending in list(manifest['pending_attempts'].items()):
        try:
            target = contained_path(drive, relative)
            digest = pending['sha256']
            source = target if target.is_dir() else contained_path(drive, pending['staging'])
            scoped = pending.get('scope') == 'training_v1'
            if not source.is_dir() or directory_digest(source, training_only=scoped) != digest:
                report['rejected'][relative] = ['pending_copy_incomplete']
                continue
            if source != target:
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
            manifest['attempts'][relative] = digest
            if scoped:
                manifest['attempt_scopes'][relative] = 'training_v1'
            del manifest['pending_attempts'][relative]
            _write_manifest(drive, manifest)
        except (OSError, ValueError, KeyError, TypeError):
            report['rejected'][relative] = ['untrusted_pending_copy']


def restore_finished_attempts(drive: Path, artifacts: Path, campaign_id: str, *, trust=None) -> Dict[str, object]:
    drive, artifacts = Path(drive), Path(artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)
    with run_lock(contained_path(drive, '.sync.lock')):
        return _restore(drive, artifacts, campaign_id, trust or _trust_reasons)


def _restore(drive, artifacts, campaign_id, trust):
    manifest = _read_manifest(drive)
    report = {'restored_complete': [], 'restored_failed': [], 'rejected': {}, 'present': [],
              'files': [], 'conflicts': [], 'kept_local': []}
    if manifest.get('campaign_id') not in (None, campaign_id):
        report['conflicts'].append('foreign_campaign')
        return report
    local_path = contained_path(artifacts, 'campaign_manifest.json')
    if local_path.is_file() and _read(local_path).get('campaign_id') != campaign_id:
        report['conflicts'].append('foreign_local_campaign')
        return report
    _recover_pending(drive, manifest, report)
    for relative, digest in sorted(manifest['files'].items()):
        try:
            source, target = contained_path(drive, relative), contained_path(artifacts, relative)
            if source.is_file() and _file_digest(source) == manifest['pending_files'].get(relative):
                digest = manifest['pending_files'][relative]
            if not source.is_file() or _file_digest(source) != digest:
                report['conflicts'].append(relative)
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                staging = _unique_staging(target, 'restoring')
                shutil.copy2(source, staging)
                if _file_digest(staging) != digest:
                    report['conflicts'].append(relative)
                    continue
                staging.rename(target)
                report['files'].append(relative)
            elif not target.is_file() or _file_digest(target) != digest:
                report['kept_local' if _is_stage_log(relative) else 'conflicts'].append(relative)
        except (OSError, ValueError, TypeError):
            report['conflicts'].append(relative)
    if report['conflicts']:
        return report
    for relative, digest in sorted(manifest['attempts'].items()):
        try:
            source, target = contained_path(drive, relative), contained_path(artifacts, relative)
            if not source.is_dir() or _snapshot_digest(source, manifest, relative) != digest:
                report['rejected'][relative] = ['drive_copy_digest_mismatch']
                continue
            if target.exists():
                if not target.is_dir() or _snapshot_digest(target, manifest, relative) != digest:
                    report['conflicts'].append(relative)
                else:
                    complete = _read(target/'completion.json').get('training_complete') is True
                    reasons = trust(artifacts, campaign_id, target) if complete else []
                    if reasons:
                        report['rejected'][relative] = list(reasons)
                    else:
                        report['present'].append(relative)
                continue
            staging = _unique_staging(target, 'restoring')
            staging.parent.mkdir(parents=True, exist_ok=True)
            if manifest['attempt_scopes'].get(relative) == 'training_v1':
                _copy_training(source, staging)
            else:
                shutil.copytree(source, staging)
            if _snapshot_digest(staging, manifest, relative) != digest:
                report['rejected'][relative] = ['local_copy_digest_mismatch']
                continue
            complete = _read(staging/'completion.json').get('training_complete') is True
            reasons = trust(artifacts, campaign_id, staging) if complete else []
            if reasons:
                report['rejected'][relative] = list(reasons)
                continue
            staging.rename(target)
            report['restored_complete' if complete else 'restored_failed'].append(relative)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report['rejected'][relative] = [f'untrusted_copy:{type(exc).__name__}']
    if report['conflicts'] or report['rejected']:
        return report
    for relative, digest in sorted(manifest['post_files'].items()):
        try:
            parts = relative.split('/')
            if not ((parts[0] == 'analysis') or any(
                    relative.startswith(attempt+'/evaluation/') for attempt in manifest['attempts'])):
                raise ValueError('postprocessing path outside declared artifacts')
            source, target = contained_path(drive, relative), contained_path(artifacts, relative)
            if not source.is_file() or _file_digest(source) != digest:
                raise ValueError('postprocessing digest mismatch')
            if target.exists():
                if not target.is_file() or _file_digest(target) != digest:
                    raise ValueError('conflicting local postprocessing')
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                staging = _unique_staging(target, 'restoring')
                shutil.copy2(source, staging)
                if _file_digest(staging) != digest:
                    raise ValueError('copied postprocessing digest mismatch')
                staging.rename(target)
                report['files'].append(relative)
        except (OSError, ValueError, TypeError):
            report['conflicts'].append(relative)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--drive', type=Path, required=True)
    parser.add_argument('--campaign-id')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--sync', action='store_true')
    action.add_argument('--restore', action='store_true')
    args = parser.parse_args(argv)
    if args.restore and not args.campaign_id:
        parser.error('--restore needs --campaign-id')
    try:
        result = (restore_finished_attempts(args.drive, args.artifacts, args.campaign_id) if args.restore
                  else sync_finished_attempts(args.artifacts, args.drive))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {'status': 'refused', 'reason': f'{type(exc).__name__}: {exc}'}
    print(json.dumps(result))
    return 2 if result.get('status') == 'refused' or result.get('conflicts') or result.get('rejected') else 0


if __name__ == '__main__':
    sys.exit(main())
