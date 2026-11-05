"""Inventory duplicate candidates and plan one canonical file per responsibility.

Exact SHA-256 groups and semantic candidates (shared normalized AST function
bodies or shared normalized text lines) only *propose* review. The canonical
file of a group is chosen, in this order, by the role registry
(``consolidation.canonical_sources``), by coverage (the only member that
contains every capability of the others) and by active consumers. Size,
modification time, suffixes such as ``_v2``/``final`` and basenames never
decide. Protected Word documents, data identities, evidence snapshots,
facades and generated-asset sources are never proposed for removal.

This module never deletes. ``scripts/maintenance/consolidate_repository.ps1
-Phase Execute`` asks :func:`verify_plan` for a fresh decision immediately
before each removal.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from tools.ops.audit_repository_layout import (
    DEPENDENCY_ROOTS,
    FILE_ATTRIBUTE_REPARSE_POINT,
    consolidation_section,
    excluded_scope_rows,
    load_registry,
    norm,
    scan_exclusions,
    under,
    walk_tree,
)

SCHEMA_VERSION = 1
CLASSIFICATIONS = ('redundant_clone', 'distinct_role', 'facade', 'generated_asset',
                   'protected_unique', 'needs_review')
SELECTION_RULE = ('canonical = role registry, else the only member covering all capabilities, '
                  'else the member with most active consumers; never size, mtime or name suffix')
TEXT_SUFFIXES = frozenset({'.py', '.md', '.ps1', '.psm1', '.yaml', '.yml', '.json', '.toml', '.txt',
                           '.ipynb', '.cfg', '.ini', '.sh', '.bat', '.cmd', '.html', '.js', '.ts',
                           '.css', '.rst', '.in'})
SEMANTIC_SUFFIXES = frozenset({'.py', '.md', '.ps1', '.psm1', '.yaml', '.yml', '.toml', '.sh', '.bat',
                               '.cmd', '.cfg', '.ini', '.ipynb', '.rst'})
DEFAULT_RECORD_ROOTS: Tuple[str, ...] = ('governance', 'data/maintenance', 'docs/audits',
                                         'docs/design', 'docs/plans')
MAX_TEXT_BYTES = 2*1024*1024
MIN_LINE_CHARS = 8
COMMON_LIMIT = 25          # a line/function shared by more files is boilerplate, not a clone signal
MIN_LINES = 15
LINE_OVERLAP = 0.8
MIN_SHARED_FUNCTIONS = 2
FUNCTION_OVERLAP = 0.6
MIN_FUNCTION_STATEMENTS = 3
PACKAGE_MARKER_BYTES = 512
CAPABILITY_LIST_LIMIT = 40
PATH_TOKEN = re.compile(r'[A-Za-z0-9_.\-/\\]*[A-Za-z0-9_\-]\.[A-Za-z0-9]{1,8}\b')
MODULE_TOKEN = re.compile(r'\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\b')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def module_name(rel: str) -> Optional[str]:
    if not rel.endswith('.py'):
        return None
    parts = rel[:-3].split('/')
    if parts[-1] == '__init__':
        parts = parts[:-1]
    if not parts or not all(p.isidentifier() for p in parts):
        return None
    return '.'.join(parts)


# --- registry ----------------------------------------------------------------

@dataclass
class Rules:
    protected: List[Tuple[str, str]]
    data_identity: Dict[str, str]
    evidence_snapshots: Dict[str, str]
    per_package: Dict[str, str]
    facades: Dict[str, dict]
    generated: Dict[str, dict]
    roles: Dict[str, str]
    record_roots: Tuple[str, ...]
    errors: List[str]

    def protected_reason(self, rel: str) -> Optional[str]:
        for root, reason in DEPENDENCY_ROOTS.items():
            if under(rel, root):
                return reason
        for pattern, reason in self.protected:
            if fnmatchcase(rel, pattern) or under(rel, pattern):
                return reason
        return None

    def special_reason(self, rel: str) -> Optional[str]:
        for root, reason in self.data_identity.items():
            if under(rel, root):
                return f'data identity by provenance ({root}): {reason}'
        for root, reason in self.evidence_snapshots.items():
            if under(rel, root):
                return f'evidence snapshot ({root}): {reason}'
        for pattern, reason in self.per_package.items():
            if fnmatchcase(rel, pattern):
                return f'per-package file ({pattern}): {reason}'
        return None

    def is_record(self, rel: str) -> bool:
        return any(under(rel, root) for root in self.record_roots) or self.special_reason(rel) is not None

    def role_of(self, rel: str) -> Optional[str]:
        for role, path in self.roles.items():
            if path == rel:
                return role
        return None


def load_rules(registry: Mapping) -> Rules:
    section = consolidation_section(registry)
    errors: List[str] = []
    roles: Dict[str, str] = {}
    owners: Dict[str, str] = {}
    for role, path in (section.get('canonical_sources') or {}).items():
        if not isinstance(path, str):
            errors.append(f'role {role} must name exactly one canonical path')
            continue
        rel = norm(path)
        if rel in owners:
            errors.append(f'{rel} is canonical for two roles: {owners[rel]} and {role}')
        owners[rel] = str(role)
        roles[str(role)] = rel
    protected = [(norm(str(row['pattern'])), str(row.get('reason', 'protected')))
                 for row in section.get('protected') or []]
    record = tuple(norm(str(p)) for p in section.get('record_roots', DEFAULT_RECORD_ROOTS))
    return Rules(
        protected=protected,
        data_identity={norm(str(k)): str(v) for k, v in (section.get('data_identity_roots') or {}).items()},
        evidence_snapshots={norm(str(k)): str(v) for k, v in (section.get('evidence_snapshot_roots') or {}).items()},
        per_package={str(k): str(v) for k, v in (section.get('per_package_files') or {}).items()},
        facades={norm(str(k)): dict(v or {}) for k, v in (section.get('facades') or {}).items()},
        generated={norm(str(k)): dict(v or {}) for k, v in (section.get('generated_assets') or {}).items()},
        roles=roles, record_roots=record, errors=errors)


# --- content features ----------------------------------------------------------

def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_bytes().decode('utf-8')
    except (OSError, UnicodeDecodeError):
        return None


def notebook_lines(text: str) -> List[str]:
    try:
        cells = json.loads(text).get('cells', [])
    except (ValueError, AttributeError):
        return text.splitlines()
    lines: List[str] = []
    for cell in cells:
        source = cell.get('source', '')
        lines += (''.join(source) if isinstance(source, list) else str(source)).splitlines()
    return lines


def normalized_lines(rel: str, text: str) -> Set[str]:
    raw = notebook_lines(text) if rel.endswith('.ipynb') else text.splitlines()
    lines = set()
    for line in raw:
        stripped = ' '.join(line.split())
        if len(stripped) >= MIN_LINE_CHARS and any(ch.isalnum() for ch in stripped):
            lines.add(stripped)
    return lines


def _strip_docstring(body: List[ast.stmt]) -> List[ast.stmt]:
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def _body_hash(node: ast.AST) -> str:
    body = _strip_docstring(list(getattr(node, 'body', [])))
    dump = '\n'.join(ast.dump(stmt, annotate_fields=False) for stmt in body)
    return hashlib.sha256(dump.encode('utf-8')).hexdigest()


def python_capabilities(text: str) -> Optional[Dict[str, Tuple[str, int]]]:
    """Map capability name -> (normalized body hash, statement count)."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    caps: Dict[str, Tuple[str, int]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            caps[node.name] = (_body_hash(node), len(_strip_docstring(node.body)))
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        caps[f'{node.name}.{item.name}'] = (_body_hash(item), len(_strip_docstring(item.body)))
    return caps


