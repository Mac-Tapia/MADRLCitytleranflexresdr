"""Renaming must preserve bytes, resolve consumers and refuse unsafe batches."""
import json
import subprocess
from pathlib import Path

import pytest

from tools.ops import audit_names as names


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'scripts/maintenance/rename_paths.ps1'


def put(root, name, content='sentinel'):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode('utf-8') if isinstance(content, str) else content)
    return path


def policy(moves=None, **extra):
    return {'schema_version': 1, 'excluded_roots': ['external', 'CityLearn', 'tools/skills'],
            'excluded_components': ['.git', '__pycache__'], 'exceptions': {},
            'mandatory_names': ['README.md'], 'moves': moves or {}, **extra}


def prepare(root, moves, **extra):
    rules = policy(moves, **extra)
    return names.build_rename_map(names.inventory_names(root, rules), moves, policy=rules)


def run_batch(root, manifest, phase):
    path = put(root, 'map.json', json.dumps(manifest))
    return subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                           '-File', str(SCRIPT), '-Phase', phase, '-Root', str(root),
                           '-Manifest', str(path)], capture_output=True, text=True)


def test_inventory_excludes_dependencies_and_runtime_state(tmp_path):
    put(tmp_path, 'external/long_20260101.py')
    put(tmp_path, 'tools/skills/long_20260101.md')
    put(tmp_path, 'docs/report_20260101.md')
    inv = names.inventory_names(tmp_path, policy())
    assert [f['path'] for f in inv['files']] == ['docs/report_20260101.md']
    assert inv['candidates'][0]['path'] == 'docs/report_20260101.md'


@pytest.mark.parametrize('name', ['report_20260101.json', '2026-01-01-report.md', 'a'*41+'.py'])
def test_long_date_and_hash_names_are_candidates(tmp_path, name):
    put(tmp_path, name)
    assert names.inventory_names(tmp_path, policy())['candidates']


@pytest.mark.parametrize('target', ['../escape.md', 'CON.md', 'docs/aux.json',
                                  'docs/REPORT.md', 'docs/20260101.md'])
def test_external_and_invalid_target_rejected(tmp_path, target):
    put(tmp_path, 'old.md')
    with pytest.raises(ValueError):
        prepare(tmp_path, {'old.md': target})


def test_casefold_collision_rejected(tmp_path):
    put(tmp_path, 'old.md')
    put(tmp_path, 'Report.md')
    with pytest.raises(ValueError, match='occupied|collision'):
        prepare(tmp_path, {'old.md': 'report.md'})


def test_two_versions_cannot_overwrite_one_destination(tmp_path):
    put(tmp_path, 'one.md')
    put(tmp_path, 'two.md', 'other role')
    with pytest.raises(ValueError, match='collision'):
        prepare(tmp_path, {'one.md': 'report.md', 'two.md': 'report.md'})


def test_parent_child_moves_have_single_owner(tmp_path):
    put(tmp_path, 'old/long.md')
    batch = prepare(tmp_path, {'old/': 'new/', 'old/long.md': 'new/short.md'})
    assert [(m['old_path'], m['new_path']) for m in batch['moves']] == [('old/long.md', 'new/short.md')]


def test_active_writer_blocks_rename(tmp_path):
    put(tmp_path, 'old.md')
    inv = names.inventory_names(tmp_path, policy(), blocked_paths=['old.md'])
    with pytest.raises(ValueError, match='active'):
        names.build_rename_map(inv, {'old.md': 'new.md'}, policy=policy())


def test_plan_links_resolve_after_move_and_imports_change(tmp_path):
    put(tmp_path, 'docs/old/long.md', '# title\r\n![figure](../image_20260101.png)\r\n')
    put(tmp_path, 'docs/image_20260101.png', b'PNG sentinel')
    put(tmp_path, 'tools/long_module.py', 'VALUE = 1\r\n')
    put(tmp_path, 'README.md', '[doc](docs/old/long.md)\r\n')
    put(tmp_path, 'tests/use.py', 'from tools.long_module import VALUE\r\n')
    batch = prepare(tmp_path, {'docs/old/long.md': 'docs/plans/short.md',
                              'docs/image_20260101.png': 'docs/figure.png',
                              'tools/long_module.py': 'tools/simple.py'})
    updates = {r['old_path']: names.reference_bytes(r).decode('utf-8') for r in batch['references']}
    assert '[doc](docs/plans/short.md)' in updates['README.md']
    assert '(../figure.png)' in updates['docs/old/long.md']
    assert 'from tools.simple import VALUE' in updates['tests/use.py']
    assert '\r\n' in updates['README.md']


