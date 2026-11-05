"""T12: the deployed tree is read from the filesystem, never from a drawing.

Behaviour is checked on disposable trees under pytest's tmp_path. One test
runs the read-only auditors on the real repository (phase C-software) and
asserts that the checked indexes carry no active broken reference.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from tools.ops import audit_duplicate_files as adf
from tools.ops import audit_repository_layout as arl

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO/'governance/repository_layout.yaml'
CHECKED_INDEXES = ('README.md', 'docs/00_INDEX.md', 'scripts/README.md', 'tools/README.md',
                   'docs/architecture/runbook.md')


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


def test_required_layout_exists_for_phase(tmp_path):
    consolidation = {
        'required_paths_by_phase': {
            'A': ['README.md', 'governance/repository_layout.yaml'],
            'C-software': ['tools/ops/audit_tree.py'],
        },
        'checked_indexes': ['README.md'],
    }
    root, registry = make_tree(tmp_path, {'README.md': '# project\n'}, consolidation)

    phase_a = arl.audit_repository_layout(root, registry, 'A')
    assert phase_a.repository_layout_verified is True
    assert phase_a.missing_paths == []

    phase_c = arl.audit_repository_layout(root, registry, 'C-software')
    assert phase_c.required_paths == ['README.md', 'governance/repository_layout.yaml',
                                      'tools/ops/audit_tree.py']
    assert phase_c.missing_paths == ['tools/ops/audit_tree.py']
    assert phase_c.repository_layout_verified is False
    assert any('tools/ops/audit_tree.py' in reason for reason in phase_c.reasons)
    assert 'tools' not in {entry['path'] for entry in phase_c.actual_tree['entries']}

    (root/'tools/ops').mkdir(parents=True)
    (root/'tools/ops/audit_tree.py').write_text('"""tree"""\n', encoding='utf-8')
    phase_c = arl.audit_repository_layout(root, registry, 'C-software')
    assert phase_c.repository_layout_verified is True
    assert {'tools', 'tools/ops'} <= {entry['path'] for entry in phase_c.actual_tree['entries']}

    with pytest.raises(ValueError):
        arl.audit_repository_layout(root, registry, 'Z')


def test_junction_is_recorded_and_not_followed(tmp_path):
    root, registry = make_tree(tmp_path, {'README.md': '# project\n'},
                               {'required_paths_by_phase': {'A': ['README.md']}})
    outside = tmp_path/'outside'
    outside.mkdir()
    (outside/'secret.py').write_text('x = 1\n', encoding='utf-8')
    made = subprocess.run(['cmd', '/c', 'mklink', '/J', str(root/'linked'), str(outside)],
                          capture_output=True, text=True)
    assert made.returncode == 0, made.stdout + made.stderr
    report = arl.audit_repository_layout(root, registry, 'A')
    assert report.links_not_followed == ['linked']
    assert all(not entry['path'].startswith('linked') for entry in report.actual_tree['entries'])
    inventory = adf.find_duplicate_candidates(root, registry)
    assert 'linked' in inventory.scope['links_not_followed']


def test_no_active_broken_reference_after_move(tmp_path):
    guide = ''.join(f'Step {index}: configure the campaign carefully.\n' for index in range(30))
    consolidation = {
        'canonical_sources': {'doc.guide': 'docs/guide.md'},
        'checked_indexes': ['README.md'],
        'required_paths_by_phase': {'A': ['README.md']},
    }
    root, registry = make_tree(tmp_path, {
        'README.md': 'See the [guide](docs/guide_old.md) and `docs/guide_old.md`.\n',
        'docs/guide.md': guide,
        'docs/guide_old.md': guide,
    }, consolidation)

    inventory = adf.find_duplicate_candidates(root, registry)
    [group] = [g for g in inventory.exact_groups if 'docs/guide.md' in g.paths]
    assert group.classification == 'redundant_clone'
    assert group.canonical_path == 'docs/guide.md'
    plan = adf.build_canonicalization_plan(inventory, [])
    assert plan.removed_paths == []
    [blocked] = [b for b in plan.blocked if b['path'] == 'docs/guide_old.md']
    assert any('README.md' in reason for reason in blocked['reasons'])

    # Removing before updating the reader leaves a broken active reference.
    moved = root/'docs/guide_old.md'
    moved.rename(root/'docs/guide_old.bak')
    report = arl.audit_repository_layout(root, registry, 'A')
    assert report.repository_layout_verified is False
    assert {ref['target'] for ref in report.active_broken_references} == {'docs/guide_old.md'}
    (root/'docs/guide_old.bak').rename(moved)

    (root/'README.md').write_text('See the [guide](docs/guide.md).\n', encoding='utf-8')
    inventory = adf.find_duplicate_candidates(root, registry)
    plan = adf.build_canonicalization_plan(inventory, [])
    assert [row['path'] for row in plan.removed_paths] == ['docs/guide_old.md']
    moved.unlink()
    report = arl.audit_repository_layout(root, registry, 'A')
    assert report.active_broken_references == []
    assert report.repository_layout_verified is True


def test_retired_mentions_and_runtime_paths_are_not_broken_links(tmp_path):
    root, registry = make_tree(tmp_path, {
        'README.md': ('El script `scripts/old_launcher.ps1` fue retirado.\n'
                      'Escribe `outputs/campaigns/iquitos_v5/campaign_manifest.json`.\n'
                      'Usa `scripts/missing_tool.py`.\n'),
        'scripts/keep.ps1': 'Write-Output ok\n',
    }, {'checked_indexes': ['README.md'], 'required_paths_by_phase': {'A': ['README.md']},
        'runtime_reference_roots': ['outputs']})
    report = arl.audit_repository_layout(root, registry, 'A')
    assert [ref['target'] for ref in report.active_broken_references] == ['scripts/missing_tool.py']
    assert [ref['target'] for ref in report.retired_mentions] == ['scripts/old_launcher.ps1']


def test_real_repository_indexes_have_no_active_broken_reference():
    report = arl.audit_repository_layout(REPO, REGISTRY, 'C-software')
    payload = json.loads(json.dumps(report.as_dict()))
    assert payload['phase'] == 'C-software'
    assert payload['schema_version'] == arl.SCHEMA_VERSION
    assert set(CHECKED_INDEXES) <= set(payload['checked_indexes'])
    broken = [f"{ref['source']}:{ref['line']} -> {ref['target']}"
              for ref in payload['active_broken_references'] if ref['source'] in CHECKED_INDEXES]
    assert broken == [], broken


def test_real_repository_inventory_and_plan_serialize():
    inventory = adf.find_duplicate_candidates(REPO, REGISTRY)
    data = json.loads(json.dumps(inventory.as_dict()))
    excluded = {row['path'] for row in data['scope']['excluded_scope']}
    assert {'CityLearn', 'external'} <= excluded
    listed = [p for g in data['exact_groups'] + data['semantic_candidates'] for p in g['paths']]
    assert not any(p.split('/')[0] in {'CityLearn', 'external', '.git'} for p in listed)
    assert not any(part.startswith('.venv') for p in listed for part in p.split('/'))
    plan = adf.build_canonicalization_plan(inventory, [])
    json.dumps(plan.as_dict())
    assert all(row['coverage_verified'] is True for row in plan.removed_paths)
    assert not any(row['path'].lower().endswith('.docx') for row in plan.removed_paths)
    assert os.path.isfile(REGISTRY)
