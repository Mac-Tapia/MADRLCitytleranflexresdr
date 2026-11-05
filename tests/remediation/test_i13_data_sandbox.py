"""Only the five fixture safety checks; all targets stay inside this test's tmp_path."""
import os

import pytest

from test_i13_data_security import (
    SandboxWriteViolation, _WRITE_ROOT, _write_audit,
    case_write_sandbox, junction, S3Client,
)


def test_guard_allows_mkdir_and_write_inside_case(tmp_path):
    case = tmp_path/'case'
    case.mkdir()
    with case_write_sandbox(case):
        (case/'nested').mkdir()
        (case/'nested'/'value.txt').write_text('inside')
    assert (case/'nested'/'value.txt').read_text() == 'inside'


def test_guard_rejects_mkdir_before_os_and_dir_fd(tmp_path):
    case = tmp_path/'case'
    case.mkdir()
    sibling = tmp_path/'sibling'
    with case_write_sandbox(case):
        with pytest.raises(SandboxWriteViolation, match='outside case sandbox'):
            sibling.mkdir()
        with pytest.raises(SandboxWriteViolation, match='dir_fd'):
            _write_audit('os.mkdir', (str(case/'unverifiable'), 0o777, 0))
    assert not sibling.exists()
    assert not (case/'unverifiable').exists()


def test_guard_rejects_writable_open_os_open_and_fd(tmp_path):
    case = tmp_path/'case'
    case.mkdir()
    sibling = tmp_path/'sibling'
    sibling.mkdir()
    target = sibling/'must_not_exist.txt'
    descriptor = os.open(str(case/'descriptor.txt'), os.O_CREAT | os.O_RDWR)
    try:
        with case_write_sandbox(case):
            with pytest.raises(SandboxWriteViolation, match='outside case sandbox'):
                target.write_text('blocked')
            with pytest.raises(SandboxWriteViolation, match='outside case sandbox'):
                os.open(str(target), os.O_CREAT | os.O_WRONLY)
            with pytest.raises(SandboxWriteViolation, match='file descriptor'):
                open(descriptor, 'w', closefd=False)
    finally:
        os.close(descriptor)
    assert not target.exists()
    assert (case/'descriptor.txt').read_bytes() == b''


def test_guard_rejects_junction_escape_and_independent_downloader(tmp_path):
    case = tmp_path/'case'
    case.mkdir()
    sibling = tmp_path/'sibling'
    sibling.mkdir()
    junction(case/'linked', sibling)
    with case_write_sandbox(case):
        with pytest.raises(SandboxWriteViolation, match='outside case sandbox'):
            (case/'linked'/'nested').mkdir()
        with pytest.raises(SandboxWriteViolation, match='outside case sandbox'):
            (case/'linked'/'blocked.txt').write_text('blocked')
    client = S3Client([], case)
    with pytest.raises(SandboxWriteViolation, match='outside case sandbox'):
        client.download_file('bucket', 'key', str(sibling/'blocked.txt'))
    assert list(sibling.iterdir()) == []


def test_guard_restores_context_after_failure(tmp_path):
    case = tmp_path/'case'
    case.mkdir()
    assert _WRITE_ROOT.get() is None
    with pytest.raises(SandboxWriteViolation):
        with case_write_sandbox(case):
            (tmp_path/'outside_case.txt').write_text('blocked')
    assert _WRITE_ROOT.get() is None
    # Outside the case, but still inside this test's tmp_path, confirms reset.
    result = tmp_path/'after_context.txt'
    result.write_text('restored')
    assert result.read_text() == 'restored'
    assert not (tmp_path/'outside_case.txt').exists()
