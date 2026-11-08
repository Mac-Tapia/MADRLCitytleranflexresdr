"""SPEC-017 FR-017.5: every owner decision and rule of SPEC-015, SPEC-016 and SPEC-017 has a trace.

Each identifier found in the three specs needs an entry in ``governance/decision_traceability.yaml``:
either ``code`` (repo-relative files that carry the identifier) or ``no_code`` with a kind and a reason.
The checker is a pure function so a falsified registry can prove that it rejects what it must reject.
"""
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / 'governance' / 'decision_traceability.yaml'
SPECS = ('specs/015-modulo3-algoritmos/spec.md', 'specs/016-iquitos-v6/spec.md',
         'specs/017-universalidad/spec.md')
ID_PATTERN = re.compile(r'(?:D-V6-\d+|D-M3-\d+|D-017-\d+|P-V6-\d+|P-M3-\d+|P-017-\d+|FR-01[567]\.\d+)(?!\d)')
CODE_ROOTS = ('uc3m/', 'tools/', 'configs/', 'CityLearn/citylearn/', 'CityLearn/scripts/', 'scripts/')
KINDS = ('superseded', 'process', 'pending', 'rationale')


class _UniqueKeyLoader(yaml.SafeLoader):
    """A repeated identifier would silently overwrite its first entry; reject it instead."""


def _unique_mapping(loader, node, deep=False):
    keys = [loader.construct_object(k, deep=deep) for k, _ in node.value]
    repeated = sorted({k for k in keys if keys.count(k) > 1})
    if repeated:
        raise yaml.constructor.ConstructorError(None, None, f'repeated keys {repeated}', node.start_mark)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def spec_identifiers(texts):
    """Identifiers named anywhere in the spec texts."""
    return {m.group(0) for text in texts for m in ID_PATTERN.finditer(text)}


def _tagged(identifier, text):
    return re.search(re.escape(identifier) + r'(?!\d)', text) is not None


def check_traceability(identifiers, registry, read_file):
    """Violations of the registry against the spec identifiers.

    ``read_file(path)`` returns the text of a repo-relative path, or None when the path does not exist.
    """
    out = []
    decisions = registry.get('decisions') or {}
    untagged = list(registry.get('implemented_without_tag') or [])
    for ident in sorted(set(identifiers) - set(decisions)):
        out.append(f'{ident}: no entry in the registry')
    for ident in sorted(set(decisions) - set(identifiers)):
        out.append(f'{ident}: entry for an identifier absent from the specs')
    for ident in sorted(set(u for u in untagged if untagged.count(u) > 1)):
        out.append(f'{ident}: repeated in implemented_without_tag')
    for ident, entry in sorted(decisions.items()):
        entry = entry or {}
        has_code, has_no_code = 'code' in entry, 'no_code' in entry
        if has_code == has_no_code:
            out.append(f'{ident}: needs exactly one of code or no_code')
            continue
        if has_code:
            paths = entry['code']
            if not isinstance(paths, list) or not paths:
                out.append(f'{ident}: code must be a non-empty list of paths')
                continue
            for path in paths:
                if not str(path).startswith(CODE_ROOTS):
                    out.append(f'{ident}: {path} is outside the code roots {CODE_ROOTS}')
                    continue
                text = read_file(path)
                if text is None:
                    out.append(f'{ident}: {path} does not exist')
                elif not _tagged(ident, text):
                    out.append(f'{ident}: {path} does not contain the identifier')
            if ident in untagged:
                out.append(f'{ident}: listed in implemented_without_tag but traced by code')
            continue
        no_code = entry['no_code'] or {}
        kind = no_code.get('kind')
        if kind not in KINDS:
            out.append(f'{ident}: kind {kind!r} is not one of {KINDS}')
        if not str(no_code.get('reason') or '').strip():
            out.append(f'{ident}: no_code without a reason')
        target = no_code.get('superseded_by')
        if kind == 'superseded':
            if not target:
                out.append(f'{ident}: superseded without superseded_by')
            elif target not in identifiers:
                out.append(f'{ident}: superseded_by {target} is not an identifier of the specs')
            elif target == ident:
                out.append(f'{ident}: superseded by itself')
        elif target is not None:
            out.append(f'{ident}: superseded_by is only for kind superseded')
        implemented_in = no_code.get('implemented_in')
        if (implemented_in is not None) != (ident in untagged):
            out.append(f'{ident}: implemented_in and implemented_without_tag must go together')
        if implemented_in is not None:
            if kind != 'pending':
                out.append(f'{ident}: implemented without tag must be kind pending')
            if not isinstance(implemented_in, list) or not implemented_in:
                out.append(f'{ident}: implemented_in must be a non-empty list of paths')
            else:
                for path in implemented_in:
                    if read_file(path) is None:
                        out.append(f'{ident}: implemented_in {path} does not exist')
    for ident in sorted(set(untagged) - set(decisions)):
        out.append(f'{ident}: in implemented_without_tag without an entry')
    return out


