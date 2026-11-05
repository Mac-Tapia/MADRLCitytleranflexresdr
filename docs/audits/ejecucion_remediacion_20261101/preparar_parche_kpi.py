"""Propose/test the terminal billing bound without editing CityLearn."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'CityLearn'))
import citylearn.internal.kpi as original_module  # noqa: E402

relative = 'CityLearn/citylearn/internal/kpi.py'
source = (ROOT/relative).read_text(encoding='utf-8')
old = "        final_t = int(max(getattr(env, 'time_step', 0), 0))\n"
new = old + "        final_t = min(final_t, int(getattr(env, 'time_steps', final_t + 1)) - 1)\n"
assert source.count(old) == 1
assert new not in source, 'Patch already applied: preserve the original reviewed proposal/preflight.'
candidate = source.replace(old, new)
compile(candidate, relative, 'exec')
diff = ''.join(difflib.unified_diff(source.splitlines(True), candidate.splitlines(True),
                                 fromfile='a/'+relative, tofile='b/'+relative))
(OUT/'proposed_citylearn_kpi_terminal.patch').write_text(diff, encoding='utf-8')
scope = dict(vars(original_module))
exec(compile(candidate, relative, 'exec'), scope)
fixed_class = scope['CityLearnKPIService']
rows = []
for horizon in (24, 48):
    buildings = [SimpleNamespace(name=name, net_electricity_consumption=np.ones(horizon),
                 pricing=SimpleNamespace(electricity_pricing=np.full(horizon, price)))
                 for name, price in [('A', 0.1), ('B', 0.2)]]
    env = SimpleNamespace(buildings=buildings, time_step=horizon, time_steps=horizon)
    conditions = {b.name: SimpleNamespace(value='') for b in buildings}
    try:
        original_module.CityLearnKPIService(env)._condition_settled_cost_totals(condition_by_building=conditions)
    except IndexError:
        original_rejected = True
    else:
        raise AssertionError('Original terminal overrun did not reproduce')
    totals, district = fixed_class(env)._condition_settled_cost_totals(condition_by_building=conditions)
    np.testing.assert_allclose([totals['A'], totals['B'], district],
                               [0.1*horizon, 0.2*horizon, 0.3*horizon])
    env.time_step = horizon//2
    assert original_module.CityLearnKPIService(env)._condition_settled_cost_totals(
        condition_by_building=conditions) == fixed_class(env)._condition_settled_cost_totals(
            condition_by_building=conditions)
    env.time_step = horizon
    buildings[0].pricing.electricity_pricing = np.full(horizon-1, 0.1)
    try:
        fixed_class(env)._condition_settled_cost_totals(condition_by_building=conditions)
    except IndexError:
        malformed_prices_still_rejected = True
    else:
        raise AssertionError('Candidate silently accepted a short pricing vector')
    rows.append({'horizon': horizon, 'original_terminal_rejected': original_rejected,
                 'candidate_terminal_total': district, 'expected_total': 0.3*horizon,
                 'intermediate_behavior_equal': True,
                 'short_pricing_still_rejected': malformed_prices_still_rejected})
report = {'target': relative, 'applied': False, 'candidate_compiles': True,
    'scope': 'analytical synthetic settlement probe, not native annual acceptance',
    'before_sha256_lf': hashlib.sha256(source.encode('utf-8')).hexdigest(),
    'after_sha256_lf': hashlib.sha256(candidate.encode('utf-8')).hexdigest(), 'cases': rows}
(OUT/'citylearn_kpi_patch_preflight.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
