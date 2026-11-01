from pathlib import Path

import pytest

from uc3m.application.configuration import load_scenario_catalog
from uc3m.domain.experiments import ExperimentSpec


@pytest.mark.parametrize('algorithm', ['HAPPO', 'MASAC', 'MATD3', 'MAAC'])
@pytest.mark.parametrize('scenario', ['E1', 'E2', 'E3'])
def test_native_backend_command_preserves_scientific_inputs(tmp_path, algorithm, scenario):
    from uc3m.adapters.algorithms.native import NativeBackend
    root = Path(__file__).resolve().parents[3]
    spec = ExperimentSpec(algorithm, load_scenario_catalog(root/'configs/scenarios.yaml')[scenario],
                          3, 'a'*64, 'b'*40, {}, 2)
    backend = NativeBackend(root, Path('schema.json'), episode_time_steps=8)
    command = backend.command(spec, tmp_path, resume=False)
    assert command[1].endswith('train_citylearn_v3_' + algorithm.lower() + '.py')
    assert command[command.index('--scenario') + 1] == scenario
    assert command[command.index('--seed') + 1] == '3'
    assert command[command.index('--episodes') + 1] == '2'
    assert '--no-resume' in command
    assert Path(command[command.index('--output-dir') + 1]) == tmp_path / (scenario + '_s3')
