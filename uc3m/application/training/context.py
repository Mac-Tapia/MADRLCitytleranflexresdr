"""Project boundary checks for Windows development and authorized Colab runtime."""
import os
import subprocess
from pathlib import Path


ORIGIN = 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git'


def validate_colab_context(root, git_root, origin):
    root = str(root).rstrip('/')
    if root != '/content/MADRLCitytleranflexresdr' or str(git_root).rstrip('/') != root or origin.strip() != ORIGIN:
        raise ValueError('Colab project context mismatch')


def verify_runtime_context(root: Path):
    root = Path(root).resolve()
    if os.name == 'nt':
        subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File',
                        str(root/'scripts/verify_project_context.ps1')], cwd=root, check=True)
    else:
        if str(root) != '/content/MADRLCitytleranflexresdr':
            raise ValueError('Only the authorized Colab project path is supported on Linux')
        top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=root, text=True).strip()
        origin = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=root, text=True).strip()
        validate_colab_context(root, top, origin)


def repository_revision(root):
    verify_runtime_context(root)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    submodules = {}
    for line in subprocess.check_output(['git', 'submodule', 'status'], cwd=root, text=True).splitlines():
        fields = line.strip().lstrip('+-').split()
        if len(fields) >= 2:
            submodules[fields[1]] = fields[0]
    return commit, submodules
