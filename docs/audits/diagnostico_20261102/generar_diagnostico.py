#!/usr/bin/env python
"""Per-file mechanical diagnosis of the repository; it never edits what it reads.

Reading a file to EOF is not a semantic review. The semantic state comes only from the
review ledgers, and it counts only while the file still has the SHA-256 that was reviewed.
A text match counts as a consumer, so "sin_consumidor" is reliable and "con consumidor" is only a hint.
"""
from __future__ import annotations

import ast
import collections
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

import yaml

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LEDGERS = ('docs/audits/revision_semantica_20261102/ledger_revisor_a.csv',
           'docs/audits/revision_semantica_20261102/ledger_revisor_b.csv')
# Evidence folders: inventoried as a block, they are not source to diagnose.
BULK = ('data/maintenance/', 'data/campaigns/', 'docs/audits/', 'outputs/')
SENSITIVE = {'login data', 'state.json', 'auth_info.json'}
TEXT = {'.py', '.md', '.json', '.yaml', '.yml', '.txt', '.log', '.csv', '.sh', '.ps1', '.toml', '.ipynb', '.bib',
        '.cfg', '.ini', '.patch', '.tex', '.html', '.css', '.js', '.ts', '.tsx', '.dockerfile', ''}
CODE = {'.py', '.ps1', '.sh', '.yaml', '.yml', '.toml', '.ipynb', '.json', ''}
GENERIC_STEMS = {'__init__', 'readme', 'conftest', 'skill', 'main', 'app', 'config', 'index', 'license', 'utils',
                 'dockerfile', 'requirements', 'agents', 'claude'}
MARKERS = re.compile(r'\b(TODO|FIXME|XXX|HACK)\b')
SWALLOW = re.compile(r'except(\s+Exception)?\s*:\s*(#.*)?\n\s*pass\b')
RUFF_DEFECTS = 'F,E9,B006,B008,B012,B023,PLE'


def git_files():
    def listing(*args):
        raw = subprocess.run(['git', '-c', 'core.quotepath=off', 'ls-files', '-z', *args], cwd=REPO,
                             capture_output=True, check=True).stdout
        return [p for p in raw.decode('utf-8').split('\0') if p]
    tracked = listing()
    return [(p, 'rastreado') for p in tracked] + [(p, 'sin_rastrear') for p in listing('--others', '--exclude-standard')]


def module_name(path):
    return '.'.join(PurePosixPath(path).with_suffix('').parts).removesuffix('.__init__')


