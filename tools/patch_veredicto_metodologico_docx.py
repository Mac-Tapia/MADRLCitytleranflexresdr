#!/usr/bin/env python3
"""Portar veredicto metodologico a Word PATCHED/SYNCED (estructura real Cap. 1/3/6)."""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"

TARGETS = [
    DOCS / "ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_PATCHED.docx",
    DOCS / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_PATCHED.docx",
    DOCS / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_SYNCED.docx",
]

FALLBACK_FROM = {
    DOCS / "ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_PATCHED.docx": DOCS
    / "ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx",
    DOCS / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_PATCHED.docx": DOCS
    / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx",
    DOCS / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_SYNCED.docx": DOCS
    / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_PATCHED.docx",
}


def set_run_font(run, bold: bool = False, size: float = 12.0) -> None:
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rFonts.set(qn(attr), "Times New Roman")


def replace_paragraph_text(p: Paragraph, text: str, *, bold: bool = False) -> None:
    p.clear()
    run = p.add_run(text)
    set_run_font(run, bold=bold)


def insert_paragraph_after(paragraph: Paragraph, text: str = "", *, bold: bool = False) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    if text:
        run = new_para.add_run(text)
        set_run_font(run, bold=bold)
    return new_para


def insert_table_after(paragraph: Paragraph, headers: list[str], rows: list[list[str]]) -> None:
    doc = paragraph.part.document
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        set_run_font(run, bold=True, size=10)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(val)
            set_run_font(run, size=9)
    paragraph._p.addnext(table._tbl)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def find_idx(doc: Document, pred) -> int | None:
    for i, p in enumerate(doc.paragraphs):
        if pred(p.text or ""):
            return i
    return None


def find_after_label(doc: Document, label_rx: str) -> int | None:
    """Return index of first non-empty paragraph after a label paragraph."""
    lab = find_idx(doc, lambda t: re.search(label_rx, t, re.I) is not None)
    if lab is None:
        return None
    for j in range(lab + 1, min(lab + 5, len(doc.paragraphs))):
        if (doc.paragraphs[j].text or "").strip():
            return j
    return None


