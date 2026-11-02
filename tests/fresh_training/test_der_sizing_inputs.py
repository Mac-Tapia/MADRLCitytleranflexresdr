"""T2: PV, EV, BESS and load classes of the fresh campaign builder (iquitos_v2).

Owner decisions (2026-11-01, superseding the earlier roof x 0.63 rule): PV kWp and
BESS kWh come from the MicroGrids LP on pvlib ModelChain SAPM AC per kWp, with the
covered built area as an upper bound only; EV only as the B01 pilot; controlled
machines inside the bills; heat pumps calibrated with CityLearn's own COP.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import size_der_microgrids as sd  # noqa: E402
from buildingcsv_inputs import load_building_inventory  # noqa: E402

BUILDER = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')


def test_pv_bound_is_covered_area_and_capacity_comes_from_microgrids():
    inventory = load_building_inventory()
    module = {'Area': 2.0, 'Vmpo': 40.0, 'Impo': 10.0}
    bound = sd.roof_bound_kwp(inventory[6].area_techada_m2, module)
    assert bound == pytest.approx(int(inventory[6].area_techada_m2//2.0)*0.4)
    assert sd.round_pv(10.1, module, bound) == (25, pytest.approx(10.0))
    assert sd.round_pv(1e9, module, 4.0) == (10, pytest.approx(4.0))  # never above the bound
    assert "capacity_method='sandia-area'" not in BUILDER and 'AREA_UTIL_FACTOR' not in BUILDER
    assert 'sd.solve_microgrids(' in BUILDER and 'sd.prosumpy_check(' in BUILDER
    assert '_calc_solar_simple' not in BUILDER  # no silent linear fallback


def test_campaign_v2_der_chain_order():
    steps = ['scm.sync_controlled_machines(', 'dl.calibrate_building', 'size_der(out', 'ev.write_pilot(',
             'fsc.main()', 'clean_orphans(out']
    positions = [BUILDER.index(step) for step in steps]
    assert positions == sorted(positions)
    # The earlier mass-EV sizing and rule-based BESS are not part of the chain.
    assert 'ev.main()' not in BUILDER and 'sb.apply_results(' not in BUILDER
    assert 'machine_elec=machine_baseline(' in BUILDER
