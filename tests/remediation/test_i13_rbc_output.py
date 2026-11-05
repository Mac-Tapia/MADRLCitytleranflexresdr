"""District KPI names survive actual CityLearn evaluate rows."""
from pathlib import Path

from uc3m.adapters.citylearn.rbc_baseline import run_rbc_baseline


def test_rbc_retains_distinct_named_district_kpis():
    schema = Path.cwd()/'data/campaigns/iquitos_v1/splits/validation_2024/schema.json'
    result = run_rbc_baseline(schema, episode_time_steps=24)
    assert 'cost_total' in result and 'carbon_emissions_total' in result
    assert 'District' not in result
    assert result['_meta']['kpi_level'] == 'district'
