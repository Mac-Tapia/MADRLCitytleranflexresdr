#!/usr/bin/env python3
"""Cap.5 training figures/tables + USD cost relabel + APA captions in Word canons.

Idempotent via marker CAP5_TRAINING_USD_APA_20260807.
Does NOT re-inject the 150-PNG job catalog.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from thesis_word_canons import CANONS, RUN_ID  # noqa: E402

BACKUP_DIR = REPO / "outputs" / "_word_backups"
RUN = REPO / "outputs" / RUN_ID
MC_DIR = REPO / "outputs" / "madrl_multicriteria_selection" / "figures"
REPORT = REPO / "outputs" / f"_patch_cap5_training_usd_apa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
MARKER = "CAP5_TRAINING_USD_APA_20260807"
GREY = RGBColor(0x55, 0x55, 0x55)

# Primary training figures (curated; no 150 dump)
PRIMARY_FIGS = (
    ("MATD3", "E1"),
    ("MASAC", "E2"),
    ("MAAC", "E3"),
    ("HAPPO", "E1"),
)


def set_run_font(run, *, size: float = 12.0, italic: bool = False, bold: bool = False, grey: bool = False) -> None:
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run.italic = italic
    run.bold = bold
    if grey:
        run.font.color.rgb = GREY
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        r_fonts.set(qn(attr), "Times New Roman")


def insert_paragraph_after(anchor: Paragraph, text: str = "", *, bold: bool = False, italic: bool = False, size: float = 12.0) -> Paragraph:
    new_p = OxmlElement("w:p")
    anchor._p.addnext(new_p)
    para = Paragraph(new_p, anchor._parent)
    if text:
        run = para.add_run(text)
        set_run_font(run, bold=bold, italic=italic, size=size, grey=italic and size <= 10.5)
    # APA-ish body spacing
    pf = para.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    return para


def set_heading(paragraph: Paragraph, level: int) -> None:
    try:
        paragraph.style = f"Heading {level}"
    except KeyError:
        if paragraph.runs:
            set_run_font(paragraph.runs[0], bold=True, size=14.0 if level <= 2 else 12.0)


def insert_figure_after(anchor: Paragraph, path: Path, caption: str, width_cm: float = 14.0) -> Paragraph:
    pic = insert_paragraph_after(anchor)
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = pic.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    cap = insert_paragraph_after(anchor=pic, text=caption, italic=True, size=10.0)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if cap.runs:
        set_run_font(cap.runs[0], size=10.0, italic=True, grey=True)
    return cap


def insert_table_after(anchor: Paragraph, headers: list[str], rows: list[list[str]], caption: str) -> Paragraph:
    cap = insert_paragraph_after(anchor, caption, italic=True, size=10.0)
    cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if cap.runs:
        set_run_font(cap.runs[0], size=10.0, italic=True)

    # Create table at body end, then move XML after caption
    table = anchor._parent.add_table(rows=1 + len(rows), cols=len(headers), width=Cm(16.0))
    tbl = table._tbl
    # remove from current position (body end) and place after caption
    tbl.getparent().remove(tbl)
    cap._p.addnext(tbl)

    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(h)
        set_run_font(run, bold=True, size=10.0)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(val)
            set_run_font(run, size=10.0)

    note_el = OxmlElement("w:p")
    tbl.addnext(note_el)
    note_p = Paragraph(note_el, cap._parent)
    run = note_p.add_run(
        "Nota. Retornos episódicos de entrenamiento (señal de aprendizaje). "
        "No sustituyen KPI-gains ni Δcosto distrital evaluate_v2 (USD). "
        f"Fuente: outputs/{RUN_ID}/{{ALGO}}/{{E}}/figures/tables/training_efficiency.csv."
    )
    set_run_font(run, size=9.0, italic=True, grey=True)
    note_p.paragraph_format.space_after = Pt(6)
    return note_p


def fmt_int_es(n: float) -> str:
    s = f"{int(round(n)):,}".replace(",", " ")
    return s


def load_training_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for algo in ("MATD3", "MAAC", "MASAC", "HAPPO"):
        for scen in ("E1", "E2", "E3"):
            path = RUN / algo / scen / "figures" / "tables" / "training_efficiency.csv"
            with path.open(encoding="utf-8") as f:
                data = list(csv.DictReader(f))
            first, last = data[0], data[-1]
            rows.append(
                [
                    algo,
                    scen,
                    str(len(data)),
                    fmt_int_es(float(first["return_total"])),
                    fmt_int_es(float(last["return_total"])),
                    fmt_int_es(float(last["steps"])),
                ]
            )
    return rows


def find_anchor(doc: Document) -> Paragraph | None:
    """Insert figures after markdown 5.1-bis note, or before §5.2."""
    paras = list(doc.paragraphs)
    bis_idx = None
    for i, p in enumerate(paras):
        t = (p.text or "").strip()
        if t.startswith("5.1-bis") or "Entrenamiento canónico" in t:
            bis_idx = i
    if bis_idx is not None:
        for j in range(bis_idx + 1, len(paras)):
            t = (paras[j].text or "").strip()
            if t.startswith("5.2 ") or "Criterio cuantitativo de efecto" in t:
                return paras[j - 1] if j > 0 else paras[j]
        return paras[bis_idx]
    for i, p in enumerate(paras):
        t = (p.text or "").strip()
        if t.startswith("5.2 ") or "Criterio cuantitativo de efecto" in t:
            return paras[i - 1] if i else p
    for i, p in enumerate(paras):
        t = (p.text or "").strip()
        if t.startswith("5.3 ") and ("OE.1" in t or "Flexibilidad" in t):
            return paras[i - 1] if i else p
    return None


def already_patched(doc: Document) -> bool:
    text = "\n".join(p.text or "" for p in doc.paragraphs)
    return MARKER in text and "Figura 5.1b." in text


def remove_partial_training_block(doc: Document) -> int:
    """Remove only an incomplete figure insert (marker without figures). Cap at 40 paras."""
    paras = list(doc.paragraphs)
    start = None
    for i, p in enumerate(paras):
        if MARKER in (p.text or ""):
            start = i
            break
    if start is None:
        return 0
    text_all = "\n".join(p.text or "" for p in doc.paragraphs)
    if "Figura 5.1b." in text_all:
        return 0
    end = min(len(paras), start + 40)
    for j in range(start + 1, min(len(paras), start + 40)):
        t = (paras[j].text or "").strip()
        if t.startswith("5.2 ") or "Criterio cuantitativo de efecto" in t or (
            t.startswith("5.3 ") and "OE.1" in t
        ):
            end = j
            break
    end = min(end, start + 40)
    removed = 0
    for p in paras[start:end]:
        el = p._element
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)
            removed += 1
    return removed


def relabel_eur_costs_in_doc(doc: Document) -> int:
    """Replace cost-display EUR with USD; skip European / Neural false positives."""
    n = 0
    patterns = [
        (re.compile(r"\bEUR\b"), "USD"),
        (re.compile(r"\beuros?\b", re.I), "dólares"),
    ]
    skip_if = ("European", "Neural", "Neurocomputing", "Europe")

    def fix_text(s: str) -> str:
        nonlocal n
        if any(k in s for k in skip_if):
            # only replace clear cost contexts
            if not re.search(r"(costo|Δcosto|delta|Baseline|Control|\d[\d\s]*\s*EUR)", s, re.I):
                return s
        out = s
        for rx, repl in patterns:
            out2, c = rx.subn(repl, out)
            if c:
                n += c
                out = out2
        return out

    for p in doc.paragraphs:
        for run in p.runs:
            if run.text and ("EUR" in run.text or "euro" in run.text.lower()):
                new = fix_text(run.text)
                if new != run.text:
                    run.text = new
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        if run.text and ("EUR" in run.text or "euro" in run.text.lower()):
                            new = fix_text(run.text)
                            if new != run.text:
                                run.text = new
    return n


def apply_apa_fonts_cap5_region(doc: Document) -> int:
    """Times New Roman 12 on Cap.5 body paragraphs (best-effort)."""
    in_cap5 = False
    touched = 0
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        style = (p.style.name if p.style is not None else "") or ""
        if re.match(r"(?i)^cap[ií]tulo\s*5\b", t) and "Heading" in style:
            in_cap5 = True
        elif in_cap5 and re.match(r"(?i)^cap[ií]tulo\s*6\b", t) and "Heading" in style:
            break
        if not in_cap5:
            continue
        for run in p.runs:
            if run.text:
                set_run_font(run, size=12.0 if "Heading" not in style else (14.0 if style.endswith("1") else 12.0), bold=("Heading" in style), italic=run.italic)
                touched += 1
        pf = p.paragraph_format
        if "Heading" not in style:
            pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    return touched


def required_pngs() -> list[Path]:
    paths = [MC_DIR / "learning_curves.png"]
    for algo, scen in PRIMARY_FIGS:
        paths.append(RUN / algo / scen / "figures" / "convergence_returns.png")
        paths.append(RUN / algo / scen / "figures" / "learning_efficiency.png")
    return paths


def patch_doc(doc_path: Path) -> dict:
    missing = [str(p.relative_to(REPO)).replace("\\", "/") for p in required_pngs() if not p.is_file()]
    if missing:
        return {"path": doc_path.name, "ok": False, "error": "missing_pngs", "missing": missing}

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{doc_path.stem}_training_usd_apa_{STAMP}{doc_path.suffix}"
    shutil.copy2(doc_path, backup)

    doc = Document(str(doc_path))
    eur_fixed = relabel_eur_costs_in_doc(doc)
    apa_runs = apply_apa_fonts_cap5_region(doc)

    skipped_training = False
    fig_count = 0
    partial_removed = 0
    if already_patched(doc):
        skipped_training = True
    else:
        partial_removed = remove_partial_training_block(doc)
        anchor = find_anchor(doc)
        if anchor is None:
            doc.save(str(doc_path))
            return {
                "path": str(doc_path.relative_to(REPO)).replace("\\", "/"),
                "ok": False,
                "error": "anchor_not_found",
                "backup": str(backup.relative_to(REPO)).replace("\\", "/"),
                "eur_fixed": eur_fixed,
            }

        cursor = insert_paragraph_after(
            anchor,
            "Figuras de entrenamiento (curadas)",
            bold=True,
            size=12.0,
        )
        cursor = insert_paragraph_after(
            cursor,
            "Se embeden 9 figuras reales de la corrida canónica (convergencia y eficiencia "
            "en el escenario primario por algoritmo, más curva multicriterio). "
            "La Tabla 5.1b del texto resume los retornos; la recompensa no sustituye HE.",
        )
        cursor = insert_paragraph_after(cursor, MARKER, italic=True, size=8.0)

        # Skip re-creating the table if markdown already injected Tabla 5.1b
        body_text = "\n".join(p.text or "" for p in doc.paragraphs)
        if "Tabla 5.1b." not in body_text:
            headers = ["Algoritmo", "Esc.", "Episodios", "Retorno ep. 0", "Retorno final", "Pasos"]
            rows = load_training_rows()
            cursor = insert_table_after(
                cursor,
                headers,
                rows,
                "Tabla 5.1b. Resumen de entrenamiento canónico (retorno episódico; seed = 0).",
            )

        cursor = insert_paragraph_after(
            cursor,
            "Las Figuras 5.1b–5.1j muestran convergencia y eficiencia (MATD3–E1, MASAC–E2, MAAC–E3, HAPPO–E1).",
        )
        # Multicriteria learning curves
        cursor = insert_figure_after(
            cursor,
            MC_DIR / "learning_curves.png",
            "Figura 5.1b. Curvas de aprendizaje multicriterio (50 episodios).",
            width_cm=14.5,
        )
        fig_count += 1

        fig_letters = list("cdefghij")
        letter_i = 0
        for algo, scen in PRIMARY_FIGS:
            for name, title in (
                ("convergence_returns.png", "convergencia de retornos episódicos"),
                ("learning_efficiency.png", "eficiencia de aprendizaje"),
            ):
                letter = fig_letters[letter_i]
                letter_i += 1
                path = RUN / algo / scen / "figures" / name
                cursor = insert_figure_after(
                    cursor,
                    path,
                    f"Figura 5.1{letter}. {algo}/{scen} — {title}.",
                    width_cm=13.8,
                )
                fig_count += 1

        cursor = insert_paragraph_after(
            cursor,
            "Nota. Figuras de entrenamiento curadas (9 PNG). No se reinyecta el catálogo "
            "completo por job. Fuentes: madrl_multicriteria_selection/figures/ y "
            f"outputs/{RUN_ID}/{{ALGO}}/{{E}}/figures/.",
            italic=True,
            size=9.0,
        )

    doc.save(str(doc_path))

    verify = Document(str(doc_path))
    text = "\n".join(p.text or "" for p in verify.paragraphs)
    blips = verify.element.body.xml.count("a:blip")
    eur_left = len(re.findall(r"\bEUR\b", text))
    # filter European false positives roughly
    eur_costish = len(re.findall(r"(costo|Δcosto|delta|Baseline|Control).{0,40}\bEUR\b|\bEUR\b.{0,20}(costo|delta)", text, re.I))

    return {
        "path": str(doc_path.relative_to(REPO)).replace("\\", "/"),
        "ok": True,
        "backup": str(backup.relative_to(REPO)).replace("\\", "/"),
        "skipped_training": skipped_training,
        "partial_removed": partial_removed,
        "eur_fixed": eur_fixed,
        "apa_runs_touched": apa_runs,
        "fig_count": fig_count,
        "checks": {
            "marker": MARKER in text,
            "table_caption": "Tabla 5.1b." in text,
            "fig_5_1b": "Figura 5.1b." in text,
            "usd_mention": "USD" in text,
            "blips": blips,
            "eur_tokens_total": eur_left,
            "eur_cost_context": eur_costish,
        },
    }


def main() -> int:
    report: dict = {"stamp": STAMP, "run_id": RUN_ID, "files": {}}
    ok_all = True
    for path in CANONS:
        if not path.is_file():
            report["files"][path.name] = {"ok": False, "error": "missing"}
            ok_all = False
            continue
        result = patch_doc(path)
        report["files"][path.name] = result
        ok_all = ok_all and bool(result.get("ok"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {REPORT}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
