"""Non-mutating source inventory and thesis extraction; outputs beside this file.

Run from the verified project root with the canonical Python. Does not follow
reparse points, inspect credentials, execute notebooks or deserialize models.
"""
import ast
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import stat
from zipfile import ZipFile
from lxml import etree

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SKIP_NAMES = {'.git', '__pycache__', '.pytest_cache', '.ruff_cache',
              'node_modules', '.mypy_cache', '.superpowers', 'build', 'uc3m.egg-info'}
BOUNDARIES = {'CityLearn', 'external', 'tools/skills/google-drive-mcp',
              'tools/skills/notebooklm-mcp', 'docs/audits'}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def write_csv(name, rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/name).open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    files, folders, imports, errors, modules = [], [], [], [], []
    for parent, dirs, names in os.walk(ROOT, followlinks=False):
        base = Path(parent)
        for name in list(dirs):
            path = base/name
            rel = path.relative_to(ROOT).as_posix()
            attrs = path.lstat()
            excluded = (name in SKIP_NAMES or name.startswith('.venv') or rel in BOUNDARIES
                        or bool(getattr(attrs, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))
            folders.append({'path': rel, 'scope': 'boundary_not_recursed' if excluded else 'inventoried',
                            'reason': ('dependency/evidence/runtime/tool boundary or reparse point' if excluded else '')})
            if excluded:
                dirs.remove(name)
        for name in names:
            path = base/name
            rel = path.relative_to(ROOT).as_posix()
            try:
                info = path.lstat()
                if getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    files.append({'path': rel, 'review': 'reparse_not_opened'})
                    continue
                # Avoid opening connector secrets or local environment settings.
                if name.startswith('.env') or name in {'credentials.json', 'token.json'}:
                    files.append({'path': rel, 'review': 'sensitive_not_opened'})
                    continue
                row = {'path': rel, 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns,
                       'sha256': digest(path), 'review': 'inventory_hash_only'}
                files.append(row)
                if path.suffix == '.py':
                    text = path.read_text(encoding='utf-8-sig')
                    tree = ast.parse(text, filename=rel)
                    row['review'] = 'AST_parsed_not_full_semantic_review'
                    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    modules.append({'path': rel, 'lines': len(text.splitlines()), 'functions': len(functions),
                                    'classes': len(classes),
                                    'max_function_lines': max([n.end_lineno-n.lineno+1 for n in functions] or [0])})
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            imports.extend({'path': rel, 'line': node.lineno, 'module': n.name, 'level': 0} for n in node.names)
                        elif isinstance(node, ast.ImportFrom):
                            imports.append({'path': rel, 'line': node.lineno, 'module': node.module or '', 'level': node.level})
            except Exception as exc:
                errors.append({'path': rel, 'error': str(exc), 'type': type(exc).__name__})
    write_csv('files.csv', files)
    write_csv('folders.csv', folders)
    write_csv('imports.csv', imports)
    write_csv('modules.csv', modules)
    write_json('errors.json', errors)
    groups = collections.defaultdict(list)
    for row in files:
        if row.get('sha256') and row.get('bytes'):
            groups[row['sha256']].append(row['path'])
    write_json('equal_bytes.json', [v for v in groups.values() if len(v) > 1])
    thesis = ROOT/'PT_TAPIA_ZAMBRANO_v6_Iquitos_2.docx'
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    with ZipFile(thesis) as archive:
        root = etree.fromstring(archive.read('word/document.xml'))
        paragraphs = root.xpath('//w:body/w:p|//w:body/w:tbl//w:p', namespaces=ns)
        texts = [''.join(p.xpath('.//w:t/text()|.//m:t/text()', namespaces=ns)) for p in paragraphs]
        controls = root.xpath('//w:body/w:sdt//w:p', namespaces=ns)
        control_texts = [''.join(p.xpath('.//w:t/text()|.//m:t/text()', namespaces=ns)) for p in controls]
        (OUT/'PT_TAPIA_ZAMBRANO.extracted.txt').write_text(
            '\n'.join(f'P{i:04d}: {text}' for i, text in enumerate(texts)), encoding='utf-8')
        write_json('thesis.json', {'path': thesis.relative_to(ROOT).as_posix(), 'sha256': digest(thesis),
                   'paragraphs': len(texts), 'equations': len(root.xpath('//m:oMath', namespaces=ns)),
                   'content_control_paragraphs': len(controls),
                   'content_control_nonempty': sum(bool(t.strip()) for t in control_texts),
                   'review': 'full body text including OMML extracted; no edit or visual pagination claim'})
    summary = {'files': len(files), 'folders_and_boundaries': len(folders), 'python_modules': len(modules),
               'errors': len(errors), 'bytes': sum(r.get('bytes', 0) for r in files),
               'by_root': dict(collections.Counter(r['path'].split('/')[0] for r in files)),
               'scope': 'own tree recursively; dependencies, prior audits and runtime boundaries explicitly recorded',
               'scientific_acceptance': False}
    write_json('inventory_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
