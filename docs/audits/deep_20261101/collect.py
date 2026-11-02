"""Read-only project inspection. Writes only beside this script, never fixes inputs.

Run from the project root after scripts/verify_project_context.ps1. External
dependencies, environments, caches and junctions are boundary entries, not
recursively inspected. Signals are leads for manual review, not vulnerabilities.
"""
import ast
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SKIP = {'.git', '.venv39-citylearn-v3', '.superpowers', '.pytest_cache',
        '.ruff_cache', '__pycache__', 'node_modules', '.mypy_cache'}
BOUNDARY = {'CityLearn', 'external', '.agents/skills', '.claude/skills',
            'tools/skills/notebooklm-mcp', 'tools/skills/google-drive-mcp'}
TEXT = {'.py', '.md', '.json', '.yaml', '.yml', '.toml', '.ps1', '.sh',
        '.bat', '.txt', '.ini', '.cfg', '.conf', '.html', '.js', '.ts', '.tf'}
signals, files, imports, folders, errors = [], [], [], [], []


def emit(path, rows):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def signal(path, line, rule, detail=''):
    signals.append({'path': path, 'line': line, 'rule': rule, 'detail': detail})


def inspect_python(relative, source, row):
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as exc:
        signal(relative, exc.lineno, 'syntax_error', exc.msg)
        row['inspection'] = 'syntax_error'
        return
    row['inspection'] = 'AST_and_text_review_automatic'
    row['functions'] = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
    row['classes'] = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or '']
            for name in names:
                imports.append({'path': relative, 'line': node.lineno, 'module': name,
                                'relative_level': getattr(node, 'level', 0)})
        if isinstance(node, ast.ExceptHandler) and (node.type is None or
                isinstance(node.type, ast.Name) and node.type.id in {'Exception', 'BaseException'}):
            if all(isinstance(n, (ast.Pass, ast.Continue)) for n in node.body):
                signal(relative, node.lineno, 'silent_broad_exception')
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            span = getattr(node, 'end_lineno', node.lineno) - node.lineno + 1
            if span > 150:
                signal(relative, node.lineno, 'long_function', str(span))
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        if name in {'eval', 'exec', 'pickle.load', 'pickle.loads', 'torch.load'} or name.endswith('.extractall'):
            signal(relative, node.lineno, 'security_sensitive_call', name)
        for kw in node.keywords:
            if kw.arg in {'shell', 'verify'} and isinstance(kw.value, ast.Constant):
                if (kw.arg == 'shell' and kw.value.value is True) or (kw.arg == 'verify' and kw.value.value is False):
                    signal(relative, node.lineno, 'unsafe_call_option', kw.arg)
        if name.startswith(('requests.', 'urllib.request.urlopen', 'subprocess.run')):
            if not any(k.arg == 'timeout' for k in node.keywords):
                signal(relative, node.lineno, 'no_explicit_timeout', name)


def inspect_csv(path, row):
    # Structural scan of every CSV, all rows. Numerical/physical dataset checks
    # are recorded separately; strings in billing tables are valid, not errors.
    for encoding in ('utf-8-sig', 'cp1252'):
      try:
        with path.open(newline='', encoding=encoding) as stream:
            first = stream.readline()
            stream.seek(0)
            delimiter = ';' if first.count(';') > first.count(',') else ','
            reader = csv.reader(stream, delimiter=delimiter)
            header = next(reader, [])
            count = malformed = empty = nonfinite = 0
            for values in reader:
                count += 1
                malformed += len(values) != len(header)
                empty += sum(not v.strip() for v in values)
                nonfinite += sum(v.strip().lower() in {'nan', 'inf', '-inf', '+inf', 'infinity'} for v in values)
        row.update(inspection='CSV_all_rows_structural', csv_rows=count, csv_columns=len(header),
                   csv_ragged_rows=malformed, csv_empty_cells=empty, csv_nonfinite_tokens=nonfinite,
                   encoding=encoding, delimiter=delimiter)
        if malformed or nonfinite:
            signal(row['path'], 0, 'csv_quality_signal', f'ragged={malformed}; nonfinite={nonfinite}')
        return
      except UnicodeError:
        continue
      except (OSError, csv.Error) as exc:
        row['inspection'] = 'CSV_unreadable'
        errors.append({'path': row['path'], 'error_type': type(exc).__name__})
        return
    row['inspection'] = 'CSV_unreadable'
    errors.append({'path': row['path'], 'error_type': 'UnsupportedEncoding'})


