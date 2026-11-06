"""Training children that never outlive their launcher (SPEC-003 FR-003.5).

A training attempt is a child process (``native_entrypoint``) that may start its own children
(vectorized environments). Before this module a parent that died, was interrupted or was killed
left those processes training on the GPU, and an interrupted CLI waited forever on worker threads
blocked on a child that could run for hours.

Two independent mechanisms, standard library only:

* **Parent side.** ``run_child`` starts each child as the leader of its own process group (a new
  session on POSIX, a new process group on Windows) and registers it. ``cancel_all`` terminates
  every registered tree, grandchildren included, and refuses later launches, so an interrupted
  stage never starts a replacement attempt. ``cancellation_scope`` binds SIGINT/SIGTERM (and
  SIGBREAK on Windows) of the main thread to ``cancel_all``.
* **Child side.** ``exit_with_parent`` waits on a daemon thread for the parent to disappear,
  however it died (including SIGKILL or a closed Colab cell), and the child then ends its own
  tree. On POSIX the child holds the read end of a dedicated pipe (``pass_fds``) whose write end
  only the parent holds: end of file means the parent is gone. On Windows the child opens the
  parent process and waits on it; the parent PID is passed explicitly because a venv
  ``python.exe`` is a redirector that sits between them.

The watch never uses stdin, whose handle the child keeps as ``DEVNULL``: on Windows a thread
blocked reading a pipe freezes every other use of that handle, including starting a process
that inherits it, which froze HAPPO at start-up (reproduced in
``tests/integration/test_training_interruption.py``).
"""
from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import threading
import time
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence

PARENT_WATCH_ENV = 'UC3M_PARENT_WATCH'
PARENT_GONE_EXIT_CODE = 70
GRACE_SECONDS = 10.0
WINDOWS = os.name == 'nt'

_lock = threading.Lock()
_live: Dict[int, subprocess.Popen] = {}
_cancelled = threading.Event()


class ChildCancelled(RuntimeError):
    """The launcher was cancelled: the child was ended or never started."""


def _group_options() -> Dict[str, Any]:
    if WINDOWS:
        return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    return {'start_new_session': True}


def run_child(command: Sequence[str], *, cwd: Any, env: Optional[Mapping[str, str]], stdout: Any,
              stderr: Any = subprocess.STDOUT) -> int:
    """Run ``command`` to completion as a cancellable process tree; return its exit code.

    Raises ``ChildCancelled`` when the launcher is cancelled before or while the child runs, so
    the caller never records a cancelled attempt as an ordinary exit.
    """
    child_env = dict(os.environ if env is None else env)
    options = _group_options()
    keep = None
    with _lock:
        if _cancelled.is_set():
            raise ChildCancelled('launches are cancelled')
        if WINDOWS:
            child_env[PARENT_WATCH_ENV] = f'pid:{os.getpid()}'
        else:
            # Both ends are created non-inheritable; only this child receives the read end.
            read_end, keep = os.pipe()
            child_env[PARENT_WATCH_ENV] = f'fd:{read_end}'
            options['pass_fds'] = (read_end,)
        try:
            process = subprocess.Popen(list(command), cwd=cwd, env=child_env, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, **options)
        except BaseException:
            if keep is not None:
                os.close(keep)
            raise
        finally:
            if not WINDOWS:
                os.close(read_end)
        _live[process.pid] = process
    try:
        code = process.wait()
    except BaseException:
        _end_trees([process])
        raise
    finally:
        with _lock:
            _live.pop(process.pid, None)
        if keep is not None:
            with contextlib.suppress(OSError):
                os.close(keep)
    if _cancelled.is_set():
        raise ChildCancelled(f'child {process.pid} was cancelled (exit code {code})')
    return int(code)


def live_children() -> Sequence[int]:
    with _lock:
        return tuple(_live)


def cancel_all(grace_seconds: float = GRACE_SECONDS) -> int:
    """Refuse new launches and end every live tree; return how many trees were ended."""
    _cancelled.set()
    with _lock:
        processes = list(_live.values())
    _end_trees(processes, grace_seconds)
    return len(processes)


def reset_cancellation() -> None:
    """Allow launches again (a new stage in the same interpreter)."""
    _cancelled.clear()


def _signal_tree(process: subprocess.Popen, *, force: bool) -> None:
    if WINDOWS:
        # taskkill /T walks the tree by parent PID; it ends every descendant, then the child.
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T'] + (['/F'] if force else []),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)


def _end_trees(processes: Sequence[subprocess.Popen], grace_seconds: float = GRACE_SECONDS) -> None:
    """Ask every tree to stop, wait ``grace_seconds`` in total, then force the rest."""
    for process in processes:
        _signal_tree(process, force=WINDOWS)  # Windows has no graceful signal for a console-less tree
    deadline = time.monotonic() + max(0.0, grace_seconds)
    for process in processes:
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=max(0.0, deadline - time.monotonic()))
    for process in processes:
        # The group can outlive its leader on POSIX, so it is forced even after the leader exited.
        _signal_tree(process, force=True)
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=GRACE_SECONDS)


@contextlib.contextmanager
def cancellation_scope() -> Iterator[None]:
    """Bind the main thread's interrupt and termination signals to ``cancel_all``.

    The handler ends the children first, so the worker threads blocked on them return and the
    interrupt reaches the caller instead of waiting for the trees to finish. Any exception leaving
    the scope also ends what is still alive.
    """
    reset_cancellation()
    installed = {}

    def handler(signum, frame):
        cancel_all()
        raise KeyboardInterrupt(f'signal {signum}: training children cancelled')

    if threading.current_thread() is threading.main_thread():
        names = ('SIGINT', 'SIGTERM', 'SIGBREAK')
        for number in [getattr(signal, name) for name in names if hasattr(signal, name)]:
            with contextlib.suppress(OSError, ValueError):
                installed[number] = signal.signal(number, handler)
    try:
        yield
    except BaseException:
        cancel_all()
        raise
    finally:
        for number, previous in installed.items():
            with contextlib.suppress(OSError, ValueError, TypeError):
                signal.signal(number, previous)


def _end_own_tree() -> None:
    if WINDOWS:
        subprocess.run(['taskkill', '/PID', str(os.getpid()), '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        # run_child made this process a session leader: its group holds it and its descendants.
        with contextlib.suppress(OSError):
            os.killpg(os.getpgid(0), signal.SIGKILL)
    os._exit(PARENT_GONE_EXIT_CODE)


def exit_with_parent() -> bool:
    """In a child started by ``run_child``, end this process tree when the parent disappears.

    Returns whether the watch was installed (only under ``run_child``, never on a manual run).
    The variable is removed so that descendants started by this process do not watch it again.
    """
    kind, _, value = os.environ.pop(PARENT_WATCH_ENV, '').partition(':')
    if not value.isdigit() or kind not in ('fd', 'pid'):
        return False
    number = int(value)

    def watch_pipe():
        with contextlib.suppress(OSError):
            while os.read(number, 65536):
                pass
        _end_own_tree()

    def watch_process():
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
        handle = kernel.OpenProcess(0x00100000, False, number)  # SYNCHRONIZE
        if handle:
            kernel.WaitForSingleObject(handle, 0xFFFFFFFF)       # INFINITE
        # No handle: the parent was already gone when the watch started.
        _end_own_tree()

    if kind == 'fd' and not WINDOWS:
        target = watch_pipe
    elif kind == 'pid' and WINDOWS:
        target = watch_process
    else:
        return False
    threading.Thread(target=target, name='uc3m-parent-watch', daemon=True).start()
    return True
