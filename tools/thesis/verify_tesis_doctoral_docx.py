"""Verifica completitud del informe final doctoral (.docx).

Por defecto verifica el Word Tesis canónico.
Con --all-canons verifica los 2 Word vigentes (Tesis + Informe).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from docx import Document  # noqa: E402
from thesis_doctoral_sections import verify_doctoral_docx  # noqa: E402
from thesis_word_canons import CANONS, TESIS  # noqa: E402

CAP5_RE = re.compile(r"(?i)cap[ií]tulo\s*5\b")


def has_cap5(path: Path) -> bool:
    doc = Document(str(path))
    return any(CAP5_RE.search((p.text or "").strip()) for p in doc.paragraphs[:400])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=None)
    parser.add_argument(
        "--all-canons",
        action="store_true",
        help="Verificar los 2 Word canónicos (existencia + Cap.5 + Tesis completa)",
    )
    args = parser.parse_args()

    if args.all_canons:
        report: dict = {"canons": [], "ok": True}
        for path in CANONS:
            entry: dict = {"file": path.name, "exists": path.is_file()}
            if not path.is_file():
                entry["ok"] = False
                report["ok"] = False
                report["canons"].append(entry)
                continue
            entry["cap5"] = has_cap5(path)
            if path.resolve() == TESIS.resolve():
                checks = verify_doctoral_docx(path)
                entry["doctoral"] = {
                    "complete": checks.get("complete"),
                    "tables_count": checks.get("tables_count"),
                    "images_count": checks.get("images_count"),
                }
                entry["ok"] = bool(checks.get("complete") and entry["cap5"])
            else:
                entry["ok"] = bool(entry["cap5"])
            if not entry["ok"]:
                report["ok"] = False
            report["canons"].append(entry)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 2

    path = args.path or TESIS
    if not path.is_file():
        print(f"FALTA: {path}")
        return 1
    checks = verify_doctoral_docx(path)
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    return 0 if checks["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
