"""Capture read-only commands and Git relocation evidence; never stage or publish."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main():
    commands = [
        ('git_status', ['git', 'status', '--short']),
        ('git_head', ['git', 'rev-parse', 'HEAD']),
        ('git_tree', ['git', '-c', 'core.quotepath=false', 'ls-tree', '-r', 'HEAD']),
        ('skills_basic', [sys.executable, '-B', 'tools/skills/validate_skills.py']),
        ('skills_discovery', [sys.executable, '-B', 'tools/skills/validate_skills.py', '--check-discovery']),
        ('workflow', [sys.executable, '-B', 'tools/ops/verify_workflow_integrity.py', '--manifest-out',
                      str(OUT/'workflow.json')]),
        ('lint_ci_scope', [sys.executable, '-m', 'ruff', 'check', 'uc3m', 'tests', 'tools/ops',
                           'scripts/quality', '--output-format', 'json']),
        ('pip_check', [sys.executable, '-m', 'pip', 'check']),
    ]
    results = []
    for name, command in commands:
        start = time.perf_counter()
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                encoding='utf-8', errors='replace', timeout=240)
        (OUT/f'{name}.log').write_text(result.stdout, encoding='utf-8')
        results.append({'name': name, 'command': command, 'returncode': result.returncode,
                        'seconds': time.perf_counter()-start, 'log': f'{name}.log'})
    (OUT/'commands.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    # Same Git blob at a new path proves byte preservation only, not behavior parity.
    by_blob = collections.defaultdict(list)
    inventory = list(csv.DictReader((OUT/'files.csv').open(encoding='utf-8-sig')))
    for row in inventory:
        path = ROOT/row['path']
        if (row.get('bytes') and int(row['bytes']) < 5*1024*1024 and path.is_file()
                and path.suffix in {'.py', '.md', '.json', '.yaml', '.yml', '.ps1', '.ipynb', '.txt'}):
            payload = path.read_bytes()
            oid = hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
            by_blob[oid].append(row['path'])
    missing = []
    for line in (OUT/'git_tree.log').read_text(encoding='utf-8').splitlines():
        metadata, name = line.split('\t', 1)
        mode, kind, oid = metadata.split(' ')
        if kind != 'blob' or name.startswith(('CityLearn/', 'external/')) or (ROOT/name).exists():
            continue
        replacements = by_blob.get(oid, [])
        missing.append({'old_path': name, 'head_blob': oid,
                        'exact_current_paths': replacements,
                        'status': 'bytes_preserved_at_new_path' if replacements else 'not_proven_by_exact_bytes',
                        'note': 'retirement/rewriting may be intentional; absence is not proof of lost capability'})
    (OUT/'migration_paths.json').write_text(json.dumps(missing, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'commands': [{k:r[k] for k in ('name','returncode')} for r in results],
                      'missing_head_paths': len(missing), 'exact_relocations': sum(bool(r['exact_current_paths']) for r in missing)}))


if __name__ == '__main__':
    main()
