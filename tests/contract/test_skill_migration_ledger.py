"""FR-007.6 and module 7 tasks 7.1/7.2: legacy skills and invocations stay evidence-based.

A legacy skill is either fully migrated (pinned source, approved license, hashes)
or explicitly not migrated with its reason. The invocation log never closes the
gate without measured records.
"""
import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
LEGACY_NAMES = {
    'madrl-citylearn-thesis-plan',
    'madrl-citylearn-thesis-integrated',
    'iquitos-citylearn-dataset',
    'madrl-citylearn-literature-review',
}
ENTRY_FIELDS = {'skill', 'client', 'task', 'result', 'evidence'}


@pytest.fixture(scope='module')
def registry():
    return yaml.safe_load((REPO / 'tools/skills/registry.yaml').read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def invocation_log():
    return json.loads((REPO / 'data/audits/skill_invocation_log.json').read_text(encoding='utf-8'))


def _require_full_history():
    shallow = subprocess.run(
        ['git', 'rev-parse', '--is-shallow-repository'],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.strip()
    if shallow == 'true':
        pytest.skip('Shallow clone: pinned legacy commits are not available')


def test_the_owner_retired_every_legacy_skill(registry):
    review = registry['legacy_skills_review']
    assert registry['legacy_skills'] == []
    assert set(review['retired']) == LEGACY_NAMES
    assert 'legacy_skills_migration' not in registry['pending']
    active = {record['name'] for record in registry['skills']}
    assert not active & LEGACY_NAMES
    for name, source in zip(review['retired'], review['source_paths']):
        assert not (REPO / 'tools/skills' / name).exists(), name
        assert not (REPO / source).exists(), source


def test_retired_skills_stay_recoverable_from_the_pinned_commit(registry):
    _require_full_history()
    review = registry['legacy_skills_review']
    assert re.fullmatch(r'[0-9a-f]{40}', review['recover_from_commit'])
    for source in review['source_paths']:
        listed = subprocess.run(['git', 'ls-tree', '-r', '--name-only', review['recover_from_commit'], source + '/'],
                                cwd=REPO, check=True, capture_output=True, text=True).stdout
        assert listed.strip(), source


def test_registry_text_names_no_global_skill_root():
    """scripts/verify_project_context.ps1 rejects these literals in tools/skills files."""
    text = (REPO / 'tools/skills/registry.yaml').read_text(encoding='utf-8')
    for pattern in ('.agents/skills', r'.agents\skills', '.codex/skills', r'.codex\skills'):
        assert pattern not in text, pattern


def test_invocation_log_schema_and_gate(invocation_log, registry):
    assert invocation_log['schema_version'] == 1
    assert invocation_log['requirement'] == 'FR-007.6'
    assert invocation_log['entries_schema']['required'] == sorted(ENTRY_FIELDS)
    assert invocation_log['note'].strip()
    known = {record['name'] for record in registry['skills']}
    for entry in invocation_log['entries']:
        assert ENTRY_FIELDS <= set(entry), entry
        assert entry['skill'] in known, entry['skill']
        assert all(str(entry[field]).strip() for field in ENTRY_FIELDS), entry
        assert entry.get('tokens') is not None or entry.get('time_seconds') is not None, entry
    if not invocation_log['entries']:
        assert invocation_log['gate_closed'] is False
