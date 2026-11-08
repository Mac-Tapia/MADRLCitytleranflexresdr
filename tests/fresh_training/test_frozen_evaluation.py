"""T7: frozen evaluation of fresh native policies and fresh baselines.

Runs the real CityLearn validation split of the fresh campaign for short
episodes. Native policies come only from verified micro-training attempts of
this campaign (T5); there are no downloaded/historical models and no mocks as
native acceptance. A backend without a verified attempt fails, it is not
skipped. KPI come from per-step physical traces through the T4 contract, never
from env.evaluate() aggregates.
"""
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = (lambda c: REPO/c['dataset_root'])(__import__('yaml').safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8')))   # the active campaign dataset (configs/experiments/iquitos.yaml)
SPLIT = CAMPAIGN/'splits/validation_2024'
STEPS = 48  # two complete days (baselines)
NATIVE_STEPS = 24  # one complete day per native policy
SEED = 2024  # exogenous evaluation seed, shared by every policy of a comparison
ATTEMPTS = {}
NATIVE = ('HAPPO', 'MASAC', 'MATD3', 'MAAC')


@pytest.fixture(scope='module', autouse=True)
def _bind_native_attempts(native_attempts):
    ATTEMPTS.update(native_attempts)


def attempt_for(algorithm: str) -> Path:
    return ATTEMPTS[algorithm]


_POLICIES, _RUNS, _BASELINES = {}, {}, {}


def native_policy(algorithm):
    from uc3m.adapters.citylearn import policy_inference as pi
    if algorithm not in _POLICIES:
        try:
            _POLICIES[algorithm] = pi.load_native_policy(algorithm, attempt_for(algorithm))
        except (FileNotFoundError, PermissionError) as exc:
            pytest.fail(f'{algorithm}: no verified fresh native policy loadable from '
                        f'{attempt_for(algorithm)}: {exc}')
    return _POLICIES[algorithm]


def native_run(algorithm):
    from uc3m.adapters.citylearn import policy_inference as pi
    if algorithm not in _RUNS:
        policy = native_policy(algorithm)
        _RUNS[algorithm] = pi.run_frozen_episode(SPLIT, policy, CAMPAIGN, steps=NATIVE_STEPS, seed=SEED)
        _RUNS[algorithm] = (_RUNS[algorithm], list(policy.history))
    return _RUNS[algorithm]


def baselines(scenario=None, seed=None, steps=STEPS, scenario_catalog=None):
    from uc3m.adapters.citylearn import policy_inference as pi
    key = (scenario, seed, steps, str(scenario_catalog) if scenario_catalog is not None else None)
    if key not in _BASELINES:
        _BASELINES[key] = tuple(pi.run_frozen_episode(SPLIT, policy, CAMPAIGN, steps=steps, seed=seed,
                                                      scenario=scenario, scenario_catalog=scenario_catalog)
                                for policy in (pi.RbcPolicy(), pi.NoStorageReferencePolicy()))
    return _BASELINES[key]


@pytest.fixture(scope='module')
def runs():
    assert (SPLIT/'schema.json').is_file(), 'fresh validation split missing (T3 not complete)'
    return baselines()


# --- baselines ---------------------------------------------------------------------------------

def test_baseline_eval_has_no_optimizer_steps(runs):
    rbc, reference = runs
    assert rbc.training_updates == 0 and reference.training_updates == 0
    assert rbc.completed_steps == reference.completed_steps == STEPS


def test_baseline_same_ev_services_and_initial_energy(runs):
    rbc, reference = runs
    assert rbc.ev_connection_hash == reference.ev_connection_hash  # same EV sessions offered
    assert rbc.initial_storage_kwh == reference.initial_storage_kwh
    assert rbc.trace.exogenous_hash == reference.trace.exogenous_hash
    assert reference.battery_throughput_kwh == pytest.approx(0.0, abs=1e-6)  # no storage optimization


def test_baseline_kpi_from_physical_trace(runs):
    from uc3m.application.evaluation import kpi_contract as kc
    rbc, reference = runs
    from uc3m.application.evaluation.bill_cost import bill_measures, load_bill_tariffs
    catalog = kc.load_kpi_catalog(REPO/'configs/evaluation/kpis.yaml')
    # The primary cost is the official bill (D02); it is unavailable without its tariff table.
    measures = bill_measures(load_bill_tariffs(REPO/'data/tariffs/osinergmin/bill_tariffs.csv'))
    report = kc.compute_fresh_kpis(rbc.trace, reference.trace, catalog, extra_measures=measures)
    result = kc.validate_kpi_report(report, catalog)
    assert result.passed, result.reasons
    assert rbc.trace.currency == 'USD' and 'World Bank' in rbc.trace.currency_provenance
    assert len(rbc.trace.timestamps) == STEPS and rbc.trace.timestamps[0].startswith('2024-01-01T00:00:00')


# --- native policies ---------------------------------------------------------------------------

def _rebuild_actions(algorithm, policy, history):
    """Rebuild each acting network from the checkpoint files and replay the observations."""
    import torch
    backend = policy.backend
    files = {Path(p).name: Path(p) for p in policy.checkpoint_files}
    rebuilt = []
    with torch.no_grad():
        if algorithm == 'HAPPO':
            nets = []
            for index, space in enumerate(policy.observation_spaces):
                net = backend['StochasticPolicy'](policy.model_args, space, policy.action_spaces[index],
                                                  torch.device('cpu'))
                net.load_state_dict(torch.load(files[f'actor_agent{index}.pt'], map_location='cpu'))
                net.eval()
                nets.append(net)
            hidden = policy.model_args['hidden_sizes'][-1]
            rnn = np.zeros((1, len(nets), policy.model_args['recurrent_n'], hidden), dtype=np.float32)
            masks = np.ones((1, len(nets), 1), dtype=np.float32)
            for step in history:
                obs = np.asarray(step['observations'], dtype=np.float32)[None]
                actions = []
                for index, net in enumerate(nets):
                    action, _, state = net(obs[:, index], rnn[:, index], masks[:, index], None, True)
                    rnn[:, index] = state.numpy()
                    actions.append(action.numpy()[0])
                rebuilt.append(np.asarray(actions))
        elif algorithm == 'MASAC':
            args = policy.backend_args
            net = backend['rnn_policy'](policy.policy_input_shape, args)
            net.load_state_dict(torch.load(files[next(n for n in files if n.endswith('_policy_net_params.pkl'))],
                                           map_location='cpu'))
            net.eval()
            agents, n_actions = args.n_agents, args.n_actions
            hidden = torch.zeros((1, agents, args.rnn_hidden_dim))
            last = np.zeros((agents, n_actions))
            for step in history:
                actions = []
                for index in range(agents):
                    inputs = np.asarray(step['observations'][index], dtype=np.float64)
                    if args.last_action:
                        inputs = np.hstack((inputs, last[index]))
                    if args.reuse_network:
                        inputs = np.hstack((inputs, np.eye(agents)[index]))
                    out, hidden[:, index, :] = net(torch.tensor(inputs, dtype=torch.float32).unsqueeze(0),
                                                   hidden[:, index, :])
                    # D03: the native agent sets unavailable actions to -inf before choosing.
                    available = torch.tensor(policy.env.get_avail_agent_actions(index)).unsqueeze(0)
                    out = out.masked_fill(available == 0, float('-inf'))
                    branches = getattr(args, 'action_branches', None)
                    if branches:            # D-M3-9: greedy level of every branch (softmax per branch)
                        k, levels_per_branch = branches
                        levels = torch.softmax(out.view(k, levels_per_branch)/args.temp, dim=1).argmax(dim=1).numpy()
                        last[index] = policy.adapter.action_grid.onehot(index, levels)
                        actions.append(levels)
                        continue
                    action = int(torch.softmax(out/args.temp, dim=1).argmax(dim=1)[0])
                    last[index] = np.eye(n_actions)[action]
                    actions.append(action)
                rebuilt.append(np.asarray(actions))
        elif algorithm == 'MATD3':
            nets = {}
            for agent_id, policy_id in enumerate(policy.policy_ids):
                net = backend['MATD3_Actor'](policy.backend_args, policy.observation_dims_by_policy[policy_id],
                                             policy.action_dims_by_policy[policy_id], torch.device('cpu'))
                net.load_state_dict(torch.load(Path(policy.model_dir)/policy_id/'actor.pt', map_location='cpu'))
                net.eval()
                nets[agent_id] = net
            for step in history:
                obs = np.asarray(step['observations'], dtype=np.float32)
                rebuilt.append(np.asarray([nets[i](obs[i][None]).numpy()[0] for i in range(len(nets))]))
        elif algorithm == 'MAAC':
            saved = torch.load(files['model.pt'], map_location='cpu', weights_only=False)
            hidden = saved['init_dict']['pol_hidden_dim']
            nets = []
            for params, sizes in zip(saved['agent_params'], saved['init_dict']['agent_init_params']):
                net = backend['DiscretePolicy'](sizes['num_in_pol'], sizes['num_out_pol'], hidden_dim=hidden,
                                                branches=sizes.get('branches'))
                net.load_state_dict(params['policy'])
                net.eval()
                nets.append(net)
            if policy.adapter.discrete_action_mode == 'grid':   # D-M3-9: the level of each real equipment
                for step in history:
                    obs = np.asarray(step['observations'], dtype=np.float32)
                    rebuilt.append([policy.env.grid_indices(i, net(torch.tensor(obs[i][None]), sample=False)
                                                            .numpy()[0]).tolist() for i, net in enumerate(nets)])
                return rebuilt
            # D03: each agent's one-hot over its own actions is recorded as its row of the shared table.
            rows = [policy.adapter.discrete_action_rows_by_agent[agent] for agent in policy.adapter.agents]
            for step in history:
                obs = np.asarray(step['observations'], dtype=np.float32)
                rebuilt.append(np.asarray([rows[i][int(np.argmax(net(torch.tensor(obs[i][None]), sample=False)
                                                                 .numpy()[0]))]
                                           for i, net in enumerate(nets)]))
    return rebuilt


@pytest.mark.parametrize('algorithm', NATIVE)
def test_loaded_actions_match_saved_policy(algorithm):
    run, history = native_run(algorithm)
    policy = native_policy(algorithm)
    assert len(history) == run.completed_steps == NATIVE_STEPS
    rebuilt = _rebuild_actions(algorithm, policy, history)
    grid = algorithm in ('MASAC', 'MAAC') and policy.adapter.discrete_action_mode == 'grid'
    for step, (record, expected) in enumerate(zip(history, rebuilt)):
        if grid:   # D-M3-9: one level per equipment, agents may have different equipment counts (MAAC)
            assert [list(np.asarray(a).reshape(-1)) for a in record['actions']] == \
                [list(np.asarray(a).reshape(-1)) for a in expected], f'{algorithm} step {step}'
            continue
        np.testing.assert_allclose(np.asarray(record['actions'], dtype=np.float64),
                                   np.asarray(expected, dtype=np.float64), rtol=0, atol=1e-6,
                                   err_msg=f'{algorithm} step {step}')
    if grid:   # every level is on the grid and a padded branch only takes PAD_LEVEL
        from citylearn.v3.action_grid import LEVELS, PAD_LEVEL
        branches = policy.adapter.action_grid.branches
        for step, record in enumerate(history):
            for index, action in enumerate(record['actions']):
                levels = np.asarray(action).reshape(-1)
                assert all(0 <= v < LEVELS for v in levels[:branches[index]]), (algorithm, step, index)
                assert all(v == PAD_LEVEL for v in levels[branches[index]:]), (algorithm, step, index)
    elif algorithm in ('MASAC', 'MAAC'):  # D03: every recorded action moves real equipment only
        rows = policy.adapter.discrete_action_rows_by_agent
        for step, record in enumerate(history):
            for agent, action in zip(policy.agents, record['actions']):
                assert int(action) in rows[agent], f'{algorithm} step {step} {agent} chose row {action}'
    contract = run.contract
    assert contract['algorithm'] == algorithm and contract['deterministic'] is True
    assert contract['agents'] == list(policy.agents) and len(contract['agents']) == 17
    assert contract['checkpoint_bundle_hash'] == json.loads(
        (attempt_for(algorithm)/'learning_evidence.json').read_text(encoding='utf-8'))['checkpoint_bundle_hash']
    assert set(contract['observation_dims']) == set(contract['agents'])
    assert contract['max_observation_dim'] == max(contract['observation_dims'].values())
    assert contract['normalizer_sha256'] and contract['scenario'] == policy.scenario
    if grid:
        meta = contract['discrete_action_metadata']
        assert meta['mode'] == 'grid' and meta['n_actions'] == meta['max_branches']*meta['levels']
        assert set(contract['grid_action_map']) == set(contract['agents'])
    elif algorithm in ('MASAC', 'MAAC'):
        table = np.asarray(contract['discrete_action_table'])
        assert table.shape == (contract['discrete_action_metadata']['n_discrete_actions'],
                               contract['max_action_dim'])
    else:
        assert contract['discrete_action_table'] is None


@pytest.mark.parametrize('algorithm', ('rbc', 'no_storage_reference') + NATIVE)
def test_eval_has_no_optimizer_steps(algorithm):
    if algorithm in NATIVE:
        run, _ = native_run(algorithm)
        expected = NATIVE_STEPS
        assert run.contract['parameter_hash_before'] == run.contract['parameter_hash_after']
        assert run.contract['grad_enabled_during_act'] is False
    else:
        run = dict(zip(('rbc', 'no_storage_reference'), baselines()))[algorithm]
        expected = STEPS
    assert run.training_updates == 0
    assert run.completed_steps == expected


@pytest.mark.parametrize('algorithm', NATIVE)
def test_recurrent_state_resets(algorithm):
    from uc3m.adapters.citylearn import policy_inference as pi
    first, history = native_run(algorithm)
    policy = native_policy(algorithm)
    if policy.recurrent:
        assert policy.recurrent_state_nonzero(), 'a recurrent policy must carry state between steps'
    second = pi.run_frozen_episode(SPLIT, policy, CAMPAIGN, steps=NATIVE_STEPS, seed=SEED)
    assert first.trace.exogenous_hash == second.trace.exogenous_hash
    for step, (a, b) in enumerate(zip(history, policy.history)):
        np.testing.assert_array_equal(np.asarray(a['actions']), np.asarray(b['actions']),
                                      err_msg=f'{algorithm} step {step}: state leaked across reset')
    assert first.trace.series_by_building == second.trace.series_by_building
    policy.reset(SEED)
    assert policy.recurrent_state_is_initial()
    assert policy.recurrent == (algorithm == 'MASAC' or bool(getattr(policy, 'model_args', {})
                                                             .get('use_recurrent_policy', False)))


@pytest.mark.parametrize('algorithm', NATIVE)
def test_same_ev_services_and_initial_energy(algorithm):
    run, _ = native_run(algorithm)
    policy = native_policy(algorithm)
    rbc, reference = baselines(scenario=policy.scenario, seed=SEED, steps=NATIVE_STEPS,
                              scenario_catalog=policy.scenario_catalog_path)
    assert run.ev_connection_hash == rbc.ev_connection_hash == reference.ev_connection_hash
    assert run.initial_storage_kwh == rbc.initial_storage_kwh == reference.initial_storage_kwh
    assert run.trace.exogenous_hash == rbc.trace.exogenous_hash == reference.trace.exogenous_hash
    assert run.trace.timestamps == rbc.trace.timestamps
    assert reference.battery_throughput_kwh == pytest.approx(0.0, abs=1e-6)
    assert rbc.contract['agents'] == run.contract['agents']


def test_test_split_locked_until_freeze():
    from uc3m.adapters.citylearn import policy_inference as pi
    assert not (CAMPAIGN/'test_unlock.json').exists()
    with pytest.raises(PermissionError):
        pi.run_frozen_episode(CAMPAIGN/'splits/test_2025', pi.RbcPolicy(), CAMPAIGN, steps=STEPS)
    with pytest.raises(PermissionError):
        pi.run_frozen_episode(CAMPAIGN/'splits/test_2025', native_policy('MAAC'), CAMPAIGN, steps=STEPS, seed=SEED)


def _copy_attempt(algorithm, destination):
    source = attempt_for(algorithm)
    evidence = json.loads((source/'learning_evidence.json').read_text(encoding='utf-8'))
    campaign = next(p for p in source.parents if (p/'campaign_manifest.json').is_file())
    destination.parent.mkdir(parents=True, exist_ok=True)
    for name in ('campaign_manifest.json', 'campaign.json'):
        shutil.copyfile(campaign/name, destination.parent/name)
    shutil.copytree(campaign/'stages', destination.parent/'stages', dirs_exist_ok=True)
    destination.mkdir(exist_ok=True)
    for name in ('attempt.json', 'resolved_treatment.json', 'completion.json'):
        shutil.copyfile(source/name, destination/name)
    for relative in evidence['checkpoint_files']:
        relative = Path(relative.replace('\\', '/'))
        (destination/relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/relative, destination/relative)
    (destination/'learning_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')
    return evidence


@pytest.mark.parametrize('algorithm', ('MASAC', 'MAAC'))
def test_policy_without_its_trained_action_map_is_rejected(algorithm):
    from uc3m.adapters.citylearn import policy_inference as pi
    missing = pi.load_native_policy(algorithm, ATTEMPTS[algorithm])
    missing.hyperparameters.pop('discrete_action_map', None)
    with pytest.raises(pi.FrozenPolicyRejected, match='action map'):
        pi.run_frozen_episode(SPLIT, missing, CAMPAIGN, steps=NATIVE_STEPS, seed=SEED)
    altered = pi.load_native_policy(algorithm, ATTEMPTS[algorithm])
    mapping = altered.hyperparameters['discrete_action_map']
    first = sorted(mapping)[0]
    mapping[first] = mapping[first][:1]  # trained without the actions of its real equipment
    with pytest.raises(pi.FrozenPolicyRejected, match='action map'):
        pi.run_frozen_episode(SPLIT, altered, CAMPAIGN, steps=NATIVE_STEPS, seed=SEED)


def test_no_model_fails_closed(tmp_path):
    from uc3m.adapters.citylearn import policy_inference as pi
    with pytest.raises(FileNotFoundError):
        pi.load_native_policy('MATD3', tmp_path/'missing_attempt')
    with pytest.raises(ValueError):
        pi.load_native_policy('RANDOM', ATTEMPTS['HAPPO'])
    with pytest.raises(PermissionError):  # evidence of another algorithm
        pi.load_native_policy('MAAC', ATTEMPTS['HAPPO'])

    unverified = tmp_path/'unverified'
    evidence = _copy_attempt('HAPPO', unverified)
    (unverified/'learning_evidence.json').write_text(json.dumps(dict(evidence, verified=False)), encoding='utf-8')
    with pytest.raises(PermissionError):
        pi.load_native_policy('HAPPO', unverified)

    wrong_hash = tmp_path/'wrong_hash'
    evidence = _copy_attempt('HAPPO', wrong_hash)
    (wrong_hash/'learning_evidence.json').write_text(
        json.dumps(dict(evidence, checkpoint_bundle_hash='0'*64)), encoding='utf-8')
    with pytest.raises(PermissionError, match='hash'):
        pi.load_native_policy('HAPPO', wrong_hash)

    tampered = tmp_path/'tampered'
    evidence = _copy_attempt('HAPPO', tampered)
    actor = tampered/Path(evidence['checkpoint_files'][3].replace('\\', '/'))
    payload = bytearray(actor.read_bytes())
    payload[-1] ^= 0xFF
    actor.write_bytes(bytes(payload))
    with pytest.raises(PermissionError, match='hash'):
        pi.load_native_policy('HAPPO', tampered)

    incomplete = tmp_path/'incomplete'
    evidence = _copy_attempt('HAPPO', incomplete)
    (incomplete/Path(evidence['checkpoint_files'][-2].replace('\\', '/'))).unlink()  # critic_agent.pt
    with pytest.raises(PermissionError, match='missing|incomplete|untrusted_checkpoint'):
        pi.load_native_policy('HAPPO', incomplete)

    no_files = tmp_path/'no_files'
    _copy_attempt('HAPPO', no_files)
    record = json.loads((no_files/'learning_evidence.json').read_text(encoding='utf-8'))
    (no_files/'learning_evidence.json').write_text(json.dumps(dict(record, checkpoint_files=[])), encoding='utf-8')
    with pytest.raises(PermissionError, match='no_checkpoint|incomplete|untrusted_checkpoint'):
        pi.load_native_policy('HAPPO', no_files)
