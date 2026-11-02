"""Strict profile for the fresh campaign: an omitted check is not a passed check.

Any skip, xfail or xpass of a test collected from this directory turns the
session exit status non-zero, so a missing dependency or a missing input can
never be read as acceptance of the new campaign.
"""
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_NOT_ACCEPTED = []


def _in_fresh_profile(nodeid_path):
    try:
        return Path(nodeid_path).resolve().is_relative_to(_HERE)
    except AttributeError:  # pragma: no cover - Python < 3.9 has no is_relative_to
        return str(Path(nodeid_path).resolve()).startswith(str(_HERE))


def pytest_runtest_logreport(report):
    path = report.fspath if hasattr(report, 'fspath') else report.location[0]
    if not _in_fresh_profile(path):
        return
    if report.skipped and hasattr(report, 'wasxfail'):
        _NOT_ACCEPTED.append((report.nodeid, 'xfail'))
    elif report.skipped:
        _NOT_ACCEPTED.append((report.nodeid, 'skip'))
    elif report.when == 'call' and report.passed and hasattr(report, 'wasxfail'):
        _NOT_ACCEPTED.append((report.nodeid, 'xpass'))


def pytest_terminal_summary(terminalreporter):
    for nodeid, outcome in _NOT_ACCEPTED:
        terminalreporter.write_line(f'FRESH-PROFILE REJECTED {outcome}: {nodeid}', red=True)


def pytest_sessionfinish(session, exitstatus):
    if _NOT_ACCEPTED and session.exitstatus == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