@dataclass
class Features:
    lines: Set[str]
    caps: Optional[Dict[str, Tuple[str, int]]]


# --- facades -------------------------------------------------------------------

def _is_main_guard(node: ast.If) -> bool:
    test = node.test
    return (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name) and test.left.id == '__name__')


def _delegating_call(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        return True
    return isinstance(stmt, ast.Raise)


def facade_findings(text: str) -> List[str]:
    """Statements that make a registered facade more than a delegation bridge."""
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [f'unparseable: {exc.msg}']
    findings: List[str] = []
    for node in _strip_docstring(list(tree.body)):
        line = getattr(node, 'lineno', 0)
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, (ast.Call, ast.Constant)):
            continue
        if isinstance(node, ast.If) and (_is_main_guard(node) or all(_delegating_call(s) for s in node.body)):
            if all(_delegating_call(s) or isinstance(s, (ast.Assign, ast.Import, ast.ImportFrom))
                   for s in node.body + node.orelse):
                continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = _strip_docstring(node.body)
            if len(body) == 1 and _delegating_call(body[0]):
                continue
            findings.append(f'line {line}: function {node.name} implements logic ({len(body)} statements)')
            continue
        findings.append(f'line {line}: {type(node).__name__} is not a delegation statement')
    return findings


# --- inventory ------------------------------------------------------------------

