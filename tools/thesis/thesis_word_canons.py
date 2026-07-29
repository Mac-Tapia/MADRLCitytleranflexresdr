"""Rutas canónicas de los 2 Word de tesis vigentes (2026-07-29).

Fuente de verdad: docs/CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md
y docs/workflow_manifest.json → canonical_50ep_drive.word_canons.

Política: exactamente 2 .docx en docs/ raíz (Tesis + Informe).
ABRIR_ESTE_WORD_* fue eliminado; no recrear.
Backups temporales, si existen, van a outputs/_word_backups/ — nunca a docs/.
"""

from __future__ import annotations

from pathlib import Path

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
DOCS = REPO / "docs"

TESIS = DOCS / "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx"
INFORME = DOCS / "Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx"

CANONS: tuple[Path, ...] = (TESIS, INFORME)

RUN_ID = "madrl_v3_20260627_164047"
DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX"
)


def existing_canons() -> list[Path]:
    """Return canon paths that exist and are non-empty."""
    return [p for p in CANONS if p.is_file() and p.stat().st_size > 0]


def require_tesis() -> Path:
    if not (TESIS.is_file() and TESIS.stat().st_size > 0):
        raise FileNotFoundError(f"Falta Word canónico Tesis: {TESIS}")
    return TESIS


def mirrors_of_tesis() -> tuple[Path, ...]:
    """Destinos de sync Cap.5 desde Tesis (solo Informe)."""
    return (INFORME,)
