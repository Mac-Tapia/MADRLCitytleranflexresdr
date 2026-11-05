"""Finite engineering inputs: preserve the original panel/tolerance result.

The scalar reference is deliberately bounded to small requests. Never rerun
the old 1-GW loop: its 636.644-second observation is preserved in general JUnit.
No dataset, LP solution or installed PV capacity is changed by this check.
"""
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/dataset'))
from size_der_microgrids import round_pv  # noqa: E402


def scalar_reference(pv_kwp_lp, module_kwp, roof_kwp):
    n = int(round(pv_kwp_lp/module_kwp))
    while n > 0 and n*module_kwp > roof_kwp + 1e-9:
        n -= 1
    return n, n*module_kwp


def main():
    rng = random.Random(20261102)
    cases = 0
    for module_watts in (200.0, 235.0, 400.0, 525.0):
        module = {'Vmpo': module_watts, 'Impo': 1.0}
        module_kwp = module_watts/1000.0
        for _ in range(1000):
            pv_kwp, roof = rng.uniform(0, 100), rng.uniform(0, 100)
            assert round_pv(pv_kwp, module, roof) == scalar_reference(pv_kwp, module_kwp, roof)
            cases += 1
        for panels in (0, 1, 9, 10, 25, 251):
            for offset in (-2e-9, -1e-9, -0.5e-9, 0.0, 0.5e-9):
                roof = max(0.0, panels*module_kwp+offset)
                assert round_pv(110.0, module, roof) == scalar_reference(110.0, module_kwp, roof)
                cases += 1
    extreme_module = {'Vmpo': 40.0, 'Impo': 10.0}
    assert round_pv(1.0000000000000004e16, extreme_module, 1e16) == scalar_reference(
        1.0000000000000004e16, 0.4, 1e16)
    cases += 1
    started = time.perf_counter()
    result = round_pv(1e9, {'Vmpo': 40.0, 'Impo': 10.0}, 4.0)
    seconds = time.perf_counter()-started
    assert result == (10, 4.0)
    report = {'scope': 'finite nonnegative engineering inputs; no dataset regeneration',
              'seed': 20261102, 'scalar_parity_cases': cases, 'all_equal': True,
              'oversized_request_kwp': 1e9, 'roof_kwp': 4.0, 'result': result,
              'oversized_call_seconds': seconds,
              'prior_case_seconds_in_general_junit': 636.644}
    target = ROOT/'data/maintenance/integracion/c20261101i01/I12/pv_parity.json'
    target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
