"""Pytest evidence plugin: independent full-scope collection and strict execution.

Load explicitly with ``-p uc3m.application.training.gate_pytest``. Collection
does not run fixtures. Evidence records source cuts before and after each phase.

A run also reports its own liveness: ``<evidence>.progress.jsonl`` is written as tests
run, idle sleep is held off during execution, and a test that outlives the watchdog
stops the run with its stack in ``<evidence>.hang.txt``. Without a JUnit the gate rejects it.
"""
from __future__ import annotations

from collections import Counter
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import threading
import time

import pytest

from uc3m.application.training.gate_report import capture_context, validate_invocation, DISCOVERY_RULES

SCOPES = ("tests/fresh_training", "tests")
# About 3.7 times the slowest test measured (1 957 s, paying for shared setup). A false stop
# costs a whole gate, so this catches hangs, not slow tests.
WATCHDOG_SECONDS = 7200
WATCHDOG_ENV = "GATE_TEST_TIMEOUT_SECONDS"
HEARTBEAT_SECONDS = 30
# Native calls can hold the GIL for a while; only a longer silence counts as a frozen process.
GAP_SECONDS = 300
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


def watchdog_seconds(environ=os.environ):
    """The environment may shorten the limit for a test; it can never relax the gate."""
    try:
        value = int(environ.get(WATCHDOG_ENV, ""))
    except ValueError:
        return WATCHDOG_SECONDS
    return value if 0 < value < WATCHDOG_SECONDS else WATCHDOG_SECONDS


def _kernel32():
    if os.name != "nt":
        return None
    import ctypes
    return ctypes.windll.kernel32


def hold_system_awake(kernel=None):
    """Hold off idle sleep for this thread only. No power setting changes; the OS clears it on exit."""
    kernel = kernel or _kernel32()
    return bool(kernel and kernel.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED))


def release_system_awake(kernel=None):
    kernel = kernel or _kernel32()
    if kernel:
        kernel.SetThreadExecutionState(ES_CONTINUOUS)


class Liveness:
    """Flushed record of what the run is doing, readable while it runs or after it dies."""

    def __init__(self, path, clock=time.time):
        self.clock, self.gaps, self.current, self.outcome = clock, 0, None, "passed"
        self.test_started = self.last_tick = clock()
        self._lock = threading.Lock()
        self._file = open(path, "w", encoding="utf-8")
        self._stop = threading.Event()
        self._thread, self._hang, self._limit = None, None, None

    def _write(self, event, **fields):
        self._file.write(json.dumps({"event": event, "utc": self.clock(), **fields}) + "\n")
        self._file.flush()

    def start_heartbeat(self):
        def beat():
            while not self._stop.wait(HEARTBEAT_SECONDS):
                self.tick()
        self._thread = threading.Thread(target=beat, name="gate-heartbeat", daemon=True)
        self._thread.start()

    def arm_watchdog(self, seconds, hang_path):
        self._limit, self._hang = seconds, open(hang_path, "w", encoding="utf-8")
        self._rearm()

    def _rearm(self):
        if self._limit is not None:
            # Runs in a native thread, so it still fires if the test holds the GIL.
            faulthandler.dump_traceback_later(self._limit, exit=True, file=self._hang)

    def start(self, nodeid):
        with self._lock:
            self.current, self.outcome, self.test_started = nodeid, "passed", self.clock()
            self._write("start", nodeid=nodeid)
        self._rearm()

    def report(self, outcome):
        # A failed setup or teardown outranks a passed call.
        if outcome == "failed" or self.outcome == "passed":
            self.outcome = outcome

    def finish(self, nodeid):
        with self._lock:
            self._write("finish", nodeid=nodeid, outcome=self.outcome, seconds=self.clock() - self.test_started)
            self.current = None

    def tick(self):
        with self._lock:
            now = self.clock()
            if now - self.last_tick > GAP_SECONDS:
                self.gaps += 1
                self._write("gap", seconds=now - self.last_tick, current=self.current)
            self.last_tick = now
            self._write("heartbeat", current=self.current, test_seconds=now - self.test_started)

    def close(self):
        if self._file.closed:
            return
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        if self._limit is not None:
            faulthandler.cancel_dump_traceback_later()
            self._hang.close()
            hang = Path(self._hang.name)
            if hang.stat().st_size == 0:
                hang.unlink()
        with self._lock:
            self._write("closed", gaps=self.gaps)
            self._file.close()


