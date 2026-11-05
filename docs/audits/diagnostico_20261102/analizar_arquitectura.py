#!/usr/bin/env python
"""Import graph of uc3m/: layer violations, cycles and modules nothing reaches. Reads source, writes arquitectura.json.

Only static imports are seen, including those inside functions; dynamic loading is reported separately because
it can hide a consumer. Layers follow the modular monolith: domain < application < adapters/presentation.
"""
from __future__ import annotations

import ast
import collections
import json
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent/'arquitectura.json'
# A key may not import the listed packages.
FORBIDDEN = {'uc3m.domain': ('uc3m.application', 'uc3m.adapters', 'uc3m.presentation', 'citylearn', 'torch', 'harl'),
             'uc3m.ports': ('uc3m.application', 'uc3m.adapters', 'uc3m.presentation', 'citylearn', 'torch'),
             'uc3m.application': ('uc3m.adapters', 'uc3m.presentation', 'citylearn', 'torch', 'harl')}
DYNAMIC = ('import_module', 'spec_from_file_location', '__import__', 'load_native_common')


def module_of(path):
    return '.'.join(PurePosixPath(path).with_suffix('').parts).removesuffix('.__init__')


def resolve_relative(module, is_package, node):
    parts = module.split('.')
    base = parts if is_package else parts[:-1]
    base = base[:len(base) - node.level + 1]
    return '.'.join(base + ([node.module] if node.module else []))


def scan(path, module):
    tree = ast.parse((REPO/path).read_text(encoding='utf-8-sig'))
    is_package = path.endswith('__init__.py')
    imports, dynamic = [], []
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def scope(node):
        while node in parents:
            node = parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return 'funcion'
        return 'modulo'

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [(alias.name, node.lineno, scope(node)) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = resolve_relative(module, is_package, node) if node.level else node.module
            imports.append((base, node.lineno, scope(node)))
            imports += [(f'{base}.{alias.name}', node.lineno, scope(node)) for alias in node.names]
        elif isinstance(node, ast.Call):
            name = getattr(node.func, 'attr', getattr(node.func, 'id', ''))
            if name in DYNAMIC:
                dynamic.append((name, node.lineno))
    return imports, dynamic


def cycles(graph):
    """Strongly connected components with more than one module (Tarjan)."""
    index, low, stack, on_stack, found, counter = {}, {}, [], set(), [], [0]

    def visit(node):
        index[node] = low[node] = counter[0]
        counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        for target in graph.get(node, ()):
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], index[target])
        if low[node] == index[node]:
            component = []
            while True:
                item = stack.pop()
                on_stack.discard(item)
                component.append(item)
                if item == node:
                    break
            if len(component) > 1:
                found.append(sorted(component))

    for node in sorted(graph):
        if node not in index:
            visit(node)
    return found


def main():
    files = sorted(p.relative_to(REPO).as_posix() for p in (REPO/'uc3m').rglob('*.py'))
    modules = {module_of(p): p for p in files}
    graph, violations, dynamic_use = collections.defaultdict(set), [], {}
    for path in files:
        module = module_of(path)
        imports, dynamic = scan(path, module)
        if dynamic:
            dynamic_use[path] = dynamic
        for name, line, scope in imports:
            target = name if name in modules else None
            if target and target != module:
                graph[module].add(target)
            for layer, banned in FORBIDDEN.items():
                if module == layer or module.startswith(layer + '.'):
                    if any(name == b or name.startswith(b + '.') for b in banned):
                        violations.append({'modulo': path, 'linea': line, 'importa': name, 'ambito': scope})

    # Reached from outside uc3m/ or by a sibling; the package root's re-exports count only if something else uses them.
    outside = collections.defaultdict(set)
    roots = [p for folder in ('tools', 'scripts', 'tests', 'deploy', 'examples_madrl_v3')
             for p in (REPO/folder).rglob('*.py')]
    for full in roots:
        rel = full.relative_to(REPO).as_posix()
        try:
            tree = ast.parse(full.read_text(encoding='utf-8-sig'))
        except (SyntaxError, UnicodeDecodeError):
            continue
        kind = 'prueba' if rel.startswith('tests/') else 'herramienta'
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module] + [f'{node.module}.{a.name}' for a in node.names]
            for name in names:
                if name in modules:
                    outside[name].add(kind)

    entry = {m for m, p in modules.items() if "__name__ ==" in (REPO/p).read_text(encoding='utf-8-sig')}
    incoming = collections.Counter(t for targets in graph.values() for t in targets)
    production = set(entry) | {m for m, kinds in outside.items() if 'herramienta' in kinds}
    reached, pending = set(), list(production)
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending += graph.get(node, ())
    report = {'modulos': len(modules), 'aristas': sum(len(v) for v in graph.values()),
              'puntos_de_entrada': sorted(entry),
              'violaciones_de_capa': violations, 'ciclos': cycles(graph),
              'solo_pruebas_lo_alcanzan': sorted(m for m in modules if m not in reached and 'prueba' in outside.get(m, ())
                                                 and not m.endswith('__init__')),
              'nadie_lo_alcanza': sorted(m for m in modules if m not in reached and 'prueba' not in outside.get(m, ())
                                         and not incoming[m] and modules[m].rsplit('/', 1)[-1] != '__init__.py'),
              'carga_dinamica': {k: [list(x) for x in v] for k, v in sorted(dynamic_use.items())}}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in report.items()}))


if __name__ == '__main__':
    main()
