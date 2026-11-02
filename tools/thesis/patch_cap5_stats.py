#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inserta en Cap. 5.5 la redacción con valores exactos de problemas_objetivos_hipotesis/.

Fuente canónica (50 ep Drive, run madrl_v3_20260627_164047):
  outputs/.../estadistica/problemas_objetivos_hipotesis/

Política Word: solo los 2 canónicos en docs/.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from thesis_word_canons import CANONS, existing_canons  # noqa: E402

BACKUP_DIR = REPO / "outputs" / "_word_backups"
MARKER = "[[STATS_EXACTAS_KPI_GAINS_50EP]]"

# Redacción bloque único con valores exactos (coma decimal, como Cap. 5).
STATS_EXACT_PARAS: list[str] = [
    MARKER,
    (
        "Síntesis de pruebas estadísticas con valores exactos (KPI-gains, 50 episodios Drive, "
        "carpeta problemas_objetivos_hipotesis/; α = 0,05; MAAC, MASAC y MATD3; HAPPO sin "
        "KPI-gains finales comparables). Los números siguientes son la referencia obligatoria "
        "para HG/HE1–HE3 y no deben sustituirse por cifras de analisis_estadistico_madrl.csv "
        "cuando el contraste sea de hipótesis."
    ),
    (
        "Shapiro–Wilk (W y p) por objetivo. OE.1/E1: MAAC W = 0,7152, p = 0,001184; "
        "MASAC W = 0,5997, p = 1,066e-04; MATD3 W = 0,7160, p = 0,001208. "
        "OE.2/E2: MAAC W = 0,6993, p = 0,009419; MASAC W = 0,6999, p = 0,009548; "
        "MATD3 W = 0,7012, p = 0,009848. "
        "OE.3/E3: MAAC W = 0,5575, p = 3,029e-05; MASAC W = 0,5879, p = 6,905e-05; "
        "MATD3 W = 0,5464, p = 2,246e-05. "
        "GLOBAL (E1+E2+E3): MAAC W = 0,6772, p = 2,628e-06; MASAC W = 0,6011, p = 3,047e-07; "
        "MATD3 W = 0,6734, p = 2,343e-06. En todos los grupos calculables se rechaza normalidad; "
        "la ruta paramétrica queda descartada."
    ),
    (
        "Kruskal–Wallis (H y p) por objetivo. OE.1: H = 1,5164, p = 0,4685 (no se rechaza igualdad). "
        "OE.2: H = 0,5364, p = 0,7648 (no se rechaza). "
        "OE.3: H = 0,6138, p = 0,7357 (no se rechaza). "
        "GLOBAL: H = 1,8108, p = 0,4044 (no se rechaza)."
    ),
    (
        "Friedman pareado por KPI y Kendall's W. OE.1: χ² = 5,5897, p = 0,0611, Kendall's W = 0,2329. "
        "OE.2: χ² = 6,0000, p = 0,0498, Kendall's W = 0,6000. "
        "OE.3: χ² = 3,4286, p = 0,1801, Kendall's W = 0,1905. "
        "GLOBAL (integración multi-eje): χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787."
    ),
    (
        "Mann–Whitney U (U, p ajustado Holm y tamaño de efecto Cliff's δ). "
        "OE.1: MAAC–MASAC U = 89,0, p-Holm = 0,8498, δ = 0,2361; "
        "MAAC–MATD3 U = 67,5, p-Holm = 0,8498, δ = −0,0625; "
        "MASAC–MATD3 U = 53,0, p-Holm = 0,8498, δ = −0,2639. "
        "OE.2: MAAC–MASAC U = 15,0, p-Holm = 1,0000, δ = 0,2000; "
        "MAAC–MATD3 U = 10,0, p-Holm = 1,0000, δ = −0,2000; "
        "MASAC–MATD3 U = 10,0, p-Holm = 1,0000, δ = −0,2000. "
        "OE.3: MAAC–MASAC U = 49,0, p-Holm = 1,0000, δ = 0,2099; "
        "MAAC–MATD3 U = 44,0, p-Holm = 1,0000, δ = 0,0864; "
        "MASAC–MATD3 U = 35,0, p-Holm = 1,0000, δ = −0,1358. "
        "GLOBAL: MAAC–MASAC U = 393,0, p-Holm = 0,6294, δ = 0,1627; "
        "MAAC–MATD3 U = 325,5, p-Holm = 0,8251, δ = −0,0370; "
        "MASAC–MATD3 U = 269,0, p-Holm = 0,6191, δ = −0,2041. "
        "Ningún par es significativo tras Holm."
    ),
    (
        "Wilcoxon signed-rank pareado (estadístico W, p ajustado Holm). "
        "OE.1: MAAC–MASAC W = 7,0, p-Holm = 0,1100; MAAC–MATD3 W = 17,0, p-Holm = 0,5143; "
        "MASAC–MATD3 W = 14,0, p-Holm = 0,3376. "
        "OE.2: los tres pares W = 0,0, p-Holm = 0,3074. "
        "OE.3: MAAC–MASAC W = 6,0, p-Holm = 0,5266; MAAC–MATD3 W = 13,0, p-Holm = 1,0000; "
        "MASAC–MATD3 W = 11,0, p-Holm = 1,0000. "
        "GLOBAL: MAAC–MASAC W = 31,0, p-Holm = 0,0172 (único par significativo tras Holm); "
        "MAAC–MATD3 W = 69,0, p-Holm = 0,2953; MASAC–MATD3 W = 54,0, p-Holm = 0,1137."
    ),
    (
        "Decisión de hipótesis (HG ≡ H0G/H1G; HE1 ≡ HE10/HE11; HE2 ≡ HE20/HE21; HE3 ≡ HE30/HE31). "
        "HG: se rechaza H0G y se respalda H1G de forma exploratoria (Friedman integración "
        "χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; impacto GLOBAL vs baseline significativo "
        "tras Holm para MAAC/MASAC/MATD3), sin ganador global único (KW GLOBAL p = 0,4044). "
        "HE1: no se rechaza HE10; no se respalda HE11 (KW p = 0,4685; sin conjunción "
        "impacto+diferencias en E1). "
        "HE2: no se rechaza HE20; no se respalda HE21 (KW p = 0,7648; sin impacto vs cero "
        "tras Holm; 0/15 KPI mejorados). "
        "HE3: no se rechaza HE30; no se respalda HE31 (KW p = 0,7357; sin ómnibus ni impacto "
        "vs cero tras Holm en E3)."
    ),
]

