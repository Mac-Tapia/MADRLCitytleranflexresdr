"""SPEC-003 FR-003.5: training children end with their launcher, and an interrupted stage resumes.

Real processes, no mocks of the operating system: a child that starts a grandchild, a launcher
that is cancelled or killed outright, and the stage relaunch that must start the interrupted
attempts from zero without a replacement attempt in the interrupted run.
"""
import json
import os
import signal
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

from uc3m.adapters import process_tree as pt

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
DEADLINE_SECONDS = 30.0


@pytest.fixture(autouse=True)
def _fresh_cancellation():
    pt.reset_cancellation()
    yield
    pt.cancel_all(grace_seconds=1.0)
    pt.reset_cancellation()


def _alive(pid: int) -> bool:
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        kernel.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    stat = Path(f'/proc/{pid}/stat')
    if stat.is_file():
        try:
            return stat.read_text().rsplit(')', 1)[1].split()[0] != 'Z'
        except (OSError, IndexError):
            return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait(predicate, what):
    end = time.monotonic() + DEADLINE_SECONDS
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.1)
    raise AssertionError(f'timed out waiting for {what}')


def _scripts(tmp_path):
    """A child (with the parent watch) that starts a grandchild and records both PIDs."""
    pids = tmp_path/'pids.json'
    child = tmp_path/'child.py'
    child.write_text(textwrap.dedent(f'''
        import json, subprocess, sys, time
        from uc3m.adapters.process_tree import exit_with_parent
        watched = exit_with_parent()
        # Once the watch is waiting, the child must still start processes that inherit its
        # standard handles (platform, torch and the launchers do): a watch blocked on stdin
        # froze this on Windows.
        time.sleep(1.0)
        subprocess.run([sys.executable, '-c', 'pass'], check=True, timeout=20)
        grandchild = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])
        open({str(pids)!r} + '.tmp', 'w').write(json.dumps({{'child': __import__('os').getpid(),
                                                            'grandchild': grandchild.pid, 'watched': watched}}))
        __import__('os').replace({str(pids)!r} + '.tmp', {str(pids)!r})
        time.sleep(600)
    '''), encoding='utf-8')
    return child, pids


def _env():
    return dict(os.environ, PYTHONPATH=os.pathsep.join([str(REPO), os.environ.get('PYTHONPATH', '')]))


def _read_pids(pids):
    _wait(pids.is_file, 'the child to record its PIDs')
    return json.loads(pids.read_text(encoding='utf-8'))


def test_cancel_all_ends_the_child_and_its_grandchild_and_refuses_new_launches(tmp_path):
    child, pids = _scripts(tmp_path)
    outcome = {}

    def launch():
        try:
            outcome['code'] = pt.run_child([sys.executable, str(child)], cwd=REPO, env=_env(),
                                           stdout=subprocess.DEVNULL)
        except BaseException as exc:  # noqa: BLE001 - the outcome is asserted below
            outcome['error'] = exc

    worker = threading.Thread(target=launch)
    worker.start()
    recorded = _read_pids(pids)
    assert recorded['watched'] is True
    assert pt.cancel_all(grace_seconds=2.0) == 1
    worker.join(DEADLINE_SECONDS)
    assert not worker.is_alive()
    assert isinstance(outcome.get('error'), pt.ChildCancelled), outcome
    _wait(lambda: not _alive(recorded['child']) and not _alive(recorded['grandchild']), 'the tree to end')
    assert pt.live_children() == ()
    with pytest.raises(pt.ChildCancelled):
        pt.run_child([sys.executable, '-c', 'pass'], cwd=REPO, env=_env(), stdout=subprocess.DEVNULL)


def test_a_child_ends_its_tree_when_the_launcher_is_killed_outright(tmp_path):
    # A closed Colab cell kills the CLI without letting it clean up: only the child can notice.
    child, pids = _scripts(tmp_path)
    launcher = tmp_path/'launcher.py'
    launcher.write_text(textwrap.dedent(f'''
        import subprocess, sys
        from uc3m.adapters.process_tree import run_child
        run_child([sys.executable, {str(child)!r}], cwd={str(REPO)!r}, env=None, stdout=subprocess.DEVNULL)
    '''), encoding='utf-8')
    parent = subprocess.Popen([sys.executable, str(launcher)], cwd=REPO, env=_env())
    try:
        recorded = _read_pids(pids)
        parent.kill()
        parent.wait(DEADLINE_SECONDS)
        _wait(lambda: not _alive(recorded['child']) and not _alive(recorded['grandchild']),
              'the orphaned tree to end itself')
    finally:
        if parent.poll() is None:
            parent.kill()