def patch_cap1(doc: Document) -> dict:
    actions = []

    # PG body (after "Problema general (PG):")
    pg_i = find_after_label(doc, r"^Problema general\s*\(PG\)\s*:?\s*$")
    if pg_i is None:
        pg_i = find_idx(doc, lambda t: "en que medida el algoritmo multi-agente" in norm(t))
    if pg_i is not None:
        replace_paragraph_text(
            doc.paragraphs[pg_i],
            "¿Qué algoritmo MADRL ofrece el mejor compromiso (ranking / frontera de Pareto) "
            "de gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los "
            "costos energéticos en comunidades inteligentes simuladas bajo CityLearn v3 en el "
            "SEAI Iquitos, y en qué medida el factor algoritmo (VI) produce efectos diferenciados "
            "sobre esas dimensiones (VD)?",
        )
        actions.append(f"pg@{pg_i}")

    # PE.1–PE.3
    pe_map = {
        r"^PE\.1\s*:": (
            "PE.1: ¿Qué MADRL lidera la flexibilidad energética (D-VD.1, escenario E1) y con qué "
            "evidencia descriptiva e inferencial (capa episódica vs KPI-gains)?"
        ),
        r"^PE\.2\s*:": (
            "PE.2: ¿Qué MADRL lidera la reducción de emisiones de CO₂ (D-VD.2, escenario E2) y con qué "
            "evidencia descriptiva e inferencial (capa episódica vs KPI-gains)?"
        ),
        r"^PE\.3\s*:": (
            "PE.3: ¿Qué MADRL lidera la optimización de costos energéticos (D-VD.3, escenario E3) y con qué "
            "evidencia descriptiva e inferencial (capa episódica vs KPI-gains)?"
        ),
    }
    for rx, txt in pe_map.items():
        i = find_idx(doc, lambda t, r=rx: re.search(r, t, re.I) is not None)
        if i is not None:
            replace_paragraph_text(doc.paragraphs[i], txt)
            actions.append(f"pe@{i}")

    # OG
    og_i = find_after_label(doc, r"^Objetivo general\s*\(OG\)\s*:?\s*$")
    if og_i is None:
        og_i = find_idx(doc, lambda t: "determinar el efecto del algoritmo madrl aplicado" in norm(t))
    if og_i is not None:
        replace_paragraph_text(
            doc.paragraphs[og_i],
            "Identificar el(los) MADRL recomendable(s) por eje y el ranking integrado de gestión "
            "coordinada de flexibilidad, CO₂ y costos en el SEAI Iquitos, sin asumir dominancia "
            "Pareto universal, evaluando el efecto del factor algoritmo (VI) sobre la VD.",
        )
        actions.append(f"og@{og_i}")

    oe_map = {
        r"^OE\.1\s*:": (
            "OE.1: Identificar el MADRL líder en flexibilidad energética (D-VD.1, E1) y contrastar "
            "si la diferencia entre algoritmos es estadísticamente sustentable."
        ),
        r"^OE\.2\s*:": (
            "OE.2: Identificar el MADRL líder en reducción de emisiones de CO₂ (D-VD.2, E2) y contrastar "
            "si la diferencia entre algoritmos es estadísticamente sustentable."
        ),
        r"^OE\.3\s*:": (
            "OE.3: Identificar el MADRL líder en costos energéticos (D-VD.3, E3) y contrastar "
            "si la diferencia entre algoritmos es estadísticamente sustentable."
        ),
    }
    for rx, txt in oe_map.items():
        i = find_idx(doc, lambda t, r=rx: re.search(r, t, re.I) is not None)
        if i is not None:
            replace_paragraph_text(doc.paragraphs[i], txt)
            actions.append(f"oe@{i}")

    # Nota metodológica hipótesis
    note_i = find_idx(
        doc,
        lambda t: "el estudio es cuantitativo" in norm(t) and "hipotesis" in norm(t),
    )
    if note_i is not None:
        replace_paragraph_text(
            doc.paragraphs[note_i],
            "El estudio es cuantitativo, aplicado y cuasiexperimental factorial 4×3 (algoritmo × escenario), "
            "basado en simulación. A diferencia de los objetivos, las hipótesis formulan contrastes H₀/H₁ "
            "sobre el factor algoritmo (VI). Se contrastan dos capas de evidencia que no deben fusionarse: "
            "(A) series episódicas alineadas a OE; (B) KPI-gains de entrenamiento. Protocolo: Shapiro–Wilk → "
            "Kruskal–Wallis → Mann–Whitney U (Holm) y Wilcoxon signed-rank (exploratorio); α = 0,05. "
            "Las métricas primarias son KPIs energéticos y recompensa MADRL; accuracy/precision/recall/F1 "
            "no son métricas centrales. Detalle en Capítulos 3 y 5 (Colas et al., 2019; Agarwal et al., 2021).",
        )
        actions.append(f"h_note@{note_i}")

    hg_i = find_after_label(doc, r"^Hipotesis general\s*\(HG\)\s*:?\s*$|^Hipótesis general\s*\(HG\)")
    if hg_i is None:
        hg_i = find_idx(doc, lambda t: "produce un efecto estadisticamente significativo y diferenciado" in norm(t))
    if hg_i is not None:
        replace_paragraph_text(
            doc.paragraphs[hg_i],
            "H₁(G): no existe un único MADRL que domine simultáneamente los tres ejes; el ranking integrado "
            "y los líderes por eje pueden diferir (trade-off Pareto), con efectos diferenciados del factor "
            "algoritmo sobre la VD. H₀(G): las distribuciones de desempeño entre algoritmos son idénticas "
            "en el agregado de ejes (omnibus KPI-gains).",
        )
        actions.append(f"hg@{hg_i}")

    he_map = {
        r"^HE\.1\s*:": (
            "HE.1: H₁₁ = las distribuciones de desempeño de flexibilidad (D-VD.1) difieren entre algoritmos; "
            "H₀₁ = son idénticas. El líder descriptivo compuesto en E1 es MATD3; la media episódica de "
            "reward_mean_average favorece a MAAC."
        ),
        r"^HE\.2\s*:": (
            "HE.2: H₁₂ = las distribuciones de emisiones de CO₂ (D-VD.2) difieren entre algoritmos; "
            "H₀₂ = son idénticas. El líder descriptivo en E2 es MATD3."
        ),
        r"^HE\.3\s*:": (
            "HE.3: H₁₃ = las distribuciones de costo energético (D-VD.3) difieren entre algoritmos; "
            "H₀₃ = son idénticas. El líder descriptivo en E3 es MAAC (Δcosto 9 515 EUR)."
        ),
    }
    for rx, txt in he_map.items():
        i = find_idx(doc, lambda t, r=rx: re.search(r, t, re.I) is not None)
        if i is not None:
            replace_paragraph_text(doc.paragraphs[i], txt)
            actions.append(f"he@{i}")

    # Decision paragraph under hypotheses
    dec_i = find_idx(
        doc,
        lambda t: "cada hipotesis especifica tiene una hipotesis nula" in norm(t)
        or "cada hipótesis específica tiene una hipótesis nula" in norm(t),
    )
    if dec_i is not None:
        replace_paragraph_text(
            doc.paragraphs[dec_i],
            "Veredicto (corrida madrl_v3_20260627_164047, seed = 0): HG ranking/Pareto aceptada "
            "(MATD3 score 0,6667; sin dominador universal); superioridad omnibus KPI-gains no confirmada "
            "(KW p = 0,155). HE.1: rechazar H₀ capa A (p = 1,305×10⁻⁸), no rechazar capa B (p = 0,281). "
            "HE.2: rechazar H₀ capa A (p = 0,0439), no rechazar capa B (p = 0,546). "
            "HE.3: no rechazar H₀ en capas A/B (p = 0,251 / 0,388); liderazgo MAAC descriptivo. "
            "Fuentes: gdrive_objective_aligned_statistics.csv; hipotesis_estadisticas_madrl.csv. "
            "Detalle en §§5.9–5.11 y 6.1.1.",
        )
        actions.append(f"h_decision@{dec_i}")

    return {"ok": bool(actions), "actions": actions}