@dataclass
class DuplicateGroup:
    group_id: str
    kind: str
    logical_role: Optional[str]
    paths: List[str]
    hashes: Dict[str, str]
    consumers: Dict[str, List[str]]
    active_consumers: Dict[str, List[str]]
    canonical_path: Optional[str]
    canonical_basis: Optional[str]
    classification: str
    reasons: List[str]
    preserved_paths: Dict[str, str] = field(default_factory=dict)
    unique_capabilities: Dict[str, List[str]] = field(default_factory=dict)
    unique_counts: Dict[str, int] = field(default_factory=dict)
    divergent_capabilities: Dict[str, List[str]] = field(default_factory=dict)
    similarity: Optional[float] = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class DuplicateInventory:
    schema_version: int
    scope: dict
    exact_groups: List[DuplicateGroup]
    semantic_candidates: List[DuplicateGroup]
    facades: List[dict]
    facade_violations: List[dict]
    protected_documents: List[dict]
    generated_sources_missing: List[str]
    registry_errors: List[str]
    classification_counts: Dict[str, int]

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload['exact_groups'] = [g.as_dict() for g in self.exact_groups]
        payload['semantic_candidates'] = [g.as_dict() for g in self.semantic_candidates]
        return payload


class _ConsumerIndex:
    def __init__(self) -> None:
        self.paths: Dict[str, Set[str]] = defaultdict(set)
        self.modules: Dict[str, Set[str]] = defaultdict(set)

    def add(self, rel: str, text: str) -> None:
        base = rel.rsplit('/', 1)[0] if '/' in rel else ''
        for token in set(PATH_TOKEN.findall(text)):
            plain = norm(token)
            if not plain:
                continue
            self.paths[plain].add(rel)
            if base and not token.startswith(('/', '\\')):
                self.paths[norm(f'{base}/{token}')].add(rel)
        for token in set(MODULE_TOKEN.findall(text)):
            self.modules[token].add(rel)

    def of(self, rel: str) -> Set[str]:
        found = set(self.paths.get(rel, ()))
        name = module_name(rel)
        if name:
            found |= self.modules.get(name, set())
        found.discard(rel)
        return found


def _union_find(pairs: Iterable[Tuple[str, str]]) -> List[List[str]]:
    parent: Dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for left, right in pairs:
        a, b = find(left), find(right)
        if a != b:
            parent[max(a, b)] = min(a, b)
    groups: Dict[str, List[str]] = defaultdict(list)
    for item in parent:
        groups[find(item)].append(item)
    return sorted(sorted(members) for members in groups.values())


def _semantic_pairs(features: Mapping[str, Features]) -> Dict[Tuple[str, str], float]:
    by_line: Dict[str, List[str]] = defaultdict(list)
    by_func: Dict[str, List[str]] = defaultdict(list)
    for rel, feat in features.items():
        for line in feat.lines:
            by_line[line].append(rel)
        for digest, count in set((feat.caps or {}).values()):
            if count >= MIN_FUNCTION_STATEMENTS:
                by_func[digest].append(rel)
    shared_lines: Dict[Tuple[str, str], int] = defaultdict(int)
    for members in by_line.values():
        if 1 < len(members) <= COMMON_LIMIT:
            members = sorted(members)
            for i, left in enumerate(members):
                for right in members[i + 1:]:
                    shared_lines[(left, right)] += 1
    shared_funcs: Dict[Tuple[str, str], int] = defaultdict(int)
    for members in by_func.values():
        if 1 < len(members) <= COMMON_LIMIT:
            members = sorted(members)
            for i, left in enumerate(members):
                for right in members[i + 1:]:
                    shared_funcs[(left, right)] += 1
    pairs: Dict[Tuple[str, str], float] = {}
    for (left, right), count in shared_lines.items():
        smaller = min(len(features[left].lines), len(features[right].lines))
        if smaller >= MIN_LINES and count/smaller >= LINE_OVERLAP:
            pairs[(left, right)] = round(count/smaller, 4)
    for (left, right), count in shared_funcs.items():
        def nontrivial(rel: str) -> int:
            return len({d for d, c in (features[rel].caps or {}).values() if c >= MIN_FUNCTION_STATEMENTS})
        smaller = min(nontrivial(left), nontrivial(right))
        if count >= MIN_SHARED_FUNCTIONS and smaller and count/smaller >= FUNCTION_OVERLAP:
            pairs[(left, right)] = max(pairs.get((left, right), 0.0), round(count/smaller, 4))
    return pairs


