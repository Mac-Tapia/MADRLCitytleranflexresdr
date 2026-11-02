"""Scientific evaluation: KPI validation, multiseed statistics, Pareto summary."""
from typing import Dict, List, Sequence

import numpy as np

from uc3m.application.evaluation.fresh_analysis import iqm as canonical_iqm
from uc3m.domain.pareto import hypervolume_3d, non_dominated_indices

REQUIRED_KPI_KEYS = {'cost_total', 'co2_emissions', 'peak_demand'}


def validate_kpis(kpis: Dict[str, float]) -> bool:
    return REQUIRED_KPI_KEYS.issubset(kpis.keys()) and all(
        isinstance(v, (int, float)) and np.isfinite(v)
        for k, v in kpis.items()
        if k in REQUIRED_KPI_KEYS
    )


def compute_multiseed_stats(values: List[float]) -> dict:
    if len(values) < 3:
        raise ValueError("minimum 3 seeds required for multiseed statistics")
    arr = np.array(values, dtype=float)
    iqm = float(canonical_iqm(arr))
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr, ddof=1)),
        'iqm': iqm,
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'n_seeds': len(values),
    }


def compute_pareto_summary(
    points: List[dict],
    maximize: Sequence[bool],
) -> dict:
    objectives = np.array([p['objectives'] for p in points], dtype=float)
    front_idx = non_dominated_indices(objectives.tolist(), maximize=list(maximize))
    ref = []
    for col in range(objectives.shape[1]):
        if maximize[col]:
            ref.append(float(np.min(objectives[:, col])) - 1.0)
        else:
            ref.append(float(np.max(objectives[:, col])) + 1.0)
    hv = hypervolume_3d(objectives.tolist(), reference=ref, maximize=list(maximize))
    return {
        'front_indices': list(front_idx),
        'front_algorithms': [points[i]['algorithm'] for i in front_idx],
        'hypervolume': hv,
        'n_points': len(points),
    }