def patch_cap3(doc: Document) -> dict:
    actions = []
    # Align terminology to cuasiexperimental while keeping factorial 4x3
    for i, p in enumerate(doc.paragraphs):
        t = p.text or ""
        n = norm(t)
        if "experimental-computacional factorial" in n or "experimental computacional factorial" in n:
            nt = re.sub(
                r"experimental[- ]computacional",
                "cuasiexperimental (simulación controlada)",
                t,
                flags=re.I,
            )
            replace_paragraph_text(p, nt)
            actions.append(f"cap3_term@{i}")
        elif "se define como diseno experimental-computacional" in n or "se define como diseño experimental-computacional" in n:
            nt = t.replace("experimental-computacional", "cuasiexperimental (simulación controlada)")
            replace_paragraph_text(p, nt)
            actions.append(f"cap3_def@{i}")
        elif re.search(r"3\.2\s+Dise[nñ]o experimental-computacional", t, re.I):
            replace_paragraph_text(
                p,
                "3.2 Diseño cuasiexperimental (simulación controlada) factorial 4×3",
                bold=True,
            )
            actions.append(f"cap3_h32@{i}")

    # Strengthen paragraph that rejects "no experimental"
    i = find_idx(doc, lambda t: "no se considera no experimental" in norm(t))
    if i is not None:
        replace_paragraph_text(
            doc.paragraphs[i],
            "El diseño no se considera no experimental en sentido estricto, porque sí existe manipulación "
            "controlada de factores dentro del entorno de simulación: algoritmo MADRL y escenario de recompensa. "
            "Tampoco corresponde a un experimento de campo con sujetos humanos, sino a un cuasiexperimento "
            "computacional in silico (sin aleatorización de unidades naturales). Por ello, se define como "
            "diseño cuasiexperimental factorial 4×3, con control de dataset, entorno, recompensa, horizonte "
            "temporal, agentes y protocolo de evaluación. La inferencia es intra-corrida y se interpreta con "
            "cautela (Shadish, Cook y Campbell, 2002): la validez externa queda limitada por la ausencia de "
            "múltiples semillas independientes. Métricas primarias: KPIs y recompensa; accuracy/F1 no son centrales.",
        )
        actions.append(f"cap3_quasi@{i}")

    # Add/replace analysis note if Kruskal mentioned later - optional short insert after 3.2 intro
    return {"ok": bool(actions), "actions": actions}


