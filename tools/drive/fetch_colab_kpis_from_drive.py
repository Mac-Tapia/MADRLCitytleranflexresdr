"""Descarga selectiva de KPIs Colab desde Drive (gdown) y renombra por output_dir."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN_FOLDER = "https://drive.google.com/drive/folders/1dsQrpSJVVLFi5Jg9gn30Y0xMSKYwFj05"
OUT = REPO / "outputs" / "_drive_madrl" / "kpis"

WANTED = (
    "results.json",
    "core_kpis.csv",
    "axis_baseline.csv",
    "training_summary.json",
)


def list_folder(url: str) -> list[dict]:
    proc = subprocess.run(
        [sys.executable, "-m", "gdown", "--folder", "--json", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def job_key(title: str) -> str | None:
    """MAAC/E3/data/results.json -> maac_E3_results.json"""
    m = re.search(r"/(HAPPO|MASAC|MATD3|MAAC)/(E[123])/(?:data/)?([^/]+)$", title.replace("\\", "/"))
    if not m:
        # figures/tables/core_kpis.csv
        m = re.search(
            r"/(HAPPO|MASAC|MATD3|MAAC)/(E[123])/figures/tables/([^/]+)$",
            title.replace("\\", "/"),
        )
    if not m:
        return None
    algo, scen, fname = m.group(1), m.group(2), m.group(3)
    stem = fname.replace(".json", "").replace(".csv", "").replace(".md", "")
    if fname == "results.json":
        return f"{algo.lower()}_{scen}_results.json"
    if fname == "core_kpis.csv":
        return f"{algo.lower()}_{scen}_core_kpis.csv"
    if fname == "axis_baseline.csv" or stem == "axis_baseline_comparison":
        return f"{algo.lower()}_{scen}_axis_baseline.csv"
    if fname == "training_summary.json":
        return f"{algo.lower()}_{scen}_training_summary.json"
    return None


def download(file_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-m", "gdown", file_id, "-O", str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{dest.name}: {proc.stderr or proc.stdout}")


def main() -> int:
    items = list_folder(RUN_FOLDER)
    manifest: list[dict] = []
    for item in items:
        if item.get("type") == "application/vnd.google-apps.folder":
            continue
        title = item.get("title") or ""
        if not any(title.endswith(w) or w in title for w in WANTED):
            continue
        local = job_key(title)
        if not local:
            continue
        manifest.append(
            {
                "id": item["id"],
                "drive_path": title,
                "local_name": local,
            }
        )

    manifest_path = OUT.parent / "drive_kpi_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest: {len(manifest)} archivos -> {manifest_path}")

    ok, fail = 0, 0
    for row in manifest:
        dest = OUT / row["local_name"]
        try:
            download(row["id"], dest)
            print(f"OK  {row['local_name']} <- {row['drive_path']}")
            ok += 1
        except RuntimeError as exc:
            print(f"ERR {row['local_name']}: {exc}", file=sys.stderr)
            fail += 1

    print(f"\nDescargados: {ok} OK, {fail} errores")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
