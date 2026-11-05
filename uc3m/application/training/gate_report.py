"""Bind a strict fresh-profile JUnit to the tested source cut and campaign."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Mapping

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.preflight import hash_files, source_snapshot

COUNTERS = ('tests', 'failures', 'errors', 'skipped')
SCOPES = ('tests/fresh_training', 'tests')
CONTEXT_KEYS = ('git_head', 'source_sha256', 'test_source_sha256')
PYTEST_CONFIG_FILES = ('pytest.ini', '.pytest.ini', 'pyproject.toml', 'tox.ini', 'setup.cfg')
DISCOVERY_RULES = ('python_files', 'python_classes', 'python_functions', 'testpaths', 'norecursedirs')
# Only tests/fresh_training/gate_fixture.py turns this on. Hashes detect corruption and
# incoherent edits, not forgery: whoever can rewrite every artefact can forge a gate,
# so a gate is evidence only under custody of the people who ran it.
ACCEPT_SYNTHETIC_FIXTURES = False


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _context_valid(value) -> bool:
    return (isinstance(value, dict) and set(value) == set(CONTEXT_KEYS)
            and all(isinstance(value[k], str) and len(value[k]) == (40 if k == 'git_head' else 64)
                    and all(c in '0123456789abcdef' for c in value[k]) for k in CONTEXT_KEYS))


def test_source_digest(root: Path) -> str:
    root = Path(root).resolve()
    selected = {p for p in (root/'tests').rglob('*')
                if p.is_file() and (p.suffix == '.py' or p.name in PYTEST_CONFIG_FILES)
                and '__pycache__' not in p.parts}
    selected.update(root/name for name in (*PYTEST_CONFIG_FILES, 'conftest.py') if (root/name).is_file())
    paths = [contained_path(root, p.relative_to(root).as_posix()) for p in selected]
    return hash_files(root, paths, normalize_newlines=True)


def git_head(root: Path) -> str:
    return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True,
                          text=True, check=True).stdout.strip()


def capture_context(root: Path) -> dict:
    return {'git_head': git_head(root), 'source_sha256': source_snapshot(root, scope='fresh'),
            'test_source_sha256': test_source_digest(root)}


def junit_totals(path: Path) -> dict:
    """Count actual cases/outcomes and reject lying aggregate attributes."""
    if path.stat().st_size > 64*1024*1024:
        raise ValueError('JUnit exceeds the 64 MiB gate limit')
    root = ET.parse(path).getroot()
    if root.tag not in {'testsuite', 'testsuites'}:
        raise ValueError('not a JUnit document')
    def counts(node):
        cases = list(node.iter('testcase'))
        return {'tests': len(cases), **{key: sum(c.find(tag) is not None for c in cases)
                for key, tag in [('failures', 'failure'), ('errors', 'error'), ('skipped', 'skipped')]}}
    for suite in root.iter('testsuite'):
        actual = counts(suite)
        if any(int(suite.get(key, '-1')) != actual[key] for key in COUNTERS):
            raise ValueError('JUnit counters do not match its cases')
    return counts(root)


def _json_artifact(path: Path) -> dict:
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) > 64*1024*1024:
        raise ValueError('gate evidence exceeds 64 MiB')
    payload = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(payload, dict):
        raise ValueError('gate evidence must be an object')
    return {'path': path.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'payload': payload}


def _read_artifact(folder: Path, record) -> dict:
    if not isinstance(record, dict):
        raise ValueError('missing evidence record')
    actual = _json_artifact(contained_path(folder, record['path']))
    if actual['sha256'] != record.get('sha256') or actual['payload'] != record.get('payload'):
        raise ValueError('evidence hash or embedded payload changed')
    actual['path'] = record['path']
    return actual


def validate_invocation(arguments, *, project_root, scope, mode):
    """Allow only the gate's explicit CLI; discovery overrides are not a scope.

    Shared by plugin and offline readback. No filesystem access is needed here.
    -c is deliberately unsupported; implicit configuration must be hash-bound.
    """
    if not isinstance(arguments, list) or not all(isinstance(a, str) for a in arguments):
        raise ValueError('pytest arguments must be a list of strings')
    def normal(value):
        return value.replace('\\', '/').rstrip('/').casefold()
    seen, positional, collect_only, plugin, i = set(), [], False, False, 0
    value_options = {'--rootdir', '--confcutdir', '--gate-mode', '--gate-scope', '--gate-context',
                     '--gate-evidence', '--gate-inventory', '--junitxml', '--junit-xml', '--tb'}
    while i < len(arguments):
        arg = arguments[i]
        i += 1
        if arg == scope:
            positional.append(arg)
            continue
        if arg in ('-q', '--quiet', '-v', '--verbose'):
            continue
        if arg == '--collect-only':
            if collect_only:
                raise ValueError('duplicate collect-only option')
            collect_only = True
            continue
        if arg.startswith('-r') and not arg.startswith('--'):
            value = arg[2:]
            if not value and i < len(arguments):
                value, i = arguments[i], i + 1
            if not value or any(c not in 'fEsxXwPpaA' for c in value):
                raise ValueError('unsupported pytest report option')
            continue
        if arg in ('-o', '--override-ini') or arg.startswith(('-o', '--override-ini=')):
            if arg in ('-o', '--override-ini'):
                value = arguments[i] if i < len(arguments) else None
                i += 1
            else:
                value = arg[2:] if arg.startswith('-o') else arg.split('=', 1)[1]
            if value != 'addopts=':
                raise ValueError('only the empty addopts= override is authorized')
            continue
        if arg == '-p' or (arg.startswith('-p') and not arg.startswith('--')):
            if arg == '-p':
                value = arguments[i] if i < len(arguments) else None
                i += 1
            else:
                value = arg[2:]
            if value not in ('no:cacheprovider', 'uc3m.application.training.gate_pytest'):
                raise ValueError('unsupported explicit pytest plugin')
            plugin = plugin or value == 'uc3m.application.training.gate_pytest'
            continue
        name, separator, inline = arg.partition('=')
        if name not in value_options:
            raise ValueError('unauthorized pytest argument: ' + arg)
        if separator:
            value = inline
        else:
            value = arguments[i] if i < len(arguments) else None
            i += 1
        if value is None or name in seen:
            raise ValueError('missing or duplicate pytest option: ' + name)
        seen.add(name)
        if name in ('--rootdir', '--confcutdir') and normal(value) != normal(project_root):
            raise ValueError(name + ' must equal the declared project root')
        if name == '--gate-mode' and value != mode:
            raise ValueError('pytest gate mode changed')
        if name == '--gate-scope' and value != scope:
            raise ValueError('pytest gate scope changed')
        if name == '--tb' and value not in ('auto', 'long', 'short', 'line', 'native', 'no'):
            raise ValueError('unsupported traceback option')
    if (positional != [scope] or collect_only != (mode == 'collection') or not plugin
            or not {'--rootdir', '--confcutdir', '--gate-mode', '--gate-scope', '--gate-context',
                    '--gate-evidence'}.issubset(seen)):
        raise ValueError('pytest invocation does not match the explicit gate contract')


def _check_discovery(payload):
    discovery = payload.get('discovery_config')
    if not isinstance(discovery, dict) or set(discovery) != {'config_file', 'config_sha256', 'rules'}:
        raise ValueError('effective pytest discovery configuration missing')
    config_file, config_hash = discovery['config_file'], discovery['config_sha256']
    if config_file is None:
        if config_hash is not None:
            raise ValueError('unexpected pytest configuration hash')
    elif (not isinstance(config_file, str) or '\\' in config_file or ':' in config_file
          or '..' in Path(config_file).parts or Path(config_file).is_absolute()
          or Path(config_file).name not in PYTEST_CONFIG_FILES
          or (len(Path(config_file).parts) > 1 and not config_file.startswith('tests/'))
          or not isinstance(config_hash, str) or len(config_hash) != 64):
        raise ValueError('pytest configuration is not a contained hash-bound discovery input')
    rules = discovery['rules']
    if (not isinstance(rules, dict) or set(rules) != set(DISCOVERY_RULES)
            or any(not isinstance(v, list) or not all(isinstance(x, str) for x in v) for v in rules.values())
            or not isinstance(payload.get('pytest_version'), str) or not payload['pytest_version']):
        raise ValueError('effective pytest discovery rules or version missing')
    return discovery


def _check_session(payload, *, mode, context, project_root, scope):
    if (not isinstance(payload, dict) or payload.get('schema_version') != 1
            or payload.get('kind') != 'pytest_' + mode or payload.get('mode') != mode
            or payload.get('scope') != scope or scope not in SCOPES
            or payload.get('project_root') != project_root
            or payload.get('scope_args') != [scope]
            or payload.get('collect_only') is not (mode == 'collection')
            or payload.get('complete') is not True
            or type(payload.get('exit_code')) is not int or payload['exit_code'] != 0
            or payload.get('filters') != []
            or any(type(payload.get(k)) is not int or payload[k] != 0
                   for k in ('deselected', 'collection_errors', 'collection_skipped'))
            or payload.get('context') != context or payload.get('source_before') != context
            or payload.get('source_after') != context or not _context_valid(context)
            or payload.get('context_sha256') != _digest(context)):
        raise ValueError('pytest session is not an unfiltered complete source-bound scope')
    arguments = payload.get('arguments')
    if (not isinstance(arguments, list) or not all(isinstance(v, str) for v in arguments)
            or arguments.count(scope) != 1
            or ('--collect-only' in arguments) != (mode == 'collection')
            or not isinstance(payload.get('environment_addopts'), str)
            or payload['environment_addopts'].strip() or payload.get('ini_addopts') != []):
        raise ValueError('pytest invocation options are not an explicit unfiltered scope')
    validate_invocation(arguments, project_root=project_root, scope=scope, mode=mode)
    _check_discovery(payload)
    omissions = payload.get('omissions')
    if (not isinstance(omissions, dict) or set(omissions) != {'skipped', 'xfail', 'xpass'}
            or any(type(v) is not int or v != 0 for v in omissions.values())):
        raise ValueError('pytest omitted or unexpectedly passed tests')
    ids = payload.get('nodeids')
    if not isinstance(ids, list) or not ids or not all(isinstance(n, str) for n in ids):
        raise ValueError('missing independent nodeids')
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate pytest nodeids')
    for nodeid in ids:
        filename, separator, case = nodeid.partition('::')
        if (not separator or not case or not filename.startswith(scope + '/')
                or '\\' in filename or '..' in Path(filename).parts or ':' in filename):
            raise ValueError('nodeid outside the declared full scope')
    plugin_hash = payload.get('plugin_sha256')
    if plugin_hash != hashlib.sha256(Path(__file__).with_name('gate_pytest.py').read_bytes()).hexdigest():
        raise ValueError('pytest evidence was not produced by the current gate plugin')
    return ids


def _junit_nodeids(junit: Path, *, scope, context_hash, inventory_hash):
    nodeids, references = [], set()
    for case in ET.parse(junit).getroot().iter('testcase'):
        properties = {}
        for prop in case.findall('properties/property'):
            name = prop.get('name')
            if name.startswith('gate_'):
                if name in properties:
                    raise ValueError('duplicate JUnit gate property')
                properties[name] = prop.get('value')
        if (properties.get('gate_scope') != scope
                or properties.get('gate_context_sha256') != context_hash
                or properties.get('gate_inventory_sha256') != inventory_hash
                or not properties.get('gate_nodeid') or not properties.get('gate_execution')):
            raise ValueError('JUnit missing exact nodeid and evidence binding')
        nodeids.append(properties['gate_nodeid'])
        references.add(properties['gate_execution'])
    if len(references) != 1:
        raise ValueError('JUnit execution reference must be unique')
    return nodeids, references.pop()


def _coverage(junit, collection, execution, *, context, project_root):
    inventory = collection['payload']
    scope = inventory.get('scope')
    expected = _check_session(inventory, mode='collection', context=context,
                              project_root=project_root, scope=scope)
    run = execution['payload']
    actual = _check_session(run, mode='execution', context=context,
                            project_root=project_root, scope=scope)
    if (run['discovery_config'] != inventory['discovery_config']
            or run['pytest_version'] != inventory['pytest_version']):
        raise ValueError('pytest discovery configuration differs between collection and execution')
    if (run.get('inventory_sha256') != collection['sha256']
            or run.get('plugin_sha256') != inventory.get('plugin_sha256')
            or run.get('junit_sha256') != hashlib.sha256(Path(junit).read_bytes()).hexdigest()):
        raise ValueError('execution not bound to the independent inventory and JUnit')
    junit_ids, reference = _junit_nodeids(Path(junit), scope=scope, context_hash=_digest(context),
                                        inventory_hash=collection['sha256'])
    # Order is immaterial; repetitions and missing cases are never interchangeable.
    if Counter(expected) != Counter(actual) or Counter(expected) != Counter(junit_ids):
        raise ValueError('executed JUnit nodeid multiset differs from independent collection')
    reports = run.get('reports')
    if not isinstance(reports, list):
        raise ValueError('runtime phase reports missing')
    for phase in ('setup', 'call', 'teardown'):
        phase_reports = [r for r in reports if r.get('when') == phase]
        if (Counter(r.get('nodeid') for r in phase_reports) != Counter(expected)
                or any(r.get('outcome') != 'passed' or r.get('wasxfail') is not False for r in phase_reports)):
            raise ValueError('runtime phases are incomplete or omitted')
    if len(reports) != 3*len(expected):
        raise ValueError('unexpected extra runtime reports')
    fresh = [nodeid for nodeid in expected if nodeid.startswith('tests/fresh_training/')]
    if not fresh:
        raise ValueError('full repository gate lacks the fresh-training subset')
    return {'complete': True, 'scope': scope, 'nodeids': expected, 'fresh_nodeids': fresh,
            'nodeids_sha256': _digest(sorted(expected)), 'execution_reference': reference}


def _test_files_without_cases(root: Path, scope: str, nodeids) -> list:
    """Test modules on disk with no collected case: a committed filter is still a filter."""
    collected = {nodeid.partition('::')[0] for nodeid in nodeids}
    on_disk = {p.relative_to(root).as_posix() for p in (root/scope).rglob('test_*.py') if '__pycache__' not in p.parts}
    return sorted(on_disk - collected)


def verify_gate_report(path: Path, manifest: Mapping) -> bool:
    try:
        path = Path(path)
        path = contained_path(path.parent, path.name)
        gate = json.loads(path.read_text(encoding='utf-8-sig'))
        identity = manifest['identity']
        if not isinstance(gate, dict) or not isinstance(identity, dict):
            return False
        if gate.get('fixture_only') and not ACCEPT_SYNTHETIC_FIXTURES:
            return False
        if (gate.get('schema_version') != 3 or gate.get('profile') not in ('fresh', 'repository')
                or type(gate.get('exit_code')) is not int or gate['exit_code'] != 0
                or gate.get('software_acceptance') is not True
                or gate.get('source_state_stable') is not True
                or gate.get('campaign_binding_matches') is not True
                or gate.get('campaign_id') != manifest.get('campaign_id')
                or gate.get('spec_hash') != manifest.get('spec_hash')):
            return False
        for report_key, identity_key in [('source_sha256', 'source_sha256'),
                                         ('test_source_sha256', 'test_source_sha256'),
                                         ('git_head', 'source_git_head')]:
            expected = identity.get(identity_key)
            if not isinstance(expected, str) or not expected or gate.get(report_key) != expected:
                return False
        junit = contained_path(path.parent, gate['junit'])
        if hashlib.sha256(junit.read_bytes()).hexdigest() != gate.get('junit_sha256'):
            return False
        before, after = gate.get('source_before'), gate.get('source_after')
        if not _context_valid(before) or before != after or any(gate.get(k) != after[k] for k in CONTEXT_KEYS):
            return False
        collection = _read_artifact(path.parent, gate.get('collection'))
        execution = _read_artifact(path.parent, gate.get('execution'))
        coverage = _coverage(junit, collection, execution, context=after, project_root=gate.get('project_root'))
        if coverage != gate.get('coverage') or execution['path'] != coverage['execution_reference']:
            return False
        if gate['profile'] != ('fresh' if coverage['scope'] == 'tests/fresh_training' else 'repository'):
            return False
        actual = junit_totals(junit)
        counters = gate.get('counters')
        return (isinstance(counters, dict) and actual['tests'] > 0
                and all(type(counters.get(k)) is int and counters[k] == actual[k] for k in COUNTERS)
                and all(actual[k] == 0 for k in COUNTERS[1:])
                and all(type(counters.get(k, 0)) is int and counters.get(k, 0) == 0
                        for k in ('xfail', 'xpass')))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, ET.ParseError):
        return False


def build_gate_report(root: Path, junit: Path, exit_code: int, before: Mapping, *, manifest=None, collection=None) -> dict:
    root, junit = Path(root).resolve(), Path(junit)
    after = capture_context(root)
    reasons = []
    try:
        counters = junit_totals(junit)
        junit_hash = hashlib.sha256(Path(junit).read_bytes()).hexdigest()
    except (OSError, ValueError, ET.ParseError):
        counters, junit_hash = {key: 0 for key in COUNTERS}, None
        reasons.append('junit_unavailable')
    stable = dict(before) == after
    identity = (manifest or {}).get('identity', {})
    bound = manifest is None or all(after[key] == identity.get(identity_key) for key, identity_key in
                                   [('git_head', 'source_git_head'), ('source_sha256', 'source_sha256'),
                                    ('test_source_sha256', 'test_source_sha256')])
    inventory_record, execution_record = None, None
    coverage = {'complete': False, 'scope': None, 'nodeids': [], 'fresh_nodeids': []}
    if collection is None:
        reasons.append('independent_collection_missing')
    else:
        try:
            inventory_record = _json_artifact(Path(collection))
            _, reference = _junit_nodeids(
                junit, scope=inventory_record['payload'].get('scope'), context_hash=_digest(after),
                inventory_hash=inventory_record['sha256'])
            execution_record = _json_artifact(contained_path(junit.parent, reference))
            execution_record['path'] = reference
            coverage = _coverage(junit, inventory_record, execution_record, context=after, project_root=str(root))
            uncollected = _test_files_without_cases(root, coverage['scope'], coverage['nodeids'])
            if uncollected:
                reasons.append('test_files_not_collected:' + ','.join(uncollected))
        except (OSError, ValueError, TypeError, KeyError, AttributeError, ET.ParseError) as exc:
            reasons.append('incomplete_collection_or_execution:' + str(exc))
    profile = ('fresh' if coverage['scope'] == 'tests/fresh_training' else 'repository') if coverage['complete'] else 'junit_only'
    return {'schema_version': 3, 'profile': profile, **after, 'reasons': reasons,
            'project_root': str(root), 'source_before': dict(before), 'source_after': after,
            'collection': inventory_record, 'execution': execution_record, 'coverage': coverage,
            'campaign_id': (manifest or {}).get('campaign_id'), 'spec_hash': (manifest or {}).get('spec_hash'),
            'source_state_stable': stable, 'campaign_binding_matches': bound,
            'exit_code': exit_code, 'counters': counters, 'junit': Path(junit).name,
            'junit_sha256': junit_hash,
            'software_acceptance': (type(exit_code) is int and exit_code == 0 and stable and bound and counters['tests'] > 0
                                    and coverage['complete'] and not reasons
                                    and not any(counters[k] for k in COUNTERS[1:])),
            'scientific_acceptance': False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--junit', type=Path)
    parser.add_argument('--exit-code', type=int)
    parser.add_argument('--source-before', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--collection', type=Path)
    args = parser.parse_args(argv)
    if args.capture:
        payload = capture_context(args.project_root)
    else:
        if args.junit is None or args.source_before is None or args.exit_code is None:
            parser.error('building a gate needs --junit, --exit-code and --source-before')
        manifest = json.loads(args.manifest.read_text(encoding='utf-8')) if args.manifest else None
        before = json.loads(args.source_before.read_text(encoding='utf-8'))
        payload = build_gate_report(args.project_root, args.junit, args.exit_code, before, manifest=manifest,
                                    collection=args.collection)
        payload['junit'] = Path(args.junit).resolve().relative_to(args.output.parent.resolve()).as_posix()
        if args.collection is not None and payload['collection'] is not None:
            payload['collection']['path'] = args.collection.resolve().relative_to(args.output.parent.resolve()).as_posix()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
