"""A gate run must be visible while it runs, must not idle-sleep and must not hang forever."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from uc3m.application.training import gate_pytest, gate_report as gr

REPO = Path(__file__).resolve().parents[2]
PLUGIN = 'uc3m.application.training.gate_pytest'
SCOPE = 'tests/fresh_training'
HOUR = 3600


def _repo(root, body):
    """A temporary Git cut, so the real repository's context never enters the test."""
    hooks = root/'empty_hooks'
    hooks.mkdir()
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                    'scripts/verify_project_context.ps1'], cwd=REPO, check=True, capture_output=True, text=True)
    git = ['git', '-c', f'core.hooksPath={hooks}']
    subprocess.run([*git, 'init', '-q', str(root)], check=True)
    subprocess.run([*git, '-c', 'user.name=Gate temporary test', '-c', 'user.email=gate@example.invalid',
                    'commit', '--allow-empty', '-qm', 'isolated cut'], cwd=root, check=True)
    (root/SCOPE).mkdir(parents=True)
    (root/'pytest.ini').write_text('[pytest]\n', encoding='utf-8')
    (root/SCOPE/'test_body.py').write_text(body, encoding='utf-8')
    return root


def _run(root, mode, env=None, inventory=None):
    folder = root/'artifacts'
    folder.mkdir(exist_ok=True)
    context = folder/'context.json'
    before = gr.capture_context(root)
    context.write_text(json.dumps(before), encoding='utf-8')
    evidence, junit = folder/f'{mode}.json', folder/'junit.xml'
    args = [SCOPE, '-q', '-p', 'no:cacheprovider', '-p', PLUGIN, f'--rootdir={root}', f'--confcutdir={root}',
            f'--gate-mode={mode}', f'--gate-scope={SCOPE}', f'--gate-context={context}', f'--gate-evidence={evidence}']
    args += ['--collect-only'] if mode == 'collection' else [f'--gate-inventory={inventory}', f'--junitxml={junit}']
    full_env = dict(os.environ, PYTHONPATH=str(REPO), PYTEST_ADDOPTS='', PYTEST_PLUGINS='',
                    PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1', **(env or {}))
    result = subprocess.run([sys.executable, '-B', '-m', 'pytest', *args], cwd=root, env=full_env,
                            capture_output=True, text=True, timeout=300)
    return result, evidence, junit, before


def _events(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def test_every_test_is_recorded_as_it_starts_and_finishes(tmp_path):
    root = _repo(tmp_path, 'def test_one():\n    pass\n\ndef test_two():\n    assert False\n')
    _, inventory, _, _ = _run(root, 'collection')
    result, evidence, _, _ = _run(root, 'execution', inventory=inventory)
    assert result.returncode == 1  # test_two really fails; the record must not hide it.
    events = _events(evidence.with_suffix('.progress.jsonl'))
    one, two = f'{SCOPE}/test_body.py::test_one', f'{SCOPE}/test_body.py::test_two'
    assert [(e['event'], e['nodeid']) for e in events if e['event'] in ('start', 'finish')] == [
        ('start', one), ('finish', one), ('start', two), ('finish', two)]
    finished = {e['nodeid']: e for e in events if e['event'] == 'finish'}
    assert finished[one]['outcome'] == 'passed' and finished[two]['outcome'] == 'failed'
    assert all(e['seconds'] >= 0 for e in finished.values())


def test_liveness_fields_do_not_break_a_complete_certified_run(tmp_path):
    root = _repo(tmp_path, 'def test_one():\n    pass\n')
    _, inventory, _, _ = _run(root, 'collection')
    result, evidence, junit, before = _run(root, 'execution', inventory=inventory)
    assert result.returncode == 0, result.stdout + result.stderr
    liveness = json.loads(evidence.read_text(encoding='utf-8'))['liveness']
    assert liveness['watchdog_seconds'] == gate_pytest.WATCHDOG_SECONDS
    assert liveness['progress'] == 'execution.progress.jsonl' and liveness['gaps'] == 0
    assert liveness['system_awake_held'] is (os.name == 'nt')
    assert not evidence.with_suffix('.hang.txt').exists()
    report = gr.build_gate_report(root, junit, 0, before, collection=inventory)
    assert report['software_acceptance'] is True, report


def test_a_hung_test_is_stopped_with_its_stack_and_the_gate_is_rejected(tmp_path):
    root = _repo(tmp_path, 'import time\n\ndef test_hangs():\n    time.sleep(600)\n')
    _, inventory, _, _ = _run(root, 'collection')
    result, evidence, junit, before = _run(root, 'execution', env={gate_pytest.WATCHDOG_ENV: '3'}, inventory=inventory)
    assert result.returncode != 0
    assert 'test_hangs' in evidence.with_suffix('.hang.txt').read_text(encoding='utf-8')
    events = _events(evidence.with_suffix('.progress.jsonl'))
    assert events[-1]['event'] == 'start' or events[-1]['current'] == f'{SCOPE}/test_body.py::test_hangs'
    assert not junit.exists()
    report = gr.build_gate_report(root, junit, result.returncode, before, collection=inventory)
    assert report['software_acceptance'] is False and 'junit_unavailable' in report['reasons']


@pytest.mark.parametrize('value, expected', [
    (None, gate_pytest.WATCHDOG_SECONDS), ('', gate_pytest.WATCHDOG_SECONDS), ('abc', gate_pytest.WATCHDOG_SECONDS),
    ('0', gate_pytest.WATCHDOG_SECONDS), ('-5', gate_pytest.WATCHDOG_SECONDS),
    ('999999', gate_pytest.WATCHDOG_SECONDS), ('30', 30)])
def test_the_environment_can_only_shorten_the_watchdog(value, expected):
    assert gate_pytest.watchdog_seconds({} if value is None else {gate_pytest.WATCHDOG_ENV: value}) == expected


def test_the_limit_covers_the_slowest_test_measured():
    # test_baseline_eval_has_no_optimizer_steps took 1 957 s while paying for shared setup.
    assert 1957*3 < gate_pytest.WATCHDOG_SECONDS <= 2*HOUR


def test_a_jump_in_the_heartbeat_is_recorded_as_a_gap(tmp_path):
    now = [1000.0]
    path = tmp_path/'run.progress.jsonl'
    liveness = gate_pytest.Liveness(path, clock=lambda: now[0])
    liveness.start('t::a')
    now[0] += gate_pytest.HEARTBEAT_SECONDS
    liveness.tick()
    assert liveness.gaps == 0
    now[0] += 6*HOUR  # Lid closed, hibernation: the process froze and the wall clock did not.
    liveness.tick()
    assert liveness.gaps == 1
    liveness.close()
    gap = [e for e in _events(path) if e['event'] == 'gap']
    assert len(gap) == 1 and gap[0]['seconds'] == pytest.approx(6*HOUR) and gap[0]['current'] == 't::a'


def test_a_heartbeat_names_the_running_test_and_its_age(tmp_path):
    now = [50.0]
    path = tmp_path/'run.progress.jsonl'
    liveness = gate_pytest.Liveness(path, clock=lambda: now[0])
    liveness.start('t::slow')
    now[0] += 40
    liveness.tick()
    liveness.close()
    beat = [e for e in _events(path) if e['event'] == 'heartbeat'][-1]
    assert beat['current'] == 't::slow' and beat['test_seconds'] == pytest.approx(40)


def test_holding_the_system_awake_uses_a_reversible_thread_state():
    calls = []

    class Kernel:
        def SetThreadExecutionState(self, flags):
            calls.append(flags)
            return 0x80000000

    assert gate_pytest.hold_system_awake(Kernel()) is True
    gate_pytest.release_system_awake(Kernel())
    # ES_CONTINUOUS | ES_SYSTEM_REQUIRED, then ES_CONTINUOUS alone restores the default.
    assert calls == [0x80000001, 0x80000000]


def test_a_refused_awake_request_is_reported_not_assumed():
    class Kernel:
        def SetThreadExecutionState(self, flags):
            return 0

    assert gate_pytest.hold_system_awake(Kernel()) is False