def _read_repo_file(path):
    full = REPO / path
    return full.read_text(encoding='utf-8') if full.is_file() else None


def _load_registry():
    return yaml.load(REGISTRY.read_text(encoding='utf-8'), Loader=_UniqueKeyLoader)


def _repo_identifiers():
    return spec_identifiers((REPO / s).read_text(encoding='utf-8') for s in SPECS)


def test_every_spec_decision_and_rule_is_traced():
    identifiers = _repo_identifiers()
    assert len(identifiers) >= 100, 'the spec parser found too few identifiers'
    violations = check_traceability(identifiers, _load_registry(), _read_repo_file)
    assert violations == [], '\n'.join(violations)


def test_registry_rejects_repeated_identifiers():
    import pytest
    with pytest.raises(yaml.constructor.ConstructorError):
        yaml.load('decisions:\n  D-V6-1: {code: [a]}\n  D-V6-1: {code: [b]}\n', Loader=_UniqueKeyLoader)


def test_spec_parser_does_not_take_a_prefix_of_a_longer_identifier():
    assert spec_identifiers(['D-V6-50 and FR-016.10, D04, D-VD.3']) == {'D-V6-50', 'FR-016.10'}


def test_checker_rejects_a_falsified_registry():
    files = {'uc3m/a.py': '# D-V6-1, D-V6-10 and D-V6-50','configs/b.yaml': 'nothing here', 'tests/t.py': 'D-V6-2'}
    identifiers = {'D-V6-1', 'D-V6-2', 'D-V6-3', 'D-V6-5', 'D-V6-7', 'D-V6-8', 'P-V6-1'}
    registry = {
        'implemented_without_tag': ['D-V6-8', 'D-V6-99'],
        'decisions': {
            'D-V6-1': {'code': ['uc3m/a.py']},                         # valid
            'D-V6-2': {'code': ['configs/b.yaml']},                    # path without the tag
            # D-V6-3: missing entry
            'D-V6-5': {'code': ['tests/t.py']},                        # outside the code roots
            'D-V6-7': {'no_code': {'kind': 'superseded', 'reason': 'x', 'superseded_by': 'D-V6-77'}},
            'D-V6-8': {'no_code': {'kind': 'pending', 'reason': 'untagged',
                                   'implemented_in': ['uc3m/missing.py']}},
            'P-V6-1': {'no_code': {'kind': 'obsolete', 'reason': ''}},
            'D-V6-10': {'code': ['uc3m/a.py']},                        # absent from the specs
        }}
    violations = check_traceability(identifiers, registry, files.get)
    expected = ['D-V6-3: no entry', 'D-V6-10: entry for an identifier absent',
                'D-V6-2: configs/b.yaml does not contain', 'D-V6-5: tests/t.py is outside',
                'D-V6-7: superseded_by D-V6-77 is not', 'D-V6-8: implemented_in uc3m/missing.py does not exist',
                "P-V6-1: kind 'obsolete'", 'P-V6-1: no_code without a reason',
                'D-V6-99: in implemented_without_tag without an entry']
    for fragment in expected:
        assert any(v.startswith(fragment) for v in violations), (fragment, violations)
    assert not any(v.startswith('D-V6-1:') for v in violations), violations
    assert len(violations) == len(expected), violations


def test_checker_rejects_the_tag_of_a_longer_identifier():
    files = {'uc3m/a.py': 'only D-V6-10 here'}
    violations = check_traceability({'D-V6-1'}, {'decisions': {'D-V6-1': {'code': ['uc3m/a.py']}}}, files.get)
    assert violations == ['D-V6-1: uc3m/a.py does not contain the identifier']