def _capability_delta(member: Features, others: Sequence[Features]) -> Tuple[List[str], List[str], int]:
    """(unique, divergent, unique_count) of ``member`` against ``others`` combined."""
    if member.caps is not None and all(o.caps is not None for o in others):
        theirs: Dict[str, Set[str]] = defaultdict(set)
        for other in others:
            for name, (digest, _) in other.caps.items():
                theirs[name].add(digest)
        unique = sorted(n for n in member.caps if n not in theirs)
        divergent = sorted(n for n, (d, _) in member.caps.items() if n in theirs and d not in theirs[n])
        return unique, divergent, len(unique)
    covered: Set[str] = set().union(*(o.lines for o in others)) if others else set()
    unique_lines = sorted(member.lines - covered)
    return [f'line: {line[:100]}' for line in unique_lines[:CAPABILITY_LIST_LIMIT]], [], len(unique_lines)


def _scannable_text(root: Path, rel: str, size: int, rules: Rules) -> Optional[str]:
    """Text of a file the consumer and feature scans may read, else None."""
    if os.path.splitext(rel)[1].lower() not in TEXT_SUFFIXES or size > MAX_TEXT_BYTES:
        return None
    if rules.special_reason(rel) and not any(under(rel, r) for r in rules.evidence_snapshots):
        return None  # data identity / per-package bytes are neither consumers nor code
    return read_text(root/rel)


