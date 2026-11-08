"""SPEC-003 FR-003.1 and FR-003.4: the experiment tracker port with its local adapter, and the figure adapter."""
import json
import math

import pytest

from uc3m.adapters.jsonl_tracker import JsonlExperimentTracker
from uc3m.adapters.matplotlib_figures import FigureRenderer
from uc3m.ports import ExperimentTrackerPort


def test_the_local_tracker_satisfies_the_port_and_records_every_event(tmp_path):
    tracker = JsonlExperimentTracker(tmp_path/'runs'/'events.jsonl')
    assert isinstance(tracker, ExperimentTrackerPort)
    artifact = tmp_path/'model.bin'
    artifact.write_bytes(b'weights')
    tracker.start_run('r1', {'seed': 1})
    tracker.log_metrics({'reward': -1.5}, step=3)
    tracker.log_artifact(artifact)
    tracker.end_run('complete')
    events = [json.loads(line) for line in (tmp_path/'runs'/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [e['event'] for e in events] == ['start', 'metrics', 'artifact', 'end']
    assert events[1]['metrics'] == {'reward': -1.5} and events[1]['step'] == 3
    assert len(events[2]['sha256']) == 64


def test_the_tracker_refuses_non_finite_metrics_and_events_without_a_run(tmp_path):
    tracker = JsonlExperimentTracker(tmp_path/'e.jsonl')
    with pytest.raises(RuntimeError):
        tracker.log_metrics({'a': 1.0})
    tracker.start_run('r', {})
    with pytest.raises(ValueError, match='non-finite'):
        tracker.log_metrics({'a': math.nan})


def test_the_renderer_writes_figures_and_refuses_bad_values(tmp_path):
    renderer = FigureRenderer(dpi=50)
    curves = renderer.learning_curves({'HAPPO': [1.0, 2.0], 'MAAC': [0.5, 1.5]}, tmp_path/'f'/'curves.png')
    bars = renderer.kpi_bars({'E1': 0.9, 'E2': 1.1}, tmp_path/'bars.png', ylabel='cost ratio')
    assert curves.stat().st_size > 0 and bars.stat().st_size > 0
    with pytest.raises(ValueError):
        renderer.kpi_bars({'E1': math.nan}, tmp_path/'x.png', ylabel='k')
    with pytest.raises(ValueError):
        renderer.learning_curves({}, tmp_path/'y.png')
