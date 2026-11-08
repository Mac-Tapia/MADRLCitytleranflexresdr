"""SPEC-015 D-M3-8: on iquitos_v6 MASAC searches only rnn_hidden_dim 128 (the 256 candidate needs 105 GiB of VRAM,
above an 80 GB GPU), keeping its author's native capacity; the other three keep the shared grid."""
from pathlib import Path

from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
GRID = CONFIG['hyperparameter_grid']


def _all_candidates():
    import itertools
    return {f'c{i}': dict(zip(fc.HYPERPARAMETERS, v)) for i, v in
            enumerate(itertools.product(*(GRID[n] for n in fc.HYPERPARAMETERS)), 1)}


def test_masac_searches_only_hidden_dimension_128_and_keeps_the_labels():
    candidates = _all_candidates()
    masac = fc.algorithm_candidates('MASAC', candidates, CONFIG)
    assert masac and {h['hidden_dimension'] for h in masac.values()} == {128}
    assert all(candidates[label] == hyper for label, hyper in masac.items())        # labels c1.. unchanged
    assert len(masac) == len(candidates)//len(GRID['hidden_dimension'])
    for name in ('HAPPO', 'MATD3', 'MAAC'):
        assert fc.algorithm_candidates(name, candidates, CONFIG) == candidates


def test_the_masac_reservation_covers_only_its_searched_candidates():
    row = CONFIG['algorithms']['MASAC']
    assert row['hyperparameter_grid_override'] == {'hidden_dimension': [128]}
    assert set(row['runtime_requirements']['min_vram_gib_by_rnn_hidden_dim']) == {128}
    assert any('D-M3-8' in text for text in row['declared_limitations'])