def find_duplicate_candidates(root: Path, registry_path: Path) -> DuplicateInventory:
    root = Path(root)
    registry = load_registry(registry_path)
    rules = load_rules(registry)
    exclusions = scan_exclusions(registry)
    walk = walk_tree(root, exclusions)

    hashes: Dict[str, str] = {}
    zero = 0
    for rel, size in walk.files:
        if size == 0:
            zero += 1
            continue
        try:
            hashes[rel] = sha256_file(root/rel)
        except OSError:
            walk.unreadable.append(rel)
    by_hash: Dict[str, List[str]] = defaultdict(list)
    for rel, digest in hashes.items():
        by_hash[digest].append(rel)

    index = _ConsumerIndex()
    features: Dict[str, Features] = {}
    sizes = dict(walk.files)
    for rel in sorted(hashes):
        text = _scannable_text(root, rel, sizes.get(rel, 0), rules)
        if text is None:
            continue
        if not rules.is_record(rel):
            index.add(rel, text)
        suffix = os.path.splitext(rel)[1].lower()
        if suffix in SEMANTIC_SUFFIXES and rules.protected_reason(rel) is None:
            features[rel] = Features(normalized_lines(rel, text),
                                     python_capabilities(text) if suffix == '.py' else None)

    exact: List[DuplicateGroup] = []
    for digest, members in sorted(by_hash.items(), key=lambda item: sorted(item[1])[0]):
        if len(members) > 1:
            exact.append(_classify(f'X{len(exact) + 1:04d}', 'exact', sorted(members), hashes,
                                   index, features, rules, root, sizes, None))

    representatives = {sorted(members)[0] for members in by_hash.values()}
    semantic_feats = {rel: feat for rel, feat in features.items() if rel in representatives}
    pairs = _semantic_pairs(semantic_feats)
    semantic: List[DuplicateGroup] = []
    for members in _union_find(pairs):
        score = max(v for (a, b), v in pairs.items() if a in members and b in members)
        semantic.append(_classify(f'S{len(semantic) + 1:04d}', 'semantic', members, hashes,
                                  index, features, rules, root, sizes, score))

    facades, violations = _facade_rows(root, rules, index)
    protected_docs = [{'path': rel, 'sha256': hashes.get(rel, hashlib.sha256(b'').hexdigest()),
                       'reason': rules.protected_reason(rel), 'classification': 'protected_unique'}
                      for rel, _ in walk.files if rules.protected_reason(rel)]
    missing_sources = sorted({norm(str(spec.get('source', ''))) for asset, spec in rules.generated.items()
                              if spec.get('source') and not (root/norm(str(spec['source']))).is_file()})
    counts = {name: 0 for name in CLASSIFICATIONS}
    for group in exact + semantic:
        counts[group.classification] += 1
    counts['facade'] += len(facades)
    scope = {
        'scanned_files': len(walk.files),
        'hashed_files': len(hashes),
        'zero_byte_files': zero,
        'zero_byte_rule': 'zero-byte files carry no content to duplicate; identity is the path',
        'excluded_scope': excluded_scope_rows(root, exclusions, walk),
        'links_not_followed': walk.links_not_followed,
        'unreadable': walk.unreadable,
        'semantic_scope': {
            'suffixes': sorted(SEMANTIC_SUFFIXES), 'files_compared': len(semantic_feats),
            'excluded': 'data identity roots, per-package files, protected documents, files over 2 MiB',
            'line_overlap_threshold': LINE_OVERLAP, 'function_overlap_threshold': FUNCTION_OVERLAP,
            'boilerplate_limit_files': COMMON_LIMIT,
            'note': 'similarity proposes review only; it never authorizes a removal',
        },
        'consumer_rule': ('a consumer names the exact relative path (or the dotted module); '
                          'mentions inside record roots are not active consumers; basename-only mentions are not detected'),
        'record_roots': list(rules.record_roots),
    }
    return DuplicateInventory(SCHEMA_VERSION, scope, exact, semantic, facades, violations, protected_docs,
                              missing_sources, rules.errors, counts)


def _facade_rows(root: Path, rules: Rules, index: _ConsumerIndex) -> Tuple[List[dict], List[dict]]:
    rows: List[dict] = []
    for rel, spec in sorted(rules.facades.items()):
        text = read_text(root/rel)
        findings = ['facade file is missing'] if text is None else facade_findings(text)
        canonical = norm(str(spec.get('canonical', '')))
        consumers = sorted(index.of(rel))
        rows.append({'path': rel, 'canonical': canonical, 'reason': spec.get('reason'),
                     'canonical_exists': bool(canonical) and (root/canonical).is_file(),
                     'has_business_logic': bool(findings), 'findings': findings,
                     'consumers': consumers,
                     'active_consumers': [c for c in consumers if not rules.is_record(c)],
                     'classification': 'facade'})
    violations = [row for row in rows if row['has_business_logic'] or not row['canonical_exists']]
    return rows, violations


