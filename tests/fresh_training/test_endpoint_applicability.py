"""A flat tariff has no inverse-price response target; never impute its KPI."""
import dataclasses
import json

import pytest

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
