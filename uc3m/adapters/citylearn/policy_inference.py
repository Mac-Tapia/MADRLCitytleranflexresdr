"""Frozen-policy evaluation on CityLearn with per-step physical traces (T7).

A frozen policy only acts: no optimizer step, no exploration, no replay. Every
policy, baseline or native, runs on the same environment stack the native
trainers use (``CityLearnV3BackendAdapter`` of
``CityLearn/scripts/citylearn_v3_training_common.py``) built with the same
split schema, scenario, seed and episode length, with the training-split
observation bounds frozen for the whole episode. One extraction turns the
underlying CityLearnEnv into a PhysicalTrace for the T4 KPI contract
(per-building net power, battery throughput, district price and carbon);
env.evaluate() aggregates are not used. The test split is locked until a
configuration freeze unlocks it.

Baselines are fresh policies: the CityLearn EV-aware RBC and a reference that
never dispatches the battery but serves the same EV sessions.

Native policies are reloaded only from a verified fresh attempt of this
campaign: learning_evidence.json must be verified, its checkpoint bundle
complete and hashing to the recorded bundle hash. Each backend is rebuilt with
its original classes and its trainer's own environment adapter, with
hyperparameters recovered from the attempt (the trainer's ``parse_args`` over
the recorded native arguments plus the job's data/results.json). There is no
random, substitute or partially loaded policy.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np

from uc3m.adapters.citylearn.fresh_observations import frozen_observation_limits, load_normalizer
from uc3m.application.evaluation.kpi_contract import PhysicalTrace

REPO_ROOT = Path(__file__).resolve().parents[3]
UNITS = {'net_power': 'kW', 'carbon_intensity': 'kgCO2/kWh', 'price': 'USD/kWh', 'battery_throughput': 'kWh'}
NATIVE_ALGORITHMS = ('HAPPO', 'MASAC', 'MATD3', 'MAAC')
ADAPTER_PADDING = ('CityLearnV3BackendAdapter.padded_observations: CityLearn observations of the agent, '
                   'then its EV-type codes, then trailing zeros up to max_observation_dim')
# Optimizer-only HARL keys: they never change the acting network.
_HARL_OPTIMIZER_KEYS = frozenset({'lr', 'critic_lr', 'opti_eps', 'weight_decay'})


class FrozenPolicyRejected(PermissionError):
    """The attempt cannot provide a trustworthy frozen policy."""


@dataclass(frozen=True)
class FrozenRun:
    policy: str
    split: str
    trace: PhysicalTrace
    completed_steps: int
    training_updates: int
    ev_connection_hash: str
    initial_storage_kwh: float
    final_storage_kwh: float
    battery_throughput_kwh: float
    contract: Mapping[str, Any] = field(default_factory=dict)
    # citylearn.v3.objectives.evaluate_objectives of the run's own environment (Layer B KPIs).
    citylearn_v3_report: Mapping[str, Any] = field(default_factory=dict)


# --- shared environment helpers -------------------------------------------------------------------

def _common():
    from uc3m.adapters.algorithms.native_entrypoint import load_native_common
    return load_native_common(REPO_ROOT)


def _split_record(campaign_root: Path, split_id: str):
    manifest = json.loads((campaign_root/'split_manifest.json').read_text(encoding='utf-8'))
    return next(s for s in manifest['splits'] if s['split_id'] == split_id)


def _storage_kwh(building, step=None) -> float:
    storage = building.electrical_storage
    soc = storage.initial_soc if step is None else storage.soc[step]
    return float(soc or 0.0)*float(storage.capacity or 0.0)


def _citylearn_env(adapter):
    """The CityLearnEnv under the adapter's wrappers (raw observations, buildings, physics)."""
    core = adapter._core_env()
    return getattr(core, 'unwrapped', core)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _adapter_contract(adapter) -> Dict[str, Any]:
    names = json.dumps(adapter.observation_names_by_agent, sort_keys=True).encode('utf-8')
    return {'agents': list(adapter.agents),
            'citylearn_observation_dims': dict(adapter._citylearn_observation_dims),
            'ev_type_code_dims': {a: int(len(adapter._ev_type_codes_per_agent.get(a, ()))) for a in adapter.agents},
            'observation_dims': dict(adapter.observation_dims),
            'max_observation_dim': int(adapter.max_observation_dim),
            'observation_padding': ADAPTER_PADDING,
            'observation_names_sha256': hashlib.sha256(names).hexdigest(),
            'normalize_observations': bool(adapter.normalize_observations),
            'state_dim': int(adapter.state_dim),
            'action_dims': dict(adapter.action_dims),
            'max_action_dim': int(adapter.max_action_dim),
            'action_names_by_agent': {a: list(n) for a, n in adapter.action_names_by_agent.items()},
            'action_transform': ('per agent: first action_dims[agent] entries, clipped to the CityLearn '
                                 'action space (CityLearnV3BackendAdapter._continuous_action_for_agent)')}


