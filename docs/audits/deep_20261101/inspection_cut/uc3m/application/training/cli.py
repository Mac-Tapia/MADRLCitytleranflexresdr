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

STAGES = ('prepare', 'pilot', 'hpo', 'confirm', 'sensitivity')


def native_learner(project_root: Path, campaign_id: str, dataset_root: Path, scenario_catalog: Path):
    """Adapter wiring: one child process of the native entrypoint per attempt."""
    def learn(treatment, attempt_root):
        command = [sys.executable, '-B', '-m', 'uc3m.adapters.algorithms.native_entrypoint',
                   '--algorithm', treatment['algorithm'], '--campaign-id', campaign_id,
                   '--attempt-id', Path(attempt_root).name, '--attempt-root', str(attempt_root),
                   '--normalizer', str(dataset_root/'normalizer.json'), '--'] + list(treatment['native_arguments'])
        env = dict(os.environ, UC3M_SCENARIO_CATALOG=str(scenario_catalog),
                   PYTHONPATH=os.pathsep.join([str(project_root), str(project_root/'CityLearn'),
                                               os.environ.get('PYTHONPATH', '')]))
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
    artifacts = root/'outputs/campaigns'/config['storage_alias']
    manifest_path = artifacts/'campaign_manifest.json'
    if not manifest_path.is_file():
        fc.prepare_campaign(args.config, root, artifact_root=artifacts)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if args.stage == 'prepare' or not args.execute:
        stage = None if args.stage == 'prepare' else manifest['stages'][args.stage]
        print(json.dumps({'status': 'prepared_not_executed', 'manifest': str(manifest_path),
                          'budget': manifest['budget'], 'stage': stage}))
        return 0
    authorized = args.stage in config['resource_authorization'].get('authorized_stages', [])
    learner = native_learner(root, config['campaign_id'], root/config['dataset_root'], root/config['scenario_catalog'])
    try:
        result = fc.run_stage(manifest_path, args.stage, learner, root, authorized=authorized)
    except PermissionError as refused:
        print(json.dumps({'status': 'not_authorized', 'stage': args.stage, 'reason': str(refused)}))
        return 2
    print(json.dumps({key: result[key] for key in ('stage', 'planned_treatments', 'completed_treatments',
                                                    'failed_attempts', 'status')}))
    return 0 if result['status'] == 'training_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
