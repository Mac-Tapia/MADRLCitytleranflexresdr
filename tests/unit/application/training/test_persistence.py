import csv
import json

import pytest


def test_atomic_json_preserves_valid_file_on_failed_replace(tmp_path, monkeypatch):
    from uc3m.application.training import persistence as p
    path = tmp_path / 'state.json'
    p.write_json_atomic(path, {'episode': 1})
    def fail(*args):
        raise OSError('interrupted')
    monkeypatch.setattr(p.os, 'replace', fail)
    with pytest.raises(OSError):
        p.write_json_atomic(path, {'episode': 2})
    assert json.loads(path.read_text()) == {'episode': 1}
    assert not list(tmp_path.glob('*.tmp'))


def test_csv_append_rejects_schema_drift_without_losing_rows(tmp_path):
    from uc3m.application.training.persistence import write_csv_atomic, append_csv_stable_schema
    path = tmp_path / 'episodes.csv'
    write_csv_atomic(path, [{'episode': 1, 'reward': -1}])
    append_csv_stable_schema(path, [{'episode': 2, 'reward': 2}], ['episode', 'reward'])
    before = path.read_bytes()
    with pytest.raises(ValueError, match='schema'):
        append_csv_stable_schema(path, [{'episode': 3, 'new': 9}], ['episode', 'reward'])
    assert path.read_bytes() == before
    assert len(list(csv.DictReader(path.open()))) == 2


def test_heartbeat_is_explicit_and_persists_progress(tmp_path):
    from uc3m.application.training.persistence import ProgressHeartbeat
    path = tmp_path / 'progress.json'
    heartbeat = ProgressHeartbeat(path)
    heartbeat.update(completed_episodes=4, status='running')
    assert json.loads(path.read_text())['completed_episodes'] == 4
