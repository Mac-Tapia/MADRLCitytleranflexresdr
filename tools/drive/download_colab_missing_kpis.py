"""Descarga KPIs faltantes/corregidos desde Drive y renombra por output_dir."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "outputs" / "_drive_madrl" / "kpis"

# IDs verificados en log gdown (terminal 509375) por carpeta data/ del job
DOWNLOADS: list[tuple[str, str]] = [
    # MAAC E3 (50 ep, checkpoint_episode_50 en Drive)
    ("1IZULxjSCg29GqtSZXmDKQfTX4vbTIxLT", "maac_E3_results.json"),
    ("1zw_gxGNBXgSc6DXD4OKglyI8HG-nR-Xa", "maac_E3_core_kpis.csv"),
    ("1n-t7FtKKVs0QAigi69UOQS3SVOJK74Um", "maac_E3_axis_baseline.csv"),
    # MASAC E3
    ("1wfHw6iVaQTWD532AqThF7up6JQYWkvQx", "masac_E3_results.json"),
    ("13C1AT6tRMyfqGRy5_8eCC4GkaCOv5SXQ", "masac_E3_core_kpis.csv"),
    ("1xooGJANpzROxsjvh8D05laNv80WzVbCX", "masac_E3_axis_baseline.csv"),
    # MASAC E2 (re-descarga; local masac_E2 era duplicado de E1)
    ("1q5kVW2wfsfxOXxK5S46pBoFc5EJwRAke", "masac_E2_results.json"),
    ("1W9GuDtwxbh8LSLOh404uWUmJFR-PSA4o", "masac_E2_core_kpis.csv"),
    # HAPPO (re-descarga; renombrar luego por output_dir)
    ("1olxD27rUnzhJEdrKIh2SA6Paz_Vqnmqa", "_tmp_happo_E1_results.json"),
    ("1WPRaW19wNcXBkxKDmEGatqx9TPqoURWD", "_tmp_happo_slot2_results.json"),
    ("1SwUdTL3rVcpmvqQMnPQEX0Shlsu8NCTc", "_tmp_happo_slot3_results.json"),
]


def gdown(file_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-m", "gdown", file_id, "-O", str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)


def scenario_from_output_dir(output_dir: str) -> tuple[str, str] | None:
    m = re.search(r"/(HAPPO|MASAC|MATD3|MAAC)/(E[123])$", output_dir.rstrip("/"))
    if not m:
        return None
    return m.group(1).lower(), m.group(2)


def normalize_results_json(path: Path) -> Path | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = data.get("output_dir") or ""
    key = scenario_from_output_dir(out)
    if not key:
        return None
    algo, scen = key
    target = OUT / f"{algo}_{scen}_results.json"
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


def main() -> int:
    for fid, name in DOWNLOADS:
        dest = OUT / name
        try:
            gdown(fid, dest)
            print(f"OK  {name}")
        except RuntimeError as exc:
            print(f"ERR {name}: {exc}", file=sys.stderr)

    for tmp in OUT.glob("_tmp_happo_*_results.json"):
        target = normalize_results_json(tmp)
        if target:
            print(f"REN {tmp.name} -> {target.name}")
            tmp.unlink()

    # Validar MAAC/MASAC E3
    for name in ("maac_E3_results.json", "masac_E3_results.json"):
        path = OUT / name
        if not path.exists():
            print(f"MISSING {name}", file=sys.stderr)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        out = data.get("output_dir", "")
        rec = data.get("episodes_recorded", "?")
        print(f"CHK {name}: output_dir ends {out[-20:]} episodes_recorded={rec}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
