from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_spec_000_has_consistent_constitution_plan_and_tasks() -> None:
    constitution = (PROJECT_ROOT / ".specify/memory/constitution.md").read_text(
        encoding="utf-8"
    )
    spec = (PROJECT_ROOT / "specs/000-foundation/spec.md").read_text(encoding="utf-8")
    plan = (PROJECT_ROOT / "specs/000-foundation/plan.md").read_text(encoding="utf-8")
    tasks = (PROJECT_ROOT / "specs/000-foundation/tasks.md").read_text(encoding="utf-8")

    principle_titles = (
        "Código abierto verificable",
        "Local primero",
        "Dependencias externas aisladas",
        "Una decisión, una fuente",
        "Recompensa no equivale a aceptación",
        "Resultados históricos inmutables",
        "Fallo cerrado",
        "Pruebas proporcionales al riesgo",
        "Sin secretos en el repositorio",
        "Especificación antes del cambio",
    )
    for index, title in enumerate(principle_titles, start=1):
        assert f"{index}. **{title}:**" in constitution

    for document in (spec, plan, tasks):
        assert "SPEC-000" in document
        assert "modernization_baseline.json" in document
        assert "D:\\MADRLCitytleranflexresdr" in document
        assert "D:\\madrl_lima" in document

    assert "FR-001" in spec
    assert "FR-001" in plan
    assert "FR-001" in tasks


EXPECTED_SPECS = {
    "000-foundation",
    "001-open-source-provenance",
    "002-multiobjective-policy",
    "003-modular-orchestration",
    "004-execution-manifests",
    "005-scientific-evaluation",
    "006-thesis-evidence",
    "007-local-agent-harness",
    "008-artifacts-data",
    "009-jury-observations",
    "010-local-training-panel",
    "011-dataset-to-delivery-pipeline",
    "012-repository-hygiene",
}

REQUIRED_FILES = ("spec.md", "plan.md", "tasks.md")


def test_all_spec_folders_have_required_files() -> None:
    specs_root = PROJECT_ROOT / "specs"
    for folder_name in sorted(EXPECTED_SPECS):
        folder = specs_root / folder_name
        assert folder.is_dir(), f"Missing spec folder: {folder_name}"
        for required in REQUIRED_FILES:
            path = folder / required
            assert path.is_file(), f"Missing {required} in {folder_name}"
            content = path.read_text(encoding="utf-8")
            assert len(content.strip()) > 0, f"Empty {required} in {folder_name}"


def test_spec_000_consumes_the_generated_baseline_schema() -> None:
    baseline = json.loads(
        (PROJECT_ROOT / "data/audits/modernization_baseline.json").read_text(
            encoding="utf-8"
        )
    )
    assert baseline["schema_version"] == "1.0"
    assert baseline["repository"]["root"] == "D:/MADRLCitytleranflexresdr"
