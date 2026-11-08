"""The fresh campaign: strict configuration, treatment DAG and completion rules.

One use case for every stage (pilot, hpo, confirm, sensitivity). Weights come
from the single scenario catalog; sensitivity extremes are derived from it by
the design rule, never typed as a second table, and reach the reward through a
generated, hashed catalog. Hyperparameters map only to flags the native
launcher parses; native clamps are applied here so the effective value is the
one passed and recorded. Confirm and sensitivity run the configuration frozen
on validation (configuration_freezes.json), never native defaults. A treatment
is complete only from attempt evidence: a salvaged, interrupted or shortened
trajectory, runtime weights different from the treatment, or constraint terms
dominating the weighted axes never promote. Preparing the DAG neither trains
nor probes a GPU.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

from uc3m.application.configuration import load_scenario_catalog
from uc3m.application.training.integrity import campaign_inputs, verify_campaign_inputs
from uc3m.application.training.preflight import source_snapshot
from uc3m.domain.campaigns import ALGORITHMS, SCENARIOS, STAGES, ConfigurationFreeze, canonical_hash
from uc3m.domain.objectives import CANONICAL_AXES

CAMPAIGN_KEYS = {'schema_version', 'campaign_id', 'storage_alias', 'dataset_root', 'scenario_catalog', 'training_phases',
                 'algorithm_config', 'kpi_catalog', 'algorithms', 'scenarios', 'seeds', 'splits', 'stages',
                 'supervision', 'resource_authorization'}
STAGE_KEYS = {'episodes', 'episode_time_steps', 'seeds', 'scenarios', 'grid', 'dominance', 'secondary_to_residual'}
SUPERVISION_KEYS = {'max_constraint_dominance_ratio'}
ALGORITHM_KEYS = {'mapping', 'fixed_flags', 'fixed', 'native_clamps', 'declared_limitations', 'optimizer_owners',
                  'hyperparameter_grid_override',
                  'runtime_requirements', 'phase_buffer'}
OWNER_KEYS = {'per_agent', 'shared'}
CLAMP_KEYS = {'max', 'when_episode_time_steps_at_least'}
HYPERPARAMETERS = ('learning_rate', 'hidden_dimension', 'gamma')
PROTECTED_FLAGS = {'--schema-path', '--scenario', '--seed', '--episodes', '--episode-time-steps',
                   '--num-env-steps', '--output-dir', '--no-resume', '--resume'}
NUM_ENV_STEPS_BACKENDS = {'HAPPO', 'MATD3'}
# Reward axis keys of CityLearnV3MADRLRewardFunction, in canonical axis order.
REWARD_AXIS_KEYS = ('flex', 'carbon', 'cost')
FREEZES_FILE = 'configuration_freezes.json'
WEIGHT_TOLERANCE = 1e-9


def _strict(mapping, allowed, where):
    unknown = set(mapping) - set(allowed)
    if unknown:
        raise ValueError(f'{where}: unknown keys {sorted(unknown)}')


def load_algorithm_config(path: Path) -> Mapping[str, object]:
    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    _strict(payload, {'schema_version', 'runtime_flags', 'hyperparameter_grid', 'algorithms'}, str(path))
    if set(payload.get('runtime_flags') or []) - {'--cuda'}:
        raise ValueError('runtime_flags admits only --cuda')
    _strict(payload['hyperparameter_grid'], HYPERPARAMETERS, 'hyperparameter_grid')
    if set(payload['algorithms']) != set(ALGORITHMS):
        raise ValueError('algorithm config must cover exactly HAPPO, MASAC, MATD3 and MAAC')
    for name, row in payload['algorithms'].items():
        _strict(row, ALGORITHM_KEYS, name)
        if set(row['mapping']) != set(HYPERPARAMETERS):
            raise ValueError(f'{name}: every hyperparameter needs a native flag mapping')
        _strict(row.get('fixed') or {}, row.get('fixed_flags') or {}, f'{name}.fixed')
        if set(row.get('fixed_flags') or {}) - set(row.get('fixed') or {}):
            raise ValueError(f'{name}: a declared fixed flag has no value')
        override = row.get('hyperparameter_grid_override') or {}
        _strict(override, HYPERPARAMETERS, f'{name}.hyperparameter_grid_override')
        for hyper, values in override.items():
            if not values or set(values) - set(payload['hyperparameter_grid'][hyper]):
                raise ValueError(f'{name}.hyperparameter_grid_override.{hyper} must be a non-empty subset of the grid')
        clamps = row.get('native_clamps') or {}
        _strict(clamps, HYPERPARAMETERS, f'{name}.native_clamps')
        for hyper, clamp in clamps.items():
            _strict(clamp, CLAMP_KEYS, f'{name}.native_clamps.{hyper}')
            if set(clamp) != CLAMP_KEYS:
                raise ValueError(f'{name}.native_clamps.{hyper} needs {sorted(CLAMP_KEYS)}')
    return payload


def load_campaign_config(path: Path, project_root: Path) -> Mapping[str, object]:
    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    _strict(payload, CAMPAIGN_KEYS, str(path))
    if payload['schema_version'] != 1:
        raise ValueError('unsupported campaign schema_version')
    if set(payload['stages']) - set(STAGES):
        raise ValueError(f'stages must be members of {STAGES}')
    for name, stage in payload['stages'].items():
        _strict(stage, STAGE_KEYS, f'stages.{name}')
    if set(payload['algorithms']) - set(ALGORITHMS) or set(payload['scenarios']) - set(SCENARIOS):
        raise ValueError('unknown algorithm or scenario')
    supervision = payload.get('supervision')
    if not isinstance(supervision, Mapping) or set(supervision) != SUPERVISION_KEYS:
        raise ValueError(f'supervision must declare exactly {sorted(SUPERVISION_KEYS)}')
    ratio = float(supervision['max_constraint_dominance_ratio'])
    if not (math.isfinite(ratio) and ratio > 0):
        raise ValueError('max_constraint_dominance_ratio must be a positive finite number')
    from uc3m.application.training.phases import validate_phases
    payload['training_phases'] = validate_phases(payload.get('training_phases'), payload['algorithms'])
    root = Path(project_root)
    payload = dict(payload, _path=str(Path(path).resolve()), _root=str(root.resolve()))
    payload['_algorithm_config'] = load_algorithm_config(root/payload['algorithm_config'])
    return payload


def effective_hyperparameters(algorithm: str, hyperparameters: Optional[Mapping[str, float]],
                              algorithm_config: Mapping[str, object], episode_time_steps: int):
    """Apply the native launcher clamps; returns (effective values, applied clamps)."""
    if hyperparameters is None:
        return None, {}
    _strict(hyperparameters, HYPERPARAMETERS, f'{algorithm} hyperparameters')
    clamps = algorithm_config['algorithms'][algorithm].get('native_clamps') or {}
    effective, applied = dict(hyperparameters), {}
    for name, clamp in clamps.items():
        if int(episode_time_steps) >= int(clamp['when_episode_time_steps_at_least']) \
                and effective[name] > clamp['max']:
            applied[name] = {'requested': effective[name], 'effective': clamp['max']}
            effective[name] = clamp['max']
    return effective, applied


def resolve_native_arguments(algorithm: str, hyperparameters: Optional[Mapping[str, float]],
                             algorithm_config: Mapping[str, object], extra: Sequence[str] = ()) -> List[str]:
    protected = [a for a in extra if a.split('=', 1)[0] in PROTECTED_FLAGS]
    if protected:
        raise ValueError(f'treatment identity flags cannot be overridden: {protected}')
    row = algorithm_config['algorithms'][algorithm]
    arguments: List[str] = []
    if hyperparameters is not None:
        _strict(hyperparameters, HYPERPARAMETERS, f'{algorithm} hyperparameters')
        for name in HYPERPARAMETERS:
            for flag in row['mapping'][name]:
                arguments += [flag, str(hyperparameters[name])]
    for name, value in (row.get('fixed') or {}).items():
        arguments += [row['fixed_flags'][name], str(value)]
    return arguments + list(algorithm_config.get('runtime_flags') or []) + list(extra)


def sensitivity_weights(base: Tuple[float, float, float], dominance: float, ratio: Sequence[int]):
    """Dominant axis gets p; the rest keeps the base secondary:residual order, split 5:3."""
    order = sorted(range(3), key=lambda i: -base[i])
    secondary, residual = ratio
    rest = 1.0 - dominance
    weights = [0.0, 0.0, 0.0]
    weights[order[0]] = dominance
    weights[order[1]] = rest*secondary/(secondary + residual)
    weights[order[2]] = rest*residual/(secondary + residual)
    return tuple(weights)


@dataclass(frozen=True)
class Treatment:
    stage: str
    algorithm: str
    scenario: str
    seed: int
    candidate: Optional[str]
    weights: Tuple[float, float, float]
    episodes: int
    episode_time_steps: int
    hyperparameters: Optional[Mapping[str, float]]
    native_arguments: Tuple[str, ...]
    schema_path: str
    tariff_policy: str
    constraint_policy: str
    dataset_hash: str
    requires: Tuple[str, ...] = ()
    identity_arguments: Tuple[str, ...] = ()
    effective_hyperparameters: Optional[Mapping[str, float]] = None
    native_clamps: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    hyperparameter_source: str = 'native_default'

    @property
    def treatment_id(self) -> str:
        parts = [self.stage, self.algorithm.lower(), self.scenario.lower()]
        if self.candidate:
            parts.append(self.candidate)
        return '/'.join(parts + [f'seed_{self.seed}'])

    @property
    def env_steps(self) -> int:
        return self.episodes*self.episode_time_steps

    def as_dict(self):
        return {'treatment_id': self.treatment_id, 'stage': self.stage, 'algorithm': self.algorithm,
                'scenario': self.scenario, 'seed': self.seed, 'candidate': self.candidate,
                'weights': list(self.weights), 'episodes': self.episodes,
                'episode_time_steps': self.episode_time_steps,
                'hyperparameters': dict(self.hyperparameters) if self.hyperparameters else None,
                'effective_hyperparameters': (dict(self.effective_hyperparameters)
                                              if self.effective_hyperparameters else None),
                'native_clamps': {k: dict(v) for k, v in self.native_clamps.items()},
                'hyperparameter_source': self.hyperparameter_source,
                'identity_arguments': list(self.identity_arguments),
                'native_arguments': list(self.native_arguments), 'schema_path': self.schema_path,
                'tariff_policy': self.tariff_policy, 'constraint_policy': self.constraint_policy,
                'dataset_hash': self.dataset_hash, 'requires': list(self.requires)}


@dataclass
class CampaignDag:
    config: Mapping[str, object]
    treatments: List[Treatment] = field(default_factory=list)
    candidates: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    # stage -> algorithm -> kept candidate -> grid candidates it stands for.
    collapsed_candidates: Dict[str, Dict[str, Dict[str, List[str]]]] = field(default_factory=dict)
    # algorithm -> kept candidate -> effective hyperparameters (HPO stage).
    candidates_by_algorithm: Dict[str, Dict[str, Mapping[str, float]]] = field(default_factory=dict)

    def budget(self) -> Dict[str, Dict[str, int]]:
        out: Dict[str, Dict[str, int]] = {}
        for t in self.treatments:
            row = out.setdefault(t.stage, {'treatments': 0, 'episodes': 0, 'env_steps': 0})
            row['treatments'] += 1
            row['episodes'] += t.episodes
            row['env_steps'] += t.env_steps
        return out


def algorithm_candidates(algorithm, candidates, algorithm_config):
    """SPEC-015 D-M3-8: the grid candidates an algorithm searches (its override narrows the shared grid)."""
    override = algorithm_config['algorithms'][algorithm].get('hyperparameter_grid_override') or {}
    return {label: hyper for label, hyper in candidates.items()
            if all(hyper[name] in values for name, values in override.items())}


def single_candidate_arguments(algorithm, algorithm_config) -> List[str]:
    """SPEC-015 D-M3-8: the pilot has no grid values, but an algorithm that searches a single network width runs with
    it (MASAC's guard refuses an attempt without its candidate, and the pilot must measure the width it will train)."""
    row = algorithm_config['algorithms'][algorithm]
    values = (row.get('hyperparameter_grid_override') or {}).get('hidden_dimension') or ()
    if len(values) != 1:
        return []
    return [token for flag in row['mapping']['hidden_dimension'] for token in (flag, str(values[0]))]


def _distinct_candidates(algorithm, candidates, algorithm_config, episode_time_steps):
    """Merge grid candidates whose effective native configuration is identical."""
    kept: Dict[str, Tuple[Mapping[str, float], Mapping[str, float], dict]] = {}
    members: Dict[str, List[str]] = {}
    by_effective: Dict[Tuple, str] = {}
    for label, hyper in candidates.items():
        effective, clamps = effective_hyperparameters(algorithm, hyper, algorithm_config, episode_time_steps)
        key = tuple(sorted(effective.items()))
        if key in by_effective:
            members[by_effective[key]].append(label)
            continue
        by_effective[key] = label
        kept[label] = (hyper, effective, clamps)
        members[label] = [label]
    return kept, members


def build_dag(config: Mapping[str, object], project_root: Path) -> CampaignDag:
    root = Path(project_root)
    catalog = load_scenario_catalog(root/config['scenario_catalog'])
    acceptance = json.loads((root/config['dataset_root']/'dataset_acceptance.json').read_text(encoding='utf-8'))
    if not acceptance.get('dataset_verified'):
        raise ValueError('the campaign dataset is not verified')
    schema = f"{config['dataset_root']}/splits/train_2023/schema.json"
    algorithm_config = config['_algorithm_config']
    grid = algorithm_config['hyperparameter_grid']
    candidates = {f'c{i}': dict(zip(HYPERPARAMETERS, values)) for i, values in enumerate(
        itertools.product(*(grid[name] for name in HYPERPARAMETERS)), 1)}
    dag = CampaignDag(config, candidates=candidates)
    seeds = config['seeds']
    for stage_name, stage in config['stages'].items():
        stage_seeds = seeds[stage['seeds']] if isinstance(stage['seeds'], str) else stage['seeds']
        scenarios = stage.get('scenarios') or config['scenarios']
        steps = int(stage['episode_time_steps'])
        for algorithm in config['algorithms']:
            if stage_name == 'hpo':
                kept, members = _distinct_candidates(algorithm, algorithm_candidates(algorithm, candidates,
                                                                                    algorithm_config),
                                                     algorithm_config, steps)
                dag.collapsed_candidates.setdefault(stage_name, {})[algorithm] = members
                dag.candidates_by_algorithm[algorithm] = {label: dict(v[1]) for label, v in kept.items()}
                variants = [(label, hyper, None) for label, (hyper, _, _) in kept.items()]
            elif stage_name == 'sensitivity':
                variants = [(f'p{int(round(p*100)):03d}', None, p) for p in stage['dominance']]
            else:
                variants = [(None, None, None)]
            for scenario in scenarios:
                definition = catalog[scenario]
                base = tuple(float(definition.objective_policy.weights[axis]) for axis in CANONICAL_AXES)
                for label, hyper, dominance in variants:
                    weights = base if dominance is None else sensitivity_weights(
                        base, dominance, stage['secondary_to_residual'])
                    effective, clamps = effective_hyperparameters(algorithm, hyper, algorithm_config, steps)
                    for seed in stage_seeds:
                        requires = () if stage_name in {'pilot', 'hpo'} else ('configuration_freeze',)
                        if stage_name == 'sensitivity':
                            requires += ('derived_scenario_catalog',)
                        identity = ['--schema-path', schema, '--scenario', scenario, '--seed', str(seed),
                                    '--episodes', str(stage['episodes']),
                                    '--episode-time-steps', str(steps),
                                    '--artifact-profile', 'efficient']
                        if algorithm in NUM_ENV_STEPS_BACKENDS:
                            identity += ['--num-env-steps', str(stage['episodes']*steps)]
                        native = identity + resolve_native_arguments(algorithm, effective, algorithm_config)
                        single = single_candidate_arguments(algorithm, algorithm_config) if stage_name == 'pilot' else []
                        native += single
                        source = ('grid' if hyper is not None else
                                  'configuration_freeze' if 'configuration_freeze' in requires else
                                  'single_searched_candidate' if single else 'native_default')
                        dag.treatments.append(Treatment(
                            stage_name, algorithm, scenario, int(seed), label, weights, int(stage['episodes']),
                            steps, hyper, tuple(native), schema,
                            definition.tariff_policy.policy_id, definition.constraint_policy.policy_id,
                            acceptance['dataset_hash'], requires, tuple(identity), effective, clamps, source))
    return dag


def expected_optimizer_owners(algorithm: str, algorithm_config: Mapping[str, object], *,
                              n_agents: int) -> Tuple[str, ...]:
    """Optimizers an accepted attempt of ``algorithm`` must show updating (native.yaml)."""
    row = algorithm_config['algorithms'][algorithm]
    owners = row.get('optimizer_owners')
    if not isinstance(owners, Mapping) or set(owners) != OWNER_KEYS:
        raise ValueError(f'{algorithm}: optimizer_owners must declare exactly {sorted(OWNER_KEYS)}')
    if isinstance(n_agents, bool) or not isinstance(n_agents, int) or n_agents <= 0:
        raise ValueError('n_agents must be a positive integer')
    expanded = tuple(name.format(i=i) for i in range(n_agents) for name in owners['per_agent'])
    result = expanded + tuple(str(name) for name in owners['shared'])
    if not result or len(set(result)) != len(result):
        raise ValueError(f'{algorithm}: optimizer_owners expand to an empty or repeated set')
    return result


def schema_agent_count(project_root: Path, manifest: Mapping[str, object]) -> int:
    """Buildings included in the training split schema: one agent per building."""
    inputs = manifest['inputs']
    record = inputs.get('split:train_2023') or next(
        value for name, value in sorted(inputs.items()) if name.startswith('split:'))
    schema = json.loads((Path(project_root)/record['path']/'schema.json').read_text(encoding='utf-8'))
    return sum(1 for building in schema['buildings'].values() if building.get('include', True))


def attempt_completion(evidence: Optional[Mapping[str, object]], *, target_episodes: int,
                       episode_time_steps: int, expected_weights: Optional[Sequence[float]] = None,
                       max_constraint_dominance_ratio: Optional[float] = None,
                       attempt_root: Optional[Path] = None, campaign_id: Optional[str] = None,
                       attempt_id: Optional[str] = None, treatment_id: Optional[str] = None,
                       seed: Optional[int] = None, expected_owners: Optional[Sequence[str]] = None
                       ) -> Dict[str, object]:
    """training_complete only for a verified, unsalvaged attempt that walked the whole target.

    With ``expected_weights`` the axis weights the reward read at runtime must equal
    the treatment weights; with ``max_constraint_dominance_ratio`` the supervision
    summary must show the EV/BESS terms do not dominate the weighted axes. With the
    attempt binding (root, campaign, attempt, treatment, seed and the declared
    optimizer owners) the single evidence rule
    ``fresh_acceptance.attempt_evidence_reasons`` decides identity, real updates,
    changed parameters and the checkpoint bundle; run_stage always passes it.
    Without it only the metadata checks below run (never used to promote).
    """
    if not evidence:
        return {'training_complete': False, 'reasons': ['no_evidence']}
    reasons = []
    if evidence.get('salvage'):
        reasons.append('completed_with_salvage')
    if evidence.get('exit_code') != 0 or not evidence.get('verified'):
        reasons.append('interrupted_or_failed')
    if int(evidence.get('env_steps') or 0) < target_episodes*episode_time_steps:
        reasons.append('trajectory_shorter_than_target')
    completed = evidence.get('completed_episodes')
    if type(completed) is not int or completed < target_episodes:
        reasons.append('completed_episodes_shorter_than_target')
    if expected_owners is not None:
        from uc3m.application.training.fresh_acceptance import attempt_evidence_reasons
        reasons.extend(attempt_evidence_reasons(
            evidence, Path(attempt_root), campaign_id=campaign_id, attempt_id=attempt_id,
            treatment_id=treatment_id, seed=seed, expected_owners=expected_owners))
    else:
        if not evidence.get('successful_optimizer_updates_by_owner'):
            reasons.append('no_observed_updates')
        if not evidence.get('checkpoint_files'):
            reasons.append('no_checkpoint')
    if expected_weights is not None:
        runtime = evidence.get('effective_axis_weights')
        if not isinstance(runtime, Mapping) or set(runtime) != set(REWARD_AXIS_KEYS):
            reasons.append('effective_weights_unrecorded')
        elif any(abs(float(runtime[key]) - float(value)) > WEIGHT_TOLERANCE
                 for key, value in zip(REWARD_AXIS_KEYS, expected_weights)):
            reasons.append('effective_weights_mismatch')
    if max_constraint_dominance_ratio is not None:
        supervision = evidence.get('supervision')
        ratio = supervision.get('constraint_dominance_ratio') if isinstance(supervision, Mapping) else None
        if ratio is None or not math.isfinite(float(ratio)) or float(ratio) < 0:
            reasons.append('supervision_unrecorded')
        elif float(ratio) > float(max_constraint_dominance_ratio):
            reasons.append('constraint_terms_dominate_weighted_axes')
    return {'training_complete': not reasons, 'reasons': reasons}


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def catalog_sha256(catalog_path: Path) -> str:
    """Hash of a scenario catalog together with the objective policies file it references."""
    catalog_path = Path(catalog_path)
    payload = yaml.safe_load(catalog_path.read_text(encoding='utf-8'))
    policies = catalog_path.parent/payload['objective_policies_file']
    digest = hashlib.sha256()
    for path in (catalog_path, policies):
        digest.update(path.name.encode('utf-8') + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def prepare_campaign(config_path: Path, project_root: Path, *, artifact_root: Optional[Path] = None):
    """Write the campaign and stage manifests; nothing is trained and no GPU is probed."""
    root = Path(project_root)
    config = load_campaign_config(config_path, root)
    dag = build_dag(config, root)
    artifact_root = Path(artifact_root or root/'outputs/campaigns'/config['storage_alias'])
    # Restoring from an empty Drive folder leaves an empty root: nothing was prepared there yet.
    if artifact_root.exists() and any(artifact_root.iterdir()):
        raise FileExistsError(f'{artifact_root} already exists; a prepared campaign is never overwritten')
    (artifact_root/'stages').mkdir(parents=True)
    stages = {}
    for stage in config['stages']:
        rows = [t.as_dict() for t in dag.treatments if t.stage == stage]
        path = artifact_root/'stages'/f'{stage}.json'
        path.write_text(json.dumps({'stage': stage, 'treatments': rows}, indent=2), encoding='utf-8')
        stages[stage] = {'path': f'stages/{stage}.json', 'sha256': _sha256(path), 'treatments': len(rows)}
    normalizer = root/config['dataset_root']/'normalizer.json'
    from uc3m.application.evaluation.endpoint_applicability import classify_endpoint_applicability
    applicability = classify_endpoint_applicability(root/config['dataset_root'], root,
        tariff_policy=load_scenario_catalog(root/config['scenario_catalog'])['E3'].tariff_policy)
    identity = {'config_sha256': _sha256(config['_path']),
                'algorithm_config_sha256': _sha256(root/config['algorithm_config']),
                'scenario_catalog_sha256': _sha256(root/config['scenario_catalog']),
                'dataset_hash': dag.treatments[0].dataset_hash,
                'normalizer_sha256': _sha256(normalizer) if normalizer.is_file() else None,
                'source_sha256': source_snapshot(root, scope='fresh')}
    inputs = campaign_inputs(config, root)
    from uc3m.application.training.integrity import _file_sha256
    for index, price in enumerate(applicability['price_files']):
        path = root/price['path']
        if _file_sha256(path) != price['sha256']:
            raise ValueError('price changed while applicability was being frozen')
        inputs[f'endpoint_price:{index}'] = {'kind': 'file', 'path': price['path'], 'sha256': price['sha256']}
    identity['input_manifest_sha256'] = canonical_hash(inputs)
    if inputs['dataset']['sha256'] != identity['dataset_hash']:
        raise ValueError('the dataset tree does not match the hash its acceptance recorded')
    algorithms = config['_algorithm_config']['algorithms']
    identity['algorithm_contract_sha256'] = canonical_hash(config['_algorithm_config'])
    identity['endpoint_applicability_sha256'] = canonical_hash(applicability)
    identity['supervision_sha256'] = canonical_hash(config['supervision'])
    from uc3m.application.training.gate_report import git_head, test_source_digest
    n_agents = schema_agent_count(root, {'inputs': inputs})
    owners = {name: list(expected_optimizer_owners(name, config['_algorithm_config'], n_agents=n_agents))
              for name in config['algorithms']}
    layout = yaml.safe_load((root/'governance/repository_layout.yaml').read_text(encoding='utf-8'))
    input_policy = {'retired_roots': list((layout.get('retired_historical_roots') or {}).values())
                    + list(layout.get('forbidden_input_roots') or [])}
    identity.update(optimizer_owners_sha256=canonical_hash(owners), source_git_head=git_head(root),
                    test_source_sha256=test_source_digest(root), stage_plan_sha256=canonical_hash(stages),
                    input_policy_sha256=canonical_hash(input_policy))
    manifest = {'schema_version': 1, 'campaign_id': config['campaign_id'], 'storage_alias': config['storage_alias'],
                'status': 'planned', 'spec_hash': canonical_hash(identity), 'identity': identity,
                'inputs': inputs, 'optimizer_owners': owners, 'input_policy': input_policy,
                'algorithm_contract': config['_algorithm_config'],
                'endpoint_applicability': applicability,
                'scenario_catalog': config['scenario_catalog'], 'algorithm_config': config['algorithm_config'],
                'supervision': dict(config['supervision']),
                'training_phases': [list(phase) for phase in config['training_phases']],
                'budget': dag.budget(), 'hpo_candidates': dag.candidates,
                'hpo_candidates_by_algorithm': dag.candidates_by_algorithm,
                'collapsed_candidates': dag.collapsed_candidates,
                'declared_limitations': {name: list(row.get('declared_limitations') or [])
                                         for name, row in algorithms.items()},
                'stages': stages,
                'launch_authorized': {s: True for s in config['resource_authorization'].get('authorized_stages', [])},
                'resume': 'disabled; every attempt starts at episode zero',
                'prepared_at': datetime.now(timezone.utc).isoformat()}
    (artifact_root/'campaign_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Ownership claim checked by fresh_policy before any attempt directory is created.
    (artifact_root/'campaign.json').write_text(json.dumps({
        'schema_version': 1, 'campaign_id': config['campaign_id'], 'storage_alias': config['storage_alias'],
        'spec_hash': manifest['spec_hash'], 'status': 'planned', 'scientific_acceptance': False}, indent=2),
        encoding='utf-8')
    return manifest


# --- Configuration freeze ---------------------------------------------------------------------------

def freeze_configuration(campaign_id: str, algorithm: str, hyperparameters: Mapping[str, float],
                         validation_manifest_hashes: Sequence[str], *, selection_rule: str,
                         candidates: Sequence[str] = (), reason: str = '') -> ConfigurationFreeze:
    hyper = dict(hyperparameters)
    _strict(hyper, HYPERPARAMETERS, f'{algorithm} frozen hyperparameters')
    if set(hyper) != set(HYPERPARAMETERS):
        raise ValueError(f'{algorithm}: a freeze must set {HYPERPARAMETERS}')
    return ConfigurationFreeze(campaign_id, algorithm, ConfigurationFreeze.config_hash_for(algorithm, hyper),
                               tuple(validation_manifest_hashes), selection_rule,
                               datetime.now(timezone.utc).isoformat(), tuple(candidates), reason, hyper)


def _is_candidate(manifest, freeze: ConfigurationFreeze) -> bool:
    candidates = (manifest.get('hpo_candidates_by_algorithm') or {}).get(freeze.algorithm) or {}
    return dict(freeze.hyperparameters) in [dict(v) for v in candidates.values()]


def _freeze_publication_rows(manifest, freezes: Sequence[ConfigurationFreeze]) -> Dict[str, dict]:
    """Validate selection inputs before publishing either member of the pair."""
    by_algorithm = {}
    for freeze in freezes:
        # Recheck the domain contract rather than trusting an arbitrary row-like object.
        freeze = ConfigurationFreeze.from_dict(freeze.as_dict())
        if freeze.campaign_id != manifest['campaign_id']:
            raise ValueError(f'{freeze.algorithm}: freeze belongs to another campaign')
        if freeze.algorithm in by_algorithm:
            raise ValueError(f'{freeze.algorithm}: one freeze per algorithm')
        if set(freeze.hyperparameters) != set(HYPERPARAMETERS):
            raise ValueError(f'{freeze.algorithm}: frozen hyperparameters must set {HYPERPARAMETERS}')
        if not _is_candidate(manifest, freeze):
            raise ValueError(f'{freeze.algorithm}: frozen hyperparameters are not an HPO candidate of this campaign')
        labels = (manifest.get('hpo_candidates_by_algorithm') or {}).get(freeze.algorithm) or {}
        if len(set(freeze.candidates)) != len(freeze.candidates) or set(freeze.candidates) - set(labels):
            raise ValueError(f'{freeze.algorithm}: invalid HPO candidate labels')
        if not isinstance(freeze.selection_rule, str) or not freeze.selection_rule.strip():
            raise ValueError(f'{freeze.algorithm}: a freeze needs a nonempty selection rule')
        if not isinstance(freeze.frozen_at, str) or not freeze.frozen_at.strip():
            raise ValueError(f'{freeze.algorithm}: a freeze needs its original frozen_at')
        by_algorithm[freeze.algorithm] = {**freeze.as_dict(), 'freeze_hash': freeze.freeze_hash()}
    if not by_algorithm:
        raise ValueError('configuration freeze publication requires a nonempty selection')
    return by_algorithm


def _freeze_selection(rows):
    # frozen_at contributes to freeze_hash. A retry may have a fresh timestamp,
    # but it cannot change any selection/evidence or replace the original bytes.
    return {algorithm: {key: value for key, value in row.items()
                        if key not in ('frozen_at', 'freeze_hash')}
            for algorithm, row in rows.items()}


def write_configuration_freezes(manifest_path: Path, freezes: Sequence[ConfigurationFreeze]) -> Dict[str, object]:
    """Atomically publish an immutable freeze and recover its manifest link on retry.

    The pair is serialized by an OS-owned lock. A crash after freeze publication
    leaves a verified orphan; only the identical selection may bind that orphan.
    """
    from uc3m.application.dataset.provenance import contained_path
    from uc3m.application.training.lock import run_lock
    from uc3m.application.training.persistence import write_json_atomic

    manifest_path = Path(manifest_path)
    manifest_path = contained_path(manifest_path.parent, manifest_path.name)
    target = contained_path(manifest_path.parent, FREEZES_FILE)
    lock_path = contained_path(manifest_path.parent, '.configuration_freezes.lock')
    with run_lock(lock_path):
        # Read after acquiring the lock so no stale manifest replaces a peer's update.
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        requested = _freeze_publication_rows(manifest, freezes)
        registered = 'configuration_freezes' in manifest
        if registered and not target.is_file():
            raise PermissionError('registered configuration freeze is missing; not recreated')
        if target.exists():
            try:
                payload = json.loads(target.read_text(encoding='utf-8'))
                if (set(payload) != {'schema_version', 'campaign_id', 'freezes'}
                        or payload['schema_version'] != 1 or payload['campaign_id'] != manifest['campaign_id']
                        or not isinstance(payload['freezes'], dict)):
                    raise ValueError('invalid freeze publication identity')
                stored = _freeze_publication_rows(manifest, [ConfigurationFreeze.from_dict(row)
                                                            for row in payload['freezes'].values()])
                if stored != payload['freezes']:
                    raise ValueError('stored content or freeze_hash does not verify')
            except (OSError, KeyError, TypeError, ValueError, AttributeError) as exc:
                raise PermissionError(f'configuration freeze is invalid; preserved: {exc}') from exc
            if _freeze_selection(stored) != _freeze_selection(requested):
                raise FileExistsError('configuration freeze already holds different selection or evidence')
        else:
            payload = {'schema_version': 1, 'campaign_id': manifest['campaign_id'], 'freezes': requested}
            write_json_atomic(target, payload)
            stored = requested
        record = {'path': FREEZES_FILE, 'sha256': _sha256(target),
                  'freeze_hashes': {name: row['freeze_hash'] for name, row in stored.items()}}
        if registered:
            if manifest['configuration_freezes'] != record:
                raise PermissionError('registered configuration freeze content or digest changed; preserved')
            return record
        manifest['configuration_freezes'] = record
        write_json_atomic(manifest_path, manifest)
        return record


def load_configuration_freezes(artifacts: Path, manifest: Mapping[str, object]) -> Dict[str, ConfigurationFreeze]:
    """Verified freezes by algorithm; any missing, tampered or foreign freeze is refused."""
    record = manifest.get('configuration_freezes')
    if not isinstance(record, Mapping) or not {'path', 'sha256', 'freeze_hashes'} <= set(record):
        raise PermissionError('no configuration freeze recorded in the campaign manifest')
    from uc3m.application.dataset.provenance import contained_path
    path = contained_path(Path(artifacts), record['path'])
    if not path.is_file() or _sha256(path) != record['sha256']:
        raise PermissionError('configuration freeze file missing or modified after it was recorded')
    payload = json.loads(path.read_text(encoding='utf-8'))
    out = {}
    for algorithm, row in (payload.get('freezes') or {}).items():
        try:
            freeze = ConfigurationFreeze.from_dict(row)
        except (KeyError, TypeError, ValueError) as invalid:
            raise PermissionError(f'{algorithm}: invalid configuration freeze ({invalid})') from invalid
        if (freeze.algorithm != algorithm or freeze.campaign_id != manifest['campaign_id']
                or freeze.freeze_hash() != row.get('freeze_hash')
                or record['freeze_hashes'].get(algorithm) != row.get('freeze_hash')
                or not _is_candidate(manifest, freeze)):
            raise PermissionError(f'{algorithm}: configuration freeze does not verify')
        out[algorithm] = freeze
    return out


# --- Derived scenario catalog (sensitivity) ---------------------------------------------------------

def write_derived_scenario_catalog(base_catalog: Path, scenario: str, weights: Sequence[float], label: str,
                                   out_dir: Path) -> Dict[str, object]:
    """Generate a one-scenario catalog with the derived weights; same tariff and constraints."""
    base_catalog = Path(base_catalog)
    base = yaml.safe_load(base_catalog.read_text(encoding='utf-8'))
    policy_id = f'{scenario}_{label}'
    policies = {'schema_version': 1, 'axis_order': [axis.value for axis in CANONICAL_AXES],
                'policies': {policy_id: {'method': 'compensatory_hierarchical_weighted_sum',
                                         'weights': {axis.value: float(w) for axis, w in zip(CANONICAL_AXES, weights)}}}}
    catalog = {'schema_version': 1, 'objective_policies_file': 'objective_policies.yaml',
               'tariff_policies': base['tariff_policies'], 'constraint_policies': base['constraint_policies'],
               'scenarios': {scenario: dict(base['scenarios'][scenario], objective_policy=policy_id,
                                            study_kind='weights_only')}}
    files = {'objective_policies.yaml': yaml.safe_dump(policies, sort_keys=False),
             'scenarios.yaml': yaml.safe_dump(catalog, sort_keys=False)}
    out_dir = Path(out_dir)
    if out_dir.exists():
        for name, text in files.items():
            if not (out_dir/name).is_file() or (out_dir/name).read_text(encoding='utf-8') != text:
                raise FileExistsError(f'{out_dir} holds a different derived catalog')
    else:
        out_dir.mkdir(parents=True)
        for name, text in files.items():
            (out_dir/name).write_text(text, encoding='utf-8')
    loaded = load_scenario_catalog(out_dir/'scenarios.yaml')[scenario].objective_policy
    if any(abs(loaded.weights[axis] - float(w)) > 1e-12 for axis, w in zip(CANONICAL_AXES, weights)):
        raise ValueError(f'derived catalog {out_dir} does not reproduce the treatment weights')
    digest = catalog_sha256(out_dir/'scenarios.yaml')
    (out_dir/'derivation.json').write_text(json.dumps({
        'scenario': scenario, 'label': label, 'objective_policy_id': policy_id, 'weights': list(weights),
        'axis_order': [axis.value for axis in CANONICAL_AXES], 'base_catalog_sha256': catalog_sha256(base_catalog),
        'catalog_sha256': digest, 'rule': 'dominance p, rest split secondary:residual 5:3'}, indent=2),
        encoding='utf-8')
    return {'path': out_dir/'scenarios.yaml', 'sha256': digest}


# --- Stage execution -------------------------------------------------------------------------------

def _treatment_key(treatment: Mapping[str, object], manifest: Mapping[str, object]):
    from uc3m.domain.campaigns import treatment_key_from_resolved
    return treatment_key_from_resolved(treatment, manifest)


def _materialize(row, manifest, artifacts: Path, root: Path, algorithm_config, freezes, stage):
    """Resolve what an attempt really runs: frozen hyperparameters and the catalog the reward reads."""
    row = dict(row)
    if 'configuration_freeze' in row['requires']:
        freeze = freezes.get(row['algorithm'])
        if freeze is None:
            raise PermissionError(f"{row['treatment_id']}: no configuration freeze for {row['algorithm']}")
        hyper = dict(freeze.hyperparameters)
        effective, clamps = effective_hyperparameters(row['algorithm'], hyper, algorithm_config,
                                                      row['episode_time_steps'])
        row.update(hyperparameters=hyper, effective_hyperparameters=effective, native_clamps=clamps,
                   hyperparameter_source='configuration_freeze', configuration_freeze_hash=freeze.freeze_hash(),
                   native_arguments=list(row['identity_arguments']) + resolve_native_arguments(
                       row['algorithm'], effective, algorithm_config))
    if 'derived_scenario_catalog' in row['requires']:
        out_dir = artifacts/'stages'/f'{stage}_catalogs'/f"{row['scenario']}_{row['candidate']}"
        try:
            derived = write_derived_scenario_catalog(root/manifest['scenario_catalog'], row['scenario'],
                                                     row['weights'], row['candidate'], out_dir)
        except (ValueError, FileExistsError) as invalid:
            raise PermissionError(f"{row['treatment_id']}: derived scenario catalog refused ({invalid})") from invalid
        row.update(scenario_catalog=Path(derived['path']).relative_to(artifacts).as_posix(),
                   scenario_catalog_path=str(derived['path']), scenario_catalog_sha256=derived['sha256'])
    else:
        base = root/manifest['scenario_catalog']
        row.update(scenario_catalog=manifest['scenario_catalog'], scenario_catalog_path=str(base),
                   scenario_catalog_sha256=catalog_sha256(base))
    return row


def _persisted_evidence(attempt_root: Path, returned) -> Optional[Mapping[str, object]]:
    """learning_evidence.json written in the attempt, only if it equals what the learner returned."""
    path = Path(attempt_root)/'learning_evidence.json'
    if returned is None or not path.is_file() or path.is_symlink():
        return None
    try:
        persisted = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if persisted != json.loads(json.dumps(returned, default=str)):
        return None
    return persisted


def _prior_attempts(roots, key, artifacts: Path) -> List[Dict[str, object]]:
    """Earlier attempts of this exact treatment identity, as recorded in each attempt folder.

    An attempt without completion.json was interrupted; an attempt whose attempt.json names
    another treatment identity is never counted as complete.
    """
    from uc3m.application.training.fresh_policy import _existing_attempts, attempt_base
    base = attempt_base(roots, key)
    records = []
    for name in _existing_attempts(base):
        root = base/name
        try:
            record = json.loads((root/'attempt.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        completion_path = root/'completion.json'
        decision = (json.loads(completion_path.read_text(encoding='utf-8')) if completion_path.is_file()
                    else {'training_complete': False, 'reasons': ['interrupted_without_completion']})
        if record.get('treatment') != key.as_dict():
            decision = {'training_complete': False, 'reasons': ['attempt_of_another_identity']}
        records.append({'attempt_id': record.get('attempt_id', name), 'path': root.relative_to(artifacts).as_posix(),
                        'training_complete': decision.get('training_complete') is True,
                        'reasons': list(decision.get('reasons') or [])})
    return records


# The registry (treatments.json) and attempt numbering are guarded by a non-blocking file
# lock meant for separate processes; threads of one stage serialize on this lock instead.
_ATTEMPT_LOCK = threading.Lock()


def _apply_frozen_buffer(row: Mapping[str, object], buffer: Mapping[str, object]) -> Dict[str, object]:
    """Replace the value of the buffer flag the native arguments already carry (never append it twice)."""
    row = dict(row)
    arguments = list(row['native_arguments'])
    flag = str(buffer['flag'])
    if arguments.count(flag) != 1:
        raise ValueError(f"{row['treatment_id']}: {flag} must appear exactly once to apply the phase buffer")
    arguments[arguments.index(flag) + 1] = str(int(buffer['effective']))
    row.update(native_arguments=arguments, phase_buffer=dict(buffer), phase_buffer_sha256=canonical_hash(buffer))
    return row


def run_stage(manifest_path: Path, stage: str, learner, project_root: Path, *, authorized: bool,
              max_attempts: int = 1, workers=1, execution: Optional[Mapping[str, Mapping]] = None
              ) -> Dict[str, object]:
    """Run every treatment of a stage through the injected learner, each attempt from zero.

    learner(treatment, attempt_root) -> evidence mapping (see attempt_completion).
    A failed attempt is kept as evidence; a retry is a new, empty attempt. Treatments run
    by the phases recorded in the manifest (phases.run_phases): in parallel inside a phase
    up to ``workers`` (one int, or one limit per phase from phases.worker_limit), and a
    phase starts only when every treatment of the previous one is training_complete.

    Buffers sized to the parallel share are frozen per stage in stages/<stage>_budget.json
    (written by the CLI on the first launch): they replace the native buffer value and are
    part of the treatment identity. ``execution`` (per algorithm: torch threads, CUDA memory
    fraction, worker RAM/VRAM share) is recorded with the attempt but is not identity, so a
    relaunch on other hardware still reuses the verified attempts.
    """
    from uc3m.application.training.phases import group_by_phase, run_phases, validate_phases
    from uc3m.application.training import fresh_policy
    from uc3m.application.training.fresh_policy import CampaignRoots, create_attempt
    manifest_path = Path(manifest_path)
    root = Path(project_root)
    integrity = verify_campaign_inputs(manifest_path, root)
    if not integrity.accepted:
        raise PermissionError(f"campaign inputs refused: {', '.join(integrity.reasons)}")
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    artifacts = manifest_path.parent
    from uc3m.application.training.attempt_trust import load_trust_contract
    trust = load_trust_contract(artifacts, manifest['campaign_id'])
    if trust.reasons:
        raise PermissionError('campaign contract refused: ' + ', '.join(trust.reasons))
    stage_path = artifacts/manifest['stages'][stage]['path']
    if _sha256(stage_path) != manifest['stages'][stage]['sha256']:
        raise PermissionError(f'{stage} manifest was modified after preparation')
    rows = json.loads(stage_path.read_text(encoding='utf-8'))['treatments']
    freezes = {}
    if any('configuration_freeze' in row['requires'] for row in rows):
        try:
            freezes = load_configuration_freezes(artifacts, manifest)
        except PermissionError as refused:
            raise PermissionError(f'{stage} needs the configuration freeze selected on validation: {refused}')
    if not authorized:
        raise PermissionError(f'{stage} is not authorized for execution on the available resources')
    supervision = manifest.get('supervision')
    if not isinstance(supervision, Mapping) or 'max_constraint_dominance_ratio' not in supervision:
        raise PermissionError('campaign manifest declares no supervision criterion')
    algorithm_config_path = root/manifest['algorithm_config']
    if _sha256(algorithm_config_path) != manifest['identity']['algorithm_config_sha256']:
        raise PermissionError('algorithm config changed after the campaign was prepared')
    algorithm_config = load_algorithm_config(algorithm_config_path)
    rows = [_materialize(row, manifest, artifacts, root, algorithm_config, freezes, stage) for row in rows]
    budget_path = artifacts/'stages'/f'{stage}_budget.json'
    budget_sha256 = None
    if budget_path.is_file():
        budget_sha256 = _sha256(budget_path)
        buffers = json.loads(budget_path.read_text(encoding='utf-8')).get('buffers') or {}
        rows = [_apply_frozen_buffer(row, buffers[row['algorithm']]) if row['algorithm'] in buffers else row
                for row in rows]
    if execution:
        rows = [dict(row, execution=dict(execution.get(row['algorithm']) or {})) for row in rows]
    n_agents = schema_agent_count(root, manifest)
    roots = CampaignRoots(manifest['campaign_id'], root/'data/campaigns'/manifest['storage_alias'],
                          artifacts, manifest['spec_hash'], manifest['storage_alias'])
    from uc3m.application.training.fresh_acceptance import treatment_trust_reasons
    declared = manifest.get('training_phases') or ()
    # The campaign phases cover all its algorithms; a stage (e.g. sensitivity) may hold only some.
    phases = validate_phases(declared, [a for phase in declared for a in phase])

    def run_treatment(row):
        key = _treatment_key(row, manifest)
        decision = {'training_complete': False, 'reasons': ['not_attempted']}
        # A relaunched stage (e.g. a new Colab session after a disconnect) keeps every earlier
        # attempt. A treatment whose complete attempt still passes the single trust rule is
        # reused as is; any other treatment gets a new attempt from episode zero, never a resume.
        with _ATTEMPT_LOCK:
            attempts = _prior_attempts(roots, key, artifacts)
        reused = (any(a['training_complete'] for a in attempts)
                  and not treatment_trust_reasons(artifacts, manifest['campaign_id'],
                                                  {'treatment_id': row['treatment_id'], 'attempts': attempts}))
        if reused:
            decision = {'training_complete': True, 'reasons': []}
        for _ in range(0 if reused else max_attempts):
            with _ATTEMPT_LOCK:
                identity, attempt_root = create_attempt(roots, key)
            if row.get('phase_buffer') is not None:
                from uc3m.application.training.budget_evidence import persist_buffer_proof
                persist_buffer_proof(attempt_root, row, manifest, budget_path)
            returned = learner(row, attempt_root)
            # Only the evidence the child process persisted inside the attempt counts; a value
            # returned in memory proves nothing and is never written here.
            persisted = _persisted_evidence(attempt_root, returned)
            if persisted is None:
                decision = {'training_complete': False, 'reasons': ['evidence_not_persisted']}
            else:
                decision = attempt_completion(
                    persisted, target_episodes=row['episodes'], episode_time_steps=row['episode_time_steps'],
                    expected_weights=row['weights'],
                    max_constraint_dominance_ratio=float(supervision['max_constraint_dominance_ratio']),
                    attempt_root=attempt_root, campaign_id=manifest['campaign_id'], attempt_id=identity.attempt_id,
                    treatment_id=key.treatment_id, seed=key.seed,
                    expected_owners=expected_optimizer_owners(row['algorithm'], algorithm_config, n_agents=n_agents))
            (attempt_root/'resolved_treatment.json').write_text(json.dumps(row, indent=2), encoding='utf-8')
            # completion.json is published last and atomically: its presence marks a finished
            # attempt for the Drive sync, which must never copy a half-written decision.
            fresh_policy.write_json_atomic(attempt_root/'completion.json', decision)
            attempts.append({'attempt_id': identity.attempt_id, 'path': attempt_root.relative_to(artifacts).as_posix(),
                             **decision})
            if decision['training_complete']:
                break
        return {'treatment_id': row['treatment_id'], 'attempts': attempts,
                'configuration_freeze_hash': row.get('configuration_freeze_hash'),
                'scenario_catalog_sha256': row['scenario_catalog_sha256'],
                'reused_verified_attempt': reused,
                'training_complete': decision['training_complete']}

    groups = group_by_phase(rows, phases)
    limits = [int(workers)]*len(groups) if isinstance(workers, int) else [int(w) for w in workers]
    if len(limits) != len(groups):
        raise ValueError('one worker limit per training phase is required')
    # Phases without treatments in this stage are skipped, not run with a zero limit.
    kept = [(group, limit) for group, limit in zip(groups, limits) if group['treatments']]
    report = run_phases([group for group, _ in kept], run_treatment, workers=[limit for _, limit in kept])
    ran = {entry['treatment_id']: entry for phase in report['phases'] for entry in phase['results']}
    outcome = []
    for row in rows:  # stage order; treatments of phases that never started have no attempt
        entry = ran.get(row['treatment_id'])
        if entry is None or 'attempts' not in entry:
            with _ATTEMPT_LOCK:
                prior = _prior_attempts(roots, _treatment_key(row, manifest), artifacts)
            entry = {'treatment_id': row['treatment_id'], 'attempts': prior,
                     'configuration_freeze_hash': row.get('configuration_freeze_hash'),
                     'scenario_catalog_sha256': row['scenario_catalog_sha256'], 'reused_verified_attempt': False,
                     'training_complete': False,
                     **({'error': ran[row['treatment_id']]['error']} if row['treatment_id'] in ran else {})}
        outcome.append(entry)
    completed = sum(1 for t in outcome if t['training_complete'])
    failed = sum(1 for t in outcome for a in t['attempts'] if not a['training_complete'])
    status = ('insufficient_resources' if report['status'] == 'insufficient_resources'
              else 'training_complete' if completed == len(rows) else 'incomplete')
    result = {'campaign_id': manifest['campaign_id'], 'stage': stage, 'planned_treatments': len(rows),
              'completed_treatments': completed, 'failed_attempts': failed, 'treatments': outcome,
              'phases': [{'algorithms': phase['algorithms'], 'workers': phase['workers'], 'failed': phase['failed']}
                         for phase in report['phases']],
              'stopped_at_phase': report['stopped_at_phase'], 'status': status, 'budget_sha256': budget_sha256,
              'finished_at': datetime.now(timezone.utc).isoformat()}
    # Buffers are frozen per stage; parallelism and execution parameters are refit per runtime,
    # so every launch is kept in the result to show how they varied between sessions.
    result_path = artifacts/'stages'/f'{stage}_result.json'
    previous = json.loads(result_path.read_text(encoding='utf-8')) if result_path.is_file() else {}
    result['execution_may_vary_between_launches'] = True
    result['launch_history'] = list(previous.get('launch_history') or []) + [{
        'finished_at': result['finished_at'], 'workers': [phase['workers'] for phase in result['phases']],
        'execution': {name: dict(values) for name, values in (execution or {}).items()},
        'budget_sha256': budget_sha256, 'status': status}]
    fresh_policy.write_json_atomic(result_path, result)
    return result