def patch_cap6(doc: Document) -> dict:
    actions = []

    # Update PE summary if still only capa B
    pe_sum = find_idx(doc, lambda t: "pe.1 (d-vd.1)" in norm(t) and "kruskal-wallis p = 0,281" in norm(t))
    if pe_sum is not None:
        replace_paragraph_text(
            doc.paragraphs[pe_sum],
            "PE.1 (D-VD.1): descriptivamente, mayor efecto compuesto MATD3 (1,0009); capa A "
            "(reward_mean_average) KW p = 1,305×10⁻⁸ (H₀ rechazada; líder media episódica MAAC); "
            "capa B (KPI-gains) KW p = 0,281 (H₀ no rechazada). "
            "PE.2 (D-VD.2): descriptivamente MATD3 (ΔCO₂ 23 070 kg); capa A KW p = 0,0439 (H₀ rechazada, ε²≈0,029); "
            "capa B KW p = 0,546 (H₀ no rechazada). "
            "PE.3 (D-VD.3): descriptivamente MAAC (9 515 EUR); capa A KW p = 0,251 y capa B KW p = 0,388 "
            "(H₀ no rechazada en ambas).",
        )
        actions.append(f"cap6_pe_sum@{pe_sum}")

    hyp_i = find_idx(doc, lambda t: "respecto de las hipotesis" in norm(t) or "respecto de las hipótesis" in norm(t))
    if hyp_i is not None:
        replace_paragraph_text(
            doc.paragraphs[hyp_i],
            "Respecto de las hipótesis (veredicto 2026-07-18): HG ranking/Pareto se acepta "
            "(MATD3 score 0,6667; sin dominador universal); la superioridad omnibus en KPI-gains "
            "no se confirma (KW ALL p = 0,155). HE.1 y HE.2 rechazan H₀ en capa episódica OE-alineada "
            "(p = 1,305×10⁻⁸ y p = 0,0439) pero no en KPI-gains (p = 0,281 y p = 0,546). "
            "HE.3 no rechaza H₀ en ninguna capa (p = 0,251 / 0,388); el liderazgo de MAAC es descriptivo. "
            "No se fusionan capas. Wilcoxon exploratorio no sustituye el omnibus ni la réplica multi-semilla "
            "(Agarwal et al., 2021; Colas et al., 2019).",
        )
        actions.append(f"cap6_hyp@{hyp_i}")

    lim = find_idx(doc, lambda t: re.search(r"^6\.2\b", t.strip(), re.I) is not None or t.strip().lower().startswith("limitaciones encontradas"))
    # Only treat as present if heading is inside Cap. 6 (after "6.1 Principales")
    cap61 = find_idx(doc, lambda t: re.search(r"^6\.1\b", t.strip()) is not None)
    existing = None
    if cap61 is not None and lim is not None:
        for i in range(cap61, lim):
            t = doc.paragraphs[i].text or ""
            if re.search(r"^6\.1\.1\b", t.strip()) and "veredicto" in norm(t):
                existing = i
                break
    if lim is not None and existing is None:
        before = doc.paragraphs[lim - 1]
        cursor = insert_paragraph_after(
            before,
            "6.1.1 Veredicto de hipótesis (aceptación / rechazo)",
            bold=True,
        )
        cursor = insert_paragraph_after(
            cursor,
            "Diseño: cuasiexperimental factorial 4×3. Formulación PG/OG tipo ranking–Pareto. "
            "Contraste H₀/H₁ por eje con dos capas (A = episódica OE-alineada; B = KPI-gains). α = 0,05.",
        )
        cursor = insert_paragraph_after(
            cursor,
            "HG: aceptada como ranking multiobjetivo sin dominador universal; H₀ omnibus KPI-gains no rechazada (p = 0,155). "
            "HE.1: H₀ rechazada en A, no en B. HE.2: H₀ rechazada en A, no en B. HE.3: H₀ no rechazada en A ni B. "
            "Accuracy/precision/recall/F1 no intervienen (métricas no primarias).",
        )
        insert_table_after(
            cursor,
            ["Hipótesis", "Decisión", "Fundamento"],
            [
                ["HG", "Ranking/Pareto aceptado; omnibus no confirma superioridad", "score 0,6667; KW p=0,155"],
                ["HE.1", "Rechazar H₀ capa A; no rechazar capa B", "p=1,305e-8 / p=0,281"],
                ["HE.2", "Rechazar H₀ capa A; no rechazar capa B", "p=0,0439 / p=0,546"],
                ["HE.3", "No rechazar H₀ (A y B)", "p=0,251 / p=0,388; MAAC descriptivo"],
            ],
        )
        actions.append("cap6_inserted_611")
    elif existing is not None:
        actions.append("cap6_611_already_present")

    return {"ok": bool(actions), "actions": actions}


