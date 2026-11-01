#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alinea Resumen/Abstract del Informe (y Tesis si aplica) a KPI-gains canónicos.

Sustituye Friedman/p episódicos antiguos (p=0,614935 / 1,461e-8 / 0,109906)
por la batería problemas_objetivos_hipotesis/ usada en Cap. 5.5.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from thesis_word_canons import CANONS, existing_canons  # noqa: E402

BACKUP_DIR = REPO / "outputs" / "_word_backups"

SUBS: list[tuple[str, str]] = [
    # ES — párrafo de evidencia recalculada (Resumen)
    (
        "En E1, MATD3 presentó el menor deterioro de flexibilidad (-0,0923 %), sin impacto ni "
        "diferencias significativas (Friedman p=0,614935). En E2, MATD3 presentó el menor aumento "
        "de CO₂ (-0,4193 % de efecto favorable, equivalente a +23 070 kgCO₂), con diferencias "
        "entre algoritmos (p=1,461×10⁻⁸). En E3, MAAC registró el menor incremento de costo "
        "(-0,2675 %, +18.978,30 USD), sin diferencia global (p=0,109906).",
        "En el plano descriptivo, MATD3 lidera E1 (menor deterioro de flexibilidad, -0,0923 %) "
        "y E2 (menor aumento de CO₂, -0,4193 %, +23 070 kgCO₂), y MAAC lidera E3 (menor "
        "incremento de costo, -0,2675 %). En el plano inferencial (KPI-gains, Cap. 5.5), "
        "Kruskal–Wallis no rechaza igualdad en OE.1/OE.2/OE.3 "
        "(H = 1,5164 / 0,5364 / 0,6138; p = 0,4685 / 0,7648 / 0,7357); "
        "Friedman por eje es p = 0,0611 / 0,0498 / 0,1801 "
        "(Kendall's W = 0,2329 / 0,6000 / 0,1905).",
    ),
    # EN — Abstract evidence paragraph
    (
        "MATD3 showed the smallest flexibility deterioration in E1 (-0.0923%; Friedman p=0.614935) "
        "and the smallest CO2 increase in E2 (-0.4193% favourable effect, 23,070 kgCO2; "
        "p=1.461×10^-8). MAAC showed the smallest E3 cost increase (-0.2675%, +USD 18,978.30; "
        "p=0.109906).",
        "Descriptively, MATD3 leads E1 (smallest flexibility deterioration, -0.0923%) and E2 "
        "(smallest CO2 increase, -0.4193%, +23,070 kgCO2), while MAAC leads E3 (smallest cost "
        "increase, -0.2675%). Inferentially (KPI-gains, Cap. 5.5), Kruskal–Wallis does not reject "
        "equality in OE.1/OE.2/OE.3 (H=1.5164/0.5364/0.6138; p=0.4685/0.7648/0.7357); "
        "per-axis Friedman p=0.0611/0.0498/0.1801 (Kendall's W=0.2329/0.6000/0.1905).",
    ),
    # Variantes cortas por si aparecen aisladas
    (
        "sin impacto ni diferencias significativas (Friedman p=0,614935)",
        "sin diferencias omnibus en KPI-gains (KW p = 0,4685; Friedman p = 0,0611)",
    ),
    (
        "con diferencias entre algoritmos (p=1,461×10⁻⁸)",
        "sin diferencias omnibus en KPI-gains (KW p = 0,7648; Friedman p = 0,0498, exploratorio)",
    ),
    (
        "sin diferencia global (p=0,109906)",
        "sin diferencia omnibus en KPI-gains (KW p = 0,7357; Friedman p = 0,1801)",
    ),
    (
        "(-0.0923%; Friedman p=0.614935)",
        "(-0.0923%; KPI-gains KW p=0.4685, Friedman p=0.0611)",
    ),
    (
        "23,070 kgCO2; p=1.461×10^-8)",
        "23,070 kgCO2; KPI-gains KW p=0.7648, Friedman p=0.0498)",
    ),
    (
        "+USD 18,978.30; p=0.109906)",
        "+USD 18,978.30; KPI-gains KW p=0.7357, Friedman p=0.1801)",
    ),
]


def set_run_font(run) -> None:
    run.font.size = Pt(12)
    run.font.name = "Times New Roman"
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        r_fonts.set(qn(attr), "Times New Roman")


def set_text(paragraph, text: str) -> None:
    paragraph.clear()
    run = paragraph.add_run(text)
    set_run_font(run)


def apply_subs(text: str) -> tuple[str, int]:
    n = 0
    new = text
    for old, repl in SUBS:
        if old in new:
            new = new.replace(old, repl)
            n += 1
    return new, n


def patch_doc(path: Path, stamp: str) -> dict:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bak = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, bak)
    doc = Document(str(path))
    n = 0
    for p in doc.paragraphs:
        new, c = apply_subs(p.text or "")
        if c:
            set_text(p, new)
            n += c
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                raw = cell.text or ""
                new, c = apply_subs(raw)
                if c:
                    paras = cell.paragraphs
                    if paras:
                        set_text(paras[0], new.strip())
                        for extra in paras[1:]:
                            extra.clear()
                    n += c
    doc.save(str(path))
    blob = "\n".join(p.text or "" for p in Document(str(path)).paragraphs)
    for table in Document(str(path)).tables:
        for row in table.rows:
            for cell in row.cells:
                blob += "\n" + (cell.text or "")
    return {
        "path": path.name,
        "backup": bak.name,
        "subs": n,
        "leftover_614935": ("0,614935" in blob or "0.614935" in blob),
        "leftover_1461": ("1,461" in blob or "1.461" in blob),
        "leftover_109906": ("0,109906" in blob or "0.109906" in blob),
        "has_kw_4685": ("0,4685" in blob or "0.4685" in blob),
        "has_friedman_0096": ("0,0096" in blob or "0.0096" in blob),
    }


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = [patch_doc(p, stamp) for p in existing_canons()]
    out = REPO / "outputs" / f"_patch_resumen_kpi_gains_{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={out}")
    for r in report:
        print(
            r["path"],
            "subs=",
            r["subs"],
            "leftover=",
            r["leftover_614935"] or r["leftover_1461"] or r["leftover_109906"],
        )
    # Informe must clear old episodic p-values from Resumen; Tesis may never have had them.
    informe = next((r for r in report if "Inforne" in r["path"]), None)
    if informe is None:
        return 1
    ok = (
        informe["subs"] > 0
        and not informe["leftover_614935"]
        and not informe["leftover_1461"]
        and not informe["leftover_109906"]
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
