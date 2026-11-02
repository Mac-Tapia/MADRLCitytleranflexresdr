"""Owner decision: training is launched only through the fresh campaign CLI.

The retired launchers are listed once in governance/repository_layout.yaml.
This contract checks that they are gone, that the CLI rejects the old flags,
and that no other file of the parent can start a native trainer.
"""
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
LAYOUT = yaml.safe_load((REPO/'governance/repository_layout.yaml').read_text(encoding='utf-8'))
LAUNCH = LAYOUT['launch']
TRAINER = re.compile(r'(train|launch)_citylearn_v3_[a-z0-9_]+\.(py|ps1)')
STARTS_PROCESS = re.compile(r'subprocess|Popen|check_call|os\.system|Start-Process|^\s*!python|%run')
SCANNED = ('scripts', 'tools', 'uc3m', 'examples_madrl_v3', 'deploy', '.vscode')
SUFFIXES = {'.py', '.ps1', '.bat', '.cmd', '.sh', '.ipynb', '.json', '.yml', '.yaml', '.tf'}


def test_retired_launchers_are_absent():
    present = [path for path in LAUNCH['retired'] if (REPO/path).exists()]
    assert present == []


def test_legacy_training_module_is_gone():
    # uc3m.train trained with random actions and could announce completion (H-04).
    assert LAUNCH['canonical'] == 'uc3m.application.training.cli'
    with pytest.raises(ModuleNotFoundError):
        __import__('uc3m.train')


def test_cli_rejects_the_legacy_flags():
    from uc3m.application.training import cli
    with pytest.raises(SystemExit):
        cli.main(['--algorithm', 'HAPPO', '--scenario', 'E1', '--schema', 'x.json'])
    with pytest.raises(SystemExit):
        cli.main(['--stage', 'pilot'])  # a stage always names its campaign config


def _pending(relative):
    return any(relative == p or relative.startswith(p.rstrip('/') + '/')
               for p in LAUNCH['clients_to_reconnect'])


def _code_lines(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    comment = '#' if path.suffix in {'.py', '.ps1', '.sh', '.yml', '.yaml'} else None
    return [line for line in text.splitlines() if not (comment and line.lstrip().startswith(comment))]


def test_no_other_parent_file_starts_a_native_trainer():
    allowed = set(LAUNCH['native_bridges']) | set(LAUNCH['mentions_only'])
    offenders = []
    for folder in SCANNED:
        for path in (REPO/folder).rglob('*'):
            relative = path.relative_to(REPO).as_posix()
            if (not path.is_file() or path.suffix not in SUFFIXES or '__pycache__' in path.parts
                    or relative in allowed or _pending(relative)):
                continue
            lines = _code_lines(path)
            if any(TRAINER.search(line) for line in lines) and any(STARTS_PROCESS.search(line) for line in lines):
                offenders.append(relative)
    assert offenders == []


def test_registered_exceptions_have_reasons_and_exist():
    entries = {**LAUNCH['native_bridges'], **LAUNCH['mentions_only']}
    for path, reason in entries.items():
        assert (REPO/path).is_file(), path
        assert isinstance(reason, str) and len(reason) > 20, path
    for path, reason in LAUNCH['clients_to_reconnect'].items():
        assert (REPO/path).exists(), f'kept client {path} must not be deleted, only reconnected'
        assert reason, path


def test_packaging_exposes_no_legacy_entrypoint():
    text = (REPO/'pyproject.toml').read_text(encoding='utf-8')
    assert 'uc3m.train' not in text and 'uc3m/train.py' not in text
