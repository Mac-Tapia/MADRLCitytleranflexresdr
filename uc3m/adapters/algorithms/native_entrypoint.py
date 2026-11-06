"""Child-process entrypoint of one fresh native training attempt (T5).

    python -m uc3m.adapters.algorithms.native_entrypoint --algorithm MATD3 \
        --campaign-id ID --attempt-id a001 --attempt-root DIR [--normalizer FILE] -- <native args>

Runs the original CityLearn launcher of the algorithm unchanged, with:
  - optimizer updates observed at the native finite-gradient guard;
  - the dependency's CSV pickle cache redirected into this attempt (empty at start);
  - observation bounds frozen to the training-split normalizer;
  - --no-resume forced and the output directory owned by the attempt;
  - every Dec-POMDP step supervised (reward terms, runtime axis weights,
    aggregation, action spread) into supervision.json.
It writes learning_evidence.json and exits non-zero unless learning is verified.
A salvaged run is a failed attempt, never a complete one.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import math
import runpy
import sys
import traceback
from pathlib import Path
from typing import List

from uc3m.adapters.algorithms.learning_observer import LearningObserver

TRAINERS = {'HAPPO': 'train_citylearn_v3_happo.py', 'MASAC': 'train_citylearn_v3_masac.py',
            'MATD3': 'train_citylearn_v3_matd3.py', 'MAAC': 'train_citylearn_v3_maac.py'}
# Dependency caches that would otherwise persist between runs, by attribute.
REDIRECTED_DEPENDENCY_CACHES = {'_CSV_CACHE_DIR': 'outputs/dataset_cache'}
OWNED_ARGUMENTS = ('--output-dir', '--resume', '--resume-from', '--checkpoint', '--load-checkpoint')


def trainer_script(project_root: Path, algorithm: str) -> Path:
    if algorithm not in TRAINERS:
        raise ValueError(f'no native trainer for {algorithm!r}; random or placeholder training is not accepted')
    return Path(project_root)/'CityLearn/scripts'/TRAINERS[algorithm]


def native_arguments(arguments: List[str]) -> List[str]:
    owned = [a for a in arguments if a.split('=', 1)[0] in OWNED_ARGUMENTS]
    if owned:
        raise ValueError(f'arguments owned by the fresh attempt cannot be passed: {owned}')
    return list(arguments) + ([] if '--no-resume' in arguments else ['--no-resume'])


def load_native_common(project_root: Path):
    scripts = str(Path(project_root)/'CityLearn/scripts')
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return importlib.import_module('citylearn_v3_training_common')


@contextlib.contextmanager
def attempt_isolation(common, attempt_root: Path):
    original = common._CSV_CACHE_DIR
    common._CSV_CACHE_DIR = Path(attempt_root)/'native_cache'
    try:
        yield
    finally:
        common._CSV_CACHE_DIR = original


def _option(arguments: List[str], name: str, default=None):
    for index, item in enumerate(arguments):
        if item == name and index + 1 < len(arguments):
            return arguments[index + 1]
        if item.startswith(name + '='):
            return item.split('=', 1)[1]
    return default


def job_directory(output: Path, native: List[str]) -> Path:
    """The native launcher writes into <output-dir>/<SCENARIO>[_s<seed>]."""
    from uc3m.application.training.layout import normalize_scenario_dir
    return Path(output)/normalize_scenario_dir(_option(native, '--scenario', 'E1'), int(_option(native, '--seed', '0')))


def salvage_reason(payload) -> str:
    payload = payload if isinstance(payload, dict) else {}
    hyper = payload.get('hyperparameters') or {}
    if payload.get('status') == 'completed_with_salvage' or hyper.get('run_completed_with_salvage'):
        return str(hyper.get('run_error') or payload.get('salvage_reason') or 'completed_with_salvage')
    return None


class RewardSupervisor:
    """Observe every Dec-POMDP step of the attempt without editing the native trainers.

    Wraps ``CityLearnDecPOMDPEnv.step``/``reset`` (all four native backends build
    their environment through ``citylearn.v3.make_citylearn_v3_env``) and feeds the
    reward breakdown and the actions of each step to a ``RewardTelemetryRecorder``.
    It also records the axis weights the reward really used at runtime and the
    Dec-POMDP reward aggregation, so completion can compare them with the treatment.
    At the close of EVERY episode it stores the thesis indicators (Layer A, district and
    buildings, from the step trace) and the CityLearn v3 KPI-gains (Layer B, CityLearn
    evaluate_objectives on the episode just finished, district and building rows).
    """

    def __init__(self, citylearn_v3: bool = True):
        from uc3m.reward.term_telemetry import RewardTelemetryRecorder
        self.recorder = RewardTelemetryRecorder()
        self.citylearn_v3 = citylearn_v3
        self._last_env = None
        self._weights_seen: List[dict] = []
        self._source = None
        self._aggregations: List[str] = []

    def observe_reward(self, axis_weights, source) -> None:
        weights = {key: float(value) for key, value in dict(axis_weights or {}).items()}
        if weights and weights not in self._weights_seen:
            self._weights_seen.append(weights)
        if self._source is None and source:
            self._source = dict(source)

    def _after_step(self, env, actions) -> None:
        aggregation = str(getattr(env, 'reward_aggregation', None))
        if aggregation not in self._aggregations:
            self._aggregations.append(aggregation)
        self._last_env = env
        reward_function = getattr(getattr(env, 'env', None), 'reward_function', None)
        if reward_function is None:
            return
        self.observe_reward(getattr(reward_function, 'axis_weights', None),
                            getattr(reward_function, 'axis_weights_source', None))
        self.recorder.record_step(getattr(reward_function, '_last_component_breakdown', None), actions=actions)

    @contextlib.contextmanager
    def installed(self):
        from citylearn.dec_pomdp import CityLearnDecPOMDPEnv
        original_step, original_reset = CityLearnDecPOMDPEnv.step, CityLearnDecPOMDPEnv.reset
        supervisor = self

        def step(env, actions):
            result = original_step(env, actions)
            supervisor._after_step(env, actions)
            return result

        def reset(env, *args, **kwargs):
            supervisor.close_episode(env)
            return original_reset(env, *args, **kwargs)
        CityLearnDecPOMDPEnv.step, CityLearnDecPOMDPEnv.reset = step, reset
        try:
            yield self
        finally:
            CityLearnDecPOMDPEnv.step, CityLearnDecPOMDPEnv.reset = original_step, original_reset

    def _citylearn_v3_record(self, env):
        if not self.citylearn_v3 or env is None:
            return None
        try:
            from citylearn.v3.objectives import evaluate_objectives
            from uc3m.application.evaluation.kpi_contract import comparable_kpi_gain_rows
            report = evaluate_objectives(env)
            return {'gains': comparable_kpi_gain_rows(report),
                    'building_objective_kpis': report.get('building_objective_kpis'),
                    'error': None}
        except Exception as exc:  # noqa: BLE001 - recorded, never hidden as a value
            return {'gains': None, 'building_objective_kpis': None, 'error': f'{type(exc).__name__}: {exc}'}

    def close_episode(self, env=None):
        if not self.recorder._steps:
            return None
        return self.recorder.close_episode(citylearn_v3=self._citylearn_v3_record(env or self._last_env))

    def report(self) -> dict:
        self.close_episode()
        supervision = self.recorder.summary()
        return {'effective_axis_weights': self._weights_seen[0] if len(self._weights_seen) == 1 else None,
                'effective_axis_weights_seen': list(self._weights_seen),
                'axis_weights_source': self._source,
                'reward_aggregation': list(self._aggregations),
                'supervision': supervision}


GIB = float(1024**3)


def measure_runtime_resources() -> dict:
    """Available system RAM and free CUDA VRAM in GiB (None when not measurable)."""
    ram = None
    try:
        import psutil
        ram = psutil.virtual_memory().available/GIB
    except (ImportError, OSError, RuntimeError):  # optional psutil; OS fallback stays available
        meminfo = Path('/proc/meminfo')
        if meminfo.is_file():
            for line in meminfo.read_text().splitlines():
                if line.startswith('MemAvailable:'):
                    ram = int(line.split()[1])*1024/GIB
        elif sys.platform == 'win32':
            import ctypes

            class _Status(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
            status = _Status()
            status.dwLength = ctypes.sizeof(_Status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                ram = status.ullAvailPhys/GIB
    vram, torch_error = None, None
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.mem_get_info()[0]/GIB
    except Exception as exc:  # noqa: BLE001 - resource failure is recorded and refuses the native launch
        torch_error = f'{type(exc).__name__}: {exc}'
    return {'ram_gib': ram, 'vram_gib': vram, 'torch_import_error': torch_error}


# SPEC-015 D-M3-3: requirement = max(floor, ceil(1.10 x estimate)). The 10 % margin is the one the
# earlier fixed numbers carried (72 GiB for a 65.3 GiB replay); the floor is the one already declared
# for HAPPO and MAAC, which have no estimator. A design rule, not a measurement.
REQUIREMENT_MARGIN = 1.10
RAM_FLOOR_GIB = 8
VRAM_FLOOR_GIB = 4


def requirement_from_estimate(estimate_gib: float, floor_gib: int) -> int:
    return max(int(floor_gib), math.ceil(REQUIREMENT_MARGIN*float(estimate_gib)))


def _candidate_requirements(algorithm: str, requirements: dict, native_args) -> List[str]:
    """Resolve a per-candidate VRAM requirement in place; a candidate without one is refused."""
    by_candidate = requirements.pop('min_vram_gib_by_rnn_hidden_dim', None)
    if by_candidate is None:
        return []
    value = _option(list(native_args or ()), '--rnn-hidden-dim')
    declared = {int(k): float(v) for k, v in by_candidate.items()}
    if value is None or not str(value).isdigit() or int(value) not in declared:
        return [f'unsupported_candidate:{algorithm}:rnn_hidden_dim={value}']
    requirements['min_vram_gib'] = declared[int(value)]
    return []


def check_runtime_resources(algorithm: str, requirements, *, episode_time_steps: int,
                            measure=measure_runtime_resources, native_args=()) -> dict:
    """Refuse before training when measured RAM/VRAM is below the declared requirement.

    Requirements bind from ``applies_from_episode_time_steps`` (year-long stages);
    shorter smokes are measured and recorded but not refused here (the native
    launchers still refuse their own allocations with the measured numbers). A
    requirement declared per candidate uses the attempt's own native argument.
    """
    requirements = dict(requirements or {})
    candidate = _candidate_requirements(algorithm, requirements, native_args)
    measured = measure()
    enforced = int(episode_time_steps) >= int(requirements.get('applies_from_episode_time_steps', 0))
    reasons = list(candidate) if enforced else []
    if measured.get('torch_import_error'):
        reasons.append('torch_import_failed')
    if enforced:
        for key, what in (('min_ram_gib', 'ram'), ('min_vram_gib', 'vram')):
            need = float(requirements.get(key, 0) or 0)
            have = measured.get(f'{what}_gib')
            if need > 0 and (have is None or have < need):
                reasons.append(f'insufficient_resources:{algorithm}:{what}')
    return {'accepted': not reasons, 'reasons': reasons, 'enforced': enforced, 'measured': measured,
            'requirements': requirements}


def _runtime_requirements(root: Path, algorithm: str):
    import yaml
    payload = yaml.safe_load((Path(root)/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))
    return (payload['algorithms'][algorithm] or {}).get('runtime_requirements') or {}


def _bundle_hash(files) -> str:
    """Kept for callers of the adapter; the identity rule lives in the domain."""
    from uc3m.domain.evidence import checkpoint_bundle_hash
    return checkpoint_bundle_hash(files)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    native = argv[argv.index('--') + 1:] if '--' in argv else []
    own = argv[:argv.index('--')] if '--' in argv else argv
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--algorithm', required=True, choices=sorted(TRAINERS))
    parser.add_argument('--campaign-id', required=True)
    parser.add_argument('--attempt-id', required=True)
    parser.add_argument('--attempt-root', type=Path, required=True)
    parser.add_argument('--normalizer', type=Path, default=None)
    args = parser.parse_args(own)
    root = Path(__file__).resolve().parents[3]
    attempt_root = args.attempt_root.resolve()
    output = attempt_root/'native'
    native = native_arguments(native) + ['--output-dir', str(output)]
    common = load_native_common(root)
    observer = LearningObserver(args.campaign_id, args.attempt_id)
    common.install_finite_optimizer_step_guard = observer.wrap_guard_installer(common.install_finite_optimizer_step_guard)
    record = {'campaign_id': args.campaign_id, 'attempt_id': args.attempt_id,
              'algorithm': args.algorithm, 'native_arguments': native, 'stage': 'train', 'exit_code': None,
              'error': None, 'salvage': None}
    limits = contextlib.nullcontext()
    if args.normalizer is not None:
        from uc3m.adapters.citylearn.fresh_observations import frozen_observation_limits, load_normalizer
        limits = frozen_observation_limits(load_normalizer(args.normalizer))
    script = trainer_script(root, args.algorithm)
    resources = check_runtime_resources(args.algorithm, _runtime_requirements(root, args.algorithm),
                                        episode_time_steps=int(_option(native, '--episode-time-steps', '8760')),
                                        native_args=native)
    (attempt_root/'runtime_resources.json').write_text(json.dumps(resources, indent=2), encoding='utf-8')
    if not resources['accepted']:
        refused = {**record, 'verified': False, 'reasons': resources['reasons'], 'runtime_resources': resources}
        (attempt_root/'learning_evidence.json').write_text(json.dumps(refused, indent=2), encoding='utf-8')
        return 1
    if resources['measured']['ram_gib'] is not None:
        # The MATD3 launcher refuses (never shrinks) replay above this cap: use the measured RAM.
        import os
        os.environ.setdefault('MATD3_MAX_REPLAY_RAM_GIB', f"{resources['measured']['ram_gib']:.2f}")
    if str(root/'CityLearn') not in sys.path:
        sys.path.insert(0, str(root/'CityLearn'))
    supervisor = RewardSupervisor()
    saved_argv = sys.argv
    try:
        with attempt_isolation(common, attempt_root), limits, supervisor.installed():
            sys.argv = [str(script)] + native
            try:
                runpy.run_path(str(script), run_name='__main__')
                record['exit_code'] = 0
            except SystemExit as stop:
                record['exit_code'] = stop.code if isinstance(stop.code, int) else (0 if stop.code is None else 1)
    except BaseException as exc:  # noqa: BLE001 - recorded with traceback, never hidden
        record['exit_code'] = 1
        record['error'] = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    finally:
        sys.argv = saved_argv

    if record['exit_code'] != 0:
        # A failed Torch DLL initialization cannot safely be imported again to
        # inspect checkpoints (it previously aborted with duplicate C10 registration).
        # Partial artifacts/logs remain; no completed trajectory is certified.
        failed = {**record, 'verified': False, 'reasons': [f"native_exit_code:{record['exit_code']}"],
                  'env_steps': None, 'completed_episodes': None,
                  'env_steps_source': 'not_certified_after_native_failure', 'runtime_resources': resources}
        (attempt_root/'learning_evidence.json').write_text(json.dumps(failed, indent=2), encoding='utf-8')
        return 1

    stage = 'evidence'
    try:
        job = job_directory(output, native)
        record['salvage'] = salvage_reason(common.read_job_results_json(job))
        schema = json.loads(Path(_option(native, '--schema-path')).read_text(encoding='utf-8'))
        agents = sum(1 for b in schema['buildings'].values() if b.get('include', True))
        from uc3m.adapters.algorithms.evidence import checkpoint_bundle
        bundle = checkpoint_bundle(output, args.algorithm, agents)
        episode_steps = int(_option(native, '--episode-time-steps', '8760'))
        episodes = common.infer_trustable_completed_episodes(
            job, algorithm=args.algorithm.lower(), episode_time_steps=episode_steps, rollout_threads=1,
            live_progress=common.read_live_progress_json(job))
        runtime = supervisor.report()
        observed_episode_steps = [e['steps'] for e in runtime['supervision'].get('episodes_detail', [])]
        observed_steps = int(runtime['supervision'].get('steps', 0))
        evidence = observer.finalize(env_steps=observed_steps,
                                     checkpoint_bundle_hash=_bundle_hash(bundle) if bundle else None)
        reasons = list(evidence.reasons)
        if sum(count == episode_steps for count in observed_episode_steps) < int(episodes or 0):
            reasons.append('observed_episodes_shorter_than_native_report')
        if record['salvage']:
            reasons.append('completed_with_salvage')
        if record['exit_code'] != 0:
            reasons.append(f'native_exit_code:{record["exit_code"]}')
        stage = 'supervision'
        (attempt_root/'supervision.json').write_text(json.dumps(runtime, indent=2, default=str), encoding='utf-8')
        if runtime['reward_aggregation'] != ['team_mean']:
            reasons.append(f"reward_aggregation:{runtime['reward_aggregation']}")
        if len(runtime['effective_axis_weights_seen']) > 1:
            reasons.append('inconsistent_runtime_weights')
        summary = {k: v for k, v in runtime['supervision'].items() if k != 'episodes_detail'}
        summary['episode_kpis'] = [{'episode': e['episode'], 'steps': e['steps'],
                                    'thesis_indicators_district': (e.get('thesis_indicators') or {}).get('district'),
                                    'comparable_kpi_gains': (e.get('citylearn_v3') or {}).get('gains')}
                                   for e in runtime['supervision'].get('episodes_detail', [])]
        result = {**evidence.as_dict(), 'verified': evidence.verified and not reasons and not record['salvage']
                  and record['exit_code'] == 0 and runtime['reward_aggregation'] == ['team_mean'],
                  'reasons': reasons, 'completed_episodes': episodes,
                  'env_steps_source': 'observed_native_interactions_including_internal_evaluation',
                  'trajectory_episode_steps': observed_episode_steps,
                  'native_reported_training_steps': int(episodes or 0)*episode_steps,
                  'checkpoint_files': [str(Path(p).relative_to(attempt_root)) for p in bundle],
                  'effective_axis_weights': runtime['effective_axis_weights'],
                  'axis_weights_source': runtime['axis_weights_source'],
                  'reward_aggregation': runtime['reward_aggregation'],
                  'supervision': dict(summary, path='supervision.json'),
                  'runtime_resources': resources, **record}
    except BaseException as exc:  # noqa: BLE001
        result = {**record, 'verified': False, 'reasons': [f'{stage}_failed'],
                  'evidence_error': ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}
    (attempt_root/'learning_evidence.json').write_text(json.dumps(result, indent=2, default=str), encoding='utf-8')
    return 0 if result['verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
