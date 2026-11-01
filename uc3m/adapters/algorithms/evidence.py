"""Algorithm-specific checkpoint bundles and numeric KPI acceptance."""
import math
from collections.abc import Mapping


def finite_kpis(values):
    return isinstance(values, Mapping) and bool(values) and all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) for value in values.values())


def checkpoint_bundle(root, algorithm, agents):
    import torch
    candidates = []
    if algorithm == 'HAPPO':
        for first in root.rglob('actor_agent0.pt'):
            parent = first.parent
            candidates.append([parent/f'actor_agent{i}.pt' for i in range(agents)]
                              + [parent/'critic_agent.pt', parent/'value_normalizer.pt'])
    elif algorithm == 'MATD3':
        for first in root.rglob('policy_0/actor.pt'):
            parent = first.parent.parent
            candidates.append([parent/f'policy_{i}'/name for i in range(agents)
                               for name in ('actor.pt', 'critic.pt')])
    elif algorithm == 'MASAC':
        for first in root.rglob('*_rnn_net_params.pkl'):
            prefix = first.name.split('_', 1)[0]
            candidates.append([first.parent/f'{prefix}_{name}_net_params.pkl'
                               for name in ('rnn', 'qmix', 'policy')])
    elif algorithm == 'MAAC':
        candidates = [[path] for path in root.rglob('*.pt')]

    def finite_tree(value):
        if torch.is_tensor(value):
            return bool(torch.isfinite(value).all())
        if isinstance(value, Mapping):
            return all(finite_tree(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return all(finite_tree(item) for item in value)
        if isinstance(value, float):
            return math.isfinite(value)
        return True

    for bundle in sorted(candidates, key=lambda items: max(
            (path.stat().st_mtime for path in items if path.is_file()), default=0), reverse=True):
        if not all(path.is_file() for path in bundle):
            continue
        try:
            payloads = [torch.load(path, map_location='cpu', weights_only=False) for path in bundle]
            if not all(isinstance(payload, Mapping) and payload and finite_tree(payload)
                       for payload in payloads):
                continue
            if algorithm == 'MAAC':
                saved = payloads[0]
                if (len(saved.get('agent_params', [])) != agents
                        or not {'init_dict', 'critic_params'} <= set(saved)):
                    continue
            return tuple(bundle)
        except (OSError, RuntimeError, ValueError, TypeError, EOFError, KeyError):
            continue
    return ()
