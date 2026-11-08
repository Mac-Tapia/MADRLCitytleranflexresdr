"""SPEC-012 FR-012.1 to FR-012.5: repository hygiene checked on the Git index and branches."""
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL_NAMES = re.compile(r'codex|cursor|copilot', re.IGNORECASE)
# FR-012.1: folders those tools require, and records that may name them
TOOL_FOLDERS = ('.github/', '.claude/', '.cursor/', '.agents/', '.specify/')
RECORD_ROOTS = ('docs/', 'data/', 'tools/skills/', 'specs/', 'external/', 'CityLearn/', '.superpowers/')
ALLOWED_ROOT_FILES = {
    '.dockerignore', '.gitattributes', '.gitignore', '.gitmodules', 'AGENTS.md', 'CLAUDE.md', 'CityLearn', 'Dockerfile',
    'README.md', 'pyproject.toml', 'pyrightconfig.json', 'requirements.txt', 'uv.lock',
    # canonical thesis plan: the README and immutable audits cite this path
    'PT_TAPIA_ZAMBRANO_v6_Iquitos_2.docx',
}


def _git(*args):
    return subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()


def test_no_branch_carries_a_tool_name():
    branches = [b.strip().lstrip('* ') for b in _git('branch', '-a')]
    assert [b for b in branches if re.search(r'(^|/)(codex|cursor|copilot)/', b)] == []


def test_the_root_only_holds_project_files():
    root = {p for p in _git('ls-files') if '/' not in p}
    assert root <= ALLOWED_ROOT_FILES, sorted(root - ALLOWED_ROOT_FILES)


def test_no_temporary_is_tracked():
    tracked = _git('ls-files')
    pattern = re.compile(r'(^|/)(_tmp_[^/]*|~\$[^/]*|[^/]*\.tmp|\.codex_tmp)(/|$)')
    assert [p for p in tracked if pattern.search(p)] == []


def test_code_paths_carry_no_tool_name():
    paths = [p for p in _git('ls-files') if not p.startswith(TOOL_FOLDERS + RECORD_ROOTS)]
    assert [p for p in paths if TOOL_NAMES.search(p)] == []


def test_every_hygiene_entry_records_path_reason_and_origin():
    manifest = json.loads((REPO/'data/audits/repository_hygiene_manifest.json').read_text(encoding='utf-8'))
    assert manifest['entries']
    for entry in manifest['entries']:
        # what changed (a path, renamed paths or the removed git blobs) and why, under a requirement and a date
        assert entry.get('path') or entry.get('paths') or entry.get('git_blobs'), entry
        assert entry.get('reason') and entry.get('requirement') and entry.get('date'), entry