def _physical_trace(core, taken: int, campaign_root: Path, split_id: str):
    """One trace extraction for every policy: (trace, EV connection hash, battery throughput)."""
    start = datetime.fromisoformat(_split_record(campaign_root, split_id)['start'])
    stamps = tuple((start + timedelta(hours=t)).isoformat() for t in range(taken))
    series, throughput = {}, 0.0
    connection = hashlib.sha256()
    for building in core.buildings:
        power = [float(v) for v in building.net_electricity_consumption[:taken]]
        balance = [abs(float(v)) for v in building.electrical_storage.energy_balance[:taken]]
        throughput += sum(balance)
        series[building.name] = {'net_power': power, 'battery_throughput': balance}
        for charger in building.electric_vehicle_chargers or []:
            states = charger.charger_simulation.electric_vehicle_charger_state[:taken]
            connection.update((charger.charger_id + ':' + ','.join(str(s) for s in states)).encode('utf-8'))
    first = core.buildings[0]
    district = {'carbon_intensity': [float(v) for v in first.carbon_intensity.carbon_intensity[:taken]],
                'price': [float(v) for v in first.pricing.electricity_pricing[:taken]]}
    provenance = json.loads((campaign_root/'provenance.json').read_text(encoding='utf-8'))
    currency_note = (f"bills {provenance['billing_currency']} converted with World Bank PA.NUS.FCRF "
                     f"annual PEN per USD {provenance['pen_per_usd']}")
    exogenous = hashlib.sha256(json.dumps(district, sort_keys=True).encode('utf-8')).hexdigest()
    trace = PhysicalTrace(stamps, 3600, tuple(series), series, district, UNITS, 'USD', currency_note, exogenous)
    return trace, connection.hexdigest(), throughput


@contextlib.contextmanager
def _optimizer_step_counter():
    """Count every torch optimizer step taken anywhere in the process during the block."""
    from torch.optim.optimizer import register_optimizer_step_pre_hook
    count = [0]

    def hook(optimizer, args, kwargs):
        count[0] += 1
    handle = register_optimizer_step_pre_hook(hook)
    try:
        yield count
    finally:
        handle.remove()


# --- policy protocol ------------------------------------------------------------------------------

class FrozenController:
    """reset(seed) -> observations; act(observations, deterministic=True) -> actions; step(actions)."""
    name = 'policy'
    algorithm: Optional[str] = None
    recurrent = False

    def __init__(self):
        self.adapter = None
        self.history: List[Dict[str, Any]] = []

    def resolve_scenario(self, requested: Optional[str]) -> Optional[str]:
        return requested

    def recurrent_state_is_initial(self) -> bool:
        return True

    def recurrent_state_nonzero(self) -> bool:
        return False

    def parameter_hash(self) -> Optional[str]:
        return None

    def contract(self) -> Dict[str, Any]:
        return {'policy': self.name, 'algorithm': self.algorithm, 'deterministic': True,
                'recurrent': self.recurrent, 'discrete_action_table': None, 'discrete_action_metadata': None,
                **_adapter_contract(self.adapter)}


class RbcPolicy(FrozenController):
    """CityLearn BasicElectricVehicleRBC_ReferenceController, unchanged, on the trainers' env stack."""
    name = 'rbc'

    def build_env(self, common, schema_path: Path, scenario, seed, episode_time_steps: int):
        self.adapter = common.CityLearnV3BackendAdapter(
            schema_path=str(schema_path), scenario=scenario, seed=seed, episode_time_steps=episode_time_steps,
            algorithm='MADRL', live_progress_path=None, trace_record_interval=0)
        return self.adapter

    def reset(self, seed):
        from citylearn.agents.rbc import BasicElectricVehicleRBC_ReferenceController
        if seed is not None:
            self.adapter.seed(seed)
        self.adapter.reset()
        self._core = _citylearn_env(self.adapter)
        if [b.name for b in self._core.buildings] != list(self.adapter.agents):
            raise RuntimeError('CityLearn building order differs from the Dec-POMDP agent order')
        self._agent = BasicElectricVehicleRBC_ReferenceController(self._core)
        self.history = []
        return self._core.observations

    def act(self, observations, deterministic: bool = True):
        return [list(a) for a in self._agent.predict(observations)]

    def step(self, actions):
        self.history.append({'actions': [list(a) for a in actions]})
        _, _, dones, _ = self.adapter.step_continuous(actions)
        return self._core.observations, bool(dones) and all(dones.values())


class NoStorageReferencePolicy(RbcPolicy):
    """Same EV and machine behaviour as the RBC; the battery is never dispatched."""
    name = 'no_storage_reference'

    def act(self, observations, deterministic: bool = True):
        actions = super().act(observations)
        for index, names in enumerate(self._core.action_names):
            for position, name in enumerate(names):
                if name == 'electrical_storage':
                    actions[index][position] = 0.0
        return actions