def test_notebook_paths_and_local_links_follow_parent_moves(tmp_path):
    put(tmp_path, 'docs/old/note.md', '[other](../old/other.md#title)\n')
    put(tmp_path, 'docs/old/other.md', '# title\n')
    put(tmp_path, 'example.ipynb', json.dumps({'cells': [{'source': ['tools/long_module.py\n']}]}))
    put(tmp_path, 'tools/long_module.py', 'pass\n')
    batch = prepare(tmp_path, {'docs/old/': 'docs/plans/', 'tools/long_module.py': 'tools/simple.py'})
    updated = {r['old_path']: names.reference_bytes(r).decode() for r in batch['references']}
    assert '(other.md#title)' in updated['docs/old/note.md']
    assert json.loads(updated['example.ipynb'])['cells'][0]['source'] == ['tools/simple.py\n']


def test_historical_json_is_provenance_not_rewritten(tmp_path):
    put(tmp_path, 'old.md')
    put(tmp_path, 'data/audits/snapshot.json', '{"source": "old.md", "sha256": "original"}')
    batch = prepare(tmp_path, {'old.md': 'new.md'}, immutable_roots=['data/audits'])
    assert not batch['references']
    assert batch['provenance_references'][0]['path'] == 'data/audits/snapshot.json'


def test_unique_document_content_not_dropped(tmp_path):
    put(tmp_path, 'thesis.docx', b'approved thesis')
    put(tmp_path, 'report.docx', b'different approved report')
    batch = prepare(tmp_path, {'thesis.docx': 'docs/thesis.docx', 'report.docx': 'docs/report.docx'})
    assert len(batch['moves']) == 2 and not batch['references']


def test_source_changed_since_inventory_blocks_move(tmp_path):
    put(tmp_path, 'old.md')
    batch = prepare(tmp_path, {'old.md': 'new.md'})
    put(tmp_path, 'old.md', 'concurrent changes')
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode != 0
    assert 'Source changed since inventory' in result.stderr
    assert (tmp_path/'old.md').read_text() == 'concurrent changes'
    assert not (tmp_path/'new.md').exists()


def test_occupied_target_not_overwritten(tmp_path):
    put(tmp_path, 'old.md')
    batch = prepare(tmp_path, {'old.md': 'new.md'})
    put(tmp_path, 'new.md', 'concurrent target')
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode != 0
    assert 'Occupied destination' in result.stderr
    assert (tmp_path/'new.md').read_text() == 'concurrent target'
    assert (tmp_path/'old.md').exists()


def test_no_silent_partial_success(tmp_path):
    put(tmp_path, 'one.md')
    put(tmp_path, 'two.md')
    batch = prepare(tmp_path, {'one.md': 'first.md', 'two.md': 'second.md'})
    put(tmp_path, 'two.md', 'changed')
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode != 0
    assert (tmp_path/'one.md').exists() and not (tmp_path/'first.md').exists()


def test_execute_verify_preserves_word_bytes_and_resolves_links(tmp_path):
    content = b'unmodified approved binary\x00\xff'
    put(tmp_path, 'old.docx', content)
    put(tmp_path, 'README.md', '[thesis](old.docx)\r\n')
    batch = prepare(tmp_path, {'old.docx': 'docs/thesis.docx'})
    assert run_batch(tmp_path, batch, 'Plan').returncode == 0
    assert (tmp_path/'old.docx').exists()
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode == 0, result.stderr
    assert (tmp_path/'docs/thesis.docx').read_bytes() == content
    assert not (tmp_path/'old.docx').exists()
    assert (tmp_path/'README.md').read_bytes() == b'[thesis](docs/thesis.docx)\r\n'
    assert run_batch(tmp_path, batch, 'Verify').returncode == 0


def test_exact_duplicates_consolidated_only_after_hash_match(tmp_path):
    put(tmp_path, 'canonical.png', b'identical')
    put(tmp_path, 'duplicate.png', b'identical')
    put(tmp_path, 'README.md', '![image](duplicate.png)\n')
    batch = prepare(tmp_path, {}, duplicates={'duplicate.png': 'canonical.png'})
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode == 0, result.stderr
    assert not (tmp_path/'duplicate.png').exists()
    assert (tmp_path/'README.md').read_text() == '![image](canonical.png)\n'
    assert run_batch(tmp_path, batch, 'Verify').returncode == 0


