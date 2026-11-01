"""Resource-aware Colab campaign, reusing the original launcher argument builder."""
import argparse
import importlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from uc3m.adapters.algorithms.native import NativeBackend
from uc3m.application.configuration import load_scenario_catalog
from uc3m.application.training.context import repository_revision
from uc3m.application.training.dataset_gate import (
    DEFAULT_READY_MANIFEST,
    DatasetNotValidated,
    require_validated_dataset,
)
from uc3m.application.training.persistence import write_json_atomic
from uc3m.application.training.preflight import dataset_digest, source_snapshot
from uc3m.application.training.runner import ExperimentRunner
from uc3m.domain.experiments import ExperimentSpec, RunIdentity


def resource_budget(*, cpus, ram_gib, vram_gib):
    if cpus < 1 or ram_gib < 8 or vram_gib < 8:
        raise ValueError('Insufficient measured resources for native GPU training')
    workers = min(6, max(1, cpus//3), max(1, int((ram_gib-4)//16)), max(1, int(vram_gib//10)))
    return {'max_workers': workers, 'cuda_fraction': .85/workers,
            'torch_threads': max(1, min(2, cpus//(workers*2))), 'happo_rollouts': 1,
            'cpus': cpus, 'ram_gib': ram_gib, 'vram_gib': vram_gib}


def detect_resources():
    import psutil
    cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.total',
                                    '--format=csv,noheader,nounits'], text=True).strip().splitlines()
    if len(rows) != 1:
        raise ValueError('This campaign requires one measured GPU')
    return resource_budget(cpus=cpus, ram_gib=psutil.virtual_memory().available/1024**3,
                           vram_gib=float(rows[0])/1024)


def original_jobs(root, schema, output_root, episodes, steps, seed, budget):
    """Do not fork 4 sets of scientific hyperparameters into another notebook."""
    scripts = str(root/'CityLearn/scripts')
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    launcher = importlib.import_module('colab_a100_official_launcher')
    args = launcher.parse_args(['--dry-run', '--episodes', str(episodes),
        '--episode-time-steps', str(steps), '--seed', str(seed), '--schema-path', str(schema),
        '--output-root', str(output_root)])
    args.torch_threads = budget['torch_threads']
    args.happo_n_rollout_threads = budget['happo_rollouts']
    args.cuda_memory_fraction = budget['cuda_fraction']
    if budget['ram_gib'] < 32:
        args.masac_buffer_size = 1
        args.masac_max_replay_buffer_gib = 4
        args.maac_buffer_length = 50000
    jobs = launcher.build_jobs(args, root, output_root, str(schema))
    # Identity owns these values, not launcher-specific arguments.
    protected = {'--scenario', '--schema-path', '--seed', '--episode-time-steps',
                 '--output-dir', '--episodes', '--epochs', '--num-env-steps'}
    for job in jobs:
        values, source, index = [], job['args'], 0
        while index < len(source):
            if source[index] in protected:
                index += 2
            else:
                values.append(str(source[index]))
                index += 1
        job['backend_args'] = tuple(values)
    return jobs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=50)
    parser.add_argument('--episode-time-steps', type=int, default=8760)
    parser.add_argument('--seeds', type=int, nargs='+', default=[0])
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--ready-manifest', type=Path, default=None,
                        help='dataset gate manifest; execution requires it to match the dataset')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    schema = root/'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
    if args.execute:
        try:
            require_validated_dataset(schema, args.ready_manifest or root/DEFAULT_READY_MANIFEST)
        except DatasetNotValidated as exc:
            print(json.dumps({'status': 'dataset_not_validated', 'reason': str(exc)}))
            return 2
    commit, submodules = repository_revision(root)
    budget = detect_resources()
    catalog = load_scenario_catalog(root/'configs/scenarios.yaml')
    data_hash, code_hash = dataset_digest(schema), source_snapshot(root)
    specs = []
    for seed in args.seeds:
        for job in original_jobs(root, schema, args.output_root, args.episodes, args.episode_time_steps, seed, budget):
            specs.append(ExperimentSpec(job['name'].upper(), catalog[job['scenario']], seed,
                data_hash, commit, submodules, args.episodes, args.episode_time_steps,
                code_hash, job['backend_args']))
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest = {'resources': budget, 'mode': 'execute' if args.execute else 'prepare',
                'scientific_acceptance': False, 'experiments': [spec.as_dict() for spec in specs]}
    write_json_atomic(args.output_root/'colab_campaign.json', manifest)
    if not args.execute:
        print(json.dumps({'status': 'prepared', 'runs': len(specs), 'resources': budget}))
        return 0
    def run(spec):
        run_root = args.output_root/RunIdentity.from_spec(spec).run_id
        resume = args.resume and (run_root/'evidence.json').exists()
        result = ExperimentRunner(args.output_root, NativeBackend(root, schema)).run(spec, resume=resume)
        print(f'{result.identity.run_id}: {result.status.value}', flush=True)
        return result.status.value == 'verified'
    # Preserve the original two-phase grouping, bounding measured concurrency.
    for algorithms in ({'HAPPO', 'MASAC'}, {'MATD3', 'MAAC'}):
        with ThreadPoolExecutor(max_workers=budget['max_workers']) as executor:
            outcomes = list(executor.map(run, [spec for spec in specs if spec.algorithm in algorithms]))
        if not all(outcomes):
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
