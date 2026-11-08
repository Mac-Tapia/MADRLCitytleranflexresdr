"""Local correction of the reanalysis weather with the open record of the Iquitos airport (SPEC-016 D-V6-59).

NASA POWER matches the station on average but flattens the day: daily maxima about 2 C too low. A correction by month
and hour, fitted on the training year only, restores the daily cycle; the dew point is kept, so humidity follows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import yaml

TABLE = Path(__file__).resolve().parents[3]/'configs/dataset/weather_station_correction.yaml'


def _saturation_kpa(t_c):
    return 0.6112*np.exp(17.67*np.asarray(t_c, dtype=float)/(np.asarray(t_c, dtype=float) + 243.5))


def fit_month_hour_deltas(observed, reanalysis):
    """Mean of station minus reanalysis per [month - 1][hour]; every cell needs data. Two series on one index."""
    gap = observed.to_numpy(dtype=float) - reanalysis.reindex(observed.index).to_numpy(dtype=float)
    known = np.isfinite(gap)
    months, hours = observed.index.month.to_numpy()[known] - 1, observed.index.hour.to_numpy()[known]
    totals, counts = np.zeros((12, 24)), np.zeros((12, 24))
    np.add.at(totals, (months, hours), gap[known])
    np.add.at(counts, (months, hours), 1)
    if (counts == 0).any():
        raise ValueError(f'the correction needs every month and hour; got {int((counts > 0).sum())} of 288 cells')
    return np.round(totals/counts, 4).tolist()


def correct_weather(frame, deltas, *, temperature: str = 'T2M', humidity: str = 'RH2M'):
    """A copy with the temperature corrected and the relative humidity recomputed at the same dew point."""
    table = np.asarray(deltas, dtype=float)
    if table.shape != (12, 24):
        raise ValueError('deltas must have 12 months x 24 hours')
    out = frame.copy()
    new = frame[temperature].to_numpy(float) + table[frame.index.month - 1, frame.index.hour]
    vapor = frame[humidity].to_numpy(float)/100.0*_saturation_kpa(frame[temperature].to_numpy(float))
    out[temperature] = new
    out[humidity] = np.clip(100.0*vapor/_saturation_kpa(new), 0.0, 100.0)
    return out


def load_table(path: Path = TABLE) -> Mapping:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))