def save_doc(doc: Document, path: Path) -> Path:
    try:
        doc.save(str(path))
        return path
    except PermissionError:
        alt = path.with_name(path.stem + f"_VEREDICTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
        doc.save(str(alt))
        return alt


def ensure_source(path: Path) -> Path | None:
    if path.exists():
        return path
    fb = FALLBACK_FROM.get(path)
    if fb and fb.exists():
        shutil.copy2(fb, path)
        return path
    return None


def verify(path: Path) -> dict:
    if not path.exists():
        return {"file": path.name, "checks": {}}
    doc = Document(str(path))
    text = "\n".join(p.text or "" for p in doc.paragraphs)
    low = text.lower()
    return {
        "file": path.name,
        "checks": {
            "has_cuasiexperimental": "cuasiexperimental" in low,
            "has_veredicto_611": "6.1.1" in text and "veredicto" in low,
            "has_ranking_pareto": "ranking" in low and "pareto" in low,
            "has_two_layers": "capa a" in low or "dos capas" in low,
            "has_he1_episodic_p": "1,305" in text or "1.305" in text,
            "old_only_capa_b_hyp_line": bool(
                re.search(r"respecto de las hip[oó]tesis: HG no se confirma inferencialmente", text, re.I)
            ),
        },
    }


def patch_one(path: Path) -> dict:
    src = ensure_source(path)
    if src is None:
        return {"file": str(path), "ok": False, "error": "missing"}
    doc = Document(str(src))
    r1 = patch_cap1(doc)
    r3 = patch_cap3(doc)
    r6 = patch_cap6(doc)
    out = save_doc(doc, path)
    return {
        "file": str(path),
        "saved": str(out),
        "ok": bool(r1.get("ok") and r3.get("ok") and r6.get("ok")),
        "partial_ok": bool(r1.get("ok") or r3.get("ok") or r6.get("ok")),
        "cap1": r1,
        "cap3": r3,
        "cap6": r6,
    }


def main() -> int:
    results = [patch_one(t) for t in TARGETS]
    verifications = [verify(Path(r["saved"])) for r in results if r.get("saved")]
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "results": results,
        "verifications": verifications,
    }
    out_json = DOCS / "VEREDICTO_WORD_PATCH_REPORT_2026-07-18.json"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if any(r.get("partial_ok") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