# Expansión de fundamentos en tablas 5.5.x (match parcial → reemplazo completo).
FUNDAMENTO_SUBS: list[tuple[str, str]] = [
    (
        "Friedman integracion p = 0,0096 + impacto GLOBAL vs baseline (Holm)",
        "Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; impacto GLOBAL vs baseline "
        "Holm (MAAC/MASAC/MATD3); KW GLOBAL H = 1,8108, p = 0,4044",
    ),
    (
        "Friedman integración p = 0,0096 + impacto GLOBAL vs baseline (Holm)",
        "Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; impacto GLOBAL vs baseline "
        "Holm (MAAC/MASAC/MATD3); KW GLOBAL H = 1,8108, p = 0,4044",
    ),
    (
        "Friedman integración p = 0,0096; KW ALL p = 0,1554 n.s.; no implica HE11∧HE21∧HE31",
        "Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; KW GLOBAL H = 1,8108, "
        "p = 0,4044; no implica HE11∧HE21∧HE31",
    ),
    (
        "Kruskal–Wallis E1 p = 0,4685 (KPI-gains)",
        "KW H = 1,5164, p = 0,4685; Friedman χ² = 5,5897, p = 0,0611, Kendall's W = 0,2329",
    ),
    (
        "Kruskal–Wallis E2 p = 0,7648 (KPI-gains)",
        "KW H = 0,5364, p = 0,7648; Friedman χ² = 6,0000, p = 0,0498, Kendall's W = 0,6000",
    ),
    (
        "Kruskal–Wallis E3 p = 0,7357 (KPI-gains); TOPSIS/evaluate_v2 refuerzan el juicio multiobjetivo hacia MAAC/OE.3 sin sustituir el omnibus de HE31",
        "KW H = 0,6138, p = 0,7357; Friedman χ² = 3,4286, p = 0,1801, Kendall's W = 0,1905; "
        "TOPSIS/evaluate_v2 no sustituyen el ómnibus HE31",
    ),
    (
        "KW p = 0,4685",
        "KW H = 1,5164, p = 0,4685; Friedman χ² = 5,5897, p = 0,0611, Kendall's W = 0,2329; "
        "MWU/Wilcoxon pares n.s. tras Holm",
    ),
    (
        "KW p = 0,7648",
        "KW H = 0,5364, p = 0,7648; Friedman χ² = 6,0000, p = 0,0498, Kendall's W = 0,6000; "
        "sin impacto vs cero tras Holm",
    ),
    (
        "KW p = 0,7357",
        "KW H = 0,6138, p = 0,7357; Friedman χ² = 3,4286, p = 0,1801, Kendall's W = 0,1905; "
        "sin impacto vs cero tras Holm",
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


def set_paragraph_text(paragraph, text: str) -> None:
    paragraph.clear()
    run = paragraph.add_run(text)
    set_run_font(run)


def insert_paragraph_after(paragraph, text: str) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    set_paragraph_text(new_para, text)
    return new_para


def backup(path: Path, stamp: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def remove_existing_block(doc: Document) -> int:
    """Remove previously inserted block (marker + following paras until next 5.5.x heading)."""
    paras = list(doc.paragraphs)
    start = None
    for i, para in enumerate(paras):
        if MARKER in (para.text or ""):
            start = i
            break
    if start is None:
        return 0
    end = start + 1
    while end < len(paras):
        t = (paras[end].text or "").strip()
        if t.startswith("5.5.") or t.startswith("5.6"):
            break
        end += 1
    removed = 0
    for para in paras[start:end]:
        el = para._element
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)
            removed += 1
    return removed


def insert_stats_block(doc: Document) -> bool:
    anchor = None
    for para in doc.paragraphs:
        t = (para.text or "").strip()
        if t.startswith("5.5 Contrastacion") or t.startswith("5.5 Contrastación"):
            continue
        if t.startswith("Protocolo: (1) Shapiro"):
            anchor = para
            break
    if anchor is None:
        # Fallback: after 5.5 heading
        for para in doc.paragraphs:
            t = (para.text or "").strip()
            if t.startswith("5.5 Contrastacion") or t.startswith("5.5 Contrastación"):
                anchor = para
                break
    if anchor is None:
        return False
    cursor = anchor
    for text in STATS_EXACT_PARAS:
        cursor = insert_paragraph_after(cursor, text)
    return True


def patch_table_cells(doc: Document) -> int:
    n = 0
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                raw = cell.text or ""
                new = raw
                for old, repl in FUNDAMENTO_SUBS:
                    if old in new:
                        new = new.replace(old, repl)
                if new != raw:
                    # Keep first paragraph; clear extras
                    paras = cell.paragraphs
                    if not paras:
                        continue
                    set_paragraph_text(paras[0], new.strip())
                    for extra in paras[1:]:
                        extra.clear()
                    n += 1
    return n


def verify(doc: Document) -> dict[str, bool]:
    blob = "\n".join(p.text or "" for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                blob += "\n" + (cell.text or "")
    keys = [
        "0,0096",
        "0,1787",
        "9,2911",
        "Kendall's W",
        "0,7152",
        "1,5164",
        "p-Holm",
        "Cliff's δ",
        "no se rechaza HE10",
        "se rechaza H0G",
        MARKER,
    ]
    return {k: (k in blob) for k in keys}


def patch_one(path: Path, stamp: str) -> dict:
    bak = backup(path, stamp)
    doc = Document(str(path))
    removed = remove_existing_block(doc)
    inserted = insert_stats_block(doc)
    cells = patch_table_cells(doc)
    doc.save(str(path))
    doc2 = Document(str(path))
    return {
        "path": path.name,
        "backup": bak.name,
        "removed_old_block": removed,
        "inserted": inserted,
        "table_cells_patched": cells,
        "verify": verify(doc2),
    }


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    canons = existing_canons()
    if len(canons) != len(CANONS):
        missing = [p.name for p in CANONS if p not in canons]
        print({"error": "faltan canónicos", "missing": missing})
        return 1
    report = [patch_one(p, stamp) for p in canons]
    out = REPO / "outputs" / f"_patch_cap5_stats_exactas_{stamp}.json"
    out.write_text(
        __import__("json").dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"report={out}")
    for r in report:
        print(
            r["path"],
            "inserted=",
            r["inserted"],
            "cells=",
            r["table_cells_patched"],
            "verify_ok=",
            all(r["verify"].values()),
        )
        fails = [k for k, v in r["verify"].items() if not v]
        if fails:
            print("  missing:", fails)
    ok = all(r["inserted"] and all(r["verify"].values()) for r in report)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
