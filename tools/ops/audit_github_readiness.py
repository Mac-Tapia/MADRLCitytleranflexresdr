"""Local GitHub readiness of the candidate tree (T13); never a remote verdict.

    python tools/ops/audit_github_readiness.py [--output data/maintenance/github_readiness/github_readiness.json]

Reads the candidate tree (tracked plus untracked, not-ignored files), the CI
workflow, pyproject and the collaboration files. remote_verified is false and
status_remote is pending_remote until a real Actions run of the same commit is
attached; branch protection is not configured here.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sysconfig
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

import yaml

MIB = 1024*1024
WARN_BYTES, BLOCK_BYTES = 50*MIB, 100*MIB
REQUIRED_CHECKS = ('quality-lint', 'quality-contracts', 'quality-package', 'quality-layout', 'quality-workflows')
# Import name -> distribution name, where they differ.
PACKAGE_IMPORTS = {'yaml': 'pyyaml', 'sklearn': 'scikit-learn', 'PIL': 'pillow', 'docx': 'python-docx'}
GENERATED_SUFFIXES = ('.pt', '.pkl', '.ckpt', '.pth')
# Standard-library modules that exist on one platform only (lock.py picks msvcrt or fcntl).
PLATFORM_STDLIB = {'fcntl', 'msvcrt', 'termios', 'pwd', 'grp', 'resource', 'winreg', '_winapi'}
_STDLIB = Path(sysconfig.get_paths()['stdlib']).resolve()


def is_stdlib(name: str) -> bool:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return False
    if spec is None:
        return False
    if spec.origin in ('built-in', 'frozen'):
        return True
    origin = Path(spec.origin or next(iter(spec.submodule_search_locations or []), '')).resolve()
    return 'site-packages' not in origin.parts and _STDLIB in origin.parents


def declared_distributions(pyproject: Path) -> Set[str]:
    """PyPI distributions (core and extras) plus the local dependencies of [tool.uc3m.local-dependencies]."""
    import tomli
    payload = tomli.loads(Path(pyproject).read_text(encoding='utf-8'))
    project = payload['project']
    requirements = list(project.get('dependencies', []))
    for extra in project.get('optional-dependencies', {}).values():
        requirements.extend(extra)
    local = payload.get('tool', {}).get('uc3m', {}).get('local-dependencies', {})
    return ({re.split(r'[<>=!~\[; ]', r.strip(), 1)[0].lower().replace('_', '-') for r in requirements}
            | set(local))


def _guarded(node, parents) -> bool:
    """True when the import sits in a try whose handlers catch ImportError (an optional feature)."""
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                names = [handler.type] if not isinstance(handler.type, ast.Tuple) else handler.type.elts
                if any(isinstance(n, ast.Name) and n.id in ('ImportError', 'ModuleNotFoundError') for n in names):
                    return True
    return False


def undeclared_runtime_imports(root: Path) -> dict:
    """Unguarded third-party imports of uc3m/ whose distribution pyproject does not declare."""
    root = Path(root)
    declared = declared_distributions(root/'pyproject.toml')
    missing = {}
    for path in sorted((root/'uc3m').rglob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module
                     else [])
            for name in names:
                top = name.split('.')[0]
                if top == 'uc3m' or top in PLATFORM_STDLIB or is_stdlib(top) or _guarded(node, parents):
                    continue
                if PACKAGE_IMPORTS.get(top, top).lower().replace('_', '-') not in declared:
                    missing.setdefault(top, path.relative_to(root).as_posix())
    return missing


def candidate_tree(root: Path) -> List[str]:
    done = subprocess.run(['git', '-C', str(root), 'ls-files', '-c', '-o', '--exclude-standard', '-z'],
                          capture_output=True, timeout=300, check=True)
    paths = sorted({p for p in done.stdout.decode('utf-8').split('\0') if p})
    return [p for p in paths if (Path(root)/p).is_file()]


def _workflow_report(root: Path) -> dict:
    path = Path(root)/'.github/workflows/ci.yml'
    if not path.is_file():
        return {'present': False, 'checks': [], 'pinned': False, 'read_only': False, 'timeouts': False}
    workflow = yaml.safe_load(path.read_text(encoding='utf-8'))
    jobs = workflow.get('jobs', {})
    uses = [s['uses'] for j in jobs.values() for s in j.get('steps', []) if 'uses' in s]
    return {'present': True, 'checks': sorted(j.get('name', k) for k, j in jobs.items()),
            'pinned': all(re.fullmatch(r'[^@]+@[0-9a-f]{40}', u.split()[0]) for u in uses),
            'read_only': workflow.get('permissions') == {'contents': 'read'},
            'timeouts': all(int(j.get('timeout-minutes', 0)) > 0 for j in jobs.values())}


def _head(root: Path) -> Optional[str]:
    done = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=60)
    return done.stdout.strip() or None


def audit_github_readiness(root: Path, candidate: Optional[Sequence[str]] = None,
                           layout_report: Optional[dict] = None) -> dict:
    root = Path(root)
    tree = list(candidate) if candidate is not None else candidate_tree(root)
    sizes = {p: (root/p).stat().st_size for p in tree}
    digest = hashlib.sha256()
    for path in tree:
        digest.update(path.encode('utf-8') + b'\0' + str(sizes[path]).encode('ascii') + b'\0')
    workflow = _workflow_report(root)
    generated = [p for p in tree if p.endswith(GENERATED_SUFFIXES)
                 or (p.startswith(('outputs/', 'data/maintenance/dataset_builds/')) and not p.endswith('README.md'))]
    pyproject = root/'pyproject.toml'
    submodules = re.findall(r'path = (\S+)', (root/'.gitmodules').read_text(encoding='utf-8')) \
        if (root/'.gitmodules').is_file() else []
    undeclared = undeclared_runtime_imports(root) if (root/'uc3m').is_dir() else {}
    local = (workflow['present'] and workflow['pinned'] and workflow['read_only'] and workflow['timeouts']
             and set(REQUIRED_CHECKS) <= set(workflow['checks']) and not generated and not undeclared
             and not [p for p, s in sizes.items() if s > BLOCK_BYTES]
             and bool(layout_report is None or layout_report.get('repository_layout_verified')))
    return {
        'schema_version': 1,
        'candidate_commit': _head(root) if (root/'.git').exists() else None,
        'candidate_files': len(tree),
        'candidate_listing_sha256': digest.hexdigest(),
        'submodules': submodules,
        'required_checks': list(REQUIRED_CHECKS),
        'workflow': workflow,
        'large_files_over_50_mib': sorted(p for p, s in sizes.items() if WARN_BYTES < s <= BLOCK_BYTES),
        'blocked_files_over_100_mib': sorted(p for p, s in sizes.items() if s > BLOCK_BYTES),
        'generated_in_candidate_tree': generated,
        'undeclared_runtime_imports': undeclared,
        'collaboration_files': {name: (root/name).is_file() for name in
                                ('LICENSE', 'CONTRIBUTING.md', 'SECURITY.md', '.github/CODEOWNERS', 'README.md')},
        'license_declared_in_pyproject': bool(pyproject.is_file() and 'license' in pyproject.read_text(encoding='utf-8')),
        'github_local_readiness': local,
        'local_pass': local,
        'remote_verified': False,
        'status_remote': 'pending_remote',
        'workflow_run_url': None,
        'branch_protection_status': 'not_configured_by_this_task',
        'scientific_acceptance': False,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args(argv)
    report = audit_github_readiness(args.root)
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text if not args.output else f"github_local_readiness={report['github_local_readiness']}")
    return 0 if report['github_local_readiness'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
