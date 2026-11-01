#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Follow-up: Tesis Resumen/Abstract H0G formal + Capa A numbers."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from docx import Document

REPO = Path(__file__).resolve().parents[2]
PATH = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx"
BACKUP = REPO / "outputs" / "_word_backups"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

SUBS = [
    (
        "ni respalda HE11/HE21/HE31; H0G se rechaza por Friedman integrado (p = 0,0096) "
        "con KW GLOBAL exploratorio no significativo (p = 0,4044; Capa A).",
        "ni respalda HE11/HE21/HE31; se rechaza H0G (Friedman GLOBAL χ² = 9,2911, "
        "p = 0,0096, Kendall's W = 0,1787) y se respalda H1G (sin ganador único); "
        "KW GLOBAL no es significativo (H = 1,8108, p = 0,4044).",
    ),
    (
        "and does not support HE11/HE21/HE31; H0G is rejected via Friedman (p=0.0096) "
        "while exploratory KW GLOBAL is non-significant (p=0.4044; Layer A).",
        "and does not support HE11/HE21/HE31; H0G is rejected (Friedman GLOBAL "
        "χ²=9.2911, p=0.0096, Kendall's W=0.1787) and H1G is supported (no unique "
        "winner); KW GLOBAL is non-significant (H=1.8108, p=0.4044).",
    ),
]


def rewrite(paragraph, new_text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(new_text)


def main() -> int:
    BACKUP.mkdir(parents=True, exist_ok=True)
    bak = BACKUP / f"{PATH.stem}_resumen_h0g_align_{STAMP}{PATH.suffix}"
    shutil.copy2(PATH, bak)
    doc = Document(str(PATH))
    n = 0
    samples = []
    for p in doc.paragraphs:
        text = p.text or ""
        new = text
        for old, repl in SUBS:
            if old in new:
                new = new.replace(old, repl)
                n += 1
                samples.append(old[:60])
        if new != text:
            rewrite(p, new)
    doc.save(str(PATH))
    doc2 = Document(str(PATH))
    after = {}
    for i in (24, 28):
        t = doc2.paragraphs[i].text or ""
        idx = t.find("HE11")
        after[f"p{i}"] = t[idx : idx + 320] if idx >= 0 else t[:200]
    report = {
        "backup": bak.name,
        "n": n,
        "samples": samples,
        "after": after,
        "ok": n == 2
        and "9,2911" in after.get("p24", "")
        and "9.2911" in after.get("p28", ""),
    }
    out = REPO / "outputs" / f"_patch_tesis_resumen_h0g_align_{STAMP}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
