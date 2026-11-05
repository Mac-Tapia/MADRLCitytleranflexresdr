import pytest

_omitted = []


def pytest_runtest_logreport(report):
    if report.skipped or getattr(report, 'wasxfail', None):
        _omitted.append(report.nodeid)


def pytest_sessionfinish(session, exitstatus):
    if _omitted and session.exitstatus == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
