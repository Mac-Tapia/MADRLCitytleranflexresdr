#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alinea Cap. 6 (conclusiones) a la separación descriptivo/inferencial y a KW GLOBAL canónico.

Problema: Cap. 6 citaba KW ALL p=0,1554 (otra agregación) junto a Friedman p=0,0096
de problemas_objetivos_hipotesis/. Para HG/HE la KW canónica es GLOBAL H=1,8108, p=0,4044.
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

# Sustituciones: mantener separación descriptivo vs inferencial y KW GLOBAL canónica.
SUBS: list[tuple[str, str]] = [
    (
        "Respecto de las hipótesis (Cap. 5 §5.5, KPI-gains): H0G se rechaza de forma exploratoria "
        "(Friedman p = 0,0096) mientras KW ALL no es significativo (p = 0,1554). "
        "HE10 (KW p = 0,4685), HE20 (KW p = 0,7648) y HE30 (KW p = 0,7357) no se rechazan; "
        "HE11/HE21/HE31 no se respaldan. Descriptivamente MATD3 lidera OE.1/OE.2 y MAAC lidera "
        "OE.3. Wilcoxon/Mann–Whitney exploratorios no sustituyen el contraste omnibus ni la "
        "replicación multi-semilla.",
        "Respecto de las hipótesis (Cap. 5 §5.5, KPI-gains de problemas_objetivos_hipotesis/): "
        "en el plano inferencial, H0G se rechaza de forma exploratoria "
        "(Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787), mientras que Kruskal–Wallis "
        "GLOBAL no es significativo (H = 1,8108, p = 0,4044). "
        "HE10 (KW H = 1,5164, p = 0,4685), HE20 (KW H = 0,5364, p = 0,7648) y HE30 "
        "(KW H = 0,6138, p = 0,7357) no se rechazan; HE11/HE21/HE31 no se respaldan. "
        "En el plano descriptivo —independiente del ómnibus—, MATD3 lidera OE.1/OE.2 y MAAC "
        "lidera OE.3. Wilcoxon/Mann–Whitney con Holm no sustituyen el contraste ómnibus ni la "
        "replicación multi-semilla.",
    ),
    (
        "Respecto de las hipotesis (KPI-gains Cap. 5): H0G se rechaza de forma exploratoria "
        "(Friedman p = 0,0096) mientras KW ALL no es significativo (p = 0,1554). "
        "HE10 (KW p = 0,4685), HE20 (KW p = 0,7648) y HE30 (KW p = 0,7357) no se rechazan; "
        "HE11/HE21/HE31 no se respaldan. Descriptivamente MATD3 lidera OE.1/OE.2 y MAAC lidera "
        "OE.3. Wilcoxon exploratorio detecta pares que no sustituyen el contraste omnibus ni la "
        "replicacion multi-semilla (Agarwal et al., 2021; Colas et al., 2019; Iqbal y Sha, 2019; "
        "Xie et al., 2023).",
        "Respecto de las hipotesis (Cap. 5 §5.5, KPI-gains): en el plano inferencial, H0G se "
        "rechaza de forma exploratoria (Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787), "
        "mientras KW GLOBAL no es significativo (H = 1,8108, p = 0,4044). "
        "HE10 (KW p = 0,4685), HE20 (KW p = 0,7648) y HE30 (KW p = 0,7357) no se rechazan; "
        "HE11/HE21/HE31 no se respaldan. En el plano descriptivo, MATD3 lidera OE.1/OE.2 y MAAC "
        "lidera OE.3. Wilcoxon/Mann–Whitney con Holm no sustituyen el omnibus ni la replicacion "
        "multi-semilla (Agarwal et al., 2021; Colas et al., 2019; Iqbal y Sha, 2019; Xie et al., 2023).",
    ),
    (
        "H0G rechazo exploratorio (Friedman p = 0,0096) y KW ALL p = 0,1554 no significativo.",
        "H0G rechazo exploratorio (Friedman p = 0,0096, Kendall's W = 0,1787) y KW GLOBAL "
        "p = 0,4044 no significativo.",
    ),
    (
        "H0G se rechaza de forma exploratoria (Friedman p = 0,0096) con KW ALL no significativo "
        "(p = 0,1554).",
        "H0G se rechaza de forma exploratoria (Friedman p = 0,0096, Kendall's W = 0,1787) con "
        "KW GLOBAL no significativo (H = 1,8108, p = 0,4044).",
    ),
    (
        "Friedman integración p = 0,0096; KW ALL p = 0,1554 n.s.; no implica HE11∧HE21∧HE31",
        "Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; KW GLOBAL H = 1,8108, "
        "p = 0,4044 n.s.; no implica HE11∧HE21∧HE31",
    ),
    (
        "Referencia integrada (50 ep Drive): Friedman pareado p = 0,0096 (W = 0,1787); "
        "KW ALL KPI-gains p = 0,1554; KW scores globales p = 0,4044.",
        "Referencia integrada (50 ep Drive, problemas_objetivos_hipotesis/): Friedman pareado "
        "χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; KW GLOBAL H = 1,8108, p = 0,4044. "
        "(La KW ALL p = 0,1554 de analisis_estadistico_madrl.csv es otra agregación y no decide HG/HE.)",
    ),
    # Informe Resumen / Cap.6 variantes
    (
        "H0G se rechaza solo de forma exploratoria (Friedman p = 0,0096; KW ALL p = 0,1554 no significativo).",
        "H0G se rechaza solo de forma exploratoria (Friedman p = 0,0096, Kendall's W = 0,1787; "
        "KW GLOBAL H = 1,8108, p = 0,4044 no significativo).",
    ),
    (
        "H0G se rechaza de forma exploratoria (Friedman integración p = 0,0096) mientras KW ALL "
        "no es significativo (p = 0,1554); HE11/HE21/HE31 no se respaldan.",
        "H0G se rechaza de forma exploratoria (Friedman p = 0,0096, Kendall's W = 0,1787) mientras "
        "KW GLOBAL no es significativo (H = 1,8108, p = 0,4044); HE11/HE21/HE31 no se respaldan.",
    ),
    (
        "H0G is rejected only exploratorily (Friedman p=0.0096; KW ALL p=0.1554 n.s.).",
        "H0G is rejected only exploratorily (Friedman p=0.0096, Kendall's W=0.1787; "
        "KW GLOBAL H=1.8108, p=0.4044 n.s.).",
    ),
    (
        "while H0G is rejected exploratorily (integration Friedman p = 0.0096) and KW ALL is "
        "non-significant (p = 0.1554); HE11/HE21/HE31 are not supported.",
        "while H0G is rejected exploratorily (Friedman p = 0.0096, Kendall's W = 0.1787) and "
        "KW GLOBAL is non-significant (H = 1.8108, p = 0.4044); HE11/HE21/HE31 are not supported.",
    ),
    (
        "Inferencialmente, H0G se rechaza solo de forma exploratoria (Friedman p = 0,0096) y KW ALL "
        "no es significativo (p = 0,1554); no se respalda superioridad estadística global única.",
        "Inferencialmente, H0G se rechaza solo de forma exploratoria (Friedman p = 0,0096, "
        "Kendall's W = 0,1787) y KW GLOBAL no es significativo (H = 1,8108, p = 0,4044); "
        "no se respalda superioridad estadística global única. El liderazgo de MATD3/MAAC permanece "
        "en el plano descriptivo.",
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
    n_para = 0
    n_cell = 0
    for p in doc.paragraphs:
        new, c = apply_subs(p.text or "")
        if c:
            set_text(p, new)
            n_para += c
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
                    n_cell += c
    doc.save(str(path))
    blob = "\n".join(p.text or "" for p in Document(str(path)).paragraphs)
    return {
        "path": path.name,
        "backup": bak.name,
        "para_subs": n_para,
        "cell_subs": n_cell,
        "has_kw_global_4044_in_hyp": ("KW GLOBAL" in blob and "0,4044" in blob),
        "leftover_kw_all_in_hipotesis_phrase": (
            "KW ALL no es significativo (p = 0,1554)" in blob
        ),
        "has_descriptivo_inferencial_split": (
            "plano inferencial" in blob and "plano descriptivo" in blob
        ),
    }


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    canons = existing_canons()
    report = [patch_doc(p, stamp) for p in canons]
    out = REPO / "outputs" / f"_patch_cap6_desc_inf_{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={out}")
    for r in report:
        print(
            r["path"],
            "para=",
            r["para_subs"],
            "cells=",
            r["cell_subs"],
            "split=",
            r["has_descriptivo_inferencial_split"],
            "leftover=",
            r["leftover_kw_all_in_hipotesis_phrase"],
        )
    ok = all(
        (r["para_subs"] + r["cell_subs"]) >= 0
        and not r["leftover_kw_all_in_hipotesis_phrase"]
        for r in report
    )
    # Informe may still mention 0,1554 only as "otra agregación" note in §5.3 — allowed.
    for r in report:
        if r["leftover_kw_all_in_hipotesis_phrase"]:
            ok = False
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