def run_frozen_episode(split_dir: Path, policy, campaign_root: Path, *, steps: Optional[int] = None,
                       seed: Optional[int] = None, scenario: Optional[str] = None) -> FrozenRun:
    """Run one frozen episode of ``policy`` on a split; ``steps`` actions (default: the whole split)."""
    split_dir, campaign_root = Path(split_dir), Path(campaign_root)
    if split_dir.name == 'test_2025' and not (campaign_root/'test_unlock.json').is_file():
        raise PermissionError('the test split opens only after the signed configuration freeze')
    from uc3m.application.training.integrity import verify_split_input
    split_sha256 = verify_split_input(campaign_root, split_dir)  # before any environment is built
    rows =int(_split_record(campaign_root, split_dir.name)['rows'])
    # CityLearn ends an episode of N time steps after N - 1 actions.
    horizon = rows - 1 if steps is None else int(steps)
    if not 0 < horizon < rows:
        raise ValueError(f'{split_dir.name}: steps must be in [1, {rows - 1}], got {horizon}')
    scenario = policy.resolve_scenario(scenario)
    normalizer = campaign_root/'normalizer.json'
    spec = load_normalizer(normalizer)
    common = _common()
    from uc3m.adapters.algorithms.native_entrypoint import attempt_isolation
    import torch
    with tempfile.TemporaryDirectory(prefix='frozen_eval_') as scratch, \
            attempt_isolation(common, Path(scratch)), frozen_observation_limits(spec), \
            _optimizer_step_counter() as optimizer_steps:
        policy.build_env(common, split_dir/'schema.json', scenario, seed, horizon + 1)
        core = _citylearn_env(policy.adapter)
        observations = policy.reset(seed)
        tracker = core.episode_tracker
        if tracker.episode_start_time_step != tracker.simulation_start_time_step:
            raise RuntimeError(f'{policy.name}: the episode does not start at the beginning of {split_dir.name}')
        initial = sum(_storage_kwh(b) for b in core.buildings)
        before = policy.parameter_hash()
        grad_seen, taken = False, 0
        while taken < horizon:
            actions = policy.act(observations, deterministic=True)
            grad_seen = grad_seen or bool(getattr(policy, 'grad_enabled_during_act', False))
            observations, done = policy.step(actions)
            taken += 1
            if done:
                break
        after = policy.parameter_hash()
        trace, connection, throughput = _physical_trace(core, taken, campaign_root, split_dir.name)
        final = sum(_storage_kwh(b, taken) for b in core.buildings)
        from citylearn.v3.objectives import evaluate_objectives
        citylearn_v3_report = evaluate_objectives(core)
        updates = int(optimizer_steps[0])
    contract = {**policy.contract(), 'split': split_dir.name, 'split_sha256': split_sha256, 'scenario': scenario, 'seed': seed,
                'episode_time_steps': horizon + 1, 'normalizer_sha256': _sha256_file(normalizer),
                'parameter_hash_before': before, 'parameter_hash_after': after,
                'grad_enabled_during_act': grad_seen, 'torch_grad_enabled_after': torch.is_grad_enabled(),
                'trace_record_interval': 0}
    return FrozenRun(policy.name, split_dir.name, trace, taken, updates, connection, initial, final, throughput,
                     contract, citylearn_v3_report)


# --- native policies ------------------------------------------------------------------------------

def _relative_path(text: str) -> Path:
    return Path(str(text).replace('\\', '/'))


def _module_hash(modules: Sequence) -> str:
    digest = hashlib.sha256()
    for label, module in modules:
        for key, tensor in sorted(module.state_dict().items()):
            digest.update(f'{label}.{key}'.encode('utf-8'))
            digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _training_agents(native_arguments: Sequence[str]) -> int:
    from uc3m.adapters.algorithms.native_entrypoint import _option
    schema_path = _option(list(native_arguments), '--schema-path')
    if not schema_path or not Path(schema_path).is_file():
        raise FrozenPolicyRejected(f'training schema of the attempt is not available: {schema_path}')
    schema = json.loads(Path(schema_path).read_text(encoding='utf-8'))
    return sum(1 for b in schema['buildings'].values() if b.get('include', True))


def _trainer_arguments(algorithm: str, native_arguments: Sequence[str]):
    """The trainer's own parse_args over the recorded native arguments."""
    from uc3m.adapters.algorithms.native_entrypoint import TRAINERS
    _common()  # puts CityLearn/scripts on sys.path
    trainer = importlib.import_module(Path(TRAINERS[algorithm]).stem)
    saved = sys.argv
    sys.argv = [str(trainer.__file__)] + list(native_arguments)
    try:
        return trainer.parse_args()
    except SystemExit as exc:
        raise FrozenPolicyRejected(f'{algorithm}: recorded native arguments do not parse: {exc}') from exc
    finally:
        sys.argv = saved


