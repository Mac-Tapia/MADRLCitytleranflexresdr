"""Native Git/filesystem/JUnit checks of the cut-bound software gate."""
import json
import subprocess
import xml.etree.ElementTree as ET

import pytest

from tests.fresh_training.gate_fixture import PLUGIN_SHA256, synthetic_gate
from uc3m.application.training import gate_report as gr


@pytest.fixture
def cut(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-c', 'user.name=Gate test', '-c', 'user.email=gate@example.invalid',
                    'commit', '--allow-empty', '-qm', 'test cut'], cwd=tmp_path, check=True)
    (tmp_path/'tests').mkdir()
    (tmp_path/'tests/test_value.py').write_text('VALUE=1\n', encoding='utf-8')
    (tmp_path/'uc3m').mkdir()
    (tmp_path/'uc3m/value.py').write_text('VALUE=1\n', encoding='utf-8')
    before = gr.capture_context(tmp_path)
    manifest = {'campaign_id': 'fresh_gate_v1', 'spec_hash': 'a'*64,
                'identity': {**before, 'source_git_head': before['git_head']}}
    xml = tmp_path/'junit.xml'
    suite = ET.Element('testsuite', tests='1', failures='0', errors='0', skipped='0')
    ET.SubElement(suite, 'testcase', name='test_value')
    ET.ElementTree(suite).write(xml, encoding='utf-8')
    return tmp_path, before, manifest, xml


def test_gate_rechecks_actual_junit_and_campaign_binding(cut):
    root, before, manifest, _ = cut
    gate = synthetic_gate(root/'gate', context=before, campaign_id=manifest['campaign_id'], spec_hash=manifest['spec_hash'])
    assert gr.verify_gate_report(gate, manifest)
    xml = root/'gate/gate.xml'
    xml.write_text(xml.read_text(encoding='utf-8').replace('tests="10"', 'tests="11"'), encoding='utf-8')
    assert not gr.verify_gate_report(gate, manifest)


def test_synthetic_fixture_is_refused_outside_the_test_fixture_switch(cut, monkeypatch):
    root, before, manifest, _ = cut
    gate = synthetic_gate(root/'gate', context=before, campaign_id=manifest['campaign_id'], spec_hash=manifest['spec_hash'])
    monkeypatch.setattr(gr, 'ACCEPT_SYNTHETIC_FIXTURES', False)
    assert not gr.verify_gate_report(gate, manifest)


def test_gate_from_another_plugin_build_is_refused(cut):
    root, before, manifest, _ = cut
    gate = synthetic_gate(root/'gate', context=before, campaign_id=manifest['campaign_id'], spec_hash=manifest['spec_hash'])
    for name in ('gate_collection.json', 'gate_execution.json'):
        path = root/'gate'/name
        path.write_text(path.read_text(encoding='utf-8').replace(PLUGIN_SHA256, '9'*64), encoding='utf-8')
    assert not gr.verify_gate_report(gate, manifest)


def test_committed_filter_that_drops_a_test_file_is_detected(cut):
    root, _, _, _ = cut
    (root/'tests/fresh_training').mkdir(parents=True)
    (root/'tests/fresh_training/test_kept.py').write_text('', encoding='utf-8')
    (root/'tests/fresh_training/test_dropped.py').write_text('', encoding='utf-8')
    missing = gr._test_files_without_cases(root, 'tests/fresh_training', ['tests/fresh_training/test_kept.py::test_a'])
    assert missing == ['tests/fresh_training/test_dropped.py']


def test_junit_without_independent_collection_is_never_a_full_profile(cut):
    root, before, manifest, xml = cut
    report = gr.build_gate_report(root, xml, 0, before, manifest=manifest)
    assert report['profile'] == 'junit_only' and not report['software_acceptance']
    assert 'independent_collection_missing' in report['reasons']
    gate = root/'gate.json'
    gate.write_text(json.dumps({**report, 'software_acceptance': True}), encoding='utf-8')
    assert not gr.verify_gate_report(gate, manifest)


def test_changed_test_sources_invalidate_the_cut(cut):
    root, before, manifest, xml = cut
    (root/'tests/test_value.py').write_text('VALUE=2\n', encoding='utf-8')
    report = gr.build_gate_report(root, xml, 0, before, manifest=manifest)
    assert not report['source_state_stable'] and not report['software_acceptance']


def test_boolean_exit_code_is_not_success(cut):
    root, before, manifest, xml = cut
    assert not gr.build_gate_report(root, xml, False, before, manifest=manifest)['software_acceptance']


def test_missing_junit_is_a_recorded_rejection(cut):
    root, before, manifest, xml = cut
    xml.unlink()
    report = gr.build_gate_report(root, xml, 3, before, manifest=manifest)
    assert not report['software_acceptance'] and 'junit_unavailable' in report['reasons']
