"""T12: one canonical file per responsibility, decided by role/coverage/consumers.

Hashes and similarity only propose candidates. Size, date or a repeated basename
never decide a canonical file, and protected Word documents or distinct data
identities are never removed. The PowerShell mutation path runs only on a
disposable copy under the system temp directory.
"""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import yaml

from tools.ops import audit_duplicate_files as adf

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO/'scripts/maintenance/consolidate_repository.ps1'


def make_tree(tmp_path, files, consolidation):
    root = tmp_path/'project'
    for rel, payload in files.items():
        path = root/rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload if isinstance(payload, bytes) else payload.encode('utf-8'))
    registry = root/'governance/repository_layout.yaml'
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(yaml.safe_dump({'schema_version': 1, 'consolidation': consolidation}),
                        encoding='utf-8')
    return root, registry


def function(name, flavour):
    lines = [f'def {name}(values):', f'    """Compute {name} for {flavour}."""', '    total = 0']
    lines += [f'    total += values[{i}] * {i + 3}  # {name} {flavour} term {i}' for i in range(8)]
    lines += [f'    return total / {len(name) + 7}', '', '']
    return '\n'.join(lines)


def module(*names):
    return 'import math\n\n\n' + ''.join(function(name, 'campaign') for name in names)


def groups_with(inventory, path):
    return [g for g in inventory.exact_groups + inventory.semantic_candidates if path in g.paths]


GENERATOR = module('build_cells', 'render_markdown', 'write_notebook')


def test_one_canonical_implementation_per_role(tmp_path):
    root, registry = make_tree(tmp_path, {
        'tools/colab/build_notebook.py': GENERATOR,
        'tools/colab/build_notebook_old.py': GENERATOR,
    }, {'canonical_sources': {'notebook.generator': 'tools/colab/build_notebook.py'}})
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'tools/colab/build_notebook.py')
    assert group.kind == 'exact'
    assert group.logical_role == 'notebook.generator'
    assert group.classification == 'redundant_clone'
    assert group.canonical_path == 'tools/colab/build_notebook.py'
    assert group.canonical_basis == 'role_registry'
    plan = adf.build_canonicalization_plan(inventory, [])
    assert [(r['path'], r['coverage_verified']) for r in plan.removed_paths] == [
        ('tools/colab/build_notebook_old.py', True)]
    assert plan.removed_paths[0]['canonical_path'] == 'tools/colab/build_notebook.py'

    # Two roles cannot claim the same canonical file, and a role needs one path.
    _, bad = make_tree(tmp_path/'bad', {'a.py': 'x = 1\n'},
                       {'canonical_sources': {'r1': 'a.py', 'r2': 'a.py'}})
    assert adf.find_duplicate_candidates(bad.parents[1], bad).registry_errors


def test_same_name_different_roles_are_not_duplicates(tmp_path):
    root, registry = make_tree(tmp_path, {
        'deploy/dashboard/app.py': module('render_dashboard', 'list_runs'),
        'deploy/inference/app.py': 'from http.server import HTTPServer\n\n\n' + function('predict', 'edge'),
        'uc3m/domain/__init__.py': '',
        'uc3m/ports/__init__.py': '',
        'uc3m/application/__init__.py': '"""Application layer."""\n',
        'uc3m/adapters/__init__.py': '"""Application layer."""\n',
    }, {})
    inventory = adf.find_duplicate_candidates(root, registry)
    assert not groups_with(inventory, 'deploy/dashboard/app.py')
    [markers] = groups_with(inventory, 'uc3m/application/__init__.py')
    assert markers.classification == 'distinct_role'
    assert inventory.scope['zero_byte_files'] == 2
    assert all(g.classification != 'redundant_clone'
               for g in inventory.exact_groups + inventory.semantic_candidates)
    assert adf.build_canonicalization_plan(inventory, []).removed_paths == []


def test_facade_contains_no_business_logic(tmp_path):
    shim = ('"""Compat shim."""\nimport runpy\nfrom pathlib import Path\n\n'
            '_TARGET = Path(__file__).resolve().parent / "dataset" / "real.py"\n'
            'runpy.run_path(str(_TARGET), run_name="__main__")\n')
    fat = ('"""Not a shim."""\nfrom tools.dataset.real import load\n\n\n'
           'def summarize(rows):\n    out = 0\n    for row in rows:\n        out += row\n    return out\n')
    root, registry = make_tree(tmp_path, {
        'tools/shim.py': shim,
        'tools/fat_shim.py': fat,
        'tools/dataset/real.py': module('load', 'validate'),
    }, {'facades': {
        'tools/shim.py': {'canonical': 'tools/dataset/real.py', 'reason': 'protected caller'},
        'tools/fat_shim.py': {'canonical': 'tools/dataset/real.py', 'reason': 'legacy import'},
    }})
    inventory = adf.find_duplicate_candidates(root, registry)
    facades = {row['path']: row for row in inventory.facades}
    assert facades['tools/shim.py']['has_business_logic'] is False
    assert facades['tools/shim.py']['classification'] == 'facade'
    assert facades['tools/fat_shim.py']['has_business_logic'] is True
    assert [row['path'] for row in inventory.facade_violations] == ['tools/fat_shim.py']
    plan = adf.build_canonicalization_plan(inventory, [
        {'path': 'tools/shim.py', 'canonical_path': 'tools/dataset/real.py', 'coverage_verified': True}])
    assert plan.removed_paths == []


