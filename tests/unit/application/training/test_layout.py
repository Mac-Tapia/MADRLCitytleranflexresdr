from pathlib import Path

import pytest


@pytest.mark.parametrize('seed,folder', [(0, 'E1'), (7, 'E1_s7')])
def test_layout_preserves_run_paths_and_creates_artifact_directories(tmp_path, seed, folder):
    from uc3m.application.training.layout import (
        ensure_artifact_layout, job_run_relative_parts, resolve_job_run_dir,
    )

    assert job_run_relative_parts(' happo ', ' e1 ', seed) == Path('HAPPO') / folder
    run = resolve_job_run_dir(tmp_path, 'happo', 'e1', seed)
    layout = ensure_artifact_layout(run)
    assert run == tmp_path / 'HAPPO' / folder
    assert layout == {
        'run': run, 'data': run / 'data', 'checkpoints': run / 'checkpoints',
        'figures': run / 'figures', 'tables': run / 'figures' / 'tables',
    }
    assert all(path.is_dir() for path in layout.values())


def test_legacy_training_facade_delegates_layout(tmp_path):
    import importlib.util
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location(
        'training_layout_facade', root / 'CityLearn/scripts/citylearn_v3_training_common.py'
    )
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
    from uc3m.application.training import layout
    assert common.job_run_relative_parts('MASAC', 'E3', 2) == Path('MASAC/E3_s2')
    assert common.ensure_artifact_layout(tmp_path)['tables'] == tmp_path / 'figures/tables'
    assert common.normalize_algorithm_dir is layout.normalize_algorithm_dir
