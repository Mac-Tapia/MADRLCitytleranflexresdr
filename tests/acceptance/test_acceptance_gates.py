"""Acceptance gates verifying constitutional flow artifacts exist and are valid."""
from pathlib import Path
from typing import Protocol

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_simulator_port_is_protocol():
    from uc3m.ports.simulator import SimulatorPort
    assert issubclass(SimulatorPort, Protocol)
    assert hasattr(SimulatorPort, 'reset')
    assert hasattr(SimulatorPort, 'step')


def test_citylearn_objectives_adapter_importable():
    from uc3m.adapters.citylearn.objectives import project_reward_weights
    assert callable(project_reward_weights)


def test_training_report_builder_produces_structured_kpis(tmp_path):
    from uc3m.application.evaluation.training_report import TrainingReportBuilder
    builder = TrainingReportBuilder()
    payload = {
        'algorithm': 'HAPPO',
        'scenario': 'E1',
        'citylearn_v3_report': {
            'all_values': {'electricity_consumption': 0.95, 'cost_total': 1.02},
        },
    }
    report = builder.build(payload)
    assert report['algorithm'] == 'HAPPO'
    assert report['scenario'] == 'E1'
    assert report['kpi_status'] == 'finite'
    assert isinstance(report['kpi_rows'], list)
    assert len(report['kpi_rows']) == 2
    assert report['scientific_acceptance'] is False


def test_adr_simulator_port_exists():
    path = ROOT / 'docs' / 'decisions' / 'ADR-SIMULATOR-PORT-DEFERRED.md'
    assert path.is_file(), "ADR for SimulatorPort deferred integration missing"
    content = path.read_text(encoding='utf-8')
    assert 'SimulatorPort' in content
    assert 'Deferred' in content or 'deferred' in content


def test_spec_folders_all_present():
    from tests.contract.test_spec_kit_consistency import (
        EXPECTED_SPECS, REQUIRED_FILES, PROJECT_ROOT,
    )
    specs_root = PROJECT_ROOT / 'specs'
    for name in EXPECTED_SPECS:
        for req in REQUIRED_FILES:
            assert (specs_root / name / req).is_file()