@contextlib.contextmanager
def _backend_import_scope(path: Path, top_level_names: Sequence[str], drop_uc3m_paths: bool = False):
    """Import a backend whose packages have generic top-level names, then restore sys.path/modules."""
    names = set(top_level_names)
    saved_path = list(sys.path)
    saved = {k: sys.modules.pop(k) for k in list(sys.modules) if k.split('.')[0] in names}
    if drop_uc3m_paths:
        sys.path[:] = [p for p in sys.path if not p.replace('\\', '/').rstrip('/').endswith('/uc3m')]
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        for key in [k for k in sys.modules if k.split('.')[0] in names]:
            sys.modules.pop(key)
        sys.modules.update(saved)
        sys.path[:] = saved_path


class NativeFrozenPolicy(FrozenController):
    """A verified fresh native policy; subclasses rebuild the backend's own networks."""
    env_class = ''
    discrete = False

    def __init__(self, algorithm, attempt_root, evidence, files, args, results, job_dir, common):
        super().__init__()
        self.name = self.algorithm = algorithm
        self.attempt_root = Path(attempt_root)
        self.evidence = evidence
        self.checkpoint_files = tuple(files)
        self.native_arguments = list(evidence['native_arguments'])
        self.args = args
        self.results = results
        self.hyperparameters = dict(results.get('hyperparameters') or {})
        self.job_dir = Path(job_dir)
        self.scenario = args.scenario
        self.common = common
        self.agents: List[str] = []
        self.backend: Dict[str, Any] = {}
        self._built = False
        self.grad_enabled_during_act = False

    def resolve_scenario(self, requested):
        if requested is not None and requested != self.scenario:
            raise ValueError(f'{self.algorithm} was trained in scenario {self.scenario}, not {requested}')
        return self.scenario

    def _env_kwargs(self, schema_path, seed, episode_time_steps):
        kwargs = dict(schema_path=str(schema_path), scenario=self.scenario, seed=seed,
                      episode_time_steps=episode_time_steps, algorithm=self.algorithm, live_progress_path=None,
                      trace_record_interval=0, trace_detail=self.args.trace_detail,
                      normalize_observations=self.args.normalize_observations)
        if self.discrete:
            kwargs.update(action_bins=self.args.action_bins, discrete_action_mode=self.args.discrete_action_mode)
        return kwargs

    def build_env(self, common, schema_path, scenario, seed, episode_time_steps):
        self.env = getattr(common, self.env_class)(**self._env_kwargs(schema_path, seed, episode_time_steps))
        self.adapter = self.env.adapter
        signature = self._signature()
        if not self._built:
            self.agents = list(self.adapter.agents)
            self._build_networks()
            self._built, self._built_signature = True, signature
        elif signature != self._built_signature:
            raise FrozenPolicyRejected(f'{self.algorithm}: split spaces {signature} differ from the policy '
                                       f'{self._built_signature}')
        return self.env

    def _signature(self):
        a = self.adapter
        return (tuple(a.agents), int(a.max_observation_dim), int(a.max_action_dim), int(a.n_discrete_actions),
                int(a.state_dim))

    def _no_grad_act(self, function):
        import torch
        with torch.no_grad():
            self.grad_enabled_during_act = torch.is_grad_enabled()
            return function()

    def _record(self, observations, actions):
        self.history.append({'observations': np.array(observations, dtype=np.float32, copy=True),
                             'actions': np.array(actions, copy=True)})

    def contract(self):
        payload = super().contract()
        if self.discrete:
            payload['discrete_action_table'] = np.asarray(self.adapter.discrete_action_table).tolist()
            payload['discrete_action_metadata'] = dict(self.adapter.discrete_action_metadata)
        payload.update({
            'backend_env_class': self.env_class,
            'network_classes': {k: f'{v.__module__}.{v.__qualname__}' for k, v in self.backend.items()},
            'checkpoint_files': [str(Path(p).relative_to(self.attempt_root)) for p in self.checkpoint_files],
            'checkpoint_bundle_hash': self.evidence['checkpoint_bundle_hash'],
            'campaign_id': self.evidence.get('campaign_id'), 'attempt_id': self.evidence.get('attempt_id'),
            'native_arguments': self.native_arguments,
            'hyperparameter_source': ['trainer parse_args(learning_evidence.native_arguments)',
                                      'data/results.json hyperparameters'],
            'device': 'cpu'})
        return payload