def main():
    started = time.time()
    statuses = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z'], cwd=ROOT)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    baseline = OUT/'baseline.json'
    if not baseline.exists():
      baseline.write_text(json.dumps({'commit': commit, 'python': sys.version,
        'status_porcelain_entries': statuses.decode('utf-8').split('\0'),
        'baseline_note': 'Existing dirty tree preserved. Not a clean commit snapshot.'}, indent=2), encoding='utf-8')
    tracked_set = set(tracked)
    for base, dirs, names in os.walk(ROOT, followlinks=False):
        relative_dir = Path(base).relative_to(ROOT).as_posix()
        if Path(base) == OUT:
            dirs[:] = []
            continue
        removed = []
        for name in list(dirs):
            path = Path(base)/name
            rel = path.relative_to(ROOT).as_posix()
            if name in SKIP or rel in BOUNDARY or path.is_symlink() or bool(path.stat().st_file_attributes & 0x400):
                dirs.remove(name)
                removed.append({'path': rel, 'inspection': 'excluded_boundary_no_recursion'})
        folders.extend(removed)
        folders.append({'path': relative_dir, 'inspection': 'enumerated', 'direct_files': len(names),
                        'direct_directories': len(dirs)})
        for name in sorted(names):
            path = Path(base)/name
            rel = path.relative_to(ROOT).as_posix()
            stat = path.stat()
            row = {'path': rel, 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                   'tracked': rel in tracked_set, 'inspection': 'metadata_only', 'sha256': ''}
            files.append(row)
            if path.is_symlink() or bool(stat.st_file_attributes & 0x400):
                row['inspection'] = 'link_not_followed'
                continue
            # Sensitive local config: record path/size only; no values or hashes.
            if name == '.env' or re.search(r'(credential|token|secret).*\.(json|env|txt)$', name, re.I):
                row['inspection'] = 'sensitive_metadata_only'
                continue
            if path.suffix.lower() == '.csv':
                inspect_csv(path, row)
                continue
            if path.suffix.lower() not in TEXT | {'.ipynb'} and name not in {'Dockerfile', 'LICENSE', '.gitignore', '.gitattributes', '.gitmodules'}:
                continue
            try:
                payload = path.read_bytes()
                row['sha256'] = hashlib.sha256(payload).hexdigest()
                source = payload.decode('utf-8-sig')
            except (OSError, UnicodeError) as exc:
                errors.append({'path': rel, 'error_type': type(exc).__name__})
                continue
            row['inspection'] = 'text_rules_automatic'
            row['lines'] = len(source.splitlines())
            if path.suffix == '.py':
                inspect_python(rel, source, row)
            if path.suffix == '.json' and rel.startswith('.vscode/'):
                row['inspection'] = 'JSONC_text_rules_not_strict_JSON'
            elif path.suffix in {'.json', '.ipynb'}:
                try:
                    content = json.loads(source)
                    row['inspection'] = 'JSON_parsed'
                    if path.suffix == '.ipynb':
                        row['inspection'] = 'notebook_cells_rules_automatic'
                        row['notebook_cells'] = len(content.get('cells', []))
                        for index, cell in enumerate(content.get('cells', [])):
                            code = ''.join(cell.get('source', []))
                            if re.search(r'pip install|git clone|subprocess|--execute|drive.mount', code):
                                signal(rel, index + 1, 'notebook_execution_cell', 'cell index (1-based)')
                except ValueError:
                    signal(rel, 0, 'invalid_JSON')
            for line, text in enumerate(source.splitlines(), 1):
                if re.search(r'\b(TODO|FIXME|NotImplementedError)\b', text):
                    signal(rel, line, 'unfinished_marker')
                if 'docs/tesis_capitulos/' in text or 'docs/superpowers/' in text:
                    signal(rel, line, 'old_path_reference')
                if re.search(r'0\.0\.0\.0|allow_anonymous\s+true|1883:1883|8000:8000|8501:8501', text):
                    signal(rel, line, 'network_exposure_review')
    existing = {r['path'] for r in files}
    missing = [{'path': p, 'inspection': 'tracked_missing_in_worktree'} for p in tracked if p and p not in existing
               and not p.startswith(('CityLearn/', 'external/')) and not (ROOT/p).exists()]
    emit(OUT/'files.csv', files)
    emit(OUT/'folders.csv', folders)
    emit(OUT/'signals.csv', signals)
    emit(OUT/'imports.csv', imports)
    emit(OUT/'tracked_missing.csv', missing)
    emit(OUT/'read_errors.csv', errors)
    duplicates = collections.defaultdict(list)
    for row in files:
        if row['sha256'] and row['bytes']:
            duplicates[row['sha256']].append(row['path'])
    (OUT/'duplicate_text.json').write_text(json.dumps([{'sha256': k, 'paths': v} for k, v in duplicates.items()
        if len(v) > 1], indent=2), encoding='utf-8')
    summary = {'commit': commit, 'files': len(files), 'folders': len(folders),
               'inspection_counts': dict(collections.Counter(r['inspection'] for r in files)),
               'signals_by_rule': dict(collections.Counter(r['rule'] for r in signals)),
               'csv_rows_read': sum(r.get('csv_rows', 0) for r in files), 'read_errors': len(errors),
               'tracked_missing': len(missing), 'duration_seconds': round(time.time() - started, 2),
               'scientific_acceptance': False, 'semantic_review_of_every_file': False}
    (OUT/'scan.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
