"""Figures of the campaign reports (SPEC-003 FR-003.4): the only module of the evaluation layer that draws.

The application layer computes the tables; this adapter turns them into files. A missing or non-finite value is an
error, never a blank bar or a broken line.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping, Sequence


def _finite(values: Sequence[float], what: str) -> list:
    values = [float(v) for v in values]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError(f'{what}: every value must be finite and at least one is needed')
    return values


class FigureRenderer:
    def __init__(self, dpi: int = 150):
        self.dpi = int(dpi)

    def _save(self, figure, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.tight_layout()
        figure.savefig(path, dpi=self.dpi)
        return path

    def learning_curves(self, curves: Mapping[str, Sequence[float]], path: Path, *, ylabel: str = 'episode reward') -> Path:
        """One line per algorithm over its episodes."""
        from matplotlib.figure import Figure
        figure = Figure(figsize=(7, 4))
        axis = figure.add_subplot(111)
        if not curves:
            raise ValueError('learning curves: no series')
        for name, values in curves.items():
            axis.plot(_finite(values, name), label=name)
        axis.set_xlabel('episode')
        axis.set_ylabel(ylabel)
        axis.legend()
        return self._save(figure, path)

    def kpi_bars(self, table: Mapping[str, float], path: Path, *, ylabel: str) -> Path:
        """One bar per row of a KPI table."""
        from matplotlib.figure import Figure
        if not table:
            raise ValueError('KPI bars: no rows')
        values = _finite(list(table.values()), ylabel)
        figure = Figure(figsize=(7, 4))
        axis = figure.add_subplot(111)
        axis.bar(list(table), values)
        axis.set_ylabel(ylabel)
        return self._save(figure, path)
