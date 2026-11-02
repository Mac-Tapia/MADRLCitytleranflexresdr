#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inject Capítulos 4–7 markdown into canonical Word docs (Tesis + Informe).

Replaces Cap.4 (→ Cap.5), Cap.5 (→ Cap.6), Cap.6 (→ Cap.7/Referencias),
and inserts Cap.7 before Referencias when missing.

Does not invent numeric results: content comes from docs/chapters/*.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from generate_borrador_tesis_docx import ACCENT, add_table, heading, p, style_base  # noqa: E402
from thesis_word_canons import INFORME, TESIS, require_tesis  # noqa: E402

CAPS_DIR = REPO / 'docs' / 'chapters'
BACKUP_DIR = REPO / "outputs" / "_word_backups"

CAP_RE = {
    4: re.compile(r"(?i)^\s*cap[ií]tulo\s*4\b"),
    5: re.compile(r"(?i)^\s*cap[ií]tulo\s*5\b"),
    6: re.compile(r"(?i)^\s*cap[ií]tulo\s*6\b"),
    7: re.compile(r"(?i)^\s*cap[ií]tulo\s*7\b"),
}
REF_RE = re.compile(r"(?i)^\s*(referencias\b|bibliograf)")
TOC_TAIL_RE = re.compile(r"\d+\s*$")


def is_toc_heading(text: str) -> bool:
    t = text.strip()
    if "\t" in t:
        return True
    if TOC_TAIL_RE.search(t) and re.search(r"(?i)cap[ií]tulo\s*\d+.*[a-záéíóúñ]{3,}\d+\s*$", t):
        return True
    return False


def iter_block_items(doc: Document):
    for child in list(doc.element.body.iterchildren()):
        tag = child.tag
        if tag == qn("w:p"):
            texts = [t.text or "" for t in child.iter(qn("w:t"))]
            yield child, "p", "".join(texts)
        elif tag == qn("w:tbl"):
            texts = [t.text or "" for t in child.iter(qn("w:t"))]
            yield child, "tbl", "".join(texts)
        else:
            yield child, "other", ""


def find_chapter_range(doc: Document, start_n: int, end_n: int | None, *, toc_safe: bool) -> tuple[int, int, list]:
    items = list(iter_block_items(doc))
    start = None
    end = None
    start_re = CAP_RE[start_n]
    end_re = CAP_RE[end_n] if end_n else None
    for i, (_el, _kind, text) in enumerate(items):
        t = text.strip()
        if start is None and start_re.search(t):
            if toc_safe and is_toc_heading(t):
                continue
            start = i
            continue
        if start is not None:
            if end_re and end_re.search(t) and not (toc_safe and is_toc_heading(t)):
                end = i
                break
            if end_n is None and REF_RE.search(t) and not (toc_safe and is_toc_heading(t)):
                end = i
                break
    if start is None:
        raise RuntimeError(f"Capítulo {start_n} no encontrado")
    if end is None:
        end = len(items)
    return start, end, items


def find_ref_index(doc: Document, *, toc_safe: bool) -> int:
    items = list(iter_block_items(doc))
    for i, (_el, _kind, text) in enumerate(items):
        t = text.strip()
        if REF_RE.search(t) and not (toc_safe and is_toc_heading(t)):
            return i
    raise RuntimeError("Referencias no encontradas")


def parse_md_table(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int]:
    header = [c.strip() for c in lines[start].strip().strip("|").split("|")]
    i = start + 1
    if i < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i]):
        i += 1
    rows: list[list[str]] = []
    while i < len(lines) and "|" in lines[i]:
        if re.match(r"^\s*\|?\s*:?-{3,}", lines[i]):
            i += 1
            continue
        row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if len(row) == len(header):
            rows.append(row)
        i += 1
    return header, rows, i


def md_to_elements(md_path: Path, chapter_title: str) -> list:
    """Build a temporary Document body from a markdown chapter."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tmp = Document()
    style_base(tmp)
    section = tmp.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.5)

    # Drop leading meta blockquotes until first heading
    i = 0
    while i < len(lines) and not lines[i].startswith("#"):
        i += 1

    first_h1 = True
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            # skip fenced blocks as plain paragraphs
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            if buf:
                p(tmp, "\n".join(buf), size=9, color=RGBColor(0x59, 0x59, 0x59))
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and "|" in lines[i + 1]:
            header, rows, i = parse_md_table(lines, i)
            if header and rows:
                add_table(tmp, header, rows, caption=None, col_widths=None)
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # Normalize Cap H1
            if level == 1:
                if first_h1:
                    heading(tmp, chapter_title, 1)
                    first_h1 = False
                else:
                    heading(tmp, title, 1)
            else:
                heading(tmp, title, min(level, 3))
            i += 1
            continue
        if line.strip().startswith(">"):
            # skip editorial notes
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        # accumulate paragraph until blank
        buf = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("#") and not lines[i].startswith("|") and not lines[i].startswith("```") and not lines[i].startswith(">"):
            buf.append(lines[i].strip())
            i += 1
        para = " ".join(buf)
        # strip simple markdown bold/italic markers
        para = re.sub(r"\*\*(.*?)\*\*", r"\1", para)
        para = re.sub(r"\*(.*?)\*", r"\1", para)
        para = re.sub(r"`([^`]+)`", r"\1", para)
        if para:
            p(tmp, para)
    return [deepcopy(child) for child in tmp.element.body]


def replace_range(doc: Document, start: int, end: int, new_elements: list, items: list) -> None:
    body = doc.element.body
    # Remove old nodes [start:end)
    for el, _k, _t in items[start:end]:
        body.remove(el)
    # Insert before the element that was at `end`, or append
    if end < len(items):
        anchor = items[end][0]
        for offset, child in enumerate(new_elements):
            anchor.addprevious(child) if offset == 0 else None
        # After first insert, keep inserting after previously inserted
        # Safer: insert all before anchor in reverse
        for child in reversed(new_elements):
            # remove if already inserted once
            pass
        # Clean approach: remove again if needed — rebuild insert
        # Re-find anchor (still in body)
        for child in reversed(new_elements):
            anchor.addprevious(child)
    else:
        for child in new_elements:
            body.append(child)


def replace_range_safe(doc: Document, start: int, end: int, new_elements: list) -> None:
    """Replace body block [start:end) with new_elements in forward document order.

    Skips w:sectPr from temporary markdown docs (must not be injected mid-body).
    """
    items = list(iter_block_items(doc))
    body = doc.element.body
    anchor = items[end][0] if end < len(items) else None
    for el, _k, _t in items[start:end]:
        body.remove(el)

    filtered = [el for el in new_elements if el.tag != qn("w:sectPr")]
    if anchor is None:
        for child in filtered:
            body.append(child)
        return

    # Forward order: first child immediately before anchor, each next after previous.
    last = None
    for child in filtered:
        if last is None:
            anchor.addprevious(child)
        else:
            last.addnext(child)
        last = child


def chapter_exists(doc: Document, n: int, *, toc_safe: bool) -> bool:
    for _el, _k, text in iter_block_items(doc):
        t = text.strip()
        if CAP_RE[n].search(t) and not (toc_safe and is_toc_heading(t)):
            return True
    return False


def _find_cap6_range(doc: Document, *, toc_safe: bool) -> tuple[int, int]:
    items = list(iter_block_items(doc))
    start = None
    end = None
    for i, (_el, _k, text) in enumerate(items):
        t = text.strip()
        if start is None and CAP_RE[6].search(t) and not (toc_safe and is_toc_heading(t)):
            start = i
            continue
        if start is not None:
            if CAP_RE[7].search(t) and not (toc_safe and is_toc_heading(t)):
                end = i
                break
            if REF_RE.search(t) and not (toc_safe and is_toc_heading(t)):
                end = i
                break
    if start is None:
        raise RuntimeError("Capítulo 6 no encontrado")
    if end is None:
        end = len(items)
    return start, end


def inject_into_doc(path: Path, elements_by_cap: dict[int, list], *, toc_safe: bool, dry_run: bool) -> dict:
    doc = Document(str(path))
    report: dict = {"path": str(path), "actions": []}

    s4, e4, _ = find_chapter_range(doc, 4, 5, toc_safe=toc_safe)
    report["actions"].append({"cap": 4, "start": s4, "end": e4, "blocks": len(elements_by_cap[4])})
    if not dry_run:
        replace_range_safe(doc, s4, e4, elements_by_cap[4])

    s5, e5, _ = find_chapter_range(doc, 5, 6, toc_safe=toc_safe)
    report["actions"].append({"cap": 5, "start": s5, "end": e5, "blocks": len(elements_by_cap[5])})
    if not dry_run:
        replace_range_safe(doc, s5, e5, elements_by_cap[5])

    s6, e6 = _find_cap6_range(doc, toc_safe=toc_safe)
    report["actions"].append({"cap": 6, "start": s6, "end": e6, "blocks": len(elements_by_cap[6])})
    if not dry_run:
        replace_range_safe(doc, s6, e6, elements_by_cap[6])

    if chapter_exists(doc, 7, toc_safe=toc_safe):
        s7, e7, _ = find_chapter_range(doc, 7, None, toc_safe=toc_safe)
        report["actions"].append({"cap": 7, "mode": "replace", "start": s7, "end": e7, "blocks": len(elements_by_cap[7])})
        if not dry_run:
            replace_range_safe(doc, s7, e7, elements_by_cap[7])
    else:
        ref_i = find_ref_index(doc, toc_safe=toc_safe)
        report["actions"].append({"cap": 7, "mode": "insert_before_ref", "ref_index": ref_i, "blocks": len(elements_by_cap[7])})
        if not dry_run:
            items = list(iter_block_items(doc))
            anchor = items[ref_i][0]
            for child in reversed(elements_by_cap[7]):
                anchor.addprevious(child)

    if not dry_run:
        doc.save(str(path))
    return report


def backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"{path.stem}_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject Cap4–7 MD into Word canons")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tesis-only", action="store_true")
    parser.add_argument("--informe-only", action="store_true")
    args = parser.parse_args()

    require_tesis()
    # Headings without accent to match verify_doctoral_docx anchors (Capitulo N).
    md_map = {
        4: (REPO / 'docs' / 'chapters' / 'cap4.md', "Capitulo 4. Desarrollo e implementacion de la coordinacion energetica multiobjetivo mediante MADRL"),
        5: (REPO / 'docs' / 'chapters' / 'cap5.md', "Capitulo 5. Resultados, efectos diferenciales y desempeno algoritmico"),
        6: (REPO / 'docs' / 'chapters' / 'cap6.md', "Capitulo 6. Conclusiones"),
        7: (REPO / 'docs' / 'chapters' / 'cap7.md', "Capitulo 7. Recomendaciones y trabajo futuro"),
    }
    for n, (path, _t) in md_map.items():
        if not path.exists():
            raise FileNotFoundError(path)

    elements_by_cap = {n: md_to_elements(path, title) for n, (path, title) in md_map.items()}

    targets = []
    if args.informe_only:
        targets = [(INFORME, True)]
    elif args.tesis_only:
        targets = [(TESIS, False)]
    else:
        targets = [(TESIS, False), (INFORME, True)]

    reports = []
    for path, toc_safe in targets:
        if not path.exists():
            raise FileNotFoundError(path)
        if not args.dry_run:
            b = backup(path)
            print(f"[backup] {path.name} -> {b.name}")
        rep = inject_into_doc(path, elements_by_cap, toc_safe=toc_safe, dry_run=args.dry_run)
        reports.append(rep)
        print(f"[{'dry-run' if args.dry_run else 'wrote'}] {path.name}: {rep['actions']}")

    # Quick verification of anchors in written docs
    if not args.dry_run:
        for path, _toc in targets:
            doc = Document(str(path))
            blob = "\n".join("".join(t.text or "" for t in el.iter(qn("w:t"))) for el, _k, _tx in iter_block_items(doc))
            checks = {
                "cap4_4.15": "4.15" in blob,
                "cap5_5.3.13": "5.3.13" in blob or "5.3.13" in blob.replace(" ", ""),
                "cap5_friedman": "9,2911" in blob or "9.2911" in blob,
                "cap5_no_1554": "0,1554" not in blob and "0.1554" not in blob,
                "cap6_6.6": "6.6" in blob,
                "cap7_7.7": "7.7" in blob or "Recomendación algorítmica" in blob,
                "topsis_09827": "0,9827" in blob or "0.9827" in blob,
            }
            print(f"[verify] {path.name}: {checks}")
            if not all(checks.values()):
                print("[WARN] some structural anchors missing", file=sys.stderr)
                return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
