"""The only training entrypoint: the fresh campaign CLI (composition root).

    python -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage prepare
    python -m uc3m.application.training.cli --config ... --stage pilot --execute

Without --execute nothing is trained: the DAG and manifests are prepared or
reported. --execute runs a stage through the native entrypoint only when the
campaign config authorizes that stage on the available resources. Every attempt
starts from zero; there is no resume flag.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from uc3m.application.training import fresh_campaign as fc
from uc3m.application.training.integrity import verify_campaign_inputs

STAGES = ('prepare', 'pilot', 'hpo', 'confirm', 'sensitivity')


def _artifact_root(project_root: Path, config) -> Path:
    return project_root/'outputs/campaigns'/config['storage_alias']


def native_learner(project_root: Path, campaign_id: str, dataset_root: Path):
    """Adapter wiring: one child process of the native entrypoint per attempt.

    The reward reads its axis weights from UC3M_SCENARIO_CATALOG, which points to
    the catalog run_stage resolved for this treatment (the single catalog, or the
    generated, hashed catalog of a sensitivity extreme). A treatment without a
    resolved catalog is refused instead of falling back to a default table.
    """
    def learn(treatment, attempt_root):
        scenario_catalog = treatment.get('scenario_catalog_path')
        if not scenario_catalog or not Path(scenario_catalog).is_file():
            raise PermissionError(f"{treatment['treatment_id']}: no resolved scenario catalog")
        command = [sys.executable, '-B', '-m', 'uc3m.adapters.algorithms.native_entrypoint',
                   '--algorithm', treatment['algorithm'], '--campaign-id', campaign_id,
                   '--attempt-id', Path(attempt_root).name, '--attempt-root', str(attempt_root),
                   '--normalizer', str(dataset_root/'normalizer.json'), '--'] + list(treatment['native_arguments'])
        env = dict(os.environ, UC3M_SCENARIO_CATALOG=str(scenario_catalog),
                   PYTHONPATH=os.pathsep.join([str(project_root), str(project_root/'CityLearn'),
                                               os.environ.get('PYTHONPATH', '')]))
        # Execution share of this parallel worker (not identity): the native entrypoint checks
        # resources against it, limits torch threads and the CUDA memory fraction.
        for name, value in _execution_env(treatment.get('execution') or {}).items():
            env[name] = value
        with (Path(attempt_root)/'child.log').open('w', encoding='utf-8') as log:
            subprocess.run(command, cwd=project_root, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        evidence = Path(attempt_root)/'learning_evidence.json'
        return json.loads(evidence.read_text(encoding='utf-8')) if evidence.is_file() else None
    return learn


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--stage', choices=STAGES, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    config = fc.load_campaign_config(args.config, root)
    artifacts = _artifact_root(root, config)
    manifest_path = artifacts/'campaign_manifest.json'
    if not manifest_path.is_file():
        fc.prepare_campaign(args.config, root, artifact_root=artifacts)
    else:
        # A prepared campaign keeps its identity only while its inputs are unchanged;
        # a changed YAML, dataset or source needs a new campaign, never the old manifest.
        verified = verify_campaign_inputs(manifest_path, root)
        if not verified.accepted:
            print(json.dumps({'status': 'campaign_inputs_changed', 'manifest': str(manifest_path),
                              'reasons': list(verified.reasons),
                              'action': 'prepare a new campaign identity; the prepared one is not reused'}))
            return 2
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    measured = _measured_resources()
    if args.stage == 'prepare' or not args.execute:
        # Nothing is frozen here: the plan shows what a launch on this hardware would use.
        plan = {stage: _stage_budget(manifest, artifacts, config, measured, stage, freeze=False)
                for stage in manifest['stages']}
        stage = None if args.stage == 'prepare' else manifest['stages'][args.stage]
        print(json.dumps({'status': 'prepared_not_executed', 'manifest': str(manifest_path),
                          'budget': manifest['budget'], 'stage': stage,
                          'training_phases': manifest['training_phases'], 'measured_resources': measured,
                          'phase_plan': {name: entry['phases'] for name, entry in plan.items()},
                          'buffer_plan': {name: {'buffers': entry['buffers'], 'adjustments': entry['adjustments']}
                                          for name, entry in plan.items()}}))
        return 0
    authorized = args.stage in config['resource_authorization'].get('authorized_stages', [])
    # Buffers are frozen only for a launch the campaign authorizes on these resources.
    budget = _stage_budget(manifest, artifacts, config, measured, args.stage, freeze=authorized)
    learner = native_learner(root, config['campaign_id'], root/config['dataset_root'])
    try:
        result = fc.run_stage(manifest_path, args.stage, learner, root, authorized=authorized,
                              workers=[phase['workers'] for phase in budget['phases']],
                              execution=budget['execution'])
    except PermissionError as refused:
        print(json.dumps({'status': 'not_authorized', 'stage': args.stage, 'reason': str(refused)}))
        return 2
    print(json.dumps({**{key: result[key] for key in ('stage', 'planned_treatments', 'completed_treatments',
                                                       'failed_attempts', 'phases', 'stopped_at_phase', 'status',
                                                       'budget_sha256')},
                      'phase_plan': budget['phases'], 'adjustments': budget['adjustments']}))
    return 0 if result['status'] == 'training_complete' else 1


def _measured_resources():
    """Measured RAM/VRAM (native entrypoint) plus the CPUs this process may use."""
    from uc3m.adapters.algorithms.native_entrypoint import measure_runtime_resources
    measured = dict(measure_runtime_resources())
    affinity = getattr(os, 'sched_getaffinity', None)
    measured['cpu_count'] = len(affinity(0)) if affinity else (os.cpu_count() or 1)
    return measured


EXECUTION_ENV = {'torch_threads': 'UC3M_TORCH_THREADS', 'cuda_memory_fraction': 'UC3M_CUDA_MEMORY_FRACTION',
                 'worker_ram_gib': 'UC3M_WORKER_RAM_GIB', 'worker_vram_gib': 'UC3M_WORKER_VRAM_GIB'}


def _execution_env(execution):
    return {EXECUTION_ENV[key]: str(value) for key, value in execution.items()
            if key in EXECUTION_ENV and value is not None}


def _buffer_rules(config):
    """phase_buffer of native.yaml with the native value and flag of that fixed buffer."""
    rules = {}
    for name, row in config['_algorithm_config']['algorithms'].items():
        rule = row.get('phase_buffer')
        if rule:
            key = rule['key']
            rules[name] = {'key': key, 'flag': row['fixed_flags'][key], 'native': int(row['fixed'][key]),
                           'ram_gib_per_unit': float(rule['ram_gib_per_unit']),
                           'base_ram_gib': float(rule['base_ram_gib']), 'min_value': int(rule['min_value'])}
    return rules


def _stage_budget(manifest, artifacts: Path, config, measured, stage, *, buffer_rules=None, freeze=True):
    """Workers, shares, buffers and execution parameters of every phase of ``stage``.

    Buffers are sized to the parallel share once and frozen in stages/<stage>_budget.json
    (never changed afterwards, per algorithm the first time its phase gets a worker); a
    relaunch only refits how many workers fit those frozen buffers on the measured hardware.
    """
    from uc3m.application.training import fresh_policy
    from uc3m.application.training.phases import group_by_phase, phase_budget
    rules = _buffer_rules(config) if buffer_rules is None else dict(buffer_rules)
    algorithms = config['_algorithm_config']['algorithms']
    requirements = {name: dict(row.get('runtime_requirements') or {}) for name, row in algorithms.items()}
    frozen_path = artifacts/'stages'/f'{stage}_budget.json'
    frozen = json.loads(frozen_path.read_text(encoding='utf-8')).get('buffers', {}) if frozen_path.is_file() else {}
    effective_rules = {name: (dict(rule, native=frozen[name]['effective'], min_value=frozen[name]['effective'])
                              if name in frozen else rule) for name, rule in rules.items()}
    rows = json.loads((artifacts/manifest['stages'][stage]['path']).read_text(encoding='utf-8'))['treatments']
    steps = max((int(row['episode_time_steps']) for row in rows), default=0)
    phases, buffers, execution = [], dict(frozen), {}
    for group in group_by_phase(rows, manifest['training_phases']):
        treatments = len(group['treatments'])
        budget = phase_budget(group['algorithms'], measured, requirements, effective_rules,
                              episode_time_steps=steps, treatments=treatments)
        phases.append({'algorithms': list(group['algorithms']), 'treatments': treatments,
                       'episode_time_steps': steps, 'workers': budget['workers'] if treatments else 0,
                       'reasons': budget['reasons'], 'bounds': budget['bounds'], 'share': budget['share']})
        for name, entry in budget['algorithms'].items():
            if entry['buffer'] is not None and name not in buffers:
                buffers[name] = {**entry['buffer'], 'native': rules[name]['native'],
                                 'reduced': entry['buffer']['effective'] < rules[name]['native']}
            share = budget['share'] or {}
            execution[name] = {'torch_threads': entry['torch_threads'],
                               'cuda_memory_fraction': entry['cuda_memory_fraction'],
                               'worker_ram_gib': share.get('ram_gib'), 'worker_vram_gib': share.get('vram_gib')}
    if freeze and buffers != frozen:
        fresh_policy.write_json_atomic(frozen_path, {'stage': stage, 'buffers': buffers,
                                                     'frozen_with_measured': dict(measured)})
    adjustments = [{'algorithm': name, 'key': b['key'], 'native': b['native'], 'effective': b['effective']}
                   for name, b in sorted(buffers.items()) if b.get('reduced')]
    return {'phases': phases, 'buffers': buffers, 'adjustments': adjustments, 'execution': execution}


if __name__ == '__main__':
    raise SystemExit(main())
