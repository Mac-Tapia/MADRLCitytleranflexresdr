"""Inventory, plan and verify an explicit, content-preserving path migration.

No moves are made here. Windows execution is owned by rename_paths.ps1.
Historical JSON reports are provenance; their original paths and hashes stay
literal, while the alias registry resolves their current physical locations.
"""
from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
from urllib.parse import unquote, urlsplit

import yaml

TEXT_SUFFIXES = {'.py', '.md', '.yaml', '.yml', '.json', '.toml', '.ps1', '.bat',
                 '.cmd', '.sh', '.ipynb', '.tf', '.html', '.css', '.js', '.ts',
                 '.tsx', '.cfg', '.txt', '.ini', '.svg', '.mmd'}
LINK = re.compile(r'(!?\[[^\]\n]*\]\()([^\s)]+)([^)\n]*\))')
RESERVED = re.compile(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])$', re.I)
LONG_ID = re.compile(r'\d{6,}|\d{4}-\d{2}-\d{2}|[0-9a-f]{12,}')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_policy(policy):
    return yaml.safe_load(Path(policy).read_text(encoding='utf-8')) if not isinstance(policy, dict) else policy


def _linked(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def _under(path, prefix):
    return path == prefix.rstrip('/') or path.startswith(prefix.rstrip('/') + '/')


def _key(path):
    return unicodedata.normalize('NFC', path).casefold()


def safe_relative(value):
    value = str(value).replace('\\', '/')
    parts = PurePosixPath(value).parts
    if not value or value.startswith('/') or ':' in value or '..' in parts:
        raise ValueError('external or invalid relative path: ' + value)
    if any(part in {'.git', 'CityLearn', 'external', '.superpowers'} for part in parts):
        raise ValueError('protected path: ' + value)
    if _under(value, 'tools/skills'):
        raise ValueError('protected skills path: ' + value)
    return value.rstrip('/')


def name_reasons(path, is_dir, policy):
    name = PurePosixPath(path).name
    if path in policy.get('exceptions', {}) or name in policy.get('mandatory_names', ()):
        return []
    conventional = any(fnmatch.fnmatchcase(path, pattern) for pattern in policy.get('conventional_paths', {}))
    reasons = []
    if len(name) > (24 if is_dir else 40):
        reasons.append('length')
    if LONG_ID.search(name):
        reasons.append('long_identifier')
    spec_folder = is_dir and re.fullmatch(r'specs/\d{3}-[a-z_]+', path)
    pattern = r'[a-z0-9_.-]+' if conventional else r'[a-z0-9_.]+'
    if not spec_folder and not re.fullmatch(pattern, name):
        reasons.append('style')
    if RESERVED.fullmatch(name.split('.')[0]) or name.endswith(('.', ' ')):
        reasons.append('reserved')
    return reasons


def _immutable(path, policy):
    if path in policy.get('mutable_json_paths', ()):
        return False
    return any(_under(path, p) for p in policy.get('immutable_roots', ())) or any(
        fnmatch.fnmatchcase(path, pattern) for pattern in policy.get('immutable_patterns', ()))


def _secret(path):
    name = PurePosixPath(path).name.casefold()
    suffix = PurePosixPath(path).suffix
    return (name.startswith('.env') or name in {'credentials.json', 'token.json', 'storage_state.json'}
            or suffix in {'.pem', '.key', '.pfx', '.p12', '.secret'}
            or (suffix not in {'.py', '.ps1', '.md'} and any(
                marker in name for marker in ('secret', 'credential', 'password', 'token'))))


def inventory_names(root, policy_path, blocked_paths=()):
    root, policy = Path(root).resolve(), load_policy(policy_path)
    files, directories, candidates, excluded = [], [], [], []
    for folder, dirs, names in os.walk(root, followlinks=False):
        retained = []
        for name in sorted(dirs):
            path = Path(folder)/name
            relative = path.relative_to(root).as_posix()
            if (name in policy.get('excluded_components', ()) or
                    any(_under(relative, p) for p in policy.get('excluded_roots', ())) or _linked(path)):
                excluded.append(relative)
                continue
            retained.append(name)
            directories.append(relative)
            reasons = name_reasons(relative, True, policy)
            if reasons:
                candidates.append({'path': relative, 'kind': 'directory', 'reasons': reasons})
        dirs[:] = retained
        for name in sorted(names):
            path = Path(folder)/name
            relative = path.relative_to(root).as_posix()
            if _secret(relative) or _linked(path):
                excluded.append(relative)
                continue
            data = path.read_bytes()
            files.append({'path': relative, 'sha256': sha256(data), 'bytes': len(data),
                          'mtime_ns': path.stat().st_mtime_ns,
                          'immutable': _immutable(relative, policy)})
            reasons = name_reasons(relative, False, policy)
            if reasons:
                candidates.append({'path': relative, 'kind': 'file', 'reasons': reasons})
    return {'schema_version': 1, 'root': root.as_posix(),
            'created_at': datetime.now(timezone.utc).isoformat(), 'files': files,
            'directories': directories, 'candidates': candidates, 'excluded': excluded,
            'blocked_paths': list(blocked_paths)}


def _destination(path, proposals):
    if path in proposals:
        return proposals[path].rstrip('/')
    if path + '/' in proposals:
        return proposals[path + '/'].rstrip('/')
    parents = [old for old in proposals if old.endswith('/') and path.startswith(old)]
    if parents:
        old = max(parents, key=len)
        return proposals[old].rstrip('/') + '/' + path[len(old):]
    return path


def _local_link(root, consumer, target):
    target = unquote(target.strip('<>'))
    split = urlsplit(target)
    if split.scheme or split.netloc or not split.path or split.path.startswith('/'):
        return None
    candidate = Path(os.path.abspath(root/PurePosixPath(consumer).parent/split.path))
    try:
        return candidate.relative_to(root).as_posix(), split
    except ValueError:
        return None


def _rewrite_links(text, root, old_consumer, new_consumer, mapping):
    placeholders = {}

    def replace(match):
        resolved = _local_link(root, old_consumer, match[2])
        if resolved is None:
            return match[0]
        old_target, split = resolved
        new_target = _destination(old_target, mapping)
        if new_target == old_target and old_consumer == new_consumer:
            return match[0]
        relative = Path(os.path.relpath(root/new_target, (root/new_consumer).parent)).as_posix()
        if split.query:
            relative += '?' + split.query
        if split.fragment:
            relative += '#' + split.fragment
        placeholder = f'\x00LINK{len(placeholders)}\x00'
        placeholders[placeholder] = match[1] + relative + match[3]
        return placeholder

    return LINK.sub(replace, text), placeholders


def _replace_tokens(text, mapping):
    mapping = {old.rstrip('/'): new.rstrip('/') for old, new in mapping.items()}
    tokens = {}
    for old, new in mapping.items():
        old, new = old.rstrip('/'), new.rstrip('/')
        for before, after in ((old, new), (old.replace('/', '\\'), new.replace('/', '\\')),
                              (old.replace('/', '\\\\'), new.replace('/', '\\\\'))):
            if before != after:
                tokens[before] = after
        if old.endswith('.py'):
            tokens[old[:-3].replace('/', '.')] = new[:-3].replace('/', '.')
    old_counts = Counter(PurePosixPath(p.rstrip('/')).name for p in mapping)
    for old, new in mapping.items():
        old_name, new_name = PurePosixPath(old.rstrip('/')).name, PurePosixPath(new.rstrip('/')).name
        # A directory basename such as 'specs' has unrelated consumers at the
        # repository root. Only full paths/AST/link resolution can move it.
        if not PurePosixPath(old_name).suffix and len(old_name) < 9 and not re.match(r'\d{3}-', old_name):
            continue
        if old_counts[old_name] == 1 and old_name != new_name:
            tokens[old_name] = new_name
            old_path, new_path = PurePosixPath(old_name), PurePosixPath(new_name)
            if old_path.suffix and old_path.suffix == new_path.suffix:
                tokens[old_path.stem] = new_path.stem
    if not tokens:
        return text
    pattern = re.compile(r'(?<![\w])(?:' + '|'.join(re.escape(p) for p in sorted(tokens, key=len, reverse=True)) + r')(?![\w])')
    return pattern.sub(lambda m: tokens[m[0]], text)


def _rewrite_python_paths(text, root, consumer, mapping):
    """Resolve pathlib expressions without importing or executing consumers."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    values = {'__file__': str(root/consumer)}
    # These two imported constants are the project's documented Word path
    # contract. Resolve them without executing any Word patcher or imports.
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in {
                'thesis_word_canons', 'tools.thesis.thesis_word_canons'}:
            for alias in node.names:
                if alias.name in {'DOCS', 'REPO'}:
                    values[alias.asname or alias.name] = root/'docs' if alias.name == 'DOCS' else root

    def value(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
            return node.value
        if isinstance(node, ast.Name):
            return values.get(node.id)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'Path' and len(node.args) == 1:
                item = value(node.args[0])
                return Path(item) if isinstance(item, (str, Path)) else None
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'resolve' and not node.args:
                item = value(node.func.value)
                return Path(os.path.abspath(item)) if isinstance(item, Path) else None
        if isinstance(node, ast.Attribute):
            item = value(node.value)
            if isinstance(item, Path):
                if node.attr == 'parent':
                    return item.parent
                if node.attr == 'parents':
                    return item.parents
        if isinstance(node, ast.Subscript):
            item, index = value(node.value), value(node.slice)
            if isinstance(item, type(Path().parents)) and isinstance(index, int):
                try:
                    return item[index]
                except IndexError:
                    return None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left, right = value(node.left), value(node.right)
            if isinstance(left, Path) and isinstance(right, str):
                return left/right
        return None

    for _ in range(4):
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                result = value(node.value)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if result is not None:
                    for target in targets:
                        if isinstance(target, ast.Name):
                            values[target.id] = result
    lines = text.splitlines(keepends=True)
    starts, length = [], 0
    for line in lines:
        starts.append(length)
        length += len(line)

    def offset(line, column):
        return starts[line-1] + len(lines[line-1].encode('utf-8')[:column].decode('utf-8'))

    edits = []
    bases = [(name, path) for name, path in values.items() if name in {
        'ROOT', 'REPO', 'PROJECT_ROOT', 'DOCS', 'AUDIT_DIR'} and isinstance(path, Path)]
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
            continue
        item = value(node)
        if not isinstance(item, Path):
            continue
        try:
            old = item.relative_to(root).as_posix()
        except ValueError:
            continue
        new = _destination(old, mapping)
        if new == old:
            continue
        start, end = offset(node.lineno, node.col_offset), offset(node.end_lineno, node.end_col_offset)
        if any(start >= a and end <= b for a, b, _ in edits):
            continue
        for name, base in sorted(bases, key=lambda pair: len(pair[1].parts), reverse=True):
            try:
                relative = (root/new).relative_to(base)
            except ValueError:
                continue
            replacement = name + ''.join(' / ' + repr(part) for part in relative.parts)
            if replacement != name:
                edits.append((start, end, replacement))
                break
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def plan_reference_updates(rename_map, *, inventory, policy):
    root = Path(inventory['root'])
    mapping = dict(rename_map)
    updates, provenance = [], []
    for item in inventory['files']:
        old = item['path']
        path = root/old
        if path.suffix not in TEXT_SUFFIXES and not path.name.startswith('.'):
            continue
        raw = path.read_bytes()
        if sha256(raw) != item['sha256']:
            raise ValueError('inventory_stale:' + old)
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        new = _destination(old, mapping)
        structured = _rewrite_python_paths(text, root, old, mapping) if path.suffix == '.py' else text
        protected, placeholders = _rewrite_links(structured, root, old, new, mapping)
        updated = _replace_tokens(protected, mapping)
        for key, value in placeholders.items():
            updated = updated.replace(key, value)
        if updated == text:
            continue
        if item['immutable']:
            provenance.append({'path': old, 'role': 'immutable_provenance',
                               'resolution': 'data/maintenance/names/aliases.json'})
            continue
        data = updated.encode('utf-8')
        updates.append({'old_path': old, 'new_path': new,
                        'before_sha256': sha256(raw), 'after_sha256': sha256(data),
                        'before_base64': base64.b64encode(raw).decode('ascii'),
                        'after_base64': base64.b64encode(data).decode('ascii')})
    return updates, provenance


def reference_bytes(reference):
    return base64.b64decode(reference['after_base64'])


def build_rename_map(inventory, proposals, *, policy=None):
    policy = load_policy(policy or {})
    root = Path(inventory['root'])
    proposals = dict(proposals)
    duplicates = policy.get('duplicates', {})
    mapping = {**proposals, **duplicates}
    files = {item['path']: item for item in inventory['files']}
    moves, consolidated, seen = [], [], {}
    for old, item in files.items():
        new = _destination(old, proposals)
        if new == old:
            continue
        safe_relative(old)
        safe_relative(new)
        for i, component in enumerate(PurePosixPath(new).parts):
            partial = '/'.join(PurePosixPath(new).parts[:i+1])
            if name_reasons(partial, i < len(PurePosixPath(new).parts)-1, policy):
                raise ValueError('invalid target name: ' + new)
        if any(_under(old, b) for b in inventory.get('blocked_paths', ())):
            raise ValueError('active source: ' + old)
        key = _key(new)
        if key in seen:
            raise ValueError('destination collision: ' + new)
        occupied = [p for p in files if _key(p) == key and p != old]
        if occupied or ((root/new).exists() and _key(old) != key):
            raise ValueError('occupied destination: ' + new)
        seen[key] = old
        moves.append({'old_path': old, 'new_path': new, 'source_hash': item['sha256'],
                      'role': 'canonical', 'state': 'planned', 'bytes': item['bytes']})
    for old, canonical in duplicates.items():
        if old not in files:
            continue
        safe_relative(old)
        if canonical not in files or files[canonical]['sha256'] != files[old]['sha256']:
            raise ValueError('duplicate content mismatch: ' + old)
        consolidated.append({'old_path': old, 'new_path': _destination(canonical, proposals),
                             'source_hash': files[old]['sha256'], 'role': 'identical_duplicate'})
    # Resolve all file and directory aliases in one pass; no cascaded moves.
    aliases = {p: _destination(p, proposals) for p in [*files, *inventory['directories']]}
    aliases.update({old: _destination(new, proposals) for old, new in duplicates.items()})
    aliases = {old: new for old, new in aliases.items() if old != new}
    aliases.update({old: new for old, new in mapping.items() if old.endswith('/')})
    aliases.update({old: new for old, new in proposals.items() if old not in files and not old.endswith('/')})
    updates, provenance = plan_reference_updates(aliases, inventory=inventory, policy=policy)
    touched = {m['old_path'] for m in moves} | {u['old_path'] for u in updates} | {d['old_path'] for d in consolidated}
    if any(any(_under(p, blocked) for blocked in inventory.get('blocked_paths', ())) for p in touched):
        raise ValueError('active consumer blocks batch')
    old_dirs = set()
    for item in moves + consolidated:
        parent = PurePosixPath(item['old_path']).parent
        while str(parent) != '.':
            old_dirs.add(parent.as_posix())
            parent = parent.parent
    absent = [old for old in proposals if not any(_under(p, old) for p in files)]
    return {'schema_version': 1, 'root': inventory['root'], 'created_at': inventory['created_at'],
            'moves': moves, 'duplicates': consolidated, 'references': updates,
            'aliases': aliases, 'provenance_references': provenance, 'absent_proposals': absent,
            'cleanup_directories': sorted(old_dirs, key=lambda p: (-p.count('/'), p)),
            'baseline_link_issues': audit_local_links(root, policy)}


def audit_local_links(root, policy):
    root = Path(root).resolve()
    issues = []
    inventory = inventory_names(root, policy)
    for item in inventory['files']:
        if not item['path'].endswith('.md') or item['immutable']:
            continue
        text = (root/item['path']).read_text(encoding='utf-8')
        # Code fences contain examples and regular-expression literals, not links.
        text = re.sub(r'```[\s\S]*?```', '', text)
        for match in LINK.finditer(text):
            resolved = _local_link(root, item['path'], match[2])
            if resolved and not (root/resolved[0]).exists():
                issues.append({'path': item['path'], 'target': match[2], 'reason': 'missing'})
    return issues


def verify_migration(root):
    root = Path(root).resolve()
    path = root/'data/maintenance/names/map.json'
    errors = []
    if not path.is_file():
        return {'verified': False, 'errors': ['migration_map_missing']}
    batch = json.loads(path.read_text(encoding='utf-8-sig'))
    if Path(batch['root']).resolve() != root:
        return {'verified': False, 'errors': ['migration_root_mismatch']}
    updates = {r['old_path']: r for r in batch['references']}
    for move in batch['moves']:
        old, new = safe_relative(move['old_path']), safe_relative(move['new_path'])
        expected = updates.get(old, {}).get('after_sha256', move['source_hash'])
        if not (root/new).is_file() or file_hash(root/new) != expected:
            errors.append('moved_content_mismatch:' + new)
        if _key(old) != _key(new) and (root/old).exists():
            errors.append('old_source_present:' + old)
    for ref in batch['references']:
        path_ref = root/safe_relative(ref['new_path'])
        if not path_ref.is_file() or file_hash(path_ref) != ref['after_sha256']:
            errors.append('consumer_mismatch:' + ref['new_path'])
    for duplicate in batch['duplicates']:
        current = root/safe_relative(duplicate['new_path'])
        if ((root/safe_relative(duplicate['old_path'])).exists() or not current.is_file()
                or file_hash(current) != duplicate['source_hash']):
            errors.append('duplicate_unresolved:' + duplicate['old_path'])
    result_path = root/'data/maintenance/names/results.json'
    receipt = json.loads(result_path.read_text(encoding='utf-8-sig')) if result_path.is_file() else {}
    if receipt.get('status') != 'executed' or receipt.get('manifest_sha256') != file_hash(path):
        errors.append('native_execution_receipt_missing_or_stale')
    late_path = root/'data/maintenance/names/registry_updates.json'
    if late_path.is_file():
        late = json.loads(late_path.read_text(encoding='utf-8'))
        if late['native_map_sha256'] != file_hash(path):
            errors.append('late_consumer_map_mismatch')
        for item in late['files']:
            current = root/safe_relative(item['path'])
            if not current.is_file() or file_hash(current) != item['after_sha256']:
                errors.append('late_consumer_mismatch:' + item['path'])
    return {'verified': not errors, 'errors': errors, 'moves': len(batch['moves']),
            'consumers': len(batch['references']), 'duplicates': len(batch['duplicates'])}


def verify_names(root, policy):
    rules = load_policy(policy)
    inventory = inventory_names(root, rules)
    issues = audit_local_links(root, rules)
    migration = verify_migration(root)
    return {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
            'naming_verified': not inventory['candidates'] and not issues and migration['verified'],
            'path_names_verified': not inventory['candidates'], 'links_verified': not issues,
            'migration_verified': migration['verified'], 'migration': migration,
            'unjustified_names': inventory['candidates'], 'broken_links': issues,
            'files_checked': len(inventory['files']), 'excluded': inventory['excluded'],
            'exceptions': rules.get('exceptions', {}), 'scientific_acceptance': False}


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('inventory', 'plan', 'verify'), default='inventory')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--policy', type=Path, default=Path('governance/naming.yaml'))
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    policy = load_policy(args.root/args.policy)
    if args.phase == 'inventory':
        report = inventory_names(args.root, policy)
    elif args.phase == 'plan':
        inventory = json.loads(args.inventory.read_text(encoding='utf-8')) if args.inventory else inventory_names(args.root, policy)
        report = build_rename_map(inventory, policy['moves'], policy=policy)
    else:
        batch = json.loads((args.root/'data/maintenance/names/map.json').read_text(encoding='utf-8-sig'))
        _write_json(args.root/'data/maintenance/names/aliases.json', {
            'schema_version': 1, 'created_at': batch['created_at'],
            'purpose': 'Original paths are provenance, never training inputs or compatibility copies.',
            'aliases': batch['aliases'], 'provenance_references': [item for item in
                batch['provenance_references'] if _immutable(item['path'], policy)]})
        report = verify_names(args.root, policy)
    _write_json(args.output, report)
    print(json.dumps({k: len(report[k]) for k in ('files', 'candidates', 'moves', 'references', 'duplicates', 'unjustified_names', 'broken_links') if k in report}))
    return 1 if args.phase == 'verify' and not report['naming_verified'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
