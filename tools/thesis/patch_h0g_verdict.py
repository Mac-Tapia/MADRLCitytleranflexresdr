#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quitar «exploratoria / exploratorily» del veredicto formal H0G/H1G.

Ámbito: Resumen ES, Abstract EN y Cap. VI (ambos Word canónicos).
Las mismas cadenas se aplican al documento completo para residuales Cap. V
de decisión formal (no se toca KW/MWU «exploratorio» como tipo de prueba).

Semilla única permanece como limitación metodológica aparte.
Backups: outputs/_word_backups/
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from docx import Document

REPO = Path(__file__).resolve().parents[2]
BACKUP = REPO / "outputs" / "_word_backups"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT = REPO / "outputs" / f"_patch_h0g_remove_exploratoria_verdict_{STAMP}.json"
CANONS = [
    REPO / 'docs' / 'tesis.docx',
    REPO / 'docs' / 'informe.docx',
]

# Orden: frases largas / específicas primero.
REPLACEMENTS: list[tuple[str, str]] = [
    # --- Resumen ES (Tesis) ---
    (
        "ni respalda HE11/HE21/HE31; H0G se rechaza de forma exploratoria por Friedman "
        "integrado (p = 0,0096) con KW ALL no significativo (p = 0,1554).",
        "ni respalda HE11/HE21/HE31; se rechaza H0G (Friedman GLOBAL χ² = 9,2911, "
        "p = 0,0096, Kendall's W = 0,1787) y se respalda H1G (sin ganador único); "
        "KW GLOBAL no es significativo (H = 1,8108, p = 0,4044).",
    ),
    (
        "ni respalda HE11/HE21/HE31; H0G se rechaza de forma exploratoria por Friedman "
        "integrado (p = 0,0096) con KW GLOBAL no significativo (H = 1,8108, p = 0,4044).",
        "ni respalda HE11/HE21/HE31; se rechaza H0G (Friedman GLOBAL χ² = 9,2911, "
        "p = 0,0096, Kendall's W = 0,1787) y se respalda H1G (sin ganador único); "
        "KW GLOBAL no es significativo (H = 1,8108, p = 0,4044).",
    ),
    # Tesis Resumen/Abstract tras replace genérico (sin χ² / sin H1G explícito)
    (
        "ni respalda HE11/HE21/HE31; H0G se rechaza por Friedman integrado (p = 0,0096) "
        "con KW GLOBAL exploratorio no significativo (p = 0,4044; Capa A).",
        "ni respalda HE11/HE21/HE31; se rechaza H0G (Friedman GLOBAL χ² = 9,2911, "
        "p = 0,0096, Kendall's W = 0,1787) y se respalda H1G (sin ganador único); "
        "KW GLOBAL no es significativo (H = 1,8108, p = 0,4044).",
    ),
    (
        "and does not support HE11/HE21/HE31; H0G is rejected via Friedman (p=0.0096) "
        "while exploratory KW GLOBAL is non-significant (p=0.4044; Layer A).",
        "and does not support HE11/HE21/HE31; H0G is rejected (Friedman GLOBAL "
        "χ²=9.2911, p=0.0096, Kendall's W=0.1787) and H1G is supported (no unique "
        "winner); KW GLOBAL is non-significant (H=1.8108, p=0.4044).",
    ),
    # --- Resumen ES (Informe) ---
    (
        "ni respalda HE11/HE21/HE31; H0G se rechaza solo de forma exploratoria "
        "(Friedman p = 0,0096, Kendall's W = 0,1787; KW GLOBAL H = 1,8108, p = 0,4044 "
        "no significativo).",
        "ni respalda HE11/HE21/HE31; se rechaza H0G (Friedman GLOBAL χ² = 9,2911, "
        "p = 0,0096, Kendall's W = 0,1787) y se respalda H1G (sin ganador único); "
        "KW GLOBAL no es significativo (H = 1,8108, p = 0,4044).",
    ),
    # --- Abstract EN (Tesis) ---
    (
        "and does not support HE11/HE21/HE31; H0G is rejected only exploratorily via "
        "Friedman (p=0.0096) while KW ALL is non-significant (p=0.1554).",
        "and does not support HE11/HE21/HE31; H0G is rejected (Friedman GLOBAL "
        "χ²=9.2911, p=0.0096, Kendall's W=0.1787) and H1G is supported (no unique "
        "winner); KW GLOBAL is non-significant (H=1.8108, p=0.4044).",
    ),
    (
        "and does not support HE11/HE21/HE31; H0G is rejected only exploratorily via "
        "Friedman (p=0.0096) while KW GLOBAL is non-significant (H=1.8108, p=0.4044).",
        "and does not support HE11/HE21/HE31; H0G is rejected (Friedman GLOBAL "
        "χ²=9.2911, p=0.0096, Kendall's W=0.1787) and H1G is supported (no unique "
        "winner); KW GLOBAL is non-significant (H=1.8108, p=0.4044).",
    ),
    # --- Abstract EN (Informe, párrafo principal) ---
    (
        "and does not support HE11/HE21/HE31; H0G is rejected only exploratorily "
        "(Friedman p=0.0096, Kendall's W=0.1787; KW GLOBAL H=1.8108, p=0.4044 n.s.).",
        "and does not support HE11/HE21/HE31; H0G is rejected (Friedman GLOBAL "
        "χ²=9.2911, p=0.0096, Kendall's W=0.1787) and H1G is supported (no unique "
        "winner); KW GLOBAL is non-significant (H=1.8108, p=0.4044).",
    ),
    # --- Abstract EN (Informe, párrafo evidencia) ---
    (
        "while H0G is rejected exploratorily (Friedman p = 0.0096, Kendall's W = 0.1787) "
        "and KW GLOBAL is non-significant (H = 1.8108, p = 0.4044)",
        "while H0G is rejected (Friedman GLOBAL χ² = 9.2911, p = 0.0096, "
        "Kendall's W = 0.1787) and H1G is supported (no unique winner); KW GLOBAL is "
        "non-significant (H = 1.8108, p = 0.4044)",
    ),
    # --- Cap. VI Decisión HG ---
    (
        "Decisión HG. Se rechaza H0G de forma exploratoria. Se respalda H1G de forma "
        "exploratoria (efectos diferenciales agregados sin ganador único).",
        "Decisión HG. Se rechaza H0G. Se respalda H1G (efectos diferenciales agregados "
        "sin ganador único).",
    ),
    (
        "Nivel de evidencia. Las decisiones de la hipótesis general se califican como "
        "exploratorias, porque la unidad experimental es semilla única (seed = 0) y los "
        "episodios de una sola corrida no constituyen réplicas experimentales "
        "independientes ni habilitan robustez multisemilla.",
        "Limitación metodológica. La unidad experimental es semilla única (seed = 0); "
        "los episodios de una sola corrida no constituyen réplicas experimentales "
        "independientes ni habilitan robustez multisemilla.",
    ),
    # --- Cap. V bullets residuales ---
    (
        "H0G: se rechaza de forma exploratoria.",
        "H0G: se rechaza.",
    ),
    (
        "H1G: se respalda de forma exploratoria (",
        "H1G: se respalda (",
    ),
    (
        "- H0G: se rechaza de forma exploratoria.",
        "- H0G: se rechaza.",
    ),
    (
        "- H1G: se respalda de forma exploratoria (",
        "- H1G: se respalda (",
    ),
    # --- Tabla Cap. V / consolidado ---
    (
        "Se rechaza H0G; se respalda H1G exploratoria; sin ganador único",
        "Se rechaza H0G; se respalda H1G; sin ganador único",
    ),
    (
        "Rechazar H0G de forma exploratoria; respaldar H1G exploratoria (sin ganador único)",
        "Se rechaza H0G; se respalda H1G (sin ganador único)",
    ),
    (
        "Rechazar H0G exploratorio; respaldar H1G exploratorio",
        "Se rechaza H0G; se respalda H1G",
    ),
    # --- Frases genéricas (después de las específicas) ---
    (
        "H0G se rechaza solo de forma exploratoria (",
        "H0G se rechaza (",
    ),
    (
        "H0G se rechaza de forma exploratoria (",
        "H0G se rechaza (",
    ),
    (
        "H0G se rechaza de forma exploratoria por Friedman",
        "H0G se rechaza por Friedman",
    ),
    (
        "H0G se rechaza de forma exploratoria.",
        "H0G se rechaza.",
    ),
    (
        "se respalda H1G de forma exploratoria (",
        "se respalda H1G (",
    ),
    (
        "Se respalda H1G de forma exploratoria (",
        "Se respalda H1G (",
    ),
    (
        "se rechaza H0G de forma exploratoria",
        "se rechaza H0G",
    ),
    (
        "Se rechaza H0G de forma exploratoria",
        "Se rechaza H0G",
    ),
    (
        "H0G is rejected only exploratorily (",
        "H0G is rejected (",
    ),
    (
        "H0G is rejected only exploratorily via Friedman",
        "H0G is rejected via Friedman",
    ),
    (
        "H0G is rejected exploratorily (",
        "H0G is rejected (",
    ),
    (
        "while H0G is rejected exploratorily (",
        "while H0G is rejected (",
    ),
    (
        "H1G exploratoria;",
        "H1G;",
    ),
    (
        "H1G exploratoria,",
        "H1G,",
    ),
    (
        "H0G exploratoria Friedman",
        "H0G rechazada (Friedman)",
    ),
    (
        "H1G exploratoria no equivale",
        "H1G respaldada no equivale",
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
            hits.append(old[:70])
    return out, hits


def patch_paragraph(paragraph, changes: list[str]) -> None:
    text = paragraph.text or ""
    new_text, hits = apply_replacements(text)
    if hits:
        rewrite_para(paragraph, new_text)
        changes.extend(hits)


def patch_doc(path: Path) -> dict:
    BACKUP.mkdir(parents=True, exist_ok=True)
    bak = BACKUP / f"{path.stem}_{STAMP}{path.suffix}"
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

    # Residual scan (decision-linked only)
    blob_parts: list[str] = []
    for p in Document(str(path)).paragraphs:
        blob_parts.append(p.text or "")
    for table in Document(str(path)).tables:
        for row in table.rows:
            for cell in row.cells:
                blob_parts.append(cell.text or "")
    blob = "\n".join(blob_parts)

    decision_patterns = [
        r"(?i)se\s+rechaza\s+H0G\s+de\s+forma\s+exploratoria",
        r"(?i)se\s+respalda\s+H1G\s+de\s+forma\s+exploratoria",
        r"(?i)H0G\s+se\s+rechaza\s+(?:solo\s+)?de\s+forma\s+exploratoria",
        r"(?i)H1G\s+exploratoria",
        r"(?i)rejected\s+(?:only\s+)?exploratorily",
        r"(?i)Rechazar\s+H0G\s+de\s+forma\s+exploratoria",
    ]
    residuals = []
    for pat in decision_patterns:
        for m in re.finditer(pat, blob):
            start = max(0, m.start() - 50)
            end = min(len(blob), m.end() + 50)
            residuals.append(blob[start:end].replace("\n", " "))

    return {
        "file": path.name,
        "backup": bak.name,
        "n_changes": len(changes),
        "samples": changes[:30],
        "residual_decision_hits": residuals,
    }


def main() -> int:
    report = {
        "stamp": STAMP,
        "patches": [patch_doc(p) for p in CANONS if p.is_file()],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report={REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
