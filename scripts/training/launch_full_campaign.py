"""Launch the full 4x3x3 experimental campaign via ExperimentRunner."""
import argparse
import itertools
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import yaml

from uc3m.adapters.algorithms.evidence import finite_kpis
from uc3m.application.configuration import load_scenario_catalog
from uc3m.application.training.runner import ExperimentRunner, read_manifest
from uc3m.adapters.algorithms.native import NativeBackend
from uc3m.domain.experiments import ExperimentSpec, RunStatus


def _dataset_sha(schema_path: Path) -> str:
    import hashlib
    return hashlib.sha256(schema_path.read_bytes()).hexdigest()


def _code_commit() -> str:
    return subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=str(ROOT), text=True,
    ).strip()


def _submodule_commits() -> dict:
    out = subprocess.check_output(
        ['git', 'submodule', 'status'], cwd=str(ROOT), text=True,
    )
    result = {}
    for line in out.strip().splitlines():
        parts = line.split()
        sha = parts[0].lstrip('+').lstrip('-')
        name = parts[1]
        result[name] = sha
    return result


def build_treatments(config: dict, catalog: dict, schema_path: Path):
    dataset_sha = _dataset_sha(schema_path)
    code_commit = _code_commit()
    submodule_commits = _submodule_commits()
    treatments = []
    for algo, scenario_id, seed in itertools.product(
        config['algorithms'], config['scenarios'], config['seeds'],
    ):
        spec = ExperimentSpec(
            algorithm=algo,
            scenario=catalog[scenario_id],
            seed=seed,
            dataset_sha256=dataset_sha,
            code_commit=code_commit,
            submodule_commits=submodule_commits,
            target_episodes=config['episodes'],
            episode_time_steps=config['episode_time_steps'],
        )
        treatments.append(spec)
    return treatments


def run_campaign(config_path: Path, *, execute: bool = False,
                 filter_algorithms=None, filter_seeds=None,
                 override_episodes=None):
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    if filter_algorithms:
        config['algorithms'] = [a for a in config['algorithms'] if a in filter_algorithms]
    if filter_seeds:
        config['seeds'] = [s for s in config['seeds'] if s in filter_seeds]
    if override_episodes is not None:
        config['episodes'] = override_episodes

    schema_path = ROOT / config['schema']
    catalog = load_scenario_catalog(ROOT / 'configs' / 'scenarios.yaml')
    output_root = ROOT / config['output_root']

    treatments = build_treatments(config, catalog, schema_path)
    print(f"Campaign: {len(treatments)} treatments "
          f"({len(config['algorithms'])} algos × {len(config['scenarios'])} scenarios × {len(config['seeds'])} seeds)")

    if not execute:
        print("Dry run — pass --execute to launch training.")
        for spec in treatments:
            print(f"  {spec.algorithm}/{spec.scenario.scenario_id}/seed={spec.seed}")
        return

    backend = NativeBackend(ROOT, schema_path,
                            episode_time_steps=config['episode_time_steps'])
    runner = ExperimentRunner(output_root, backend)

    results = []
    for i, spec in enumerate(treatments, 1):
        print(f"\n[{i}/{len(treatments)}] {spec.algorithm}/{spec.scenario.scenario_id}/seed={spec.seed}")
        try:
            manifest = runner.run(spec)
            results.append({
                'algorithm': spec.algorithm,
                'scenario': spec.scenario.scenario_id,
                'seed': spec.seed,
                'status': manifest.status.value,
                'episodes': manifest.completed_episodes,
            })
            print(f"  → {manifest.status.value} ({manifest.completed_episodes} episodes)")
        except Exception as exc:
            results.append({
                'algorithm': spec.algorithm,
                'scenario': spec.scenario.scenario_id,
                'seed': spec.seed,
                'status': 'error',
                'error': str(exc),
            })
            print(f"  → ERROR: {exc}")

    all_verified = all(r['status'] == 'verified' for r in results)
    acceptance = {
        'campaign_id': config['campaign_id'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_treatments': len(treatments),
        'completed': sum(1 for r in results if r['status'] == 'verified'),
        'scientific_acceptance': all_verified,
        'results': results,
    }

    acceptance_path = ROOT / 'data' / 'audits' / 'orchestration_acceptance.json'
    acceptance_path.parent.mkdir(parents=True, exist_ok=True)
    acceptance_path.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\nAcceptance manifest: {acceptance_path}")
    print(f"Scientific acceptance: {all_verified}")


def main():
    parser = argparse.ArgumentParser(description='Launch full experimental campaign')
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--algorithms', nargs='+')
    parser.add_argument('--seeds', nargs='+', type=int)
    parser.add_argument('--episodes', type=int)
    args = parser.parse_args()
    run_campaign(
        args.config, execute=args.execute,
        filter_algorithms=args.algorithms, filter_seeds=args.seeds,
        override_episodes=args.episodes,
    )


if __name__ == '__main__':
    main()
