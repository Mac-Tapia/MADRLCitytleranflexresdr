#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parche Cap. I veredicto/tabla HE y Cap. III protocolo (Friedman principal)."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from docx import Document

REPO = Path(__file__).resolve().parents[2]
BACKUP = REPO / "outputs" / "_word_backups"
REPORT = REPO / "outputs" / "_patch_cap1_cap3_manual_20260806.json"
CANONS = [
    REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx",
    REPO / "docs" / "Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx",
]

CAP3_OLD = (
    "Por ello se aplica Shapiro-Wilk para normalidad, Kruskal-Wallis para diferencias "
    "globales entre algoritmos con cobertura completa y Mann-Whitney U con ajuste Holm "
    "para comparaciones por pares."
)
CAP3_NEW = (
    "Por ello se aplica Shapiro-Wilk para normalidad; Friedman pareado por KPI "
    "(principal) con Kendall W y Wilcoxon+Holm; Kruskal-Wallis y Mann-Whitney U solo "
    "como analisis exploratorio/sensibilidad cuando no hay independencia real. Los "
    "episodios de una sola corrida (seed = 0) no son replicas independientes."
)

VERDICT_OLD = (
    "Contrastación canónica Cap. 5 sobre KPI-gains: HE10/HE20/HE30 no se rechazan "
    "(KW p = 0,4685 / 0,7648 / 0,7357); HE11/HE21/HE31 no se respaldan; H0G se rechaza "
    "de forma exploratoria (Friedman p = 0,0096, Kendall's W = 0,1787"
)
VERDICT_NEW = (
    "Contrastación canónica Cap. 5 sobre KPI-gains (omnibus principal = Friedman pareado): "
    "HE10/HE20/HE30 no se rechazan (Friedman p = 0,0611 / 0,0498 / 0,1801; KW exploratorio "
    "p = 0,4685 / 0,7648 / 0,7357); HE11/HE21/HE31 no se respaldan; H0G se rechaza "
    "(Friedman p = 0,0096, Kendall's W = 0,1787"
)
# También normaliza veredictos ya parcheados que aún digan «de forma exploratoria»
VERDICT_EXPLORATORIA = "H0G se rechaza de forma exploratoria ("
VERDICT_FORMAL = "H0G se rechaza ("


PROTO_OLD = "Protocolo: Shapiro–Wilk → Kruskal–Wallis → Mann–Whitney / Wilcoxon (Holm); α = 0,05."
PROTO_NEW = (
    "Protocolo: Shapiro–Wilk → Friedman pareado + Kendall W + Wilcoxon/Holm (principal); "
    "Kruskal–Wallis/MWU exploratorio; α = 0,05."
)


def rewrite_para(paragraph, new_text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(new_text)


def patch_paragraph_text(paragraph, changes: list[str]) -> None:
    text = paragraph.text or ""
    original = text
    if CAP3_OLD in text:
        text = text.replace(CAP3_OLD, CAP3_NEW)
        changes.append("cap3_snip")
    if VERDICT_OLD in text:
        text = text.replace(VERDICT_OLD, VERDICT_NEW)
        changes.append("cap1_verdict")
    if VERDICT_EXPLORATORIA in text:
        text = text.replace(VERDICT_EXPLORATORIA, VERDICT_FORMAL)
        changes.append("cap1_verdict_formal")
    if PROTO_OLD in text:
        text = text.replace(PROTO_OLD, PROTO_NEW)
        changes.append("cap1_protocol")
    if "Protocolo: Shapiro–Wilk → Kruskal–Wallis → Mann" in text and PROTO_NEW not in text:
        text = text.replace(
            "Protocolo: Shapiro–Wilk → Kruskal–Wallis → Mann",
            "Protocolo: Shapiro–Wilk → Friedman pareado + Kendall W + Wilcoxon/Holm "
            "(principal); Kruskal–Wallis/MWU exploratorio → Mann",
        )
        changes.append("cap1_protocol_partial")
    # Cap1 table cells
    if "HE10" in text and "KW p = 0,4685" in text and "Friedman p = 0,0611" not in text:
        text = text.replace("KW p = 0,4685", "Friedman p = 0,0611; KW exploratorio p = 0,4685")
        changes.append("he10")
    if "HE20" in text and "KW p = 0,7648" in text and "Friedman p = 0,0498" not in text:
        text = text.replace("KW p = 0,7648", "Friedman p = 0,0498; KW exploratorio p = 0,7648")
        changes.append("he20")
    if "HE30" in text and "KW p = 0,7357" in text and "Friedman p = 0,1801" not in text:
        text = text.replace("KW p = 0,7357", "Friedman p = 0,1801; KW exploratorio p = 0,7357")
        changes.append("he30")
    if text != original:
        rewrite_para(paragraph, text)


def patch_doc(path: Path) -> dict:
    BACKUP.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = BACKUP / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, bak)
    doc = Document(str(path))
    changes: list[str] = []
    for paragraph in doc.paragraphs:
        patch_paragraph_text(paragraph, changes)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    patch_paragraph_text(paragraph, changes)
    doc.save(str(path))
    return {"file": path.name, "backup": str(bak), "changes": changes, "n": len(changes)}


def main() -> int:
    report = {"patched": [patch_doc(p) for p in CANONS if p.is_file()]}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