class HappoFrozenPolicy(NativeFrozenPolicy):
    env_class = 'CityLearnHARLEnv'

    def _build_networks(self):
        import torch
        self.common.add_external_path('HARL')
        from harl.algorithms.actors import ALGO_REGISTRY
        from harl.models.policy_models.stochastic_policy import StochasticPolicy
        from harl.utils.configs_tools import get_defaults_yaml_args
        algo_args, _ = get_defaults_yaml_args('happo', 'gym')
        model, algo = dict(algo_args['model']), dict(algo_args['algo'])
        for section in (model, algo):
            for key in section:
                if key in self.hyperparameters:
                    section[key] = self.hyperparameters[key]
        directory = Path(self.checkpoint_files[0]).parent
        config_file = directory.parent/'config.json'  # HARL's save_config of this run
        if config_file.is_file():
            saved = json.loads(config_file.read_text(encoding='utf-8'))['algo_args']
            for name, section in (('model', model), ('algo', algo)):
                differing = sorted(k for k, v in saved.get(name, {}).items()
                                   if k in section and k not in _HARL_OPTIMIZER_KEYS and section[k] != v)
                if differing:
                    raise FrozenPolicyRejected(f'HAPPO {name} args {differing} differ from {config_file}')
        if algo.get('share_param'):
            raise FrozenPolicyRejected('HAPPO with shared parameters is not the trained configuration')
        self.model_args = {**model, **algo}
        self.backend = {'StochasticPolicy': StochasticPolicy, 'HAPPO': ALGO_REGISTRY['happo']}
        self.observation_spaces = list(self.env.observation_space)
        self.action_spaces = list(self.env.action_space)
        if len(self.observation_spaces) != len(self.agents):
            raise FrozenPolicyRejected('HAPPO observation spaces do not match the agents')
        self.actors = []
        for index in range(len(self.agents)):
            actor = ALGO_REGISTRY['happo'](self.model_args, self.observation_spaces[index], self.action_spaces[index],
                                           device=torch.device('cpu'))
            path = directory/f'actor_agent{index}.pt'
            actor.actor.load_state_dict(torch.load(str(path), map_location='cpu'))
            actor.prep_rollout()
            self.actors.append(actor)
        self.recurrent = bool(model.get('use_recurrent_policy') or model.get('use_naive_recurrent_policy'))
        self._rnn_shape = (1, len(self.agents), int(model['recurrent_n']), int(model['hidden_sizes'][-1]))

    def reset(self, seed):
        if seed is not None:
            self.env.seed(seed)
        observations, _, _ = self.env.reset()
        self._rnn = np.zeros(self._rnn_shape, dtype=np.float32)
        self._masks = np.ones((1, len(self.agents), 1), dtype=np.float32)
        self.history = []
        return observations

    def act(self, observations, deterministic: bool = True):
        obs = np.asarray(observations, dtype=np.float32)[None]

        def compute():
            actions = []
            for index, actor in enumerate(self.actors):
                action, state = actor.act(obs[:, index], self._rnn[:, index], self._masks[:, index], None,
                                          deterministic=deterministic)
                self._rnn[:, index] = state.cpu().numpy()
                actions.append(action.cpu().numpy()[0])
            return np.asarray(actions)
        actions = self._no_grad_act(compute)
        self._record(observations, actions)
        return actions

    def step(self, actions):
        observations, _, _, dones, _, _ = self.env.step(actions)
        return observations, all(dones)

    def recurrent_state_is_initial(self):
        return not np.any(self._rnn)

    def recurrent_state_nonzero(self):
        return bool(np.any(self._rnn))

    def parameter_hash(self):
        return _module_hash([(f'actor_agent{i}', a.actor) for i, a in enumerate(self.actors)])

    def contract(self):
        return {**super().contract(), 'actor_files': [f'actor_agent{i}.pt' for i in range(len(self.agents))],
                'action_selection': 'HARL actor.act(deterministic=True)', 'masks': 'ones'}


MASAC_TOP_LEVEL = ('common', 'agent', 'network', 'policy', 'ac_discrete')


