"""Contract test: objective weights must come from a single canonical source."""
import re
import subprocess
from pathlib import Path

CANONICAL_SOURCES = {
    'uc3m/domain/objectives.py',
    'configs/objective_policies.yaml',
}
WEIGHT_PATTERN = re.compile(
    r'0\.60.*0\.15.*0\.25|0\.25.*0\.60.*0\.15|0\.15.*0\.25.*0\.60'
    r'|0\.60.*0\.25.*0\.15|0\.15.*0\.60.*0\.25|0\.25.*0\.15.*0\.60'
)
SCAN_EXTENSIONS = {'.py', '.yaml', '.yml', '.json', '.toml', '.cfg', '.ini'}
EXCLUDED_DIRS = {'tests', '.superpowers', '.specify', 'external', '__pycache__', 'outputs', 'agent-skills'}
GENERATOR_ALLOWLIST = {
    'tools/figures/generate_architecture_pngs.py',
    'tools/thesis/_patch_notebook_hypothesis_demo.py',
    'tools/thesis/_patch_notebook_hypothesis_pipeline.py',
    'tools/thesis/generate_borrador_tesis_docx.py',
}
MAX_FILE_SIZE = 512_000


def _find_text_files(root: Path):
    """Use git ls-files for speed, fall back to glob for untracked."""
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
            capture_output=True, text=True, cwd=root, timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                yield root / line
            return
    except Exception:
        pass
    for ext in SCAN_EXTENSIONS:
        yield from root.glob(f'**/*{ext}')


def test_no_hardcoded_weights_outside_canonical():
    root = Path(__file__).resolve().parents[2]
    violations = []
    for path in _find_text_files(root):
        if path.suffix not in SCAN_EXTENSIONS:
            continue
        relative = path.relative_to(root).as_posix()
        if relative in CANONICAL_SOURCES or relative in GENERATOR_ALLOWLIST:
            continue
        parts = set(Path(relative).parts)
        if parts & EXCLUDED_DIRS:
            continue
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
            if size > MAX_FILE_SIZE or size == 0:
                continue
            text = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if WEIGHT_PATTERN.search(text):
            violations.append(relative)
    assert not violations, (
        f"Hardcoded weights found outside canonical sources in {len(violations)} files:\n"
        + '\n'.join(f'  - {v}' for v in sorted(violations))
    )


def test_generator_weights_match_canonical():
    """Allowlisted generators must embed the canonical weight values (0.60, 0.25, 0.15)."""
    import sys
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root.as_posix()))
    from uc3m.domain.objectives import canonical_objective_policies

    canonical = canonical_objective_policies()
    canonical_values = set()
    for pol in canonical.values():
        for w in pol.weights.values():
            canonical_values.add(round(w, 2))

    for rel in sorted(GENERATOR_ALLOWLIST):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        found_floats = set(float(x) for x in re.findall(r'0\.\d+', text) if float(x) in canonical_values)
        assert found_floats == canonical_values, (
            f"{rel}: expected canonical values {canonical_values} but found {found_floats}"
        )
