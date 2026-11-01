import pytest


def test_resource_budget_never_requests_six_jobs_on_small_runtime():
    from uc3m.application.training.colab import resource_budget
    small = resource_budget(cpus=2, ram_gib=12, vram_gib=15)
    assert small['max_workers'] == 1
    assert small['cuda_fraction'] <= 0.85
    large = resource_budget(cpus=24, ram_gib=160, vram_gib=80)
    assert large['max_workers'] == 6
    assert large['max_workers'] * large['cuda_fraction'] <= .90


def test_colab_context_rejects_other_repository():
    from uc3m.application.training.context import validate_colab_context
    validate_colab_context('/content/MADRLCitytleranflexresdr', '/content/MADRLCitytleranflexresdr',
                            'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git')
    with pytest.raises(ValueError):
        validate_colab_context('/content/other', '/content/other', 'https://github.com/example/other.git')


def test_backend_options_change_experiment_identity_and_cannot_override_scenario():
    from dataclasses import replace
    from pathlib import Path
    from uc3m.domain.experiments import ExperimentSpec
    from uc3m.application.configuration import load_scenario_catalog
    root = Path(__file__).resolve().parents[4]
    spec = ExperimentSpec('HAPPO', load_scenario_catalog(root/'configs/scenarios.yaml')['E1'], 0, 'a'*64, 'b'*40, {}, 2)
    assert replace(spec, backend_args=('--cuda',)).fingerprint() != spec.fingerprint()
    with pytest.raises(ValueError, match='protected'):
        replace(spec, backend_args=('--scenario', 'E3'))


def test_original_colab_builder_supplies_twelve_modular_jobs(tmp_path):
    from pathlib import Path
    from uc3m.application.training.colab import original_jobs, resource_budget
    from uc3m.application.configuration import load_scenario_catalog
    from uc3m.domain.experiments import ExperimentSpec
    root = Path(__file__).resolve().parents[4]
    budget = resource_budget(cpus=24, ram_gib=160, vram_gib=80)
    jobs = original_jobs(root, root/'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json',
                         tmp_path, 50, 8760, 0, budget)
    assert len(jobs) == 12
    catalog = load_scenario_catalog(root/'configs/scenarios.yaml')
    for job in jobs:
        spec = ExperimentSpec(job['name'].upper(), catalog[job['scenario']], 0,
            'a'*64, 'b'*40, {}, 50, backend_args=job['backend_args'])
        assert '--cuda' in spec.backend_args
        assert spec.backend_args[spec.backend_args.index('--cuda-memory-fraction')+1] == str(budget['cuda_fraction'])
