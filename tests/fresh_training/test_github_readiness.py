"""T13: package, workflows and candidate tree are reviewable on GitHub without weakening the local guard.

These are local checks. remote_verified stays false until a real Actions run of
the same commit is attached; nothing here pushes, merges or changes settings.
"""
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.quality.verify_ci_checkout import verify_ci_checkout
from tools.ops.audit_github_readiness import (MIB, audit_github_readiness, candidate_tree, declared_distributions,
                                              undeclared_runtime_imports)

REPO = Path(__file__).resolve().parents[2]
CI = REPO/'.github/workflows/ci.yml'
REQUIRED_CHECKS = {'quality-lint', 'quality-contracts', 'quality-package', 'quality-layout', 'quality-workflows'}


@pytest.fixture(scope='module')
def wheel(tmp_path_factory):
    out = tmp_path_factory.mktemp('wheel')
    subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation', '-q',
                    '-w', str(out), str(REPO)], check=True, capture_output=True, text=True, timeout=900)
    return next(out.glob('uc3m-*.whl'))


def _workflow():
    return yaml.safe_load(CI.read_text(encoding='utf-8'))


def test_flat_package_build_contains_only_declared_sources(wheel):
    names = zipfile.ZipFile(wheel).namelist()
    assert names and all(n.startswith(('uc3m/', 'uc3m-')) for n in names), [n for n in names if 'uc3m' not in n][:5]
    assert not [n for n in names if n.endswith(('.pt', '.pkl', '.ckpt', '.csv', '.zip', '.docx'))]


def test_installed_import_does_not_depend_on_repo_cwd(wheel, tmp_path):
    target = tmp_path/'site'
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '-q', '--target', str(target), str(wheel)],
                   check=True, capture_output=True, text=True, timeout=600)
    code = ('import sys; sys.path.insert(0, sys.argv[1]); import uc3m.domain.campaigns as c, '
            'uc3m.application.training.fresh_acceptance as a; print(c.__file__); print(a.__file__)')
    done = subprocess.run([sys.executable, '-I', '-c', code, str(target)], cwd=tmp_path,
                          capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-2000:]
    files = done.stdout.splitlines()
    assert len(files) == 2 and all(Path(f).resolve().is_relative_to(target.resolve()) for f in files), files


def test_explicit_config_is_portable():
    for path in [*REPO.glob('configs/**/*.yaml'), REPO/'governance/repository_layout.yaml']:
        text = path.read_text(encoding='utf-8')
        for marker in ('D:/', 'D:\\', 'C:\\', 'C:/', '/content/', 'drive/MyDrive'):
            assert marker not in text, f'{path.relative_to(REPO)} holds a machine path {marker!r}'


def test_declared_dependencies_cover_runtime_imports(tmp_path):
    missing = undeclared_runtime_imports(REPO)
    assert not missing, f'imports without a declared distribution: {missing}'
    # The rule itself: an unguarded import of an undeclared package is reported; a guarded one is optional.
    (tmp_path/'uc3m').mkdir()
    (tmp_path/'pyproject.toml').write_text('[project]\nname="x"\ndependencies=["numpy"]\n', encoding='utf-8')
    (tmp_path/'uc3m/a.py').write_text('import numpy\nimport yaml\ntry:\n    import boto3\nexcept ImportError:\n'
                                      '    boto3 = None\n', encoding='utf-8')
    assert undeclared_runtime_imports(tmp_path) == {'yaml': 'uc3m/a.py'}
    assert {'citylearn', 'harl', 'marllib'} <= declared_distributions(REPO/'pyproject.toml')


def test_workflow_checks_are_unique_and_paths_exist():
    jobs = _workflow()['jobs']
    names = [job.get('name') for job in jobs.values()]
    assert len(names) == len(set(names)) and REQUIRED_CHECKS <= set(names)
    for job in jobs.values():
        for step in job.get('steps', []):
            for token in str(step.get('run', '')).replace('\\', ' ').split():
                if token.startswith(('tests/', 'scripts/', 'tools/')):
                    assert (REPO/token).exists(), f'workflow references missing {token}'


def test_actions_pin_full_commit_and_read_only_permissions():
    workflow = _workflow()
    assert workflow.get('permissions') == {'contents': 'read'}
    for name, job in workflow['jobs'].items():
        assert int(job.get('timeout-minutes', 0)) > 0, name
        assert not set((job.get('permissions') or {}).values()) - {'read', 'none'}, name
        for step in job.get('steps', []):
            uses = step.get('uses')
            if uses:
                ref = uses.split('@', 1)[1].split()[0]
                assert len(ref) == 40 and all(c in '0123456789abcdef' for c in ref), uses
            if uses and uses.startswith('actions/checkout@'):
                assert step.get('with', {}).get('persist-credentials') is False, name


def test_untrusted_pr_has_no_write_or_secrets():
    text = CI.read_text(encoding='utf-8')
    triggers = _workflow().get(True) or _workflow().get('on')      # PyYAML reads the key `on` as True
    assert 'pull_request_target' not in (triggers or {})
    assert 'secrets.' not in text and 'github.event.pull_request' not in text
    # The local root guard is not faked on a hosted runner, directly or through the foundation gate.
    assert 'verify_project_context.ps1' not in text and 'run_foundation_gates.ps1' not in text


def test_generated_checkpoints_not_in_candidate_tree():
    tree = candidate_tree(REPO)
    generated = [p for p in tree if p.endswith(('.pt', '.pkl', '.ckpt', '.pth'))
                 or (p.startswith(('outputs/', 'data/maintenance/dataset_builds/')) and not p.endswith('README.md'))
                 or (p.startswith('data/campaigns/') and p.count('/') > 3)]
    assert not generated, generated[:10]


def test_github_blob_size_limits_are_mib(tmp_path):
    assert MIB == 1024*1024
    (tmp_path/'big.bin').write_bytes(b'0'*(50*MIB + 1))
    report = audit_github_readiness(tmp_path, candidate=['big.bin'])
    assert report['large_files_over_50_mib'] == ['big.bin'] and not report['blocked_files_over_100_mib']
    real = audit_github_readiness(REPO)
    assert not real['blocked_files_over_100_mib'], real['blocked_files_over_100_mib']


def test_unrun_workflow_cannot_claim_remote_acceptance():
    report = audit_github_readiness(REPO)
    assert report['remote_verified'] is False and report['status_remote'] == 'pending_remote'
    assert report['workflow_run_url'] is None and report['scientific_acceptance'] is False
    assert set(report['required_checks']) == REQUIRED_CHECKS


def test_local_training_guard_remains_strict(tmp_path):
    guard = (REPO/'scripts/verify_project_context.ps1').read_text(encoding='utf-8')
    assert 'D:/MADRLCitytleranflexresdr' in guard and 'Mac-Tapia/MADRLCitytleranflexresdr' in guard
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True, text=True).stdout.strip()
    assert verify_ci_checkout(REPO, 'Mac-Tapia/MADRLCitytleranflexresdr', head).ok
    assert not verify_ci_checkout(REPO, 'someone/fork', head).ok
    assert not verify_ci_checkout(REPO, 'Mac-Tapia/MADRLCitytleranflexresdr', '0'*40).ok
    assert not verify_ci_checkout(tmp_path, 'Mac-Tapia/MADRLCitytleranflexresdr', head).ok
