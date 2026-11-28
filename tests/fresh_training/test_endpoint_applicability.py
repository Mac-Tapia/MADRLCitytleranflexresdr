"""A flat tariff has no inverse-price response target; never impute its KPI."""
import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from tests.fresh_training.test_seed_statistics import _complete_table
from uc3m.application.evaluation import fresh_analysis as fa
from uc3m.application.evaluation.endpoint_applicability import (
    classify_endpoint_applicability, not_applicable_endpoints)
from uc3m.domain.campaigns import canonical_hash
from uc3m.domain.scenarios import TariffPolicy


def test_preregistered_structural_na_stays_visible_without_becoming_a_missing_replica():
    rows = _complete_table()
    endpoint = ('E3', 'price_signal_deviation')
    for row in rows:
        if (row['scenario'], row['endpoint']) == endpoint:
            row['value'] = None
    unqualified = fa.analyze_campaign(fa.SeedTable.from_rows(rows), fa.FrozenProtocol.default())
    assert not unqualified.decisions['scientifically_complete']
    protocol = dataclasses.replace(fa.FrozenProtocol.default(), not_applicable_endpoints=(endpoint,))
    report = fa.analyze_campaign(fa.SeedTable.from_rows(rows), protocol)
    assert report.decisions['scientifically_complete']
    assert report.coverage['not_applicable_endpoints'] == [list(endpoint)]
    assert not any((r['scenario'], r['endpoint']) == endpoint for r in report.seed_statistics)


def test_na_is_limited_to_a_nonconfirmatory_endpoint_and_must_have_no_numeric_result():
    table = fa.SeedTable.from_rows(_complete_table())
    with pytest.raises(ValueError):
        fa.analyze_campaign(table, dataclasses.replace(fa.FrozenProtocol.default(),
            not_applicable_endpoints=(('E3', 'energy_cost'),)))
    with pytest.raises(ValueError):
        fa.analyze_campaign(table, dataclasses.replace(fa.FrozenProtocol.default(),
            not_applicable_endpoints=(('E3', 'price_signal_deviation'),)))


def test_tariff_applicability_is_derived_before_analysis_and_bound_by_hash(tmp_path):
    dataset = tmp_path/'dataset'
    splits = []
    for name in ('train_2023', 'validation_2024', 'test_2025'):
        folder = dataset/'splits'/name
        folder.mkdir(parents=True)
        (folder/'schema.json').write_text(json.dumps({'buildings': {'B1': {'pricing': 'pricing.csv'}}}), encoding='utf-8')
        (folder/'pricing.csv').write_text('electricity_pricing\n0.1\n0.1\n0.1\n', encoding='utf-8')
        splits.append({'split_id': name, 'schema_path': name+'/schema.json', 'rows': 3})
    (dataset/'split_manifest.json').write_text(json.dumps({'splits': splits}), encoding='utf-8')
    declaration = classify_endpoint_applicability(dataset, tmp_path)
    manifest = {'endpoint_applicability': declaration,
                'identity': {'endpoint_applicability_sha256': canonical_hash(declaration)}}
    assert not_applicable_endpoints(manifest) == (('E3', 'price_signal_deviation'),)
    (dataset/'splits/test_2025/pricing.csv').write_text('electricity_pricing\n0.1\n0.2\n0.1\n', encoding='utf-8')
    varied = classify_endpoint_applicability(dataset, tmp_path)
    assert varied['not_applicable_endpoints'] == []
    transformed = classify_endpoint_applicability(dataset, tmp_path, tariff_policy=TariffPolicy('base', 'flat', 1.0))
    assert transformed['not_applicable_endpoints'] == [['E3', 'price_signal_deviation']]
    declaration['not_applicable_endpoints'] = []
    with pytest.raises(ValueError, match='frozen'):
        not_applicable_endpoints(manifest)


def test_recorded_building_tariffs_survive_scenario_setup(monkeypatch):
    from citylearn.scenario_manager import ScenarioManager
    from citylearn.v3 import objectives
    from uc3m.adapters.citylearn.tariff import recorded_tariff

    repo = Path(__file__).resolve().parents[2]
    campaign = yaml.safe_load((repo/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
    catalog = repo/campaign['scenario_catalog']
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(catalog))
    original = ScenarioManager.apply_scenario_modifications
    for scenario in campaign['scenarios']:
        manager = ScenarioManager()
        prices = [np.array([0.1, 0.1, 0.2]), np.array([0.12, 0.12, 0.22])]
        env = SimpleNamespace(buildings=[SimpleNamespace(pricing=SimpleNamespace(
            _electricity_pricing=price.copy(), electricity_pricing=price.copy(),
        )) for price in prices])
        with recorded_tariff(catalog, scenario):
            manager.select_scenario(scenario)
            manager.apply_scenario_modifications(env)
            for building, expected in zip(env.buildings, prices):
                np.testing.assert_array_equal(building.pricing._electricity_pricing, expected)
            assert objectives._district_price_signal(env, 3) is None
        assert ScenarioManager.apply_scenario_modifications is original


def test_recorded_tariff_applicability_uses_a_shared_variable_series(tmp_path):
    dataset = tmp_path/'dataset'
    splits = []
    for name in ('train_2023', 'validation_2024', 'test_2025'):
        folder = dataset/'splits'/name
        folder.mkdir(parents=True)
        buildings = {'B1': {'pricing': 'a.csv'}, 'B2': {'pricing': 'b.csv'}}
        (folder/'schema.json').write_text(json.dumps({'buildings': buildings}), encoding='utf-8')
        for file, values in [('a.csv', '0.1\n0.1\n0.2'), ('b.csv', '0.1\n0.1\n0.2')]:
            (folder/file).write_text(f'electricity_pricing\n{values}\n', encoding='utf-8')
        if name == 'test_2025':
            # Same range, different time ordering. The district does not have one tariff.
            (folder/'b.csv').write_text('electricity_pricing\n0.2\n0.1\n0.1\n', encoding='utf-8')
        splits.append({'split_id': name, 'schema_path': f'{name}/schema.json', 'rows': 3})
    (dataset/'split_manifest.json').write_text(json.dumps({'splits': splits}), encoding='utf-8')
    declaration = classify_endpoint_applicability(
        dataset, tmp_path, tariff_policy=TariffPolicy('billed', 'recorded', 1.0),
    )
    manifest = {'endpoint_applicability': declaration,
                'identity': {'endpoint_applicability_sha256': canonical_hash(declaration)}}
    assert not_applicable_endpoints(manifest, split='validation_2024') == ()
    assert not_applicable_endpoints(manifest, split='test_2025') == (('E3', 'price_signal_deviation'),)
