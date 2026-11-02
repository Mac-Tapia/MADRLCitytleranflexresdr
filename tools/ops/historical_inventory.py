"""Inventory, plan and verify the retirement of historical outputs R-01..R-07.

This module never deletes anything. It hashes bytes (never deserializes a
pickle or a checkpoint), records consumers and live processes, and decides per
target whether the closed list may be removed. The only mutation path is
``scripts/maintenance/retire_historical_outputs.ps1 -Phase Execute``, which
asks ``verify`` for a fresh decision immediately before each removal.

Maintenance record only: nothing produced here is an input of the new campaign.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = 1

# Closed list authorized by the owner (docs/audits/historicos.md
# section 1). It is the safety boundary: a plan naming anything else is refused.
ALLOWLIST: Tuple[Tuple[str, str], ...] = (
    ('R-01', 'outputs/_drive_madrl'),
    ('R-02', 'outputs/citylearn_v3_madrl_full_20260615_074011_v4'),
    ('R-03', 'outputs/madrl_v3_20260627_164047'),
    ('R-04', 'outputs/modular_smoke'),
    ('R-05', 'outputs/thesis_objective_evidence'),
    ('R-06', 'outputs/dataset_cache'),
    ('R-07', 'outputs/orchestration-tests.xml'),
)

PROTECTED_PATHS: Tuple[str, ...] = (
    '.git', 'CityLearn', 'CityLearn/data/buildingcsv', 'external', 'docs', 'data/audits',
    'data/dataset_audit', 'data/campaigns', 'data/maintenance', 'outputs/README.md',
    'outputs/campaigns',
    'outputs/campaigns',
)

# Code that writes into a target without naming it on its command line. The
# evidence string is re-checked in the file, never assumed.
IMPLICIT_PRODUCERS: Mapping[str, Mapping[str, object]] = {
    'R-06': {
        'path': 'CityLearn/scripts/citylearn_v3_training_common.py',
        'evidence': '_CSV_CACHE_DIR = PROJECT_ROOT / "outputs" / "dataset_cache"',
        'process_tokens': ('train_citylearn_v3_',),
    },
}

# Files that name the retired roots in order to refuse or retire them.
SELF_PATHS = frozenset({
    'tools/ops/historical_inventory.py',
    'scripts/maintenance/retire_historical_outputs.ps1',
    'governance/repository_layout.yaml',
})
ACTIVE_PROFILE_PREFIXES = ('uc3m/', 'configs/', 'scripts/quality/', 'scripts/maintenance/',
                           '.github/')
SCAN_SUFFIXES = {'.py', '.ps1', '.psm1', '.ipynb', '.json', '.yaml', '.yml', '.bat', '.cmd',
                 '.sh', '.toml', '.cfg'}
SCAN_SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.superpowers', '.pytest_cache',
                  '.mypy_cache', '.ruff_cache'}
SCAN_SKIP_PREFIXES = ('outputs/', 'data/campaigns/', 'CityLearn/data/', '.venv')
SCAN_MAX_BYTES = 5*1024*1024

ProcessLister = Callable[[], Iterable[Mapping[str, object]]]


class RetirementError(ValueError):
    """The plan or the tree does not satisfy the retirement contract."""


def _canonical_json(payload) -> bytes:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:  # raw bytes only; never unpickled
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _is_reparse(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    attributes = getattr(info, 'st_file_attributes', 0)
    return bool(attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)) or stat.S_ISLNK(info.st_mode)


def _walk_files(top: Path):
    """Yield (path, is_reparse) without ever entering a junction or symlink."""
    stack = [top]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                if _is_reparse(path):
                    yield path, True
                elif entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                elif entry.is_file(follow_symlinks=False):
                    yield path, False


@dataclass(frozen=True)
class RetirementTarget:
    target_id: str
    relative_path: str
    resolved_path: str
    kind: str
    files: Tuple[Mapping[str, object], ...]
    total_bytes: int
    git_tracked_paths: Optional[int]
    decision: str
    reasons: Tuple[str, ...] = ()
    covered_by: Optional[str] = None

    def as_dict(self):
        return {'target_id': self.target_id, 'relative_path': self.relative_path,
                'resolved_path': self.resolved_path, 'kind': self.kind,
                'files': [dict(item) for item in self.files], 'file_count': len(self.files),
                'total_bytes': self.total_bytes, 'git_tracked_paths': self.git_tracked_paths,
                'decision': self.decision, 'reasons': list(self.reasons),
                'covered_by': self.covered_by}


@dataclass(frozen=True)
class RetirementPlan:
    project_root: str
    allowlist_ids: Tuple[str, ...]
    targets: Tuple[RetirementTarget, ...]
    protected_paths: Tuple[str, ...]
    consumers: Tuple[Mapping[str, object], ...]
    processes: Tuple[Mapping[str, object], ...]
    regenerators: Tuple[Mapping[str, object], ...]
    diagnostic_records: Tuple[Mapping[str, object], ...]
    git_status: Mapping[str, object]
    generated_at: str
    plan_hash: str = ''

    @property
    def deletion_order(self) -> Tuple[str, ...]:
        return tuple(t.target_id for t in self.targets if t.decision == 'delete')

    def hashed_body(self):
        body = self.as_dict(include_hash=False)
        body.pop('generated_at')
        return body

    def as_dict(self, include_hash=True):
        payload = {
            'schema_version': SCHEMA_VERSION, 'project_root': self.project_root,
            'allowlist_ids': list(self.allowlist_ids),
            'targets': [t.as_dict() for t in self.targets],
            'deletion_order': list(self.deletion_order),
            'protected_paths': list(self.protected_paths),
            'consumers': [dict(c) for c in self.consumers],
            'processes': [dict(p) for p in self.processes],
            'regenerators': [dict(r) for r in self.regenerators],
            'diagnostic_records': [dict(d) for d in self.diagnostic_records],
            'git_status': dict(self.git_status), 'generated_at': self.generated_at,
        }
        if include_hash:
            payload['plan_hash'] = self.plan_hash
        return payload


def compute_plan_hash(payload: Mapping[str, object]) -> str:
    body = {key: value for key, value in payload.items() if key not in {'plan_hash', 'generated_at'}}
    return hashlib.sha256(_canonical_json(body)).hexdigest()


def list_processes() -> List[Mapping[str, object]]:
    """Live process snapshot (PID, name, command line) through CIM, read-only."""
    command = ('Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | '
               'ConvertTo-Json -Compress')
    try:
        completed = subprocess.run(['powershell', '-NoProfile', '-Command', command],
                                   capture_output=True, text=True, timeout=120, check=True)
        rows = json.loads(completed.stdout or '[]')
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise RetirementError(f'process snapshot unavailable: {exc}') from exc
    rows = rows if isinstance(rows, list) else [rows]
    return [{'pid': row.get('ProcessId'), 'name': row.get('Name'),
             'command_line': row.get('CommandLine') or ''} for row in rows]


def _git_tracked(root: Path, relative: str) -> Optional[int]:
    if not (root/'.git').exists():
        return None
    completed = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--', relative],
                               capture_output=True, check=False)
    if completed.returncode != 0:
        return None
    return len([item for item in completed.stdout.split(b'\0') if item])


def _git_status(root: Path) -> Mapping[str, object]:
    if not (root/'.git').exists():
        return {'available': False}
    completed = subprocess.run(['git', '-C', str(root), 'status', '--porcelain=v1', '--', 'outputs'],
                               capture_output=True, text=True, check=False)
    lines = [line for line in completed.stdout.splitlines() if line]
    head = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True, check=False).stdout.strip()
    return {'available': True, 'head': head, 'outputs_status_lines': lines}


def _classify(relative: str) -> str:
    if relative.startswith(('CityLearn/', 'external/')):
        return 'dependency'
    if relative.startswith(('docs/', 'data/')):
        return 'documentary'
    if relative.startswith('tests/fresh_training/'):
        return 'fresh_contract_test'
    if relative.startswith('governance/'):
        return 'registry'  # policy notes name roots; they never read or write them
    if relative.startswith(ACTIVE_PROFILE_PREFIXES):
        return 'active_profile'
    return 'archival_tool'


def _token(relative: str) -> str:
    name = Path(relative).name
    return name[:-len('.xml')] if name.endswith('.xml') else name


def scan_consumers(root: Path, allowlist: Sequence[Tuple[str, str]]) -> List[Mapping[str, object]]:
    tokens = {target_id: _token(relative) for target_id, relative in allowlist}
    findings = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        rel_dir = current_path.relative_to(root).as_posix()
        rel_dir = '' if rel_dir == '.' else rel_dir + '/'
        dirs[:] = [d for d in dirs if d not in SCAN_SKIP_DIRS
                   and not (rel_dir + d + '/').startswith(SCAN_SKIP_PREFIXES)
                   and not _is_reparse(current_path/d)]
        for name in files:
            relative = rel_dir + name
            path = current_path/name
            if Path(name).suffix not in SCAN_SUFFIXES or relative in SELF_PATHS:
                continue
            try:
                if path.stat().st_size > SCAN_MAX_BYTES:
                    continue
                text = path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            for target_id, token in tokens.items():
                lines = [number for number, line in enumerate(text.splitlines(), 1) if token in line]
                if lines:
                    findings.append({'path': relative, 'target_id': target_id,
                                     'classification': _classify(relative),
                                     'lines': lines[:20], 'line_count': len(lines)})
    return sorted(findings, key=lambda item: (item['target_id'], item['path']))


def _matching_processes(processes, allowlist, root: Path):
    matches = []
    own = {os.getpid(), os.getppid()}
    for process in processes:
        if process.get('pid') in own:
            continue
        command = str(process.get('command_line') or '')
        lowered = command.casefold()
        for target_id, relative in allowlist:
            tokens = [_token(relative), str((root/relative)).casefold()]
            tokens += list(IMPLICIT_PRODUCERS.get(target_id, {}).get('process_tokens', ()))
            hit = next((tok for tok in tokens if tok and tok.casefold() in lowered), None)
            if hit:
                # Never persist the command line: it may carry credentials or paths.
                matches.append({'pid': process.get('pid'), 'name': process.get('name'),
                                'target_id': target_id, 'matched_token': hit})
    return matches


def _regenerators(root: Path):
    rows = []
    for target_id, producer in IMPLICIT_PRODUCERS.items():
        path = root/str(producer['path'])
        if not path.is_file():
            continue
        if str(producer['evidence']) not in path.read_text(encoding='utf-8', errors='replace'):
            continue
        rows.append({'target_id': target_id, 'path': str(producer['path']),
                     'evidence': producer['evidence'], 'protected_dependency': True,
                     'fresh_profile_mitigation': _fresh_mitigation(target_id)})
    return rows


def _fresh_mitigation(target_id: str) -> Mapping[str, object]:
    """The fresh native entrypoint redirects dependency caches per attempt."""
    try:
        from uc3m.adapters.algorithms import native_entrypoint
    except ImportError:
        return {'verified': False, 'reason': 'fresh native entrypoint not implemented'}
    redirected = getattr(native_entrypoint, 'REDIRECTED_DEPENDENCY_CACHES', {})
    relative = dict(ALLOWLIST)[target_id]
    if relative in redirected.values():
        return {'verified': True, 'mechanism': 'uc3m.adapters.algorithms.native_entrypoint',
                'test': 'tests/fresh_training/test_real_learning.py::test_native_cache_redirected_per_attempt'}
    return {'verified': False, 'reason': 'entrypoint does not redirect this cache'}


def _inspect_target(root: Path, target_id: str, relative: str):
    path = root/relative
    reasons = []
    expected = (root.resolve()/relative)
    outputs = root.resolve()/'outputs'
    if not str(expected).startswith(str(outputs) + os.sep):
        reasons.append('outside_outputs')
    for ancestor in [root/Path(*Path(relative).parts[:i]) for i in range(1, len(Path(relative).parts))]:
        if _is_reparse(ancestor):
            reasons.append('reparse_point_ancestor')
    if not os.path.lexists(path):
        return 'absent', (), 0, reasons
    if _is_reparse(path):
        return 'reparse_point', (), 0, reasons + ['reparse_point']
    if path.resolve() != expected:
        reasons.append('resolved_path_mismatch')
    files = []
    total = 0
    if path.is_file():
        walked = [(path, False)]
        kind = 'file'
    else:
        walked = sorted(_walk_files(path))
        kind = 'directory'
    for item, reparse in walked:
        rel = item.relative_to(root).as_posix()
        if reparse:
            reasons.append('reparse_point_descendant')
            files.append({'path': rel, 'reparse_point': True})
            continue
        info = item.stat()
        total += info.st_size
        files.append({'path': rel, 'bytes': info.st_size, 'sha256': _sha256_file(item),
                      'mtime_utc': datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat()})
    return kind, tuple(files), total, reasons


def inventory_historical_outputs(project_root: Path, *, allowlist: Sequence[Tuple[str, str]] = ALLOWLIST,
                                 protected: Sequence[str] = PROTECTED_PATHS,
                                 process_lister: Optional[ProcessLister] = None,
                                 diagnostic_records: Sequence[Mapping[str, object]] = ()) -> RetirementPlan:
    root = Path(project_root).resolve()
    processes = list((process_lister or list_processes)())
    process_hits = _matching_processes(processes, allowlist, root)
    consumers = scan_consumers(root, allowlist)
    regenerators = _regenerators(root)
    targets = []
    ordered = sorted(allowlist, key=lambda item: len(Path(item[1]).parts))
    claimed: List[Tuple[str, str]] = []
    for target_id, relative in ordered:
        parent = next((pid for pid, prel in claimed
                       if Path(relative).parts[:len(Path(prel).parts)] == Path(prel).parts), None)
        kind, files, total, reasons = _inspect_target(root, target_id, relative)
        reasons = list(dict.fromkeys(reasons))
        if any(hit['target_id'] == target_id for hit in process_hits):
            reasons.append('active_process')
        if any(c['target_id'] == target_id and c['classification'] == 'active_profile' for c in consumers):
            reasons.append('active_profile_consumer')
        if parent:
            decision = 'covered_by_parent'
        elif kind == 'absent' and not reasons:
            decision = 'already_absent'
        elif reasons:
            decision = 'blocked'
        else:
            decision = 'delete'
        targets.append(RetirementTarget(target_id, relative, str(root/relative), kind, files, total,
                                        _git_tracked(root, relative), decision, tuple(reasons), parent))
        claimed.append((target_id, relative))
    order = {target_id: index for index, (target_id, _) in enumerate(allowlist)}
    targets.sort(key=lambda target: order[target.target_id])
    protected_present = tuple(p for p in protected if os.path.lexists(root/p))
    plan = RetirementPlan(str(root), tuple(t for t, _ in allowlist), tuple(targets), protected_present,
                          tuple(consumers), tuple(process_hits), tuple(regenerators),
                          tuple(diagnostic_records), _git_status(root),
                          datetime.now(timezone.utc).isoformat())
    return RetirementPlan(**{**plan.__dict__, 'plan_hash': compute_plan_hash(plan.as_dict(include_hash=False))})


def load_plan(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('schema_version') != SCHEMA_VERSION:
        raise RetirementError('unsupported plan schema_version')
    if compute_plan_hash(payload) != payload.get('plan_hash'):
        raise RetirementError('plan_hash does not match plan content')
    return payload


def verify_plan(plan_path: Path, project_root: Path, *, process_lister: Optional[ProcessLister] = None):
    """Fresh go/no-go per target, recomputed right before an Execute run."""
    payload = load_plan(plan_path)
    root = Path(project_root).resolve()
    if Path(payload['project_root']).resolve() != root:
        raise RetirementError('plan project_root differs from the requested root')
    declared = [(t['target_id'], t['relative_path']) for t in payload['targets']]
    if tuple(declared) != ALLOWLIST:
        raise RetirementError('plan targets differ from the closed allowlist R-01..R-07')
    current = inventory_historical_outputs(root, process_lister=process_lister)
    now = {t.target_id: t for t in current.targets}
    decisions = []
    for planned in payload['targets']:
        fresh = now[planned['target_id']]
        reasons = list(fresh.reasons)
        planned_files = {f['path']: (f.get('bytes'), f.get('sha256')) for f in planned['files']}
        fresh_files = {f['path']: (f.get('bytes'), f.get('sha256')) for f in fresh.files}
        if planned['decision'] == 'delete' and planned_files != fresh_files:
            reasons.append('inventory_changed')
        if planned['decision'] == 'blocked':
            reasons.extend(r for r in planned['reasons'] if r not in reasons)
        if fresh.decision == 'already_absent' and not reasons:
            decision = 'already_absent'
        elif planned['decision'] == 'delete' and fresh.decision == 'delete' and not reasons:
            decision = 'delete'
        else:
            decision = 'blocked'
        decisions.append({'target_id': planned['target_id'], 'relative_path': planned['relative_path'],
                          'absolute_path': str(root/planned['relative_path']),
                          'kind': fresh.kind, 'decision': decision, 'reasons': reasons})
    return {'plan_hash': payload['plan_hash'], 'decisions': decisions}


def record_result(plan_path: Path, project_root: Path, outcomes: Sequence[Mapping[str, object]]):
    payload = load_plan(plan_path)
    root = Path(project_root).resolve()
    by_id = {row['target_id']: row for row in outcomes}
    targets = []
    for planned in payload['targets']:
        outcome = dict(by_id.get(planned['target_id'], {'status': 'blocked', 'reasons': ['not_attempted']}))
        present = os.path.lexists(root/planned['relative_path'])
        if outcome['status'] in {'deleted', 'already_absent'} and present:
            outcome = {**outcome, 'status': 'failed', 'reasons': list(outcome.get('reasons', [])) + ['still_present']}
        targets.append({'target_id': planned['target_id'], 'relative_path': planned['relative_path'],
                        'status': outcome['status'], 'reasons': list(outcome.get('reasons', [])),
                        'exit_code': outcome.get('exit_code', 0), 'at_utc': outcome.get('at_utc'),
                        'present_after': present})
    protected_verified = all(os.path.lexists(root/p) for p in payload['protected_paths'])
    regenerators = _regenerators(root)
    unmitigated = [r for r in regenerators if not r['fresh_profile_mitigation'].get('verified')]
    complete = (all(t['status'] in {'deleted', 'already_absent'} for t in targets)
                and protected_verified and not unmitigated)
    result = {'schema_version': SCHEMA_VERSION, 'plan_hash': payload['plan_hash'],
              'project_root': str(root), 'targets': targets,
              'protected_paths_verified': protected_verified,
              'regenerators': regenerators, 'unmitigated_regenerators': unmitigated,
              'historical_retirement_complete': complete,
              'recorded_at': datetime.now(timezone.utc).isoformat(),
              'note': 'Hashes identify removed bytes; they are not a backup of ignored files.'}
    destination = Path(plan_path).parent/'retirement_result.json'
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    inventory = sub.add_parser('inventory')
    inventory.add_argument('--project-root', type=Path, required=True)
    inventory.add_argument('--out', type=Path, required=True)
    inventory.add_argument('--diagnostics', type=Path, default=None)
    verify = sub.add_parser('verify')
    verify.add_argument('--plan', type=Path, required=True)
    verify.add_argument('--project-root', type=Path, required=True)
    record = sub.add_parser('record')
    record.add_argument('--plan', type=Path, required=True)
    record.add_argument('--project-root', type=Path, required=True)
    record.add_argument('--outcomes', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'inventory':
            records = []
            if args.diagnostics:
                records = json.loads(args.diagnostics.read_text(encoding='utf-8'))
                records = records['records'] if isinstance(records, dict) else records
            plan = inventory_historical_outputs(args.project_root, diagnostic_records=records)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(plan.as_dict(), indent=2), encoding='utf-8')
            print(json.dumps({'plan': str(args.out), 'plan_hash': plan.plan_hash,
                              'decisions': {t.target_id: t.decision for t in plan.targets}}))
            return 0
        if args.command == 'verify':
            print(json.dumps(verify_plan(args.plan, args.project_root)))
            return 0
        outcomes = json.loads(args.outcomes.read_text(encoding='utf-8-sig'))
        outcomes = outcomes if isinstance(outcomes, list) else [outcomes]
        result = record_result(args.plan, args.project_root, outcomes)
        print(json.dumps({'historical_retirement_complete': result['historical_retirement_complete'],
                          'targets': {t['target_id']: t['status'] for t in result['targets']}}))
        return 0 if result['historical_retirement_complete'] else 3
    except RetirementError as exc:
        print(json.dumps({'status': 'refused', 'reason': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
