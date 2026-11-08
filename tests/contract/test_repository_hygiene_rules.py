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


# FR-012.4, owner decision 2026-11-08: no duplicate or obsolete file stays, and nothing active points at one.
RETIRED_TOOLS = (
    'tools/eval/kpi_rankings.py',
    'tools/eval/select_best_madrl_district_building.py',
    'tools/thesis/patch_cap5_rankings.py',
    'tools/thesis/update_word_quantitative_50episodes.py',
    'tools/training/prune_artifacts.ps1',
)
RETIRED_DOCUMENTS = (
    'docs/analisis_reorganizacion_tools_dataset.md',
    'docs/analisis_scripts_vs_tools_tesis.md',
    'docs/analisis_tesis_adenda.md',
    'docs/architecture/dataset.pdf',
    'docs/architecture/dataset_construction_pipeline.md',
    'docs/architecture/entrenamiento.md',
    'docs/architecture/entrenamiento.pdf',
    'docs/architecture/operacion.md',
    'docs/architecture/operacion.pdf',
    'docs/colab.md',
    'docs/colab_checklist.md',
    'docs/estrategia.md',
    'docs/guia_tesis.md',
    'docs/history/README_pre_integracion_20261101.txt',
    'docs/history/workflow_manifest_pre_integracion_20261101.json.txt',
)
# Records keep the names they had (governance rename maps, plans, audits); tests name them to forbid them.
ACTIVE_SURFACES = ('tools', 'scripts', 'uc3m', 'README.md', 'docs/00_INDEX.md', 'docs/workflow_manifest.json',
                   'docs/instalacion.md', 'docs/architecture/runbook.md', 'docs/architecture/defensa.md',
                   'docs/architecture/flujo.md', 'docs/plans/modulo8_campana.md')
TEXT_SUFFIXES = ('.py', '.ps1', '.md', '.json', '.yaml', '.yml', '.txt')


def test_retired_tools_and_documents_stay_out_of_the_tree():
    retired = set(RETIRED_TOOLS + RETIRED_DOCUMENTS)
    assert sorted(retired & set(_git('ls-files'))) == []


def test_no_active_surface_points_at_a_retired_file():
    needles = [Path(path).name for path in RETIRED_TOOLS] + list(RETIRED_DOCUMENTS)
    offenders = []
    for path in _git('ls-files', '--', *ACTIVE_SURFACES):
        target = REPO/path
        if path.startswith('tools/skills/') or not path.endswith(TEXT_SUFFIXES) or not target.is_file():
            continue
        text = target.read_text(encoding='utf-8', errors='ignore')
        offenders += [(path, needle) for needle in needles if needle in text]
    assert offenders == []


def test_the_word_pipeline_has_no_retired_quantitative_step():
    source = (REPO/'tools/thesis/run_thesis_word_pipeline.py').read_text(encoding='utf-8')
    assert '--with-quantitative' not in source