class MasacFrozenPolicy(NativeFrozenPolicy):
    env_class = 'CityLearnSMACDiscreteEnv'
    discrete = True
    recurrent = True  # the MASAC policy network is a GRUCell

    def _build_networks(self):
        common = self.common
        env_info = self.env.get_env_info()
        hyper = self.hyperparameters
        expected = {'n_actions': hyper.get('n_discrete_actions'), 'state_shape': hyper.get('ctde_state_shape')}
        observed = {k: env_info[k] for k in expected}
        if observed != expected:
            raise FrozenPolicyRejected(f'MASAC env {observed} differs from the trained {expected}')
        with _backend_import_scope(common.EXTERNAL_ROOT/'MARL'/'src', MASAC_TOP_LEVEL):
            from common.arguments import get_common_args, get_mixer_args
            from agent.agent_msac_mcsac import Agents
            from ac_discrete.qmix_msac import QMIX_PG
            from ac_discrete.rnn_policy import rnn_policy
            saved = sys.argv
            sys.argv = [saved[0]]
            try:
                args = get_mixer_args(get_common_args())
            finally:
                sys.argv = saved
            args.alg, args.map, args.seed = 'qmix', f'citylearn_v3_{self.scenario}', self.args.seed
            for key in ('n_actions', 'n_agents', 'state_shape', 'obs_shape'):
                setattr(args, key, env_info[key])
            for key, value in hyper.items():
                if hasattr(args, key) and not isinstance(value, (dict, list)):
                    setattr(args, key, value)
            args.use_rnn = bool(hyper.get('use_recurrent_policy', False))
            args.cuda, args.load_model = False, False
            bundle = common.find_masac_checkpoint_bundle(self.job_dir/'checkpoints'/'models')
            if not bundle or {Path(p).resolve() for p in bundle.values()} != {Path(p).resolve()
                                                                              for p in self.checkpoint_files}:
                raise FrozenPolicyRejected('MASAC: the trainer bundle finder disagrees with the verified files')
            self.agents_backend = Agents(args)
            self.learner = QMIX_PG(self.agents_backend, args)
            common.load_masac_checkpoint_bundle(self.learner, bundle, use_cuda=False)
        self.backend_args = args
        self.backend = {'rnn_policy': rnn_policy, 'Agents': Agents, 'QMIX_PG': QMIX_PG}
        self.policy_input_shape = (args.obs_shape + (args.n_actions if args.last_action else 0)
                                   + (args.n_agents if args.reuse_network else 0))
        self.agents_backend.policy.eval()

    def build_env(self, common, schema_path, scenario, seed, episode_time_steps):
        env = super().build_env(common, schema_path, scenario, seed, episode_time_steps)
        self._constructor_seed, self._constructor_reset = seed, True  # CityLearnSMACDiscreteEnv resets in __init__
        return env

    def reset(self, seed):
        if self._constructor_reset and seed in (None, self._constructor_seed):
            # A second CityLearn reset would advance to the next episode window of the split.
            observations = self.env.get_obs()
        else:
            if seed is not None:
                self.env.adapter.seed(seed)
            observations = self.env.reset()
        self._constructor_reset = False
        self.agents_backend.init_hidden(1)
        self._last_action = np.zeros((self.backend_args.n_agents, self.backend_args.n_actions))
        self.history = []
        return observations

    def act(self, observations, deterministic: bool = True):
        if not deterministic:
            raise ValueError('frozen MASAC evaluation is greedy')
        n_actions = self.backend_args.n_actions
        available = np.ones(n_actions, dtype=np.float32)

        def compute():
            actions = []
            for index in range(self.backend_args.n_agents):
                action = int(self.agents_backend.choose_action(observations[index], self._last_action[index], index,
                                                               available, 0, None, True))
                self._last_action[index] = np.eye(n_actions)[action]
                actions.append(action)
            return np.asarray(actions)
        actions = self._no_grad_act(compute)
        self._record(observations, actions)
        return actions

    def step(self, actions):
        _, terminated, _ = self.env.step([int(a) for a in actions])
        return self.env.get_obs(), bool(terminated)

    def recurrent_state_is_initial(self):
        return not bool(self.agents_backend.policy_eval_hidden.abs().sum()) and not np.any(self._last_action)

    def recurrent_state_nonzero(self):
        return bool(self.agents_backend.policy_eval_hidden.abs().sum())

    def parameter_hash(self):
        return _module_hash([('policy', self.agents_backend.policy), ('eval_rnn', self.learner.eval_rnn),
                             ('eval_qmix_net', self.learner.eval_qmix_net)])

    def contract(self):
        return {**super().contract(), 'policy_input': 'observation + last action one-hot + agent id one-hot',
                'action_selection': 'Agents.choose_action(evaluate=True, epsilon=0): argmax softmax(q/temp)'}


