#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Atomically replace Capítulos 4–7 in Word canons from markdown sources.

Deletes body from Cap.4 heading through (but not including) Referencias, then
inserts Cap.4 + Cap.5 + Cap.6 + Cap.7 built from docs/chapters/*.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from inject_md_chapters_4_7_to_canons import (  # noqa: E402
    CAP_RE,
    REF_RE,
    backup,
    is_toc_heading,
    iter_block_items,
    md_to_elements,
)
from thesis_word_canons import INFORME, TESIS, require_tesis  # noqa: E402

CAPS_DIR = REPO / 'docs' / 'chapters'


def find_cap4_and_refs(doc: Document, *, toc_safe: bool) -> tuple[int, int, list]:
    items = list(iter_block_items(doc))
    start = None
    end = None
    for i, (_el, kind, text) in enumerate(items):
        if kind != "p":
            continue
        t = text.strip()
        if len(t) > 200:
            continue
        if toc_safe and is_toc_heading(t):
            continue
        if start is None and CAP_RE[4].search(t):
            start = i
            continue
        if start is not None and REF_RE.search(t):
            end = i
            break
    if start is None:
        raise RuntimeError("Capítulo 4 no encontrado")
    if end is None:
        raise RuntimeError("Referencias no encontradas tras Capítulo 4")
    return start, end, items


def replace_cap4_through_refs(path: Path, combined: list, *, toc_safe: bool, dry_run: bool) -> dict:
    doc = Document(str(path))
    start, end, items = find_cap4_and_refs(doc, toc_safe=toc_safe)
    report = {
        "path": str(path),
        "start": start,
        "end": end,
        "old_blocks": end - start,
        "new_blocks": len(combined),
    }
    if dry_run:
        return report
    body = doc.element.body
    anchor = items[end][0]
    for el, _k, _t in items[start:end]:
        body.remove(el)
    # Forward insert: first element before Referencias, then addnext chain.
    cursor = None
    for child in combined:
        if cursor is None:
            anchor.addprevious(child)
            cursor = child
        else:
            cursor.addnext(child)
            cursor = child
    doc.save(str(path))
    return report


def verify(path: Path) -> dict:
    doc = Document(str(path))
    items = list(iter_block_items(doc))
    idxs = []
    for i, (kind, text) in enumerate((k, t) for k, _e, t in [(it[1], it[0], it[2]) for it in items]):
        pass
    # rebuild simply
    idxs = []
    for i, (_el, kind, text) in enumerate(items):
        if kind != "p":
            continue
        t = text.strip()
        if len(t) > 200:
            continue
        if CAP_RE[4].search(t) or CAP_RE[5].search(t) or CAP_RE[6].search(t) or CAP_RE[7].search(t) or REF_RE.search(t):
            idxs.append((i, t[:70]))
    blob = "\n".join(t for _e, k, t in items if k == "p")
    checks = {
        "headings": idxs,
        "has_5_3_13": "5.3.13" in blob,
        "has_5_8": "5.8" in blob,
        "has_6_6": "6.6" in blob,
        "has_7_7": "7.7" in blob or "Recomendacion algoritmica" in blob or "Recomendación algorítmica" in blob,
        "has_pe1": "Respuesta a PE.1" in blob,
        "friedman": "9,2911" in blob or "9.2911" in blob,
        "topsis": "0,9827" in blob or "0.9827" in blob,
        "no_1554": "0,1554" not in blob and "0.1554" not in blob,
    }
    # block sizes between Cap4..Ref
    cap_idxs = [(i, t) for i, t in idxs]
    sizes = {}
    for a, b in zip(cap_idxs, cap_idxs[1:]):
        sizes[a[1][:20]] = b[0] - a[0]
    checks["sizes"] = sizes
    checks["cap5_ok"] = sizes.get("Capitulo 5. Resultad", 0) >= 150 or any(
        v >= 150 and "Capitulo 5" in k for k, v in ((a[1], b[0] - a[0]) for a, b in zip(cap_idxs, cap_idxs[1:]))
    )
    # clearer cap5 size
    for a, b in zip(cap_idxs, cap_idxs[1:]):
        if CAP_RE[5].search(a[1]):
            checks["cap5_blocks"] = b[0] - a[0]
        if CAP_RE[7].search(a[1]):
            checks["cap7_blocks"] = b[0] - a[0]
    checks["ok"] = (
        checks["has_5_3_13"]
        and checks["has_5_8"]
        and checks["has_6_6"]
        and checks["has_7_7"]
        and checks["has_pe1"]
        and checks["friedman"]
        and checks["topsis"]
        and checks["no_1554"]
        and checks.get("cap5_blocks", 0) >= 150
        and checks.get("cap7_blocks", 0) >= 20
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tesis-only", action="store_true")
    parser.add_argument("--informe-only", action="store_true")
    args = parser.parse_args()

    require_tesis()
    md_map = {
        4: (REPO / 'docs' / 'chapters' / 'cap4.md', "Capitulo 4. Desarrollo e implementacion de la coordinacion energetica multiobjetivo mediante MADRL"),
        5: (REPO / 'docs' / 'chapters' / 'cap5.md', "Capitulo 5. Resultados, efectos diferenciales y desempeno algoritmico"),
        6: (REPO / 'docs' / 'chapters' / 'cap6.md', "Capitulo 6. Conclusiones"),
        7: (REPO / 'docs' / 'chapters' / 'cap7.md', "Capitulo 7. Recomendaciones y trabajo futuro"),
    }
    combined: list = []
    for n in (4, 5, 6, 7):
        path, title = md_map[n]
        els = md_to_elements(path, title)
        print(f"[build] Cap {n}: {len(els)} blocks from {path.name}")
        combined.extend(els)

    targets = []
    if args.informe_only:
        targets = [(INFORME, True)]
    elif args.tesis_only:
        targets = [(TESIS, False)]
    else:
        targets = [(TESIS, False), (INFORME, True)]

    rc = 0
    for path, toc_safe in targets:
        if not args.dry_run:
            b = backup(path)
            print(f"[backup] {path.name} -> {b.name}")
        rep = replace_cap4_through_refs(path, combined, toc_safe=toc_safe, dry_run=args.dry_run)
        print(f"[{'dry' if args.dry_run else 'wrote'}] {rep}")
        if not args.dry_run:
            checks = verify(path)
            print(f"[verify] {path.name} ok={checks['ok']} cap5_blocks={checks.get('cap5_blocks')} cap7_blocks={checks.get('cap7_blocks')}")
            print(f"         sizes={checks['sizes']}")
            if not checks["ok"]:
                rc = 2
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