def imports_of(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
            names.update(f'{node.module}.{alias.name}' for alias in node.names)
    return names


def has_main(text):
    return "__name__ == '__main__'" in text or '__name__ == "__main__"' in text


def parse_state(path, suffix, text):
    """(state, syntax tree or None)."""
    try:
        if suffix == '.py':
            return 'ok', ast.parse(text, filename=path)
        if suffix in ('.json', '.ipynb'):
            json.loads(text)
        elif suffix in ('.yaml', '.yml'):
            list(yaml.safe_load_all(text))
        else:
            return 'no_aplica', None
    except Exception as exc:
        return f'error: {type(exc).__name__}: {str(exc)[:120]}', None
    return 'ok', None


def ruff_counts(python_files):
    """{path: {code: count}} over the given files; None when ruff is not installed."""
    executable = shutil.which('ruff')
    if executable is None:
        return None
    result = collections.defaultdict(collections.Counter)
    for start in range(0, len(python_files), 150):
        chunk = python_files[start:start + 150]
        run = subprocess.run([executable, 'check', '--isolated', '--no-cache', '--target-version', 'py39',
                              '--select', RUFF_DEFECTS, '--output-format', 'json', *chunk],
                             cwd=REPO, capture_output=True)
        for item in json.loads(run.stdout.decode('utf-8') or '[]'):
            rel = Path(item['filename']).resolve().relative_to(REPO).as_posix()
            result[rel][item['code'] or 'syntax'] += 1
    return result


def semantic_states():
    states = {}
    for name in LEDGERS:
        with (REPO/name).open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                if row['estado_revision'] != 'pendiente':
                    states[row['ruta']] = (row['estado_revision'], row['sha256'], row['hallazgos'])
                else:
                    states.setdefault(row['ruta'], ('pendiente', row['sha256'], ''))
    return states


def main():
    files = git_files()
    reviews = semantic_states()
    rows, tokens, trees, by_sha = {}, {}, {}, collections.defaultdict(list)
    for path, origin in files:
        full = REPO/path
        suffix = PurePosixPath(path).suffix.lower()
        row = {'ruta': path, 'origen': origin, 'carpeta': path.split('/')[0] if '/' in path else '(raiz)',
               'modulo': str(PurePosixPath(path).parent), 'ext': suffix, 'bytes': '', 'lineas': '', 'sha256': '',
               'leido_hasta_eof': False, 'bloque': path.startswith(BULK), 'sintaxis': 'no_aplica', 'marcadores': 0,
               'except_pass': 0, 'punto_de_entrada': False}
        rows[path] = row
        if PurePosixPath(path).name.lower() in SENSITIVE:
            row['sintaxis'] = 'bloqueado: sensible, no se abre'
            continue
        if not full.is_file():  # submodule gitlink or a deletion still unstaged
            row['sintaxis'] = 'submodulo' if full.is_dir() else 'ausente_en_disco'
            continue
        raw = full.read_bytes()
        row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), leido_hasta_eof=True)
        if raw:
            by_sha[row['sha256']].append(path)
        if suffix not in TEXT:
            continue
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = raw.decode('latin-1')
            row['sintaxis'] = 'no_utf8'
        row['lineas'] = text.count('\n') + (0 if text.endswith('\n') or not text else 1)
        if row['bloque']:
            continue
        state, tree = parse_state(path, suffix, text)
        row['sintaxis'] = state if row['sintaxis'] == 'no_aplica' else row['sintaxis']
        row['marcadores'] = len(MARKERS.findall(text))
        row['except_pass'] = len(SWALLOW.findall(text)) if suffix == '.py' else 0
        row['punto_de_entrada'] = has_main(text)
        tokens[path] = set(re.findall(r'[A-Za-z_][\w-]*', text))
        if tree is not None:
            trees[path] = tree

    modules = {module_name(p): p for p in trees}
    imported_by = collections.defaultdict(set)
    for path, tree in trees.items():
        folder = PurePosixPath(path).parent.as_posix().replace('/', '.')
        for name in imports_of(tree):
            # Scripts that add their own folder to sys.path import a sibling by its bare name.
            target = modules.get(name) or modules.get(f'{folder}.{name}')
            if target and target != path:
                imported_by[target].add(path)

    stems = collections.defaultdict(set)
    for path, words in tokens.items():
        for word in words:
            stems[word].add(path)
    python_files = [p for p in trees if not rows[p]['bloque']]
    ruff = ruff_counts(python_files)

    for path, row in rows.items():
        stem = PurePosixPath(path).stem
        users = (stems.get(stem, set()) | imported_by.get(path, set())) - {path}
        kinds = collections.Counter()
        for user in users:
            kind = 'prueba' if user.startswith('tests/') or '/tests/' in user else \
                   'codigo' if PurePosixPath(user).suffix.lower() in CODE else 'documento'
            kinds[kind] += 1
        generic = stem.lower() in GENERIC_STEMS or row['bloque']
        row.update(importado_por=len(imported_by.get(path, ())), cons_codigo=kinds['codigo'], cons_prueba=kinds['prueba'],
                   cons_documento=kinds['documento'], nombre_generico=generic)
        counts = ruff.get(path, {}) if ruff is not None else {}
        row['ruff_defectos'] = sum(counts.values())
        row['ruff_codigos'] = ' '.join(f'{c}:{n}' for c, n in sorted(counts.items()))
        twins = by_sha.get(row['sha256'], [])
        row['duplicados'] = len(twins) - 1 if len(twins) > 1 else 0
        state = reviews.get(path)
        if row['bloque'] or path.startswith(('CityLearn/', 'external/')):
            row['revision_semantica'] = 'fuera_de_alcance'
        elif state is None:
            row['revision_semantica'] = 'sin_lote'
        elif state[0] == 'pendiente':
            row['revision_semantica'] = 'pendiente'
        elif state[1] != row['sha256']:
            row['revision_semantica'] = 'caducada_archivo_cambio'
        else:
            row['revision_semantica'] = state[0]
        row['hallazgos_previos'] = state[2] if state else ''
        row['senales'] = ' '.join(signals(row))

    write_outputs(list(rows.values()), ruff is not None)


