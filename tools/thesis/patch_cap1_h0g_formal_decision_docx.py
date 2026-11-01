#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quitar «exploratoria» del veredicto formal H0G/H1G en Cap. I (ambos Word).

KW/MWU «exploratorio» como etiqueta de método se conserva.
La semilla única se deja como limitación, no como calificativo del rechazo/respaldo.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from docx import Document

REPO = Path(__file__).resolve().parents[2]
BACKUP = REPO / "outputs" / "_word_backups"
REPORT = REPO / "outputs" / "_patch_cap1_h0g_formal_decision_20260807.json"
CANONS = [
    REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx",
    REPO / "docs" / "Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx",
]

# (old, new) — orden importa: frases más largas primero
REPLACEMENTS = [
    (
        "Se rechaza H0G y se respalda H1G exploratoriamente (",
        "Se rechaza H0G y se respalda H1G (",
    ),
    (
        "Se rechaza H0G y se respalda H1G **exploratoriamente** (",
        "Se rechaza H0G y se respalda H1G (",
    ),
    (
        "H0G se rechaza de forma exploratoria (",
        "H0G se rechaza (",
    ),
    (
        "H0G se rechaza de forma exploratoria;",
        "H0G se rechaza;",
    ),
    (
        "se respalda H1G de forma exploratoria (",
        "se respalda H1G (",
    ),
    (
        "Se rechaza de forma exploratoria",
        "Se rechaza",
    ),
    (
        "Se respalda de forma exploratoria (",
        "Se respalda (",
    ),
    (
        "H1G exploratoria; sin ganador",
        "se respalda H1G; sin ganador",
    ),
    (
        "H1G exploratoria,",
        "H1G respaldada,",
    ),
]


def rewrite_para(paragraph, new_text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(new_text)


def apply_replacements(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    out = text
    for old, new in REPLACEMENTS:
        if old in out:
            out = out.replace(old, new)
            hits.append(old[:50])
    return out, hits


def patch_paragraph(paragraph, changes: list[str]) -> None:
    text = paragraph.text or ""
    new_text, hits = apply_replacements(text)
    if hits:
        rewrite_para(paragraph, new_text)
        changes.extend(hits)


def patch_doc(path: Path) -> dict:
    BACKUP.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = BACKUP / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, bak)
    doc = Document(str(path))
    changes: list[str] = []

    for p in doc.paragraphs:
        patch_paragraph(p, changes)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    patch_paragraph(p, changes)

    doc.save(str(path))
    return {"file": path.name, "backup": str(bak), "n_changes": len(changes), "samples": changes[:20]}


def main() -> int:
    report = {"patches": [patch_doc(p) for p in CANONS if p.is_file()]}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
