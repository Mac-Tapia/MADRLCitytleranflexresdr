"""Observe real optimizer updates of a native trainer, without changing them.

The observer wraps the native finite-gradient guard installer. Before the guard
wraps an optimizer, a counter is placed under it, so only steps the guard lets
through (finite gradients) are counted as updates; an outer counter sees every
attempted step. Parameter hashes at install and at finalize show whether the
policy actually changed. Exit codes and file existence are never evidence.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class LearningEvidence:
    campaign_id: str
    attempt_id: str
    env_steps: int
    successful_optimizer_updates_by_owner: Mapping[str, int]
    attempted_optimizer_steps_by_owner: Mapping[str, int]
    initial_parameter_hashes: Mapping[str, str]
    final_parameter_hashes: Mapping[str, str]
    nonfinite_events: int
    checkpoint_bundle_hash: Optional[str]
    verified: bool
    reasons: Tuple[str, ...] = ()

    def as_dict(self):
        return {key: (dict(value) if isinstance(value, Mapping) else list(value) if isinstance(value, tuple) else value)
                for key, value in self.__dict__.items()}


def _named_parameters(spec: Mapping[str, Any]) -> List[Tuple[str, Any]]:
    module = spec.get('module')
    if module is not None and hasattr(module, 'named_parameters'):
        return list(module.named_parameters())
    return [(f'parameter_{i}', p) for i, p in enumerate(list(spec.get('parameters') or []))]


def parameter_hash(parameters: List[Tuple[str, Any]]) -> Tuple[str, bool]:
    import torch
    digest = hashlib.sha256()
    finite = True
    for name, parameter in parameters:
        tensor = parameter.detach().to('cpu').contiguous()
        finite = finite and bool(torch.isfinite(tensor).all().item())
        digest.update(name.encode('utf-8') + b'\0' + tensor.numpy().tobytes())
    return digest.hexdigest(), finite


@dataclass
class LearningObserver:
    campaign_id: str
    attempt_id: str
    _owners: Dict[str, List[Tuple[str, Any]]] = field(default_factory=dict)
    _initial: Dict[str, str] = field(default_factory=dict)
    _passed: Dict[str, int] = field(default_factory=dict)
    _attempted: Dict[str, int] = field(default_factory=dict)

    def wrap_guard_installer(self, install: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        def observed_install(optimizer_specs, audit_path=None, *args, **kwargs):
            specs = list(optimizer_specs)
            for index, spec in enumerate(specs):
                optimizer = spec.get('optimizer')
                parameters = _named_parameters(spec)
                if optimizer is None or not parameters or getattr(optimizer, '_uc3m_observed', False):
                    continue
                owner = str(spec.get('owner') or f'optimizer_{index}')
                self._owners[owner] = parameters
                self._initial[owner] = parameter_hash(parameters)[0]
                self._passed.setdefault(owner, 0)
                self._attempted.setdefault(owner, 0)
                inner = optimizer.step

                def counted(*a, _owner=owner, _inner=inner, **k):
                    self._passed[_owner] += 1
                    return _inner(*a, **k)
                optimizer.step = counted
                optimizer._uc3m_observed = True
            result = install(specs, audit_path, *args, **kwargs)
            for index, spec in enumerate(specs):
                optimizer = spec.get('optimizer')
                owner = str(spec.get('owner') or f'optimizer_{index}')
                if optimizer is None or owner not in self._owners or getattr(optimizer, '_uc3m_outer', False):
                    continue
                guarded = optimizer.step

                def attempted(*a, _owner=owner, _guarded=guarded, **k):
                    self._attempted[_owner] += 1
                    return _guarded(*a, **k)
                optimizer.step = attempted
                optimizer._uc3m_outer = True
            return result
        return observed_install

    def finalize(self, *, env_steps: int, checkpoint_bundle_hash: Optional[str]) -> LearningEvidence:
        if not self._owners:
            raise RuntimeError('no optimizer was registered: the native guard installer never ran')
        reasons = []
        final, nonfinite_parameters = {}, []
        for owner, parameters in self._owners.items():
            final[owner], finite = parameter_hash(parameters)
            if not finite:
                nonfinite_parameters.append(owner)
            if self._passed[owner] == 0:
                reasons.append(f'no_successful_update:{owner}')
            elif final[owner] == self._initial[owner]:
                reasons.append(f'parameters_unchanged:{owner}')
        reasons.extend(f'nonfinite_parameters:{owner}' for owner in nonfinite_parameters)
        if not checkpoint_bundle_hash:
            reasons.append('no_checkpoint')
        if env_steps <= 0:
            reasons.append('no_env_steps')
        nonfinite_events = sum(self._attempted[o] - self._passed[o] for o in self._owners)
        return LearningEvidence(self.campaign_id, self.attempt_id, int(env_steps), dict(self._passed),
                                dict(self._attempted), dict(self._initial), final, nonfinite_events,
                                checkpoint_bundle_hash, not reasons, tuple(reasons))
