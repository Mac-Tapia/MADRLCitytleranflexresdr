import pytest


def test_lock_file_left_after_crash_does_not_permanently_block_run(tmp_path):
    from uc3m.application.training.lock import run_lock
    path = tmp_path/'.runner.lock'
    path.write_bytes(b'old process')
    with run_lock(path):
        with pytest.raises(OSError):
            with run_lock(path):
                raise AssertionError('concurrent writer acquired lock')
    with run_lock(path):
        pass
