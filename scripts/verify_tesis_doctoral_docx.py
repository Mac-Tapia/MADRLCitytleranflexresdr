"""Verifica completitud del informe final doctoral (.docx)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from thesis_doctoral_sections import verify_doctoral_docx  # noqa: E402

DEFAULT = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.is_file():
        print(f"FALTA: {path}")
        return 1
    checks = verify_doctoral_docx(path)
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    return 0 if checks["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
