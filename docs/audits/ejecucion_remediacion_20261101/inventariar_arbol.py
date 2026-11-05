"""Metadata-only current tree; no model, credential or browser content reads."""
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SKIP_NAMES = {'.git', '__pycache__', '.pytest_cache', '.ruff_cache', 'node_modules', '.cache'}
SKIP_ROOTS = {'.superpowers': 'execution_workspaces_preserved',
              'tools/skills/notebooklm-mcp/data': 'private_browser_runtime_not_inspected'}


def linked(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def role(relative):
    first = relative.split('/')[0]
    return {'uc3m': 'own_runtime', 'tests': 'verification', 'CityLearn': 'protected_dependency',
        'external': 'protected_dependencies', 'data': 'data_or_evidence', 'outputs': 'generated_artifacts',
        'tools': 'tooling_or_local_skills', 'scripts': 'operational_entrypoints', 'docs': 'documentation_or_evidence',
        'configs': 'experimental_configuration', 'governance': 'policy', 'specs': 'specifications'}.get(first, 'project_support')


def main():
    files, directories, excluded, errors = [], [], [], []
    def on_error(error):
        errors.append({'path': str(error.filename), 'error': type(error).__name__})
    for current, names, leaves in os.walk(ROOT, topdown=True, followlinks=False, onerror=on_error):
        parent = Path(current)
        kept = []
        for name in sorted(names):
            path = parent/name
            relative = path.relative_to(ROOT).as_posix()
            try:
                info = path.lstat()
                reason = (SKIP_ROOTS.get(relative) or ('environment_not_inspected' if name.startswith('.venv') else None)
                          or ('generated_or_vcs_runtime' if name in SKIP_NAMES else None)
                          or ('link_or_junction_not_followed' if linked(info) else None))
                directories.append({'path': relative, 'role': role(relative), 'scope': reason or 'enumerated'})
                if reason:
                    excluded.append({'path': relative, 'reason': reason})
                else:
                    kept.append(name)
            except OSError as error:
                errors.append({'path': relative, 'error': type(error).__name__})
        names[:] = kept
        for name in sorted(leaves):
            path = parent/name
            relative = path.relative_to(ROOT).as_posix()
            if path.parent == OUT and name in {'arbol_actual.json', 'arbol_actual.txt'}:
                continue  # The inventory is written after its own scan cut.
            try:
                info = path.lstat()
                files.append({'path': relative, 'role': role(relative), 'bytes': info.st_size,
                              'kind': 'link_not_followed' if linked(info) else 'file_metadata_only'})
            except OSError as error:
                errors.append({'path': relative, 'error': type(error).__name__})
    summary = {'files_enumerated': len(files), 'directories_enumerated': len(directories),
               'roles': dict(sorted(Counter(row['role'] for row in files).items())),
               'excluded_subtrees': len(excluded), 'metadata_errors': len(errors)}
    payload = {'schema_version': 1, 'cut_utc': datetime.now(timezone.utc).isoformat(),
               'scope': 'metadata only; not semantic review, content hashes or scientific acceptance',
               'summary': summary, 'files': files, 'directories': directories, 'excluded': excluded, 'errors': errors}
    (OUT/'arbol_actual.json').write_text(json.dumps(payload, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
    lines = ['Current repository tree (directories; see JSON for every file and explicit exclusions).', '']
    lines += [f"{r['path']} [{r['role']}; {r['scope']}]" for r in directories]
    (OUT/'arbol_actual.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
