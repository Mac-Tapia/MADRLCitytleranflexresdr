#!/usr/bin/env python3
from pathlib import Path
from docx import Document

p = Path(r"D:\MADRLCitytleranflexresdr\docs\ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_PATCHED.docx")
doc = Document(str(p))
keys = [
    "problema general",
    "objetivo general",
    "hipótesis",
    "hipotesis",
    "no experimental",
    "cuasiexperimental",
    "tipo y nivel",
    "3.1",
    "6.1",
    "veredicto",
    "formulación",
    "formulacion",
    "justificación",
    "justificacion",
    "limitaciones encontradas",
]
for i, para in enumerate(doc.paragraphs):
    t = (para.text or "").strip()
    if not t:
        continue
    low = t.lower()
    if any(k in low for k in keys):
        style = para.style.name if para.style else ""
        print(f"{i}|{style}|{t[:180]}")