class Matd3FrozenPolicy(NativeFrozenPolicy):
    env_class = 'CityLearnOffPolicyVecEnv'

    def _build_networks(self):
        import torch
        common = self.common
        common.install_noop_wandb()
        common.add_external_path('off-policy')
        from offpolicy.config import get_config
        from offpolicy.utils.util import get_cent_act_dim, get_dim_from_space
        from offpolicy.algorithms.matd3.algorithm.MATD3Policy import MATD3Policy
        from offpolicy.algorithms.matd3.algorithm.actor_critic import MATD3_Actor
        args = get_config().parse_args([])
        args.algorithm_name, args.env_name = 'matd3', 'CityLearnV3'
        args.scenario_name, args.seed = self.scenario, self.args.seed
        args.hidden_size = self.args.hidden_size
        for key, value in self.hyperparameters.items():
            if hasattr(args, key) and not isinstance(value, (dict, list)):
                setattr(args, key, value)
        args.cuda, args.use_wandb, args.use_eval = False, False, False
        env = self.env
        policy_info = {f'policy_{i}': {'cent_obs_dim': get_dim_from_space(env.share_observation_space[i]),
                                       'cent_act_dim': get_cent_act_dim(env.action_space),
                                       'obs_space': env.observation_space[i],
                                       'share_obs_space': env.share_observation_space[i],
                                       'act_space': env.action_space[i]} for i in range(env.num_agents)}
        model_dir = common.find_offpolicy_model_dir(self.job_dir/'checkpoints')
        if model_dir is None:
            raise FrozenPolicyRejected('MATD3: no off-policy model directory in the attempt')
        expected = {(Path(model_dir)/f'policy_{i}'/name).resolve() for i in range(env.num_agents)
                    for name in ('actor.pt', 'critic.pt')}
        if expected != {Path(p).resolve() for p in self.checkpoint_files}:
            raise FrozenPolicyRejected('MATD3: the trainer model directory disagrees with the verified files')
        config = {'args': args, 'device': torch.device('cpu'), 'policy_info': policy_info,
                  'num_agents': env.num_agents, 'use_same_share_obs': True}
        # The off-policy runner pairs agent i with sorted(policy_ids)[i]; the same pairing is kept.
        self.policy_ids = sorted(policy_info)
        self.policies = {}
        for policy_id in self.policy_ids:
            policy = MATD3Policy(config, policy_info[policy_id], train=False)
            policy.actor.load_state_dict(torch.load(str(Path(model_dir)/policy_id/'actor.pt'), map_location='cpu'))
            policy.critic.load_state_dict(torch.load(str(Path(model_dir)/policy_id/'critic.pt'), map_location='cpu'))
            policy.actor.eval()
            self.policies[policy_id] = policy
        self.backend_args = args
        self.model_dir = str(model_dir)
        self.backend = {'MATD3_Actor': MATD3_Actor, 'MATD3Policy': MATD3Policy}
        self.observation_dims_by_policy = {p: get_dim_from_space(policy_info[p]['obs_space']) for p in policy_info}
        self.action_dims_by_policy = {p: get_dim_from_space(policy_info[p]['act_space']) for p in policy_info}

    def reset(self, seed):
        if seed is not None:
            self.env.adapter.seed(seed)
        observations = self.env.reset()[0]
        self.history = []
        return observations

    def act(self, observations, deterministic: bool = True):
        if not deterministic:
            raise ValueError('frozen MATD3 evaluation uses no exploration noise')
        obs = np.asarray(observations, dtype=np.float32)

        def compute():
            actions = []
            for agent_id, policy_id in enumerate(self.policy_ids):
                action, _ = self.policies[policy_id].get_actions(obs[agent_id][None], explore=False)
                actions.append(np.asarray(action.cpu().numpy() if hasattr(action, 'cpu') else action)[0])
            return np.asarray(actions)
        actions = self._no_grad_act(compute)
        self._record(observations, actions)
        return actions

    def step(self, actions):
        observations, _, dones, _ = self.env.step([list(actions)])
        return observations[0], bool(np.all(dones[0]))

    def parameter_hash(self):
        return _module_hash([(f'{p}.actor', self.policies[p].actor) for p in self.policy_ids])

    def contract(self):
        return {**super().contract(),
                'agent_policy_map': {agent: pid for agent, pid in zip(self.agents, self.policy_ids)},
                'action_selection': 'MATD3Policy.get_actions(explore=False): actor output, no Gaussian noise'}


MAAC_TOP_LEVEL = ('utils', 'algorithms')