def test_partial_versions_merge_unique_capabilities(tmp_path):
    root, registry = make_tree(tmp_path, {
        'tools/eval/stats.py': module('mean_score', 'median_score', 'rank_score'),
        'tools/eval/stats_v2.py': module('mean_score', 'median_score', 'bootstrap_score'),
    }, {'canonical_sources': {'eval.stats': 'tools/eval/stats.py'}})
    claim = [{'path': 'tools/eval/stats_v2.py', 'canonical_path': 'tools/eval/stats.py',
              'coverage_verified': True, 'evidence': 'reviewer claim'}]
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'tools/eval/stats_v2.py')
    assert group.kind == 'semantic'
    assert group.canonical_path == 'tools/eval/stats.py'
    assert group.unique_capabilities['tools/eval/stats_v2.py'] == ['bootstrap_score']
    assert group.classification == 'needs_review'
    plan = adf.build_canonicalization_plan(inventory, claim)
    assert plan.removed_paths == []
    assert [row['path'] for row in plan.blocked_unique_content] == ['tools/eval/stats_v2.py']

    (root/'tools/eval/stats.py').write_text(
        module('mean_score', 'median_score', 'rank_score', 'bootstrap_score'), encoding='utf-8')
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'tools/eval/stats_v2.py')
    assert group.unique_capabilities['tools/eval/stats_v2.py'] == []
    assert group.classification == 'redundant_clone'
    unverified = adf.build_canonicalization_plan(inventory, [])
    assert unverified.removed_paths == []
    assert any('coverage' in reason for reason in unverified.blocked[0]['reasons'])
    plan = adf.build_canonicalization_plan(inventory, claim)
    assert [row['path'] for row in plan.removed_paths] == ['tools/eval/stats_v2.py']


def test_largest_file_is_not_automatically_canonical(tmp_path):
    root, registry = make_tree(tmp_path, {
        'tools/x/report.py': module('load_rows', 'format_rows', 'write_rows'),
        'tools/x/report_full.py': module('load_rows', 'format_rows', 'plot_rows', 'export_rows',
                                         'audit_rows'),
        'tools/x/cli.py': 'from tools.x.report import write_rows\n',
        'tools/y/run.py': 'import tools.x.report\n',
    }, {})
    newer = time.time() + 3600
    os.utime(root/'tools/x/report_full.py', (newer, newer))
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'tools/x/report_full.py')
    assert group.canonical_path == 'tools/x/report.py'
    assert group.canonical_basis == 'consumers'
    assert group.unique_capabilities['tools/x/report_full.py'] == ['audit_rows', 'export_rows',
                                                                   'plot_rows']
    plan = adf.build_canonicalization_plan(inventory, [])
    assert 'tools/x/report.py' not in [row['path'] for row in plan.removed_paths]
    assert [row['path'] for row in plan.blocked_unique_content] == ['tools/x/report_full.py']

    # Without registry, coverage or consumers there is no autonomous choice.
    (root/'tools/x/cli.py').unlink()
    (root/'tools/y/run.py').unlink()
    [group] = groups_with(adf.find_duplicate_candidates(root, registry), 'tools/x/report_full.py')
    assert group.canonical_path is None
    assert group.classification == 'needs_review'


def test_generated_asset_keeps_one_source(tmp_path):
    png = b'\x89PNG\r\n\x1a\n' + bytes(range(256)) * 4
    root, registry = make_tree(tmp_path, {
        'tools/figures/make_fig.py': 'from pathlib import Path\nPath("docs/fig.png").write_bytes(b"")\n',
        'docs/fig.png': png,
        'docs/fig_copy.png': png,
    }, {'generated_assets': {'docs/fig.png': {'source': 'tools/figures/make_fig.py',
                                              'reason': 'rendered by the figure generator'}}})
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'docs/fig.png')
    assert group.classification == 'generated_asset'
    assert group.canonical_path == 'docs/fig.png'
    assert inventory.generated_sources_missing == []
    plan = adf.build_canonicalization_plan(inventory, [])
    removed = [row['path'] for row in plan.removed_paths]
    assert removed == ['docs/fig_copy.png']
    assert 'tools/figures/make_fig.py' not in removed

    (root/'tools/figures/make_fig.py').unlink()
    inventory = adf.find_duplicate_candidates(root, registry)
    assert inventory.generated_sources_missing == ['tools/figures/make_fig.py']
    assert adf.build_canonicalization_plan(inventory, []).removed_paths == []