def signals(row):
    if row['bloque']:
        return []
    found = []
    if str(row['sintaxis']).startswith(('error', 'no_utf8')):
        found.append('sintaxis')
    if row['ext'] == '.py' and not row['nombre_generico'] and not row['ruta'].startswith(('tests/', 'CityLearn/', 'external/')):
        if not (row['cons_codigo'] or row['cons_prueba'] or row['punto_de_entrada']):
            found.append('sin_consumidor')
        if not row['cons_prueba']:
            found.append('sin_prueba')
    if row['ruff_defectos']:
        found.append('ruff')
    if row['duplicados']:
        found.append('duplicado')
    if row['bytes'] == 0:
        found.append('vacio')
    if row['except_pass']:
        found.append('except_pass')
    if row['marcadores']:
        found.append('marcador')
    if row['ext'] == '.py' and row['lineas'] and int(row['lineas']) > 800:
        found.append('modulo_grande')
    return found


def write_outputs(rows, ruff_available):
    fields = ['ruta', 'origen', 'carpeta', 'modulo', 'ext', 'bytes', 'lineas', 'sha256', 'leido_hasta_eof', 'bloque',
              'sintaxis', 'punto_de_entrada', 'importado_por', 'cons_codigo', 'cons_prueba', 'cons_documento',
              'nombre_generico', 'ruff_defectos', 'ruff_codigos', 'except_pass', 'marcadores', 'duplicados',
              'revision_semantica', 'hallazgos_previos', 'senales']
    with (OUT/'registro_por_archivo.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)

    def summary(group):
        lines = sum(int(r['lineas'] or 0) for r in group)
        signal_counts = collections.Counter(s for r in group for s in r['senales'].split())
        states = collections.Counter(r['revision_semantica'] for r in group)
        return {'archivos': len(group), 'lineas': lines, 'leidos_hasta_eof': sum(bool(r['leido_hasta_eof']) for r in group),
                'revision': dict(sorted(states.items())), 'senales': dict(sorted(signal_counts.items()))}

    by_folder = collections.defaultdict(list)
    by_module = collections.defaultdict(list)
    for row in rows:
        by_folder[row['carpeta']].append(row)
        by_module[row['modulo']].append(row)
    report = {'schema_version': 1, 'ruff_available': ruff_available, 'ruff_rules': RUFF_DEFECTS, 'total': summary(rows),
              'por_carpeta': {k: summary(v) for k, v in sorted(by_folder.items())},
              'por_modulo': {k: summary(v) for k, v in sorted(by_module.items())}}
    (OUT/'resumen.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    text = ['# Diagnóstico mecánico por carpeta y módulo', '',
            'Generado por `generar_diagnostico.py`. Leer hasta el final no equivale a revisar: la columna *vigente* solo cuenta '
            'archivos revisados cuyo SHA-256 no ha cambiado desde la revisión.', '']
    for title, groups in (('Carpetas', by_folder), ('Módulos', by_module)):
        text += [f'## {title}', '', '| Ruta | Archivos | Líneas | EOF | Vigente | Caducada | Pendiente | Sin lote | Señales |',
                 '|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for name, group in sorted(groups.items()):
            s = summary(group)
            review = s['revision']
            current = review.get('revisado', 0) + review.get('revisado_con_hallazgos', 0)
            marks = ', '.join(f'{k} {v}' for k, v in s['senales'].items()) or '—'
            text.append(f"| `{name}` | {s['archivos']} | {s['lineas']} | {s['leidos_hasta_eof']} | {current} | "
                        f"{review.get('caducada_archivo_cambio', 0)} | {review.get('pendiente', 0)} | {review.get('sin_lote', 0)} | {marks} |")
        text.append('')
    (OUT/'por_carpeta.md').write_text('\n'.join(text), encoding='utf-8')


if __name__ == '__main__':
    main()