def test_an_ordinary_exit_code_is_returned():
    code = pt.run_child([sys.executable, '-c', 'import sys; sys.exit(3)'], cwd=REPO, env=_env(),
                        stdout=subprocess.DEVNULL)
    assert code == 3


def test_a_manual_run_installs_no_watch():
    env = {key: value for key, value in _env().items() if key != pt.PARENT_WATCH_ENV}
    out = subprocess.run([sys.executable, '-c',
                          'from uc3m.adapters.process_tree import exit_with_parent; print(exit_with_parent())'],
                         cwd=REPO, env=env, capture_output=True, text=True, check=True, timeout=DEADLINE_SECONDS)
    assert out.stdout.strip() == 'False'


def test_an_interrupt_in_the_scope_ends_the_children_before_it_propagates(tmp_path):
    child, pids = _scripts(tmp_path)
    previous = signal.getsignal(signal.SIGINT)
    outcome = {}

    def launch():
        try:
            pt.run_child([sys.executable, str(child)], cwd=REPO, env=_env(), stdout=subprocess.DEVNULL)
        except pt.ChildCancelled as exc:
            outcome['error'] = exc

    with pytest.raises(KeyboardInterrupt):
        with pt.cancellation_scope():
            worker = threading.Thread(target=launch)
            worker.start()
            recorded = _read_pids(pids)
            signal.raise_signal(signal.SIGINT)
            for _ in range(int(DEADLINE_SECONDS*10)):  # short sleeps: the handler runs between them
                time.sleep(0.1)
    worker.join(DEADLINE_SECONDS)
    assert isinstance(outcome.get('error'), pt.ChildCancelled)
    _wait(lambda: not _alive(recorded['child']) and not _alive(recorded['grandchild']), 'the tree to end')
    assert signal.getsignal(signal.SIGINT) is previous


def test_a_cancelled_stage_starts_no_replacement_and_a_relaunch_starts_from_zero(tmp_path):
    from tests.fresh_training.test_attempt_acceptance import _stage_learner
    from uc3m.application.training import fresh_campaign as fc
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    calls = []

    def cancelled(treatment, attempt_root):
        calls.append(treatment['treatment_id'])
        raise pt.ChildCancelled('interrupted')

    interrupted = fc.run_stage(manifest_path, 'pilot', cancelled, REPO, authorized=True)
    assert interrupted['status'] == 'incomplete' and interrupted['completed_treatments'] == 0
    assert len(calls) == len(set(calls)), 'a cancelled attempt was replaced within the interrupted run'
    good = _stage_learner(fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml'), 17)
    relaunched = fc.run_stage(manifest_path, 'pilot', good, REPO, authorized=True)
    assert relaunched['status'] == 'training_complete'
    for treatment in relaunched['treatments']:
        assert treatment['reused_verified_attempt'] is False
        assert treatment['attempts'][-1]['training_complete'] is True
    for treatment_id in calls:
        # The interrupted attempt stays on disk as evidence; the relaunch is a new attempt.
        attempt_dirs = sorted((manifest_path.parent/treatment_id).glob('try_*'))
        assert len(attempt_dirs) >= 2, treatment_id


def test_the_cli_reports_a_cancelled_stage(tmp_path, monkeypatch, capsys):
    from uc3m.application.training import cli
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: tmp_path/'campaign')
    monkeypatch.setattr(cli, '_measured_resources', lambda: {'ram_gib': 100.0, 'vram_gib': 100.0, 'cpu_count': 8})

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt('signal 2: training children cancelled')

    monkeypatch.setattr(cli.fc, 'run_stage', interrupted)
    assert cli.main(['--config', str(CONFIG), '--stage', 'pilot', '--execute']) == 130
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report['status'] == 'cancelled' and report['stage'] == 'pilot'
