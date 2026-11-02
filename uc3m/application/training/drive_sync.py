"""Incremental Drive persistence of finished attempts and restore at session start.

    python -m uc3m.application.training.drive_sync --artifacts outputs/campaigns/<alias> \
        --drive /content/drive/MyDrive/MADRL_campaigns/<alias>/outputs --sync
    python -m uc3m.application.training.drive_sync ... --restore --campaign-id <id>

An attempt is FINISHED when its completion.json exists (run_stage writes it last,
after the learner returned). Only finished attempts are copied, never one in
progress; each copy goes to a temporary directory on Drive, is verified by its
content digest and only then renamed into place, and a copy that already exists
on Drive is never overwritten. The Drive manifest records the digest of every
synced attempt.

Restore copies back to the local artifacts only attempts whose Drive digest
verifies; a complete attempt must also pass fresh_acceptance.treatment_trust_reasons
(checkpoint bundle hash, verified learning, campaign identity). An attempt that
was interrupted never reached Drive (it had no completion.json), so it is never
restored as complete: its treatment is repeated from zero by a new attempt.
Campaign-level files (manifest, stage manifests, configuration freezes) are
synced and restored only when the local copy is absent; a local file that
differs from Drive is reported as a conflict and left untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

MANIFEST = 'drive_sync_manifest.json'
CAMPAIGN_FILES = ('campaign_manifest.json', 'campaign.json', 'treatments.json', 'configuration_freezes.json')


def directory_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in Path(path).rglob('*') if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode('utf-8') + b'\0' + file.read_bytes() + b'\0')
    return digest.hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finished_attempts(artifacts: Path) -> List[Path]:
    """Attempt directories (attempt.json) whose completion.json exists."""
    return sorted(p.parent for p in Path(artifacts).rglob('attempt.json')
                  if (p.parent/'completion.json').is_file())


def _read_manifest(drive: Path) -> Dict[str, object]:
    path = Path(drive)/MANIFEST
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {'attempts': {}, 'files': {}}


def _write_manifest(drive: Path, manifest) -> None:
    path = Path(drive)/MANIFEST
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(path)


def _campaign_files(root: Path) -> List[Path]:
    root = Path(root)
    files = [root/name for name in CAMPAIGN_FILES if (root/name).is_file()]
    stages = root/'stages'
    if stages.is_dir():
        files += sorted(p for p in stages.rglob('*') if p.is_file())
    return files


def sync_finished_attempts(artifacts: Path, drive: Path) -> Dict[str, object]:
    """Copy every finished attempt not yet on Drive; returns what was copied or rejected."""
    artifacts, drive = Path(artifacts), Path(drive)
    drive.mkdir(parents=True, exist_ok=True)
    manifest = _read_manifest(drive)
    report = {'copied': [], 'already_synced': [], 'conflicts': [], 'files': []}
    for attempt in finished_attempts(artifacts):
        relative = attempt.relative_to(artifacts).as_posix()
        digest = directory_digest(attempt)
        target = drive/relative
        if relative in manifest['attempts']:
            key = 'already_synced' if manifest['attempts'][relative] == digest else 'conflicts'
            report[key].append(relative)
            continue
        if target.exists():
            report['conflicts'].append(relative)
            continue
        staging = target.parent/(target.name + '.partial')
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(attempt, staging)
        if directory_digest(staging) != digest:
            shutil.rmtree(staging)
            report['conflicts'].append(relative)
            continue
        staging.rename(target)
        manifest['attempts'][relative] = digest
        report['copied'].append(relative)
    for file in _campaign_files(artifacts):
        relative = file.relative_to(artifacts).as_posix()
        target = drive/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + '.partial')
        shutil.copy2(file, tmp)
        tmp.replace(target)             # campaign files are updated by run_stage; keep the latest
        manifest['files'][relative] = _file_digest(target)
        report['files'].append(relative)
    _write_manifest(drive, manifest)
    return report


def _trust_reasons(artifacts: Path, campaign_id: str, attempt: Path) -> List[str]:
    from uc3m.application.training.fresh_acceptance import treatment_trust_reasons
    completion = json.loads((attempt/'completion.json').read_text(encoding='utf-8'))
    treatment = {'treatment_id': attempt.relative_to(artifacts).as_posix(),
                 'attempts': [{'path': attempt.relative_to(artifacts).as_posix(),
                               'training_complete': completion.get('training_complete') is True}]}
    return treatment_trust_reasons(artifacts, campaign_id, treatment)


def restore_finished_attempts(drive: Path, artifacts: Path, campaign_id: str, *, trust=None) -> Dict[str, object]:
    """Restore verified finished attempts and absent campaign files from Drive."""
    drive, artifacts = Path(drive), Path(artifacts)
    trust = trust or _trust_reasons
    manifest = _read_manifest(drive)
    report = {'restored_complete': [], 'restored_failed': [], 'rejected': {}, 'present': [], 'files': [],
              'conflicts': []}
    artifacts.mkdir(parents=True, exist_ok=True)
    for relative, file_digest in sorted((manifest.get('files') or {}).items()):
        source, target = drive/relative, artifacts/relative
        if not source.is_file() or _file_digest(source) != file_digest:
            report['conflicts'].append(relative)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            report['files'].append(relative)
        elif _file_digest(target) != file_digest:
            report['conflicts'].append(relative)
    for relative, digest in sorted((manifest.get('attempts') or {}).items()):
        source, target = drive/relative, artifacts/relative
        if target.exists():
            report['present'].append(relative)
            continue
        if not source.is_dir() or directory_digest(source) != digest:
            report['rejected'][relative] = ['drive_copy_digest_mismatch']
            continue
        staging = target.parent/(target.name + '.restoring')
        if staging.exists():
            shutil.rmtree(staging)
        staging.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, staging)
        if directory_digest(staging) != digest:
            shutil.rmtree(staging)
            report['rejected'][relative] = ['local_copy_digest_mismatch']
            continue
        staging.rename(target)
        completion = json.loads((target/'completion.json').read_text(encoding='utf-8'))
        if completion.get('training_complete') is True:
            reasons = trust(artifacts, campaign_id, target)
            if reasons:
                shutil.rmtree(target)        # never accepted as complete without its verified model
                report['rejected'][relative] = list(reasons)
                continue
            report['restored_complete'].append(relative)
        else:
            report['restored_failed'].append(relative)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--drive', type=Path, required=True)
    parser.add_argument('--campaign-id', default=None)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--sync', action='store_true')
    action.add_argument('--restore', action='store_true')
    args = parser.parse_args(argv)
    if args.restore:
        if not args.campaign_id:
            parser.error('--restore needs --campaign-id')
        result = restore_finished_attempts(args.drive, args.artifacts, args.campaign_id)
    else:
        result = sync_finished_attempts(args.artifacts, args.drive)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
