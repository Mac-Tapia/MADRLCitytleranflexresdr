"""Contract of the CityLearn v3 tuple M_e = <N, S, {A_i}, P, r_e, {O_i}, Z, rho_0, gamma, H> (SPEC-016 FR-016.11).

Each check returns a list of violations (empty = the link holds), so a test can also feed a falsified input and see
the contract fail:

- ``term_violations``: every reward term belongs to an axis and to a thesis indicator of the KPI catalog that names
  it back; a defined term carries weight, a pending one carries 0;
- ``axis_violations``: every scenario axis has a primary KPI that the evaluation measures, and the E1/E2/E3 weights
  cover exactly those axes;
- ``action_violations``: every action of an agent is a piece of equipment of its building, and every controllable
  piece of equipment (D-V6-1: air conditioning, chargers and BESS) has its action, except the ones deferred by
  ``DEFERRED_ACTIONS`` (D-V6-51: air conditioning, no thermal dynamics model); no washing machine (D-V6-1);
- ``observation_violations``: every observation the reward reads is in the agent's observation O_i.
"""
from __future__ import annotations

from typing import Iterable, List, Mapping, Sequence

REWARD_AXIS_TO_CATALOG = {'flex': 'flexibility', 'carbon': 'co2_emissions', 'cost': 'energy_cost'}
# Observations the v3 reward reads (citylearn/v3/reward.py) that must be in O_i for a Markovian reward.
REWARD_OBSERVATIONS = ('hour', 'net_electricity_consumption', 'electricity_pricing', 'carbon_intensity',
                       'electrical_storage_soc')
BILL_OBSERVATIONS = ('bill_month_block_peak_kw', 'bill_in_peak_block', 'bill_demand_usd_kw_month')
CHARGER_PREFIX = 'electric_vehicle_storage_'
# Controllable equipment whose action is deferred by an owner decision, with that decision.
DEFERRED_ACTIONS = {'cooling_device': 'D-V6-51'}


def term_violations(terms: Mapping[str, tuple], subweights: Mapping[str, float], catalog: Mapping) -> List[str]:
    out = []
    indicators = {row['name']: row for row in catalog.get('thesis_indicators') or ()}
    named_back = {row.get('reward_term'): row['name'] for row in indicators.values() if row.get('reward_term')}
    for term, (axis, kpi, _source, status) in terms.items():
        if axis not in REWARD_AXIS_TO_CATALOG:
            out.append(f'{term}: axis {axis!r} is not a scenario axis')
            continue
        row = indicators.get(kpi)
        if row is None:
            out.append(f'{term}: KPI {kpi!r} is not a thesis indicator of the catalog')
        elif row.get('axis') != REWARD_AXIS_TO_CATALOG[axis]:
            out.append(f'{term}: KPI {kpi!r} is on axis {row.get("axis")!r}, the term on {axis!r}')
        elif row.get('reward_term') != term:
            out.append(f'{term}: KPI {kpi!r} names reward term {row.get("reward_term")!r}')
        weight = float(subweights.get(term, 0.0))
        if status == 'defined' and weight <= 0.0:
            out.append(f'{term}: defined but carries no weight')
        if status != 'defined' and weight != 0.0:
            out.append(f'{term}: {status} but weighted {weight}')
    for term, kpi in named_back.items():
        if term not in terms:
            out.append(f'KPI {kpi!r} names reward term {term!r}, which the reward does not have')
    return out


def axis_violations(catalog: Mapping, policies: Mapping) -> List[str]:
    out = []
    definitions = {row['name']: row for row in catalog.get('definitions') or ()}
    primaries = set(catalog.get('primary_endpoints') or ())
    axes = catalog.get('axes') or {}
    for axis in REWARD_AXIS_TO_CATALOG.values():
        measured = [k for k in axes.get(axis) or () if k in primaries and k in definitions]
        if not measured:
            out.append(f'axis {axis!r} has no primary KPI that the evaluation measures')
    for name in primaries - set(definitions):
        out.append(f'primary endpoint {name!r} has no definition')
    for scenario, policy in (policies.get('policies') or {}).items():
        weights = policy.get('weights') or {}
        if set(weights) != set(REWARD_AXIS_TO_CATALOG.values()):
            out.append(f'{scenario}: weights on {sorted(weights)}, the reward axes are '
                       f'{sorted(REWARD_AXIS_TO_CATALOG.values())}')
        elif abs(sum(float(v) for v in weights.values()) - 1.0) > 1e-9:
            out.append(f'{scenario}: weights sum {sum(weights.values())}')
    return out


def action_violations(agent: str, action_names: Sequence[str], *, chargers: Iterable[str], has_storage: bool,
                      has_cooling: bool, deferred: Mapping[str, str] = None) -> List[str]:
    out = []
    deferred = DEFERRED_ACTIONS if deferred is None else deferred
    chargers = set(chargers)
    seen_chargers = set()
    for name in action_names:
        if name == 'electrical_storage':
            if not has_storage:
                out.append(f'{agent}: action {name} without a BESS')
        elif name == 'cooling_device':
            if not has_cooling:
                out.append(f'{agent}: action {name} without air conditioning')
        elif name.startswith(CHARGER_PREFIX):
            charger = name[len(CHARGER_PREFIX):]
            if charger not in chargers:
                out.append(f'{agent}: action {name} is not a charger of the building')
            seen_chargers.add(charger)
        else:
            out.append(f'{agent}: action {name} is not air conditioning, a charger or the BESS (D-V6-1)')
    if has_storage and 'electrical_storage' not in action_names:
        out.append(f'{agent}: the BESS has no action')
    if has_cooling and 'cooling_device' not in action_names and 'cooling_device' not in deferred:
        out.append(f'{agent}: the air conditioning has no action (D-V6-1, FR-016.4)')
    for charger in sorted(chargers - seen_chargers):
        out.append(f'{agent}: charger {charger} has no action')
    return out


def observation_violations(agent: str, observation_names: Sequence[str], *, billed: bool) -> List[str]:
    required = REWARD_OBSERVATIONS + (BILL_OBSERVATIONS if billed else ())
    return [f'{agent}: the reward reads {name!r}, which is not in O_i' for name in required
            if name not in observation_names]
