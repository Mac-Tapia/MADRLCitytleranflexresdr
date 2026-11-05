"""Explicitly synthetic schema 3 gate evidence for consumer tests.

Consumers of verify_gate_report need a complete gate without re-running the whole
profile recursively. Every artefact is marked fixture_only: it is never evidence of
a real run. The real plugin is exercised in tests/remediation/test_i13_gate_inventory.py.
"""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from uc3m.application.training import gate_report

SCOPE = 'tests/fresh_training'
PLUGIN = 'uc3m.application.training.gate_pytest'
PLUGIN_SHA256 = hashlib.sha256(Path(gate_report.__file__).with_name('gate_pytest.py').read_bytes()).hexdigest()
gate_report.ACCEPT_SYNTHETIC_FIXTURES = True  # production code never imports this module


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _dump(path, payload):
    raw = json.dumps(payload).encode('utf-8')
    Path(path).write_bytes(raw)
    return {'path': Path(path).name, 'sha256': hashlib.sha256(raw).hexdigest(), 'payload': payload}


def _session(mode, root, context, nodeids, evidence):
    arguments = [SCOPE, '-q', '-p', 'no:cacheprovider', '-o', 'addopts=', '-p', PLUGIN, f'--rootdir={root}',
                 f'--confcutdir={root}', f'--gate-scope={SCOPE}', '--gate-context=sources.json',
                 f'--gate-mode={mode}', f'--gate-evidence={evidence}']
    if mode == 'collection':
        arguments.append('--collect-only')
    return {'schema_version': 1, 'kind': f'pytest_{mode}', 'mode': mode, 'fixture_only': True,
            'project_root': root, 'scope': SCOPE, 'scope_args': [SCOPE], 'collect_only': mode == 'collection',
            'context': context, 'context_sha256': _digest(context), 'source_before': context, 'source_after': context,
            'arguments': arguments, 'environment_addopts': '', 'ini_addopts': [], 'filters': [],
            'deselected': 0, 'collection_errors': 0, 'collection_skipped': 0, 'nodeids': list(nodeids), 'reports': [],
            'omissions': {'skipped': 0, 'xfail': 0, 'xpass': 0}, 'exit_code': 0, 'complete': True,
            'plugin_sha256': PLUGIN_SHA256, 'pytest_version': 'fixture',
            'discovery_config': {'config_file': None, 'config_sha256': None,
                                 'rules': {'python_files': [], 'python_classes': [], 'python_functions': [],
                                           'testpaths': [], 'norecursedirs': []}}}


def synthetic_gate(folder, *, context, campaign_id, spec_hash, tests=10, failures=0, errors=0, skipped=0):
    """Serialize collection -> JUnit -> execution -> gate, each hash taken from the real bytes."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    root = str(folder.resolve())
    nodeids = [f'{SCOPE}/test_fixture.py::test_{i}' for i in range(tests)]
    collection = _dump(folder/'gate_collection.json', _session('collection', root, context, nodeids, 'gate_collection.json'))
    counters = {'tests': tests, 'failures': failures, 'errors': errors, 'skipped': skipped}
    suite = ET.Element('testsuite', {k: str(v) for k, v in counters.items()})
    for index, nodeid in enumerate(nodeids):
        case = ET.SubElement(suite, 'testcase', name=f'test_{index}')
        properties = ET.SubElement(case, 'properties')
        for name, value in (('gate_nodeid', nodeid), ('gate_scope', SCOPE), ('gate_context_sha256', _digest(context)),
                            ('gate_inventory_sha256', collection['sha256']), ('gate_execution', 'gate_execution.json')):
            ET.SubElement(properties, 'property', name=name, value=value)
        if index < skipped:
            ET.SubElement(case, 'skipped')
        elif index < skipped + failures:
            ET.SubElement(case, 'failure')
        elif index < skipped + failures + errors:
            ET.SubElement(case, 'error')
    junit = folder/'gate.xml'
    ET.ElementTree(suite).write(junit, encoding='utf-8', xml_declaration=True)
    junit_hash = hashlib.sha256(junit.read_bytes()).hexdigest()
    run = _session('execution', root, context, nodeids, 'gate_execution.json')
    run.update(inventory_sha256=collection['sha256'], junit_sha256=junit_hash, execution_reference='gate_execution.json')
    run['arguments'] = [*run['arguments'], '--gate-inventory=gate_collection.json', '--junitxml=gate.xml']
    run['reports'] = [{'nodeid': n, 'when': when, 'outcome': 'passed', 'wasxfail': False}
                      for n in nodeids for when in ('setup', 'call', 'teardown')]
    execution = _dump(folder/'gate_execution.json', run)
    clean = not (failures or errors or skipped)
    gate = {'schema_version': 3, 'profile': 'fresh', 'fixture_only': True, **context, 'reasons': [],
            'project_root': root, 'source_before': context, 'source_after': context,
            'collection': collection, 'execution': execution,
            'coverage': {'complete': True, 'scope': SCOPE, 'nodeids': nodeids, 'fresh_nodeids': nodeids,
                         'nodeids_sha256': _digest(sorted(nodeids)), 'execution_reference': 'gate_execution.json'},
            'campaign_id': campaign_id, 'spec_hash': spec_hash, 'source_state_stable': True,
            'campaign_binding_matches': True, 'exit_code': 0, 'counters': counters, 'junit': junit.name,
            'junit_sha256': junit_hash, 'software_acceptance': clean, 'scientific_acceptance': False}
    path = folder/'gate.json'
    path.write_text(json.dumps(gate), encoding='utf-8')
    return path
