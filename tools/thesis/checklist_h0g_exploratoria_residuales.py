#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Checklist residuales «forma exploratoria» / «rejected exploratorily» en decisiones H."""
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "outputs" / "checklist_h0g_exploratoria_residuales_20260807.json"

DEC_PAT = re.compile(
    r"(?i)(?:se\s+)?(?:rechaza|respalda)\s+(?:H0G|H1G)\s+de\s+forma\s+exploratoria|"
    r"H0G\s*:?\s*se\s+rechaza\s+(?:solo\s+)?de\s+forma\s+exploratoria|"
    r"H1G\s*:?\s*se\s+respalda\s+de\s+forma\s+exploratoria|"
    r"Rechazar\s+H0G\s+de\s+forma\s+exploratoria|"
    r"respaldar\s+H1G\s+exploratoria|"
    r"H1G\s+exploratoria|"
    r"rejected\s+(?:only\s+)?exploratorily"
)
FORMA_ANY = re.compile(r"(?i)forma\s+exploratoria")
REJ_ANY = re.compile(r"(?i)rejected\s+(?:only\s+)?exploratorily|only\s+exploratorily")
CANONS = [
    "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx",
    "Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx",
]


def collect_texts(doc: Document) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []
    for i, p in enumerate(doc.paragraphs):
        texts.append((f"p{i}", p.text or ""))
    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            for ci, cell in enumerate(row.cells):
                texts.append((f"t{ti}r{ri}c{ci}", cell.text or ""))
    return texts


def main() -> int:
    checklist: dict = {
        "task": "Alinear decisiones formales H0G/H1G sin calificativo exploratoria",
        "date": "2026-08-07",
        "files_touched": [
            "docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx",
            "docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx",
            "docs/tesis_capitulos/Capitulo_6_Conclusiones.md",
            "tools/thesis/patch_h0g_remove_exploratoria_verdict_docx.py",
            "tools/thesis/patch_tesis_resumen_h0g_align_docx.py",
        ],
        "canons": {},
        "cap6_md": {},
        "summary": {},
        "before_after_key": {
            "ES_HG": {
                "before": "Se rechaza H0G de forma exploratoria. Se respalda H1G de forma exploratoria (...).",
                "after": "Se rechaza H0G. Se respalda H1G (...).",
            },
            "EN_Abstract": {
                "before": "H0G is rejected only exploratorily / rejected exploratorily (...).",
                "after": (
                    "H0G is rejected (Friedman GLOBAL chi2=9.2911, p=0.0096, W=0.1787) "
                    "and H1G is supported (no unique winner); KW GLOBAL n.s. (H=1.8108, p=0.4044)."
                ),
            },
            "limitacion": {
                "before": "Las decisiones HG se califican como exploratorias, porque seed=0...",
                "after": "Limitacion metodologica. La unidad experimental es semilla unica (seed=0);...",
            },
        },
    }

    for fname in CANONS:
        doc = Document(str(REPO / "docs" / fname))
        texts = collect_texts(doc)
        dec_hits = []
        forma_hits = []
        rej_hits = []
        for loc, t in texts:
            for m in DEC_PAT.finditer(t):
                dec_hits.append(
                    {
                        "loc": loc,
                        "sn": t[max(0, m.start() - 40) : m.end() + 50].replace("\n", " "),
                    }
                )
            for m in FORMA_ANY.finditer(t):
                forma_hits.append(
                    {
                        "loc": loc,
                        "sn": t[max(0, m.start() - 50) : m.end() + 50].replace("\n", " "),
                    }
                )
            for m in REJ_ANY.finditer(t):
                rej_hits.append(
                    {
                        "loc": loc,
                        "sn": t[max(0, m.start() - 50) : m.end() + 50].replace("\n", " "),
                    }
                )
        resumen = "\n".join(t for loc, t in texts if loc in ("p23", "p24", "p27", "p28"))
        checklist["canons"][fname] = {
            "decision_H_forma_exploratoria_or_rejected_exploratorily": len(dec_hits),
            "decision_hits": dec_hits,
            "forma_exploratoria_any_count": len(forma_hits),
            "forma_exploratoria_any_hits": forma_hits,
            "rejected_exploratorily_any_count": len(rej_hits),
            "rejected_exploratorily_hits": rej_hits,
            "resumen_has_chi2_9_2911": ("9,2911" in resumen or "9.2911" in resumen),
            "resumen_has_kw_global_0_4044": ("0,4044" in resumen or "0.4044" in resumen),
            "resumen_has_kw_all_0_1554": ("0,1554" in resumen or "0.1554" in resumen),
            "cap6_formal_HG": any("Se rechaza H0G. Se respalda H1G" in t for _, t in texts),
        }

    md = (REPO / "docs" / "tesis_capitulos" / "Capitulo_6_Conclusiones.md").read_text(
        encoding="utf-8"
    )
    checklist["cap6_md"] = {
        "forma_exploratoria_count": len(re.findall(r"(?i)forma exploratoria", md)),
        "has_formal_HG": "Se **rechaza H0G**. Se **respalda H1G**" in md,
        "kw_mwu_exploratorio_kept": bool(
            re.search(r"(?i)Kruskal–Wallis exploratorio|sensibilidad exploratoria", md)
        ),
        "seed_limitation_kept": "semilla única" in md or "seed = 0" in md,
    }

    tot_dec = sum(
        c["decision_H_forma_exploratoria_or_rejected_exploratorily"]
        for c in checklist["canons"].values()
    )
    tot_forma = sum(c["forma_exploratoria_any_count"] for c in checklist["canons"].values())
    tot_rej = sum(
        c["rejected_exploratorily_any_count"] for c in checklist["canons"].values()
    )
    checklist["summary"] = {
        "residual_decision_H_forma_exploratoria_or_rejected_exploratorily_total": tot_dec,
        "residual_forma_exploratoria_any_total": tot_forma,
        "residual_rejected_exploratorily_any_total": tot_rej,
        "ok_zero_decision_residuals": tot_dec == 0 and tot_rej == 0,
        "note_forma_any": (
            "OE.1 Cap.5 frase descriptiva «se contrastan de forma exploratoria» "
            "(no veredicto H0G/H1G). KW/MWU exploratorio conservado."
        ),
    }

    OUT.write_text(json.dumps(checklist, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(checklist["summary"], ensure_ascii=False, indent=2))
    for fname, c in checklist["canons"].items():
        print(
            fname,
            "dec",
            c["decision_H_forma_exploratoria_or_rejected_exploratorily"],
            "forma_any",
            c["forma_exploratoria_any_count"],
            "rej",
            c["rejected_exploratorily_any_count"],
        )
        for h in c["forma_exploratoria_any_hits"]:
            print(" ", h["sn"][:130])
    print(f"wrote={OUT}")
    return 0 if checklist["summary"]["ok_zero_decision_residuals"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
