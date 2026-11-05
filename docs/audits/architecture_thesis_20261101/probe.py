"""Read-only live simulator probes; no learning or production campaign writes."""
import csv
import json
import os
from pathlib import Path
import sys
import tempfile
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    from uc3m.adapters.algorithms.native_entrypoint import load_native_common, measure_runtime_resources
    from uc3m.adapters.citylearn.fresh_observations import frozen_observation_limits, load_normalizer
    from uc3m.adapters.citylearn.policy_inference import _adapter_contract
    from uc3m.application.training.fresh_campaign import load_campaign_config, build_dag
    common = load_native_common(ROOT)
    config = load_campaign_config(ROOT/'configs/experiments/iquitos.yaml', ROOT)
    campaign = ROOT/config['dataset_root']
    normalizer = load_normalizer(campaign/'normalizer.json')
    schema_path = campaign/'splits/train_2023/schema.json'
    os.environ['UC3M_SCENARIO_CATALOG'] = str(ROOT/'configs/scenarios.yaml')
    report = {'config': config, 'resources': measure_runtime_resources(), 'environments': [], 'datasets': []}
    dag = build_dag(config, ROOT)
    report['dag_budget'] = dag.budget()
    report['hpo_candidates'] = dag.candidates_by_algorithm
    from uc3m.application.training.phases import phase_budget
    from uc3m.application.training.cli import _buffer_rules
    requirements = {a: row.get('runtime_requirements') or {} for a, row in config['_algorithm_config']['algorithms'].items()}
    measured = dict(report['resources'], cpu_count=os.cpu_count() or 1)
    report['phase_budgets'] = [phase_budget(phase, measured, requirements, _buffer_rules(config),
                              episode_time_steps=8760, treatments=2) for phase in config['training_phases']]
    for path in sorted((ROOT/'data/campaigns').iterdir()):
        if not path.is_dir():
            continue
        acceptance = path/'dataset_acceptance.json'
        if not acceptance.is_file():
            continue
        payload = json.loads(acceptance.read_text(encoding='utf-8'))
        row = {'root': path.relative_to(ROOT).as_posix(), 'acceptance': payload,
               'splits_exist': (path/'split_manifest.json').is_file(),
               'normalizer_exists': (path/'normalizer.json').is_file(), 'csv_ranges': {}}
        for name in ('carbon_intensity.csv', 'pricing.csv', 'pricing_1.csv'):
            source = path/'dataset'/name
            if source.is_file():
                with source.open(encoding='utf-8-sig', newline='') as stream:
                    reader = csv.DictReader(stream)
                    key = 'carbon_intensity' if name.startswith('carbon') else 'electricity_pricing'
                    values = [float(r[key]) for r in reader]
                row['csv_ranges'][name] = {'min': min(values), 'max': max(values), 'unique': len(set(values)),
                                           'rows': len(values)}
        report['datasets'].append(row)
    with tempfile.TemporaryDirectory(prefix='madrl_audit_') as temp:
        common._CSV_CACHE_DIR = Path(temp)/'csv_cache'
        # One fresh instance measures dimensions; the separately recorded pytest
        # matrix exercises algorithm/scenario routing. This is not four learners.
        for algorithm, scenario in [('MATD3', 'E1')]:
            started = time.perf_counter()
            adapter = None
            try:
                with frozen_observation_limits(normalizer):
                    adapter = common.CityLearnV3BackendAdapter(schema_path=str(schema_path), scenario=scenario,
                              algorithm=algorithm, seed=901, episode_time_steps=6, trace_record_interval=0)
                    adapter.reset()
                    env = adapter.env
                    rewards = []
                    for _ in range(3):
                        _, rew, _, _, _ = env.step({a: np.zeros(adapter.action_dims[a]) for a in adapter.agents})
                        rewards.append([float(x) for x in rew.values()])
                    core = adapter._core_env()
                    core = getattr(core, 'unwrapped', core)
                    breakdown = core.reward_function._last_component_breakdown
                    report['environments'].append({'algorithm': algorithm, 'scenario': scenario,
                        'contract': _adapter_contract(adapter), 'reward_aggregation': env.reward_aggregation,
                        'observed_axis_weights': breakdown['axis_weights'], 'team_reward': breakdown['team_reward'],
                        'local_rewards': [c['local_reward'] for c in breakdown['components']],
                        'reward_vectors': rewards,
                        'all_agents_share_payoff': all(np.allclose(r, r[0]) for r in rewards),
                        'discrete_actions': adapter.n_discrete_actions,
                        'bact_is_appended': False, 'seconds': time.perf_counter()-started})
            except Exception as exc:
                report['environments'].append({'algorithm': algorithm, 'scenario': scenario,
                                                'error': f'{type(exc).__name__}: {exc}'})
            finally:
                if adapter is not None:
                    adapter.env.close()
    report['historical_cache_exists'] = (ROOT/'outputs/dataset_cache').exists()
    report['production_campaign_manifest_exists'] = (ROOT/'outputs/campaigns/iquitos_v1/campaign_manifest.json').is_file()
    (OUT/'runtime_probe.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print(json.dumps({'budget': report['dag_budget'], 'resources': report['resources'],
                      'environments': [{k:v for k,v in row.items() if k in {'algorithm','scenario','error','all_agents_share_payoff','observed_axis_weights'}}
                                       for row in report['environments']]}, indent=2))


if __name__ == '__main__':
    main()
