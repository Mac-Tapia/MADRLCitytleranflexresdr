"""Read-only audit of the real repository tree for a T12 phase.

The tree is read from the filesystem: junctions and symlinks are recorded and
never followed, and ``.git``, virtual environments, caches and the declared
dependency roots are skipped with a recorded reason. Required paths come from
``governance/repository_layout.yaml`` (``consolidation.required_paths_by_phase``);
the checked indexes must not carry an active broken relative reference.

Nothing here writes into the repository except the explicit ``accept``/``audit``
outputs requested on the command line.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

import yaml

SCHEMA_VERSION = 1
PHASE_ORDER: Tuple[str, ...] = ('A', 'B', 'C-software')
EXCLUDED_COMPONENTS = frozenset({'.git', '__pycache__', 'node_modules', '.pytest_cache',
                                 '.ruff_cache', '.mypy_cache'})
EXCLUDED_COMPONENT_PREFIXES: Tuple[str, ...] = ('.venv',)
# Built-in dependency boundary: never scanned, never edited, whatever the registry says.
DEPENDENCY_ROOTS: Mapping[str, str] = {
    'CityLearn': 'protected dependency (own fork, read-only for this task)',
    'external': 'protected third-party dependencies',
}
RETIRED_WORDS = re.compile(
    r'retir|elimin|removed|retired|deleted|borrad|ausente|obsolet|legacy|histor|ya no|no existe',
    re.IGNORECASE)
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
TREE_DEPTH = 2


class LayoutError(ValueError):
    """The registry or the requested phase cannot be audited."""


def load_registry(registry_path: Path) -> dict:
    data = yaml.safe_load(Path(registry_path).read_text(encoding='utf-8')) or {}
    if not isinstance(data, dict):
        raise LayoutError(f'registry {registry_path} is not a mapping')
    return data


def consolidation_section(registry: Mapping) -> dict:
    section = registry.get('consolidation') or {}
    if not isinstance(section, dict):
        raise LayoutError('consolidation section must be a mapping')
    return section


def norm(path: str) -> str:
    text = path.replace('\\', '/').strip()
    while text.startswith('./'):
        text = text[2:]
    parts: List[str] = []
    for part in text.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            if not parts or parts[-1] == '..':
                parts.append('..')
            else:
                parts.pop()
            continue
        parts.append(part)
    return '/'.join(parts)


def under(rel: str, prefix: str) -> bool:
    prefix = prefix.rstrip('/')
    return rel == prefix or rel.startswith(prefix + '/')


def matches_any(rel: str, patterns: Sequence[str]) -> bool:
    return any(fnmatchcase(rel, pattern) or under(rel, pattern) for pattern in patterns)


def scan_exclusions(registry: Mapping) -> Dict[str, str]:
    exclusions = dict(DEPENDENCY_ROOTS)
    for path, reason in (consolidation_section(registry).get('scan_exclusions') or {}).items():
        exclusions[norm(str(path))] = str(reason)
    return exclusions


def is_link(entry: os.DirEntry) -> bool:
    try:
        info = entry.stat(follow_symlinks=False)
    except OSError:
        return True
    if stat.S_ISLNK(info.st_mode):
        return True
    return bool(getattr(info, 'st_file_attributes', 0) & FILE_ATTRIBUTE_REPARSE_POINT)


@dataclass
class TreeWalk:
    files: List[Tuple[str, int]] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    links_not_followed: List[str] = field(default_factory=list)
    excluded_present: Dict[str, int] = field(default_factory=dict)
    component_skips: int = 0
    unreadable: List[str] = field(default_factory=list)


def walk_tree(root: Path, exclusions: Mapping[str, str]) -> TreeWalk:
    """Walk ``root`` without following links; records what was skipped and why."""
    walk = TreeWalk()
    stack: List[Tuple[Path, str]] = [(Path(root), '')]
    while stack:
        directory, rel_dir = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError:
            walk.unreadable.append(rel_dir or '.')
            continue
        for entry in entries:
            rel = f'{rel_dir}/{entry.name}' if rel_dir else entry.name
            if entry.name in EXCLUDED_COMPONENTS or entry.name.startswith(EXCLUDED_COMPONENT_PREFIXES):
                walk.component_skips += 1
                continue
            if is_link(entry):
                walk.links_not_followed.append(rel)
                continue
            excluded = next((key for key in exclusions if under(rel, key)), None)
            if excluded is not None:
                walk.excluded_present[excluded] = walk.excluded_present.get(excluded, 0) + 1
                continue
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                walk.unreadable.append(rel)
                continue
            if is_dir:
                walk.directories.append(rel)
                stack.append((Path(entry.path), rel))
            else:
                try:
                    size = entry.stat(follow_symlinks=False).st_size
                except OSError:
                    walk.unreadable.append(rel)
                    continue
                walk.files.append((rel, size))
    walk.files.sort()
    walk.directories.sort()
    walk.links_not_followed.sort()
    return walk


def summarize_tree(walk: TreeWalk, depth: int = TREE_DEPTH) -> dict:
    counts: Dict[str, List[int]] = {}
    for rel, size in walk.files:
        parts = rel.split('/')
        for level in range(1, min(depth, len(parts) - 1) + 1):
            key = '/'.join(parts[:level])
            bucket = counts.setdefault(key, [0, 0])
            bucket[0] += 1
            bucket[1] += size
    entries = [{'path': d, 'kind': 'dir', 'files': counts.get(d, [0, 0])[0],
                'bytes': counts.get(d, [0, 0])[1]}
               for d in walk.directories if d.count('/') < depth]
    entries += [{'path': rel, 'kind': 'file', 'files': 1, 'bytes': size}
                for rel, size in walk.files if '/' not in rel]
    entries.sort(key=lambda row: row['path'])
    return {'depth': depth, 'files_total': len(walk.files),
            'bytes_total': sum(size for _, size in walk.files), 'entries': entries}


def required_paths_for(section: Mapping, phase: str) -> List[str]:
    if phase not in PHASE_ORDER:
        raise ValueError(f'unknown phase {phase!r}; expected one of {PHASE_ORDER}')
    by_phase = section.get('required_paths_by_phase') or {}
    unknown = sorted(set(by_phase) - set(PHASE_ORDER))
    if unknown:
        raise LayoutError(f'registry declares unknown phases {unknown}')
    required: List[str] = []
    for name in PHASE_ORDER[:PHASE_ORDER.index(phase) + 1]:
        for path in by_phase.get(name) or []:
            rel = norm(str(path))
            if rel not in required:
                required.append(rel)
    return required


# --- references -----------------------------------------------------------

LINK_RE = re.compile(r'!?\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)')
CODE_RE = re.compile(r'`([^`\n]+)`')
FENCE_PATH_RE = re.compile(r'(?<![\w$%{<])((?:\.?[\w.-]+[/\\])+[\w.-]+\.\w{1,8})')
PLACEHOLDER = re.compile(r'[{}<>*$%|?\[\]]')
SCHEME = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*:')


def _clean_token(token: str) -> str:
    token = token.strip().strip('"\'')
    return token.rstrip('.,;:)')


def _candidates(text: str, in_fence: bool) -> Iterator[Tuple[str, str]]:
    for match in LINK_RE.finditer(text):
        yield 'link', match.group(1)
    if in_fence:
        for match in FENCE_PATH_RE.finditer(text):
            yield 'command_path', match.group(1)
        return
    for match in CODE_RE.finditer(text):
        body = match.group(1).strip()
        if ' ' in body:
            for found in FENCE_PATH_RE.finditer(body):
                yield 'command_path', found.group(1)
        else:
            yield 'code_path', body


def _known_roots(root: Path) -> set:
    try:
        return {entry.name for entry in os.scandir(root)}
    except OSError:
        return set()


def _same_depth_match(rel: str, pattern: str) -> bool:
    return rel.count('/') == pattern.count('/') and fnmatchcase(rel, pattern)


def check_references(root: Path, source: str, section: Mapping,
                     registry: Mapping) -> Tuple[List[dict], List[dict], List[dict]]:
    """Return (broken, retired_mentions, run_produced_paths) for one index file."""
    path = Path(root)/source
    broken: List[dict] = []
    retired: List[dict] = []
    runtime_skipped: List[dict] = []
    if not path.is_file():
        return [{'source': source, 'line': 0, 'kind': 'index', 'target': source,
                 'reason': 'checked index is missing'}], [], []
    runtime_roots = [norm(str(p)) for p in section.get('runtime_reference_roots') or []]
    runtime_patterns = [str(p) for p in section.get('runtime_reference_patterns') or []]
    retired_paths = [norm(str(p)) for p in (registry.get('launch') or {}).get('retired') or []]
    retired_paths += [norm(str(p)) for p in (registry.get('retired_historical_roots') or {}).values()]
    top = _known_roots(root)
    base = norm(str(Path(source).parent.as_posix())) if '/' in source else ''
    in_fence = False
    seen = set()
    for number, line in enumerate(path.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        for kind, raw in _candidates(line, in_fence):
            token = _clean_token(raw).split('#', 1)[0].replace('%20', ' ')
            if not token or SCHEME.match(token) or token.startswith(('//', '-')):
                continue
            if PLACEHOLDER.search(token):
                continue
            rel_root = norm(token.lstrip('/'))
            rel_local = norm(f'{base}/{token}') if base and not token.startswith('/') else rel_root
            first = rel_root.split('/')[0]
            if kind != 'link':
                if '/' not in rel_root.strip('/'):
                    continue  # bare names are prose, not paths
                local_first = (Path(root)/base/first).exists() if base else False
                if first not in top and not local_first:
                    continue  # not anchored in the repository nor next to the index
            if rel_root.startswith('..') and rel_local.startswith('..'):
                broken.append({'source': source, 'line': number, 'kind': kind, 'target': token,
                               'reason': 'reference escapes the repository root'})
                continue
            if (Path(root)/rel_local).exists() or (kind != 'link' and (Path(root)/rel_root).exists()):
                continue
            target = rel_local if kind == 'link' else rel_root
            key = (number, target)
            if key in seen:
                continue
            seen.add(key)
            row = {'source': source, 'line': number, 'kind': kind, 'target': target}
            if any(under(target, r) or under(rel_local, r) for r in runtime_roots) or \
                    any(_same_depth_match(target, pattern) for pattern in runtime_patterns):
                runtime_skipped.append({**row, 'reason': 'run-produced path; not required to exist in the tree'})
                continue
            if RETIRED_WORDS.search(line) or any(under(target, r) for r in retired_paths):
                retired.append({**row, 'reason': 'mentioned as retired/removed; not an active reference'})
                continue
            broken.append({**row, 'reason': 'relative reference does not resolve'})
    return broken, retired, runtime_skipped


@dataclass
class LayoutReport:
    schema_version: int
    phase: str
    actual_tree: dict
    excluded_scope: List[dict]
    links_not_followed: List[str]
    required_paths: List[str]
    missing_paths: List[str]
    canonical_sources_missing: List[str]
    checked_indexes: List[str]
    active_broken_references: List[dict]
    retired_mentions: List[dict]
    runtime_references_not_checked: List[dict]
    repository_layout_verified: bool
    reasons: List[str]

    def as_dict(self) -> dict:
        return asdict(self)


def excluded_scope_rows(root: Path, exclusions: Mapping[str, str], walk: TreeWalk) -> List[dict]:
    rows = [{'path': path, 'reason': reason, 'present': (Path(root)/path).exists()}
            for path, reason in sorted(exclusions.items())]
    rows.append({'path': '**/' + '|'.join(sorted(EXCLUDED_COMPONENTS)) + '|.venv*',
                 'reason': 'version control, environments and caches (never entered)',
                 'present': walk.component_skips > 0})
    return rows


def audit_repository_layout(root: Path, registry_path: Path, phase: str) -> LayoutReport:
    root = Path(root)
    registry = load_registry(registry_path)
    section = consolidation_section(registry)
    required = required_paths_for(section, phase)
    exclusions = scan_exclusions(registry)
    walk = walk_tree(root, exclusions)
    missing = [rel for rel in required if not (root/rel).exists()]
    canonical = section.get('canonical_sources') or {}
    canonical_missing = sorted({norm(str(p)) for p in canonical.values()
                                if not (root/norm(str(p))).exists()})
    indexes = [norm(str(p)) for p in section.get('checked_indexes') or []]
    broken: List[dict] = []
    retired: List[dict] = []
    runtime: List[dict] = []
    for source in indexes:
        found, mentions, skipped = check_references(root, source, section, registry)
        broken += found
        retired += mentions
        runtime += skipped
    reasons: List[str] = []
    if missing:
        reasons.append(f'missing required paths for phase {phase}: {", ".join(missing)}')
    if canonical_missing:
        reasons.append(f'registered canonical sources absent: {", ".join(canonical_missing)}')
    if broken:
        reasons.append(f'{len(broken)} active broken references in checked indexes')
    if walk.unreadable:
        reasons.append(f'unreadable entries: {", ".join(walk.unreadable[:10])}')
    return LayoutReport(
        schema_version=SCHEMA_VERSION, phase=phase, actual_tree=summarize_tree(walk),
        excluded_scope=excluded_scope_rows(root, exclusions, walk),
        links_not_followed=walk.links_not_followed, required_paths=required, missing_paths=missing,
        canonical_sources_missing=canonical_missing, checked_indexes=indexes,
        active_broken_references=broken, retired_mentions=retired,
        runtime_references_not_checked=runtime, repository_layout_verified=not reasons,
        reasons=reasons)


# --- phase acceptance ----------------------------------------------------

def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + '\n',
                    encoding='utf-8')


def build_acceptance(layout: LayoutReport, inventory, plan) -> dict:
    counts = dict(inventory.classification_counts)
    unjustified = [g.group_id for g in inventory.exact_groups + inventory.semantic_candidates
                   if g.classification == 'redundant_clone']
    needs_review = [g.group_id for g in inventory.exact_groups + inventory.semantic_candidates
                    if g.classification == 'needs_review']
    reasons = list(layout.reasons)
    if unjustified:
        reasons.append(f'{len(unjustified)} redundant clone groups still present (removal not executed)')
    if needs_review:
        reasons.append(f'{len(needs_review)} candidate groups need review; not verified')
    if plan.blocked_unique_content:
        reasons.append(f'{len(plan.blocked_unique_content)} files blocked by unique content')
    if inventory.facade_violations:
        reasons.append(f'{len(inventory.facade_violations)} registered facades contain logic')
    if inventory.registry_errors:
        reasons.append('registry errors: ' + '; '.join(inventory.registry_errors))
    if inventory.generated_sources_missing:
        reasons.append('generated asset sources missing: ' + ', '.join(inventory.generated_sources_missing))
    return {
        'schema_version': SCHEMA_VERSION,
        'phase': layout.phase,
        'scope': 'parent repository only; dependency roots and recorded exclusions are out of the clone criterion',
        'classification_counts': counts,
        'exact_groups': len(inventory.exact_groups),
        'semantic_candidates': len(inventory.semantic_candidates),
        'redundant_clone_groups': unjustified,
        'needs_review_groups': needs_review,
        'blocked_unique_content': [row['path'] for row in plan.blocked_unique_content],
        'proposed_removals': [row['path'] for row in plan.removed_paths],
        'missing_paths': layout.missing_paths,
        'active_broken_references': len(layout.active_broken_references),
        'facade_violations': [row['path'] for row in inventory.facade_violations],
        'protected_documents': [row['path'] for row in inventory.protected_documents],
        'protected_note': ('protected documents are never removed here; Word consolidation (D-05) '
                           'needs the authorized Word flow and is not certified by this audit'),
        'repository_layout_verified': not reasons,
        'reasons': reasons,
    }


def accept(root: Path, registry_path: Path, phase: str, out_dir: Path) -> dict:
    from tools.ops import audit_duplicate_files as adf

    layout = audit_repository_layout(root, registry_path, phase)
    inventory = adf.find_duplicate_candidates(root, registry_path)
    plan = adf.build_canonicalization_plan(inventory, [])
    acceptance = build_acceptance(layout, inventory, plan)
    at = datetime.now(timezone.utc).isoformat()
    _write_json(out_dir/'repository_tree.json', {**layout.as_dict(), 'at_utc': at})
    _write_json(out_dir/'duplicate_inventory.json', {**inventory.as_dict(), 'at_utc': at})
    _write_json(out_dir/'canonicalization_plan.json', {**plan.as_dict(), 'at_utc': at})
    _write_json(out_dir/'consolidation_result.json', {
        'schema_version': SCHEMA_VERSION, 'status': 'not_executed',
        'reason': 'deletion in the real repository is the coordinator decision; Execute was not run',
        'proposed_removed_paths': plan.as_dict()['removed_paths'], 'at_utc': at})
    _write_json(out_dir/'repository_layout_acceptance.json', {**acceptance, 'at_utc': at})
    return acceptance


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('audit', 'accept'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--root', type=Path, default=Path('.'))
        cmd.add_argument('--registry', type=Path, default=None)
        cmd.add_argument('--phase', required=True, choices=PHASE_ORDER)
        cmd.add_argument('--out' if name == 'audit' else '--out-dir', type=Path, required=name == 'accept')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    registry = args.registry or root/'governance/repository_layout.yaml'
    if args.command == 'audit':
        report = audit_repository_layout(root, registry, args.phase).as_dict()
        if args.out:
            _write_json(args.out, report)
        else:
            json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        return 0 if report['repository_layout_verified'] else 1
    acceptance = accept(root, registry, args.phase, args.out_dir)
    json.dump({k: acceptance[k] for k in ('repository_layout_verified', 'reasons')}, sys.stdout,
              indent=2, ensure_ascii=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