class _LivenessHooks:
    def __init__(self, liveness):
        self.liveness = liveness

    def pytest_runtest_logstart(self, nodeid):
        self.liveness.start(nodeid)

    def pytest_runtest_logreport(self, report):
        self.liveness.report(report.outcome)

    def pytest_runtest_logfinish(self, nodeid):
        self.liveness.finish(nodeid)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def pytest_addoption(parser):
    group = parser.getgroup("cut-bound gate evidence")
    group.addoption("--gate-mode", choices=("collection", "execution"))
    group.addoption("--gate-scope", choices=SCOPES)
    group.addoption("--gate-context")
    group.addoption("--gate-evidence")
    group.addoption("--gate-inventory")


def pytest_configure(config):
    mode = config.getoption("gate_mode")
    if mode is None:
        raise pytest.UsageError("gate plugin requires an explicit --gate-mode")
    for option in ("gate_scope", "gate_context", "gate_evidence"):
        if not config.getoption(option):
            raise pytest.UsageError(f"gate plugin requires --{option.replace('_', '-')}")
    root = Path(config.rootpath).resolve()
    context_path = Path(config.getoption("gate_context")).resolve()
    context = json.loads(context_path.read_text(encoding="utf-8-sig"))
    evidence = Path(config.getoption("gate_evidence")).resolve()
    filters = []
    for name in ("keyword", "markexpr", "deselect", "ignore", "ignore_glob", "pyargs", "lf", "ff", "stepwise"):
        if getattr(config.option, name, None):
            filters.append(name)
    if os.environ.get("PYTEST_ADDOPTS", "").strip():
        filters.append("PYTEST_ADDOPTS")
    # A plugin from the environment can drop files before collection is observed here.
    if os.environ.get("PYTEST_PLUGINS", "").strip():
        filters.append("PYTEST_PLUGINS")
    if os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1":
        filters.append("plugin_autoload_enabled")
    if config.getini("addopts"):
        filters.append("ini_addopts")
    if list(config.args) != [config.getoption("gate_scope")]:
        filters.append("scope_args")
    collect_only = bool(config.option.collectonly)
    if collect_only != (mode == "collection"):
        filters.append("mode")
    arguments = list(config.invocation_params.args)
    try:
        validate_invocation(arguments, project_root=str(root), scope=config.getoption("gate_scope"), mode=mode)
    except ValueError as exc:
        filters.append("invocation:" + str(exc))
    config_file, config_hash = None, None
    if config.inipath is not None:
        path = Path(config.inipath).resolve()
        try:
            config_file = path.relative_to(root).as_posix()
            config_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        except ValueError:
            config_file = str(path)
            filters.append("configuration_outside_project")
    discovery = {"config_file": config_file, "config_sha256": config_hash,
                 "rules": {name: list(config.getini(name)) for name in DISCOVERY_RULES}}
    state = {"schema_version": 1, "kind": "pytest_" + mode, "mode": mode,
             "project_root": str(root), "scope": config.getoption("gate_scope"),
             "context": context, "context_sha256": _digest(context),
             "source_before": capture_context(root), "arguments": arguments,
             "discovery_config": discovery, "pytest_version": pytest.__version__,
             "environment_addopts": os.environ.get("PYTEST_ADDOPTS", ""),
             "ini_addopts": list(config.getini("addopts")),
             "scope_args": list(config.args), "collect_only": collect_only,
             "filters": filters, "deselected": 0, "collection_errors": 0, "collection_skipped": 0,
             "nodeids": [], "reports": [], "omissions": {"skipped": 0, "xfail": 0, "xpass": 0},
             "plugin_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if mode == "execution":
        inventory = config.getoption("gate_inventory")
        if inventory is None:
            filters.append("inventory_missing")
        else:
            state["inventory_sha256"] = hashlib.sha256(Path(inventory).read_bytes()).hexdigest()
        xml = getattr(config.option, "xmlpath", None)
        if not xml:
            raise pytest.UsageError("gate execution requires --junitxml")
        try:
            state["execution_reference"] = evidence.relative_to(Path(xml).resolve().parent).as_posix()
        except ValueError as exc:
            raise pytest.UsageError("gate execution evidence must be within the JUnit artifact folder") from exc
    config._cut_gate = state
    limit = watchdog_seconds()
    liveness = Liveness(evidence.with_suffix(".progress.jsonl"))
    liveness.start_heartbeat()
    liveness.arm_watchdog(limit, evidence.with_suffix(".hang.txt"))
    config.pluginmanager.register(_LivenessHooks(liveness), "cut-gate-liveness")
    config._cut_gate_liveness = liveness
    state["liveness"] = {"progress": evidence.with_suffix(".progress.jsonl").name, "watchdog_seconds": limit,
                         "system_awake_held": hold_system_awake() if mode == "execution" else False, "gaps": 0}


def pytest_unconfigure(config):
    liveness = getattr(config, "_cut_gate_liveness", None)
    if liveness is not None:
        # Idempotent, so a run that dies before sessionfinish still ends its record.
        liveness.close()
        if config._cut_gate["liveness"]["system_awake_held"]:
            release_system_awake()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    initial = Counter(item.nodeid for item in items)
    yield
    if initial != Counter(item.nodeid for item in items):
        config._cut_gate["filters"].append("collection_modified_membership")


def pytest_deselected(items):
    # Config is available on deselected items even when all were removed.
    if items:
        items[0].config._cut_gate["deselected"] += len(items)


class _CollectionReports:
    def __init__(self, state):
        self.state = state

    def pytest_collectreport(self, report):
        if report.failed:
            self.state["collection_errors"] += 1
        if report.skipped:
            self.state["collection_skipped"] += 1

    def pytest_runtest_logreport(self, report):
        # An xfail marker with no reason sets wasxfail=""; attribute presence,
        # rather than truthiness of its text, identifies XPASS/XFAIL reliably.
        wasxfail = hasattr(report, "wasxfail")
        self.state["reports"].append({"nodeid": report.nodeid, "when": report.when,
                                       "outcome": report.outcome, "wasxfail": wasxfail})
        if report.skipped:
            self.state["omissions"]["xfail" if wasxfail else "skipped"] += 1
        if wasxfail and report.passed:
            self.state["omissions"]["xpass"] += 1


def pytest_sessionstart(session):
    session.config.pluginmanager.register(_CollectionReports(session.config._cut_gate), "cut-gate-reports")


def pytest_collection_finish(session):
    state = session.config._cut_gate
    state["nodeids"] = [item.nodeid for item in session.items]
    if state["mode"] == "execution":
        properties = [("gate_execution", state["execution_reference"]),
                      ("gate_scope", state["scope"]), ("gate_context_sha256", state["context_sha256"]),
                      ("gate_inventory_sha256", state.get("inventory_sha256", ""))]
        for item in session.items:
            item.user_properties.extend([("gate_nodeid", item.nodeid), *properties])


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    state = session.config._cut_gate
    # Every scope uses the same no-omission policy, including tests outside fresh.
    bad = (state["filters"] or state["deselected"] or state["collection_errors"]
           or state["collection_skipped"] or any(state["omissions"].values())
           or not state["nodeids"] or len(set(state["nodeids"])) != len(state["nodeids"]))
    if bad and session.exitstatus == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    yield  # JUnit plugin writes the XML before we hash its completed bytes.
    state["source_after"] = capture_context(Path(state["project_root"]))
    stable = state["context"] == state["source_before"] == state["source_after"]
    if not stable:
        state["filters"].append("source_context_changed")
        if session.exitstatus == 0:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
    state["exit_code"] = int(session.exitstatus)
    state["complete"] = bool(not bad and session.exitstatus == 0
                             and stable)
    if state["mode"] == "execution":
        xml = Path(session.config.option.xmlpath)
        state["junit_sha256"] = hashlib.sha256(xml.read_bytes()).hexdigest() if xml.is_file() else None
    state["liveness"]["gaps"] = session.config._cut_gate_liveness.gaps
    path = Path(session.config.getoption("gate_evidence"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
