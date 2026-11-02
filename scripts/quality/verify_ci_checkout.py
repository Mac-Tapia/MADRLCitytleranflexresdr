"""Identity of a hosted CI checkout: repository and commit, nothing else (T13).

    python scripts/quality/verify_ci_checkout.py --repository Mac-Tapia/MADRLCitytleranflexresdr --commit SHA

This replaces, on a hosted runner, the local root guard
(scripts/verify_project_context.ps1), which stays strict for local work and
native training. Passing it authorizes running the portable CPU contracts of
that commit; it does not authorize training or project changes elsewhere.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    repository: str
    commit: str
    reasons: Tuple[str, ...]


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, timeout=60)
    return done.stdout.strip() if done.returncode == 0 else ''


def _slug(url: str) -> str:
    url = url.strip().rstrip('/').removesuffix('.git').replace(':', '/')
    return '/'.join(url.split('/')[-2:]).lower()


def verify_ci_checkout(root: Path, expected_repository: str, expected_commit: str) -> ValidationResult:
    root = Path(root)
    reasons = []
    top = _git(root, 'rev-parse', '--show-toplevel')
    if not top or Path(top).resolve() != root.resolve():
        return ValidationResult(False, '', '', ('not_the_checkout_root',))
    repository = os.environ.get('GITHUB_REPOSITORY') or _slug(_git(root, 'remote', 'get-url', 'origin'))
    commit = _git(root, 'rev-parse', 'HEAD')
    if repository.lower() != expected_repository.lower():
        reasons.append(f'repository_mismatch:{repository}')
    if commit != expected_commit:
        reasons.append(f'commit_mismatch:{commit}')
    return ValidationResult(not reasons, repository, commit, tuple(reasons))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--repository', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    result = verify_ci_checkout(args.root, args.repository, args.commit)
    print(json.dumps(result.__dict__, default=list))
    return 0 if result.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
