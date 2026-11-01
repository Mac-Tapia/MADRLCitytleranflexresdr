"""Simulator port for environment interaction; integration deferred (see ADR)."""
from typing import Any, Mapping, Protocol, Tuple, runtime_checkable


@runtime_checkable
class SimulatorPort(Protocol):
    """Per-agent observations and actions keyed by agent id.

    Array types belong to the adapter; the port stays free of numpy so the
    domain contract does not depend on a numeric library.
    """

    def reset(self) -> Mapping[str, Any]: ...
    def step(self, actions: Mapping[str, Any]) -> Tuple[Any, ...]: ...
    @property
    def observation_space(self) -> Any: ...
    @property
    def action_space(self) -> Any: ...