def _classify(group_id: str, kind: str, members: List[str], hashes: Mapping[str, str],
              index: _ConsumerIndex, features: Mapping[str, Features], rules: Rules, root: Path,
              sizes: Mapping[str, int], score: Optional[float]) -> DuplicateGroup:
    consumers = {rel: sorted(index.of(rel)) for rel in members}
    active = {rel: [c for c in found if not rules.is_record(c) and c not in members]
              for rel, found in consumers.items()}
    group = DuplicateGroup(group_id, kind, None, members, {rel: hashes[rel] for rel in members}, consumers,
                           active, None, None, 'needs_review', [], similarity=score)
    protected = {rel: rules.protected_reason(rel) for rel in members if rules.protected_reason(rel)}
    if protected:
        group.classification = 'protected_unique'
        group.preserved_paths = protected
        group.reasons.append('protected members are never removed: ' + '; '.join(sorted(set(protected.values()))))
        return group
    special = {rel: rules.special_reason(rel) for rel in members if rules.special_reason(rel)}
    group.preserved_paths = dict(special)
    candidates = [rel for rel in members if rel not in special]
    if len(candidates) <= 1:
        group.classification = 'distinct_role'
        group.reasons += sorted(set(special.values()))
        return group
    if all(rel.rsplit('/', 1)[-1] == '__init__.py' for rel in candidates) and \
            all(sizes.get(rel, 0) <= PACKAGE_MARKER_BYTES for rel in candidates):
        group.classification = 'distinct_role'
        group.reasons.append('package markers of distinct packages; a package identity is its directory')
        return group
    facade_members = [rel for rel in candidates if rel in rules.facades]
    if facade_members:
        group.classification = 'facade'
        group.reasons.append('registered facades are bridges with their own role: ' + ', '.join(facade_members))
        return group
    roles = {rel: rules.role_of(rel) for rel in candidates if rules.role_of(rel)}
    generated = [rel for rel in candidates if rel in rules.generated]
    if len(set(roles.values())) > 1:
        group.classification = 'distinct_role'
        group.reasons.append('members are canonical for different registered roles: '
                             + ', '.join(f'{p}={r}' for p, r in sorted(roles.items())))
        return group
    canonical, basis = None, None
    if generated:
        if len(generated) > 1:
            group.reasons.append('several registered generated assets share bytes; review the generators')
            return group
        canonical, basis = generated[0], 'generated_asset_registry'
        group.logical_role = f'generated:{canonical}'
        source = norm(str(rules.generated[canonical].get('source', '')))
        if source and not (root/source).is_file():
            group.reasons.append(f'generator source missing: {source}')
    elif roles:
        canonical, basis = next(iter(roles)), 'role_registry'
        group.logical_role = roles[canonical]
    feats = {rel: features.get(rel) for rel in candidates}
    have_features = all(f is not None for f in feats.values())
    if kind == 'semantic' and have_features:
        for rel in candidates:
            others = [feats[o] for o in candidates if o != rel]
            unique, divergent, count = _capability_delta(feats[rel], others)
            group.unique_capabilities[rel] = unique
            group.divergent_capabilities[rel] = divergent
            group.unique_counts[rel] = count
        if canonical is None:
            covering = [rel for rel in candidates
                        if all(not _capability_delta(feats[o], [feats[rel]])[2]
                               and not _capability_delta(feats[o], [feats[rel]])[1]
                               for o in candidates if o != rel)]
            if len(covering) == 1:
                canonical, basis = covering[0], 'coverage'
    if canonical is None:
        ranked = sorted(candidates, key=lambda rel: -len(active[rel]))
        if len(active[ranked[0]]) > len(active[ranked[1]]):
            canonical, basis = ranked[0], 'consumers'
    if canonical is None:
        group.reasons.append('no registered role, covering member or consumer majority; '
                             'size/date/name are not admissible tie-breakers')
        return group
    group.canonical_path, group.canonical_basis = canonical, basis
    if kind == 'semantic':
        if have_features:
            for rel in candidates:
                if rel == canonical:
                    continue
                unique, divergent, count = _capability_delta(feats[rel], [feats[canonical]])
                group.unique_capabilities[rel] = unique
                group.divergent_capabilities[rel] = divergent
                group.unique_counts[rel] = count
            group.unique_capabilities[canonical] = []
            group.divergent_capabilities[canonical] = []
        pending = [rel for rel in candidates if rel != canonical and
                   (group.unique_counts.get(rel, 1) or group.divergent_capabilities.get(rel))]
        if pending or not have_features:
            group.reasons.append('non-canonical members hold unique or divergent content; merge before removal: '
                                 + ', '.join(pending))
            return group
    group.classification = 'generated_asset' if generated else 'redundant_clone'
    group.reasons.append(f'canonical chosen by {basis}')
    return group


# --- plan --------------------------------------------------------------------------

@dataclass
class CanonicalizationPlan:
    schema_version: int
    selection_rule: str
    actions: List[dict]
    removed_paths: List[dict]
    blocked: List[dict]
    blocked_unique_content: List[dict]

    def as_dict(self) -> dict:
        return asdict(self)


