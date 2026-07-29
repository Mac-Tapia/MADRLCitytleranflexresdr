"""Tests for the launcher singleton lock (prevents double-launch resetting jobs).

Run: python tools/training/test_launcher_singleton_lock.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "CityLearn" / "scripts" / "colab_a100_official_launcher.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("colab_launcher_under_test", LAUNCHER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = _load_module()
    Lock = mod.LauncherSingletonLock

    with tempfile.TemporaryDirectory() as tmp:
        lock_path = Path(tmp) / mod.LAUNCHER_LOCK_NAME

        # 1) First acquire succeeds and writes the lock file.
        a = Lock(lock_path, stale_after_s=2.0, heartbeat_s=0.2)
        assert a.acquire() is None, "first acquire must succeed"
        assert lock_path.exists(), "lock file must exist after acquire"

        # 2) A second launcher on the same root is refused while owner is alive.
        b = Lock(lock_path, stale_after_s=2.0, heartbeat_s=0.2)
        owner = b.acquire()
        assert owner is not None, "second acquire must be refused (live owner)"
        assert int(owner["pid"]) == a._payload()["pid"], "owner pid should be live launcher"

        # 3) --force-unlock overrides even a live lock.
        c = Lock(lock_path, stale_after_s=2.0, heartbeat_s=0.2)
        assert c.acquire(force=True) is None, "force=True must take the lock"
        c.release()
        a.release()  # stop the original owner's heartbeat thread

        # 4) release removes an owned lock.
        d = Lock(lock_path, stale_after_s=2.0, heartbeat_s=0.2)
        assert d.acquire() is None
        d.release()
        assert not lock_path.exists(), "release must remove an owned lock"

        # 5) A stale lock (no heartbeat refresh) is taken over.
        stale = Lock(lock_path, stale_after_s=0.5, heartbeat_s=999.0)  # never refreshes
        assert stale.acquire() is None
        time.sleep(0.7)  # let the heartbeat go stale
        taker = Lock(lock_path, stale_after_s=0.5, heartbeat_s=0.2)
        assert taker.acquire() is None, "stale lock must be taken over"
        taker.release()
        stale.release()

    print("OK: launcher singleton lock tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
