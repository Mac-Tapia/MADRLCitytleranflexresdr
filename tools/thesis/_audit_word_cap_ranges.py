#!/usr/bin/env python
# -*- coding: utf-8 -*-
from docx import Document
from docx.oxml.ns import qn
import re

CAP = re.compile(r"(?i)^\s*cap[ií]tulo\s*([4-7])\b")
REF = re.compile(r"(?i)^\s*(referencias\b|bibliograf)")


def iter_items(doc):
    for child in list(doc.element.body.iterchildren()):
        tag = child.tag
        if tag == qn("w:p"):
            texts = [t.text or "" for t in child.iter(qn("w:t"))]
            yield "p", "".join(texts).strip()
        elif tag == qn("w:tbl"):
            texts = [t.text or "" for t in child.iter(qn("w:t"))]
            yield "tbl", "".join(texts)[:60]


def audit(path: str) -> None:
    doc = Document(path)
    items = list(iter_items(doc))
    idxs = []
    for i, (k, t) in enumerate(items):
        if k == "p" and (CAP.match(t) or REF.match(t)):
            idxs.append((i, t[:90]))
    print("====", path)
    for x in idxs:
        print(x)
    for a, b in zip(idxs, idxs[1:]):
        print(f"  blocks {b[0]-a[0]}: {a[1][:28]} -> {b[1][:28]}")
    blob = "\n".join(t for k, t in items if k == "p")
    for s in [
        "5.1 ",
        "5.3.13",
        "5.4.13",
        "5.5.13",
        "5.8 ",
        "6.6 ",
        "7.7 ",
        "Respuesta a PE.1",
        "0,9827",
        "9,2911",
        "0,1554",
    ]:
        print(f"  [{s!r}] -> {s in blob}")


if __name__ == "__main__":
    audit("docs/tesis.docx")
    audit("docs/informe.docx")
