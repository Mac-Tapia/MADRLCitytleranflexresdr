"""Local experiment tracker: one JSON line per event, no service (SPEC-003 FR-003.1, no paid infrastructure)."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Optional


class JsonlExperimentTracker:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.run_id: Optional[str] = None

    def _write(self, event: str, **payload) -> None:
        if self.run_id is None:
            raise RuntimeError('start_run must come first')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'a', encoding='utf-8') as stream:
            stream.write(json.dumps({'event': event, 'run_id': self.run_id, **payload}, sort_keys=True) + '\n')

    def start_run(self, run_id: str, parameters: Mapping[str, object]) -> None:
        self.run_id = str(run_id)
        self._write('start', parameters=dict(parameters))

    def log_metrics(self, metrics: Mapping[str, float], step: Optional[int] = None) -> None:
        values = {str(k): float(v) for k, v in metrics.items()}
        bad = [k for k, v in values.items() if not math.isfinite(v)]
        if bad:
            raise ValueError(f'non-finite metrics refused: {bad}')
        self._write('metrics', metrics=values, step=step)

    def log_artifact(self, path: Path) -> None:
        path = Path(path)
        self._write('artifact', path=path.as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def end_run(self, status: str) -> None:
        self._write('end', status=str(status))
        self.run_id = None
