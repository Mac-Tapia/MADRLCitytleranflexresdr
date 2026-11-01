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


def test_spec_000_consumes_the_generated_baseline_schema() -> None:
    baseline = json.loads(
        (PROJECT_ROOT / "data/audits/modernization_baseline.json").read_text(
            encoding="utf-8"
        )
    )
    assert baseline["schema_version"] == "1.0"
    assert baseline["repository"]["root"] == "D:/MADRLCitytleranflexresdr"