def test_protected_word_unique_content_blocks_deletion(tmp_path):
    root, registry = make_tree(tmp_path, {
        'docs/tesis.docx': b'PK\x03\x04 tesis approved text',
        'docs/tesis_copia.docx': b'PK\x03\x04 tesis approved text',
        'docs/informe.docx': b'PK\x03\x04 informe with unique chapters',
    }, {'protected': [{'pattern': 'docs/*.docx', 'reason': 'approved Word; edited only by the Word flow'}]})
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'docs/tesis.docx')
    assert group.classification == 'protected_unique'
    assert {row['path'] for row in inventory.protected_documents} == {
        'docs/tesis.docx', 'docs/tesis_copia.docx', 'docs/informe.docx'}
    claims = [{'path': p, 'canonical_path': 'docs/tesis.docx', 'coverage_verified': True}
              for p in ('docs/tesis_copia.docx', 'docs/informe.docx')]
    plan = adf.build_canonicalization_plan(inventory, claims)
    assert plan.removed_paths == []
    assert 'docs/tesis_copia.docx' in {row['path'] for row in plan.blocked}

    forged = plan.as_dict()
    forged['removed_paths'] = [{'path': 'docs/tesis_copia.docx', 'canonical_path': 'docs/tesis.docx',
                                'sha256': hashlib.sha256(b'PK\x03\x04 tesis approved text').hexdigest(),
                                'canonical_sha256': hashlib.sha256(b'PK\x03\x04 tesis approved text').hexdigest(),
                                'coverage_verified': True}]
    [decision] = adf.verify_plan(forged, root, registry)
    assert decision['decision'] == 'blocked'
    assert any('protected' in reason for reason in decision['reasons'])


def test_semantically_distinct_data_identity_preserved(tmp_path):
    rows = 'hour,load_kwh\n' + ''.join(f'{h},{h * 0.5:.2f}\n' for h in range(48))
    root, registry = make_tree(tmp_path, {
        'data/campaigns/a/dataset/Building_1.csv': rows,
        'data/campaigns/a/splits/train_2023/Building_1.csv': rows,
        'data/campaigns/b/dataset/Building_7.csv': rows,
    }, {'data_identity_roots': {'data/campaigns': 'assets/splits/campaigns keep identity by provenance'}})
    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = groups_with(inventory, 'data/campaigns/a/dataset/Building_1.csv')
    assert group.classification == 'distinct_role'
    assert any('identity' in reason for reason in group.reasons)
    claims = [{'path': p, 'canonical_path': 'data/campaigns/a/dataset/Building_1.csv',
               'coverage_verified': True} for p in group.paths[1:]]
    assert adf.build_canonicalization_plan(inventory, claims).removed_paths == []


def _ps(*args):
    return subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                           str(SCRIPT), *args], capture_output=True, text=True, cwd=str(REPO))


def test_consolidate_execute_only_on_matching_plan_in_temp_copy(tmp_path):
    root, registry = make_tree(tmp_path, {
        'tools/colab/build_notebook.py': GENERATOR,
        'tools/colab/build_notebook_old.py': GENERATOR,
        'tools/colab/build_notebook_bak.py': GENERATOR,
        'docs/tesis.docx': b'PK tesis',
        'docs/tesis_copia.docx': b'PK tesis',
    }, {'canonical_sources': {'notebook.generator': 'tools/colab/build_notebook.py'},
        'protected': [{'pattern': 'docs/*.docx', 'reason': 'approved Word'}]})
    plan_path = tmp_path/'evidence/canonicalization_plan.json'
    made = _ps('-Phase', 'Plan', '-ProjectRoot', str(root), '-Plan', str(plan_path))
    assert made.returncode == 0, made.stdout + made.stderr
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    assert sorted(r['path'] for r in plan['removed_paths']) == [
        'tools/colab/build_notebook_bak.py', 'tools/colab/build_notebook_old.py']

    # A source changed after planning and a forged path outside the root are refused.
    (root/'tools/colab/build_notebook_bak.py').write_text(GENERATOR + '\n# edited\n', encoding='utf-8')
    outside = tmp_path/'outside.py'
    outside.write_text(GENERATOR, encoding='utf-8')
    sha = hashlib.sha256(GENERATOR.encode('utf-8')).hexdigest()
    plan['removed_paths'].append({'path': '../outside.py', 'canonical_path': 'tools/colab/build_notebook.py',
                                  'sha256': sha, 'canonical_sha256': sha, 'coverage_verified': True})
    plan_path.write_text(json.dumps(plan), encoding='utf-8')

    ran = _ps('-Phase', 'Execute', '-ProjectRoot', str(root), '-Plan', str(plan_path))
    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert not (root/'tools/colab/build_notebook_old.py').exists()
    assert (root/'tools/colab/build_notebook_bak.py').exists()
    assert (root/'tools/colab/build_notebook.py').exists()
    assert outside.exists()
    assert (root/'docs/tesis_copia.docx').exists()
    result = json.loads((plan_path.parent/'consolidation_result.json').read_text(encoding='utf-8-sig'))
    status = {row['path']: row['status'] for row in result['outcomes']}
    assert status == {'tools/colab/build_notebook_old.py': 'deleted',
                      'tools/colab/build_notebook_bak.py': 'blocked', '../outside.py': 'blocked'}

    refused = _ps('-Phase', 'Execute', '-ProjectRoot', str(REPO.parent), '-Plan', str(plan_path))
    assert refused.returncode != 0
