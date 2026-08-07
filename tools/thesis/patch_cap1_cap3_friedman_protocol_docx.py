#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parche quirúrgico Cap. I tabla HE + Cap. III protocolo Friedman en ambos Word canónicos."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from docx import Document

import sys

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from thesis_word_canons import INFORME, TESIS  # noqa: E402

BACKUP_DIR = REPO / "outputs" / "_word_backups"
REPORT = REPO / "outputs" / "_patch_cap1_cap3_friedman_protocol_20260806.json"

OLD_CAP3 = (
    "Friedman: solo si hubiera ≥3 semillas (bloques); no aplicable con seed única."
)
OLD_CAP3_ALT = (
    "Friedman: solo si hubiera ≥3 semillas (bloques); **no aplicable** con seed única."
)
NEW_CAP3 = (
    "Friedman (principal, datos pareados por KPI) → Kendall W → Wilcoxon signed-rank "
    "entre pares con Holm. Kruskal–Wallis y Mann–Whitney U solo como análisis "
    "exploratorio/sensibilidad cuando no hay independencia real. Los episodios de una "
    "sola corrida (seed = 0) no son réplicas experimentales independientes."
)

# Reemplazos de texto en celdas/párrafos de la tabla Cap. I §1.3.2.3
REPLACEMENTS = [
    (
        "No se rechaza HE10; no se respalda HE11 (KW p = 0,4685)",
        "No se rechaza HE10; no se respalda HE11 (Friedman p = 0,0611; KW exploratorio p = 0,4685)",
    ),
    (
        "No se rechaza HE20; no se respalda HE21 (KW p = 0,7648)",
        "No se rechaza HE20; no se respalda HE21 (Friedman p = 0,0498 sin impacto vs cero ni post hoc Holm; KW exploratorio p = 0,7648)",
    ),
    (
        "No se rechaza HE30; no se respalda HE31 (KW p = 0,7357)",
        "No se rechaza HE30; no se respalda HE31 (Friedman p = 0,1801; KW exploratorio p = 0,7357)",
    ),
    (
        "(Friedman p = 0,0096); sin ganador global único",
        "(Friedman χ² = 9,2911, p = 0,0096; Kendall W = 0,1787); sin ganador global único",
    ),
]


def _backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def _replace_in_paragraph(paragraph, old: str, new: str) -> bool:
    text = paragraph.text or ""
    if old not in text:
        return False
    # Preserve simple single-run replacement when possible
    if len(paragraph.runs) == 1:
        paragraph.runs[0].text = text.replace(old, new)
        return True
    # Multi-run: rewrite full paragraph text into first run
    new_text = text.replace(old, new)
    for i, run in enumerate(paragraph.runs):
        run.text = new_text if i == 0 else ""
    return True


def patch_doc(path: Path) -> dict:
    info: dict = {"file": path.name, "replacements": [], "cap3": False}
    if not path.is_file():
        info["ok"] = False
        info["error"] = "missing"
        return info
    info["backup"] = str(_backup(path))
    doc = Document(str(path))

    # Paragraphs
    for p in doc.paragraphs:
        t = p.text or ""
        if "Friedman" in t and ("no aplicable" in t.lower() or "solo si hubiera" in t.lower()):
            # Replace the Friedman sentence fragment if present
            new_t = t
            new_t = re.sub(
                r"Friedman[:\.]?[^\n]*?(seed única|semilla única)\.?",
                NEW_CAP3,
                new_t,
                flags=re.IGNORECASE,
            )
            if new_t != t:
                for i, run in enumerate(p.runs):
                    run.text = new_t if i == 0 else ""
                if not p.runs:
                    p.add_run(new_t)
                info["cap3"] = True
                info["replacements"].append({"where": "paragraph", "kind": "cap3_friedman"})
        for old, new in REPLACEMENTS:
            if _replace_in_paragraph(p, old, new):
                info["replacements"].append({"where": "paragraph", "old": old[:60]})

    # Tables
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    t = p.text or ""
                    if "Friedman" in t and ("no aplicable" in t.lower() or "solo si hubiera" in t.lower()):
                        new_t = re.sub(
                            r"Friedman[:\.]?[^\n]*?(seed única|semilla única)\.?",
                            NEW_CAP3,
                            t,
                            flags=re.IGNORECASE,
                        )
                        if new_t != t:
                            for i, run in enumerate(p.runs):
                                run.text = new_t if i == 0 else ""
                            if not p.runs:
                                p.add_run(new_t)
                            info["cap3"] = True
                    for old, new in REPLACEMENTS:
                        if _replace_in_paragraph(p, old, new):
                            info["replacements"].append({"where": "table", "old": old[:60]})

    doc.save(str(path))
    info["ok"] = True
    info["n_replacements"] = len(info["replacements"])
    return info


def main() -> int:
    report = {"patched": [patch_doc(TESIS), patch_doc(INFORME)]}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(x.get("ok") for x in report["patched"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