class MaacFrozenPolicy(NativeFrozenPolicy):
    env_class = 'CityLearnMAACVecEnv'
    discrete = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(self.checkpoint_files) != 1:
            raise FrozenPolicyRejected('MAAC bundle must be exactly one saved model')
        with _backend_import_scope(self.common.EXTERNAL_ROOT/'MAAC', MAAC_TOP_LEVEL, drop_uc3m_paths=True):
            from algorithms.attention_sac import AttentionSAC
            from utils.policies import DiscretePolicy
            self.model = AttentionSAC.init_from_save(str(self.checkpoint_files[0]), load_critic=True)
        self.backend = {'AttentionSAC': AttentionSAC, 'DiscretePolicy': DiscretePolicy}
        init, hyper = self.model.init_dict, self.hyperparameters
        expected = {'pol_hidden_dim': hyper.get('hidden_size'), 'critic_hidden_dim': hyper.get('hidden_size'),
                    'attend_heads': hyper.get('attend_heads'), 'gamma': hyper.get('gamma'), 'tau': hyper.get('tau'),
                    'reward_scale': hyper.get('reward_scale'), 'pi_lr': hyper.get('pi_lr'), 'q_lr': hyper.get('q_lr')}
        differing = sorted(k for k, v in expected.items() if init.get(k) != v)
        if differing:
            raise FrozenPolicyRejected(f'MAAC saved init_dict differs from the trainer results in {differing}')
        self.model.prep_rollouts(device='cpu')

    def _build_networks(self):
        sizes = [(int(p['num_in_pol']), int(p['num_out_pol'])) for p in self.model.init_dict['agent_init_params']]
        expected = [(int(self.adapter.max_observation_dim), int(self.adapter.n_discrete_actions))]*len(self.agents)
        if sizes != expected:
            raise FrozenPolicyRejected(f'MAAC agent sizes {sizes[:1]}x{len(sizes)} differ from the env {expected[:1]}'
                                       f'x{len(expected)}')

    def reset(self, seed):
        if seed is not None:
            self.env.adapter.seed(seed)
        observations = self.env.reset()
        self.history = []
        return observations

    def act(self, observations, deterministic: bool = True):
        import torch
        obs = np.asarray(observations, dtype=np.float32)

        def compute():
            torch_obs = [torch.Tensor(np.vstack(obs[:, i])) for i in range(self.model.nagents)]
            return [a.data.cpu().numpy() for a in self.model.step(torch_obs, explore=not deterministic)]
        agent_actions = self._no_grad_act(compute)
        self._record(obs[0], np.asarray([a[0] for a in agent_actions]))
        return [[a[i] for a in agent_actions] for i in range(self.env.num_envs)]

    def step(self, actions):
        observations, _, dones, _ = self.env.step(actions)
        return observations, bool(np.all(dones[0]))

    def parameter_hash(self):
        return _module_hash([(f'agent{i}.policy', a.policy) for i, a in enumerate(self.model.agents)]
                            + [('critic', self.model.critic)])

    def contract(self):
        return {**super().contract(),
                'action_selection': 'AttentionSAC.step(explore=False): one-hot argmax of each DiscretePolicy'}


NATIVE_POLICIES = {'HAPPO': HappoFrozenPolicy, 'MASAC': MasacFrozenPolicy, 'MATD3': Matd3FrozenPolicy,
                   'MAAC': MaacFrozenPolicy}


def load_native_policy(algorithm: str, attempt_root: Path) -> NativeFrozenPolicy:
    """Load a verified checkpoint of this campaign; there is no fallback policy.

    FileNotFoundError: no attempt/evidence; FrozenPolicyRejected (PermissionError): unverified
    learning, another algorithm, incomplete bundle, bundle hash mismatch or inconsistent hyperparameters.
    """
    if algorithm not in NATIVE_POLICIES:
        raise ValueError(f'no native policy loader for {algorithm!r}; random or placeholder policies are refused')
    attempt_root = Path(attempt_root).resolve()
    native = attempt_root/'native'
    evidence_file = attempt_root/'learning_evidence.json'
    if not native.is_dir() or not evidence_file.is_file():
        raise FileNotFoundError(f'no verified native model in {attempt_root}')
    evidence = json.loads(evidence_file.read_text(encoding='utf-8'))
    if evidence.get('verified') is not True:
        raise FrozenPolicyRejected(f'{attempt_root}: learning not verified; the policy is not loadable')
    if evidence.get('algorithm') != algorithm:
        raise FrozenPolicyRejected(f'{attempt_root}: evidence is for {evidence.get("algorithm")}, not {algorithm}')
    files = [(attempt_root/_relative_path(p)).resolve() for p in evidence.get('checkpoint_files') or []]
    missing = [str(p) for p in files if not p.is_file()]
    if not files or missing:
        raise FrozenPolicyRejected(f'{algorithm}: checkpoint bundle incomplete; missing {missing or "all files"}')
    if any(attempt_root not in p.parents for p in files):
        raise FrozenPolicyRejected(f'{algorithm}: checkpoint files outside the attempt')
    from uc3m.adapters.algorithms.native_entrypoint import _bundle_hash, job_directory
    recorded = evidence.get('checkpoint_bundle_hash')
    if not recorded or _bundle_hash(files) != recorded:
        raise FrozenPolicyRejected(f'{algorithm}: checkpoint bundle hash differs from learning_evidence.json')
    native_arguments = list(evidence.get('native_arguments') or [])
    from uc3m.adapters.algorithms.evidence import checkpoint_bundle
    complete = checkpoint_bundle(native, algorithm, _training_agents(native_arguments))
    if {Path(p).resolve() for p in complete} != set(files):
        raise FrozenPolicyRejected(f'{algorithm}: checkpoint bundle incomplete or not the one the trainer selects')
    args = _trainer_arguments(algorithm, native_arguments)
    job = job_directory(native, native_arguments)
    common = _common()
    results = common.read_job_results_json(job)
    if not results or not results.get('hyperparameters'):
        raise FrozenPolicyRejected(f'{algorithm}: data/results.json with hyperparameters missing in {job}')
    if str(results.get('algorithm', algorithm)).upper() != algorithm:
        raise FrozenPolicyRejected(f'{algorithm}: results.json is for {results.get("algorithm")}')
    return NATIVE_POLICIES[algorithm](algorithm, attempt_root, evidence, files, args, results, job, common)