def test_different_content_never_consolidated(tmp_path):
    put(tmp_path, 'canonical.png', b'one')
    put(tmp_path, 'duplicate.png', b'two')
    with pytest.raises(ValueError, match='duplicate'):
        prepare(tmp_path, {}, duplicates={'duplicate.png': 'canonical.png'})


def test_case_only_rename_uses_checked_temporary_path(tmp_path):
    put(tmp_path, 'Long.md')
    batch = prepare(tmp_path, {'Long.md': 'long.md'})
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode == 0, result.stderr
    assert [p.name for p in tmp_path.glob('*.md')] == ['long.md']


def test_naming_acceptance_requires_no_unresolved_move(tmp_path):
    put(tmp_path, 'old_20260101.md')
    report = names.verify_names(tmp_path, policy())
    assert report['naming_verified'] is False and report['unjustified_names']


def test_broken_relative_link_reported(tmp_path):
    put(tmp_path, 'docs/page.md', '[missing](../missing.md)\n')
    issues = names.audit_local_links(tmp_path, policy())
    assert issues == [{'path': 'docs/page.md', 'target': '../missing.md', 'reason': 'missing'}]


def test_native_open_writer_blocks_entire_batch(tmp_path):
    import ctypes
    from ctypes import wintypes
    put(tmp_path, 'one.md')
    held = put(tmp_path, 'two.md')
    batch = prepare(tmp_path, {'one.md': 'first.md', 'two.md': 'second.md'})
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(held), 0xC0000000, 0, None, 3, 0x80, None)
    assert handle != wintypes.HANDLE(-1).value
    try:
        result = run_batch(tmp_path, batch, 'Execute')
        assert result.returncode != 0
        assert (tmp_path/'one.md').exists() and not (tmp_path/'first.md').exists()
    finally:
        kernel.CloseHandle(handle)


def test_native_junction_target_refused(tmp_path):
    import _winapi
    outside = tmp_path/'outside'
    outside.mkdir()
    root = tmp_path/'project'
    put(root, 'old.md')
    batch = prepare(root, {'old.md': 'linked/new.md'})
    _winapi.CreateJunction(str(outside), str(root/'linked'))
    result = run_batch(root, batch, 'Execute')
    assert result.returncode != 0
    assert 'Linked path rejected' in result.stderr
    assert (root/'old.md').exists() and not (outside/'new.md').exists()


def test_structured_python_paths_follow_directory_change(tmp_path):
    put(tmp_path, 'docs/report_20260101.json', '{}')
    put(tmp_path, 'tools/consumer.py',
        'from pathlib import Path\nREPO = Path(__file__).resolve().parents[1]\n'
        'DOCS = REPO / "docs"\nREPORT = DOCS / "report_20260101.json"\n'
        'OTHER = REPO / "docs" / "report_20260101.json"\n')
    batch = prepare(tmp_path, {'docs/report_20260101.json': 'docs/audits/report.json'})
    update = next(r for r in batch['references'] if r['old_path'] == 'tools/consumer.py')
    namespace = {'__file__': str(tmp_path/'tools/consumer.py')}
    exec(compile(names.reference_bytes(update), 'consumer.py', 'exec'), namespace)
    assert namespace['REPORT'] == tmp_path/'docs/audits/report.json'
    assert namespace['OTHER'] == namespace['REPORT']


def test_rollback_after_duplicate_deletion_restores_every_file(tmp_path):
    put(tmp_path, 'canonical.png', b'identical')
    put(tmp_path, 'duplicate.png', b'identical')
    original = '![image](duplicate.png)\r\n'
    put(tmp_path, 'README.md', original)
    batch = prepare(tmp_path, {'canonical.png': 'docs/image.png'},
                    duplicates={'duplicate.png': 'canonical.png'})
    (tmp_path/'data/maintenance/names/results.json').mkdir(parents=True)
    result = run_batch(tmp_path, batch, 'Execute')
    assert result.returncode != 0
    assert 'results.json' in result.stderr
    assert (tmp_path/'canonical.png').read_bytes() == b'identical'
    assert (tmp_path/'duplicate.png').read_bytes() == b'identical'
    assert (tmp_path/'README.md').read_bytes() == original.encode()
    assert not (tmp_path/'docs/image.png').exists()


def test_secret_config_never_copied_into_reference_evidence(tmp_path):
    put(tmp_path, 'old.md')
    put(tmp_path, 'configs/secrets.yaml', 'private: value\npath: old.md\n')
    batch = prepare(tmp_path, {'old.md': 'new.md'})
    assert not batch['references']