def build_canonicalization_plan(inventory: DuplicateInventory,
                                coverage_rows: Optional[Iterable[Mapping]]) -> CanonicalizationPlan:
    claims = {norm(str(row['path'])): dict(row) for row in coverage_rows or []}
    used: Set[str] = set()
    actions: List[dict] = []
    removed: List[dict] = []
    blocked: List[dict] = []
    unique_blocked: List[dict] = []
    facade_paths = {row['path'] for row in inventory.facades}
    for group in inventory.exact_groups + inventory.semantic_candidates:
        canonical = group.canonical_path
        movable = [rel for rel in group.paths if rel != canonical and rel not in group.preserved_paths]
        if group.classification == 'protected_unique':
            for rel in group.paths:
                used.add(rel)
                blocked.append({'path': rel, 'group_id': group.group_id,
                                'reasons': ['protected: never deleted; consolidate through the authorized Word flow']})
            continue
        if group.classification in ('distinct_role', 'facade'):
            continue
        if group.classification == 'needs_review':
            for rel in movable:
                used.add(rel)
                row = {'path': rel, 'group_id': group.group_id, 'canonical_path': canonical,
                       'reasons': list(group.reasons) or ['needs review']}
                if group.unique_counts.get(rel) or group.divergent_capabilities.get(rel):
                    unique_blocked.append({**row, 'unique_capabilities': group.unique_capabilities.get(rel, []),
                                           'divergent_capabilities': group.divergent_capabilities.get(rel, [])})
                blocked.append(row)
            continue
        action = {'group_id': group.group_id, 'logical_role': group.logical_role, 'canonical_path': canonical,
                  'canonical_basis': group.canonical_basis, 'canonical_sha256': group.hashes[canonical],
                  'removed_paths': [], 'blocked_paths': []}
        source_missing = [r for r in group.reasons if r.startswith('generator source missing')]
        for rel in movable:
            used.add(rel)
            reasons = list(source_missing)
            if rel in facade_paths:
                reasons.append('registered facade')
            if group.active_consumers.get(rel):
                reasons.append('active consumers not updated: ' + ', '.join(group.active_consumers[rel]))
            if group.kind == 'exact' and group.hashes[rel] == group.hashes[canonical]:
                evidence, covered = 'sha256 identical to canonical', True
            else:
                claim = claims.get(rel)
                covered = bool(claim and claim.get('coverage_verified') is True
                               and norm(str(claim.get('canonical_path', ''))) == canonical
                               and not group.unique_counts.get(rel) and not group.divergent_capabilities.get(rel))
                evidence = str(claim.get('evidence', 'coverage row')) if claim else ''
                if not covered:
                    reasons.append('coverage not verified against the canonical file')
            if reasons:
                blocked.append({'path': rel, 'group_id': group.group_id, 'canonical_path': canonical,
                                'reasons': reasons})
                action['blocked_paths'].append(rel)
                continue
            row = {'path': rel, 'sha256': group.hashes[rel], 'canonical_path': canonical,
                   'canonical_sha256': group.hashes[canonical], 'coverage_verified': covered,
                   'evidence': evidence, 'logical_role': group.logical_role, 'group_id': group.group_id}
            removed.append(row)
            action['removed_paths'].append(rel)
        actions.append(action)
    for rel, claim in sorted(claims.items()):
        if rel not in used:
            blocked.append({'path': rel, 'group_id': None, 'canonical_path': claim.get('canonical_path'),
                            'reasons': ['coverage row ignored: path is not a removable member of a clone group']})
    return CanonicalizationPlan(SCHEMA_VERSION, SELECTION_RULE, actions, removed, blocked, unique_blocked)


