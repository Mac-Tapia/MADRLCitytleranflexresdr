"""CityLearn side of the T3 temporal contract: frozen observation limits.

CityLearn estimates observation bounds from the simulation window of the
schema it loads. A validation or test environment would therefore refit the
scaler on held-out data. ``frozen_observation_limits`` replaces that estimate,
for the duration of a block, with the bounds fitted once on the training
split; an observation without a frozen bound fails instead of being refit.
The dependency itself is never edited.
"""
from __future__ import annotations

import contextlib
import json
import math
from pathlib import Path
from typing import Dict, Mapping

from uc3m.application.dataset.splits import FUTURE_MARKER, NormalizerSpec, SPLITS


def _limits_by_building(split_dir: Path, periodic: bool):
    from citylearn.citylearn import CityLearnEnv
    env = CityLearnEnv(str(Path(split_dir)/'schema.json'))
    try:
        rows = {}
        for building in env.buildings:
            # CityLearn also asks for every catalog observation (include_all=True) when
            # it builds its spaces, so the frozen table covers active and inactive ones.
            low, high = building.estimate_observation_space_limits(include_all=True, periodic_normalization=periodic)
            rows[building.name] = {name: (float(low[name]), float(high[name])) for name in low}
        return rows
    finally:
        close = getattr(env, 'close', None)
        if callable(close):
            close()


DESIGN_SEED = 0  # one declared draw of unset device parameters, reused by every treatment
DEVICE_ATTRIBUTES = ('nominal_power', 'efficiency', 'target_cooling_temperature', 'target_heating_temperature')


def design_device_sizes(dataset_dir: Path, design_seed: int = DESIGN_SEED):
    """The campaign's fixed physical design, drawn once on the built dataset.

    CityLearn autosizes devices on the loaded window and samples unset device
    parameters (heat pump efficiency, target temperatures) from the env seed.
    Freezing them makes the system identical in every split and every seed.
    Parameters the schema already declares (campaign v2: the heat-pump efficiency
    and target temperature the bills were calibrated with) are kept exactly; a
    runtime value that differs from the declared one is an error, not a redraw.
    """
    from citylearn.citylearn import CityLearnEnv
    schema = json.loads((Path(dataset_dir)/'schema.json').read_text(encoding='utf-8'))
    env = CityLearnEnv(str(Path(dataset_dir)/'schema.json'), random_seed=design_seed)
    env.reset()
    sizes = {}
    for building in env.buildings:
        config = schema['buildings'][building.name]
        row = {}
        for name in ('cooling_device', 'heating_device', 'dhw_device'):
            device = getattr(building, name, None)
            if not isinstance(config.get(name), dict) or device is None or device.nominal_power is None:
                continue
            row[name] = {attr: float(getattr(device, attr)) for attr in DEVICE_ATTRIBUTES
                         if getattr(device, attr, None) is not None}
            declared = dict(config[name].get('attributes') or {})
            for attr in DEVICE_ATTRIBUTES:
                if attr == 'nominal_power' or declared.get(attr) is None:
                    continue
                if not math.isclose(row[name].get(attr, math.nan), float(declared[attr]), rel_tol=0, abs_tol=1e-12):
                    raise ValueError(f'{building.name}.{name}.{attr}: runtime {row[name].get(attr)} differs '
                                     f'from the calibration value {declared[attr]} in schema.json')
                row[name][attr] = float(declared[attr])
        if row:
            sizes[building.name] = row
    return sizes


def citylearn_limits(split_dir: Path):
    """Raw-unit bounds as CityLearn estimates them on this split's window only."""
    return _limits_by_building(split_dir, periodic=False)


def citylearn_periodic_limits(split_dir: Path):
    return _limits_by_building(split_dir, periodic=True)


@contextlib.contextmanager
def frozen_observation_limits(spec: NormalizerSpec, building_class=None):
    """Serve training-split bounds to every Building built inside the block."""
    if building_class is None:
        from citylearn.building import Building as building_class
    original = building_class.estimate_observation_space_limits

    def frozen(self, include_all=None, periodic_normalization=None):
        low, high = original(self, include_all=include_all, periodic_normalization=periodic_normalization)
        table = spec.periodic_bounds if periodic_normalization and spec.periodic_bounds else spec.bounds
        if self.name not in table:
            raise KeyError(f'{self.name}: no frozen observation bounds fitted on train')
        frozen_rows = table[self.name]
        missing = [name for name in low if name not in frozen_rows]
        if missing:
            raise KeyError(f'{self.name}: observations without frozen train bounds: {missing}')
        return ({name: frozen_rows[name][0] for name in low}, {name: frozen_rows[name][1] for name in high})

    building_class.estimate_observation_space_limits = frozen
    try:
        yield
    finally:
        building_class.estimate_observation_space_limits = original


def load_normalizer(path: Path) -> NormalizerSpec:
    return NormalizerSpec.from_dict(json.loads(Path(path).read_text(encoding='utf-8')))


def smoke_splits(campaign_root: Path, steps: int = 24) -> Dict[str, Mapping[str, object]]:
    """Reset and step each frozen split with a do-nothing action; not training."""
    from citylearn.citylearn import CityLearnEnv
    root = Path(campaign_root)
    spec = load_normalizer(root/'normalizer.json')
    report = {}
    for split_id, _, _, _ in SPLITS:
        schema = root/'splits'/split_id/'schema.json'
        with frozen_observation_limits(spec):
            env = CityLearnEnv(str(schema))
            observations = env.reset()
            observations = observations[0] if isinstance(observations, tuple) else observations
            names = [n for agent in env.observation_names for n in agent]
            finite = all(math.isfinite(float(v)) for agent in observations for v in agent)
            done, taken = False, 0
            while not done and taken < steps:
                zero = [[0.0]*space.shape[0] for space in env.action_space]
                result = env.step(zero)
                observations = result[0]
                done = bool(result[2]) if len(result) < 5 else bool(result[2] or result[3])
                finite = finite and all(math.isfinite(float(v)) for agent in observations for v in agent)
                taken += 1
            report[split_id] = {'reset_ok': True, 'steps': taken, 'finite': finite,
                                'predicted_fields_observed': sorted({n for n in names if FUTURE_MARKER in n}),
                                'time_steps': env.time_steps}
    return report