def test_short_name_alone_cannot_certify_unexecuted_map(tmp_path):
    put(tmp_path, 'short.md')
    rules = policy({'short.md': 'renamed.md'})
    report = names.verify_names(tmp_path, rules)
    assert not report['naming_verified']
    assert not report['migration_verified']


def test_imported_canonical_docs_path_is_rebased(tmp_path):
    import ast
    put(tmp_path, 'docs/report_20260101.json', '{}')
    put(tmp_path, 'tools/consumer.py', 'from thesis_word_canons import DOCS\n'
        'REPORT = DOCS / "report_20260101.json"\n')
    batch = prepare(tmp_path, {'docs/report_20260101.json': 'docs/audits/word/report.json'})
    update = next(r for r in batch['references'] if r['old_path'] == 'tools/consumer.py')
    tree = ast.parse(names.reference_bytes(update))
    tree.body = [node for node in tree.body if isinstance(node, ast.Assign)]
    namespace = {'DOCS': tmp_path/'docs'}
    exec(compile(tree, 'consumer.py', 'exec'), namespace)
    assert namespace['REPORT'] == tmp_path/'docs/audits/word/report.json'


def test_default_native_root_resolves_after_parameter_binding(tmp_path):
    put(tmp_path, 'old.md')
    batch = prepare(tmp_path, {'old.md': 'new.md'})
    manifest = put(tmp_path, 'map.json', json.dumps(batch))
    result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                             '-File', str(SCRIPT), '-Phase', 'Plan', '-Manifest', str(manifest)],
                            capture_output=True, text=True, cwd=REPO)
    assert result.returncode != 0 and 'mismatch' in result.stderr
    assert (tmp_path/'old.md').exists()


def test_generic_directory_basename_never_changes_other_roots(tmp_path):
    put(tmp_path, 'docs/superpowers/specs/design.md')
    put(tmp_path, 'specs/001-long-provenance/spec.md')
    put(tmp_path, 'tools/consumer.py', 'from pathlib import Path\n'
        'ROOT=Path(__file__).resolve().parents[1]\n'
        'SPEC=ROOT/"specs"/"001-long-provenance"/"spec.md"\n')
    batch = prepare(tmp_path, {'docs/superpowers/specs/': 'docs/design/',
                              'specs/001-long-provenance/': 'specs/001-provenance/'})
    change = next(r for r in batch['references'] if r['old_path'] == 'tools/consumer.py')
    namespace = {'__file__': str(tmp_path/'tools/consumer.py')}
    exec(compile(names.reference_bytes(change), 'consumer.py', 'exec'), namespace)
    assert namespace['SPEC'] == tmp_path/'specs/001-provenance/spec.md'


def test_inventory_change_between_read_and_plan_is_refused(tmp_path):
    put(tmp_path, 'old.md')
    inv = names.inventory_names(tmp_path, policy())
    put(tmp_path, 'old.md', 'new concurrent content')
    with pytest.raises(ValueError, match='inventory_stale'):
        names.build_rename_map(inv, {'old.md': 'new.md'}, policy=policy())


def test_atomic_consumer_update_with_mapped_reader(tmp_path):
    import ctypes
    from ctypes import wintypes
    put(tmp_path, 'old.md')
    readme = put(tmp_path, 'README.md', '[doc](old.md)\r\n')
    batch = prepare(tmp_path, {'old.md': 'new.md'})
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CreateFileMappingW.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                                         wintypes.DWORD, wintypes.DWORD, wintypes.LPCWSTR]
    kernel.CreateFileMappingW.restype = wintypes.HANDLE
    kernel.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                    wintypes.DWORD, ctypes.c_size_t]
    kernel.MapViewOfFile.restype = wintypes.LPVOID
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.UnmapViewOfFile.argtypes = [wintypes.LPVOID]
    handle = kernel.CreateFileW(str(readme), 0x80000000, 7, None, 3, 0x80, None)
    assert handle != wintypes.HANDLE(-1).value
    mapping = kernel.CreateFileMappingW(handle, None, 2, 0, 0, None)
    assert mapping
    view = kernel.MapViewOfFile(mapping, 4, 0, 0, 0)
    assert view
    kernel.CloseHandle(mapping)
    kernel.CloseHandle(handle)
    try:
        result = run_batch(tmp_path, batch, 'Execute')
        assert result.returncode == 0, result.stderr
        assert readme.read_bytes() == b'[doc](new.md)\r\n'
        assert ctypes.string_at(view, len(b'[doc](old.md)\r\n')) == b'[doc](old.md)\r\n'
    finally:
        kernel.UnmapViewOfFile(view)