def _is_reparse(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def _current_consumer_index(root: Path, registry: Mapping, rules: Rules) -> _ConsumerIndex:
    """Rebuild the inventory's active-consumer index from the tree as it is now."""
    index = _ConsumerIndex()
    for rel, size in walk_tree(root, scan_exclusions(registry)).files:
        if size == 0 or rules.is_record(rel):
            continue
        text = _scannable_text(root, rel, size, rules)
        if text is not None:
            index.add(rel, text)
    return index


def _new_consumers(row: Mapping, rel: str, planned: Mapping[str, Mapping], index: _ConsumerIndex,
                   root: Path) -> List[str]:
    """Current consumers of ``rel``; only the canonical or an unchanged group member is exempt."""
    canonical = norm(str(row.get('canonical_path', '')))
    found: List[str] = []
    for consumer in sorted(index.of(rel)):
        sibling = planned.get(consumer)
        if consumer == canonical or (sibling is not None and sibling.get('group_id') == row.get('group_id')
                                     and sha256_file(root/consumer) == sibling.get('sha256')):
            continue
        found.append(consumer)
    return found


def verify_plan(plan: Mapping, root: Path, registry_path: Optional[Path] = None) -> List[dict]:
    """Fresh go/no-go for each removed path of a plan (no deletion here)."""
    root = Path(root).resolve()
    registry_path = Path(registry_path) if registry_path else root/'governance/repository_layout.yaml'
    registry = load_registry(registry_path)
    rules = load_rules(registry)
    decisions: List[dict] = []
    rows = plan.get('removed_paths') or []
    planned = {norm(str(row.get('path', ''))): row for row in rows}
    index = _current_consumer_index(root, registry, rules) if rows else _ConsumerIndex()
    for row in rows:
        raw = str(row.get('path', ''))
        rel = norm(raw)
        reasons: List[str] = []
        target = root/rel
        if not rel or os.path.isabs(raw) or rel.startswith('..') or '..' in raw.replace('\\', '/').split('/'):
            reasons.append('path escapes the project root')
        else:
            parts = Path(rel).parts
            for depth in range(1, len(parts) + 1):
                if _is_reparse(root.joinpath(*parts[:depth])):
                    reasons.append('path crosses a link or reparse point')
                    break
            try:
                inside = os.path.commonpath([str(root), str(target.resolve())]) == str(root)
            except ValueError:
                inside = False
            if not inside:
                reasons.append('path resolves outside the project root')
        if not reasons:
            if rules.protected_reason(rel):
                reasons.append(f'protected: {rules.protected_reason(rel)}')
            if rules.special_reason(rel):
                reasons.append(rules.special_reason(rel))
            if rel in rules.facades or rules.role_of(rel) or \
                    rel in {norm(str(s.get('source', ''))) for s in rules.generated.values()}:
                reasons.append('registered canonical, facade or generator source')
            if row.get('coverage_verified') is not True:
                reasons.append('coverage_verified is not true')
            if not target.is_file():
                reasons.append('target is missing or not a regular file')
            elif sha256_file(target) != row.get('sha256'):
                reasons.append('target changed since the plan (sha256 mismatch)')
            canonical = norm(str(row.get('canonical_path', '')))
            if not canonical or canonical == rel or not (root/canonical).is_file():
                reasons.append('canonical file is missing')
            elif sha256_file(root/canonical) != row.get('canonical_sha256'):
                reasons.append('canonical changed since the plan (sha256 mismatch)')
            consumers = _new_consumers(row, rel, planned, index, root)
            if consumers:
                reasons.append('active consumers not updated: ' + ', '.join(consumers))
        decisions.append({'path': raw, 'absolute_path': str(target) if not reasons else None,
                          'sha256': row.get('sha256'), 'decision': 'blocked' if reasons else 'delete',
                          'reasons': reasons})
    return decisions


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('inventory', 'plan', 'verify'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--root', type=Path, default=Path('.'))
        cmd.add_argument('--registry', type=Path, default=None)
        if name == 'verify':
            cmd.add_argument('--plan', type=Path, required=True)
        else:
            cmd.add_argument('--out', type=Path, required=True)
        if name == 'plan':
            cmd.add_argument('--coverage', type=Path, default=None)
            cmd.add_argument('--inventory-out', type=Path, default=None)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    registry = args.registry or root/'governance/repository_layout.yaml'
    if args.command == 'verify':
        plan = json.loads(args.plan.read_text(encoding='utf-8-sig'))
        json.dump({'decisions': verify_plan(plan, root, registry)}, sys.stdout, ensure_ascii=False)
        return 0
    inventory = find_duplicate_candidates(root, registry)
    if args.command == 'inventory':
        _write_json(args.out, inventory.as_dict())
        return 0
    rows = json.loads(args.coverage.read_text(encoding='utf-8-sig')) if args.coverage else []
    plan = build_canonicalization_plan(inventory, rows)
    if args.inventory_out:
        _write_json(args.inventory_out, inventory.as_dict())
    _write_json(args.out, plan.as_dict())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
