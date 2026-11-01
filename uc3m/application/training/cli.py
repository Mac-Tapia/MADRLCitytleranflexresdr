"""Local native training entrypoint; prepare by default, execute explicitly."""
import argparse
import json
from pathlib import Path

from uc3m.adapters.algorithms.native import NativeBackend
from uc3m.application.configuration import load_scenario_catalog
from uc3m.application.training.persistence import write_json_atomic
from uc3m.application.training.preflight import dataset_digest, source_snapshot
from uc3m.application.training.runner import ExperimentRunner
from uc3m.domain.experiments import ExperimentSpec, RunIdentity
from uc3m.application.training.context import repository_revision


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--algorithm', choices=['HAPPO', 'MASAC', 'MATD3', 'MAAC'], required=True)
    parser.add_argument('--scenario', choices=['E1', 'E2', 'E3'], required=True)
    parser.add_argument('--schema', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, default=Path('outputs/modular_training'))
    parser.add_argument('--episodes', type=int, default=50)
    parser.add_argument('--episode-time-steps', type=int, default=8760)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    commit, submodules = repository_revision(root)
    spec = ExperimentSpec(args.algorithm,
        load_scenario_catalog(root/'configs/scenarios.yaml')[args.scenario],
        args.seed, dataset_digest(args.schema), commit, submodules, args.episodes,
        args.episode_time_steps, source_snapshot(root))
    backend = NativeBackend(root, args.schema)
    if not args.execute:
        identity = RunIdentity.from_spec(spec)
        output = args.output_root/'plans'/f'{identity.run_id}.json'
        write_json_atomic(output, {'experiment': spec.as_dict(), 'run_id': identity.run_id,
            'launch_authorized': False,
            'command': backend.command(spec, args.output_root/identity.run_id, args.resume)})
        print(json.dumps({'status': 'prepared_not_executed', 'plan': str(output)}))
        return 0
    result = ExperimentRunner(args.output_root, backend).run(spec, resume=args.resume)
    print(json.dumps({'run_id': result.identity.run_id, 'status': result.status.value,
                      'completed_episodes': result.completed_episodes,
                      'target_episodes': result.target_episodes,
                      'artifact_count': len(result.artifacts)}))
    return 0 if result.status.value == 'verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
