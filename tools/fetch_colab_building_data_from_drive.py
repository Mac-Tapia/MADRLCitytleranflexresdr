"""Descarga CSVs por edificio desde Drive (gdown) al mirror local full_data/."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

import gdown

REPO = Path(__file__).resolve().parents[1]
RUN_FOLDER = "https://drive.google.com/drive/folders/1dsQrpSJVVLFi5Jg9gn30Y0xMSKYwFj05"
OUT_ROOT = REPO / "outputs" / "_drive_madrl" / "full_data"

WANTED = (
    "building_kpis.csv",
    "building_behavior_summary.csv",
    "building_observation_action_schema.csv",
)


def job_dest(rel_path: str) -> Path | None:
    m = re.search(
        r"(?:^|/)(HAPPO|MASAC|MATD3|MAAC)/(E[123])/data/([^/]+)$",
        rel_path.replace("\\", "/"),
    )
    if not m:
        return None
    algo, scen, fname = m.group(1), m.group(2), m.group(3)
    if fname not in WANTED:
        return None
    return OUT_ROOT / algo / scen / "data" / fname


def collect_from_tree(root: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for src in root.rglob("*"):
        if not src.is_file():
            continue
        rel = str(src.relative_to(root)).replace("\\", "/")
        dest = job_dest(rel)
        if dest is not None:
            pairs.append((src, dest))
    return pairs


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="drive_building_") as tmp:
        tmp_root = Path(tmp)
        print(f"Descargando carpeta Drive -> {tmp_root} ...")
        gdown.download_folder(
            url=RUN_FOLDER,
            output=str(tmp_root),
            quiet=False,
            use_cookies=False,
            remaining_ok=True,
        )
        pairs = collect_from_tree(tmp_root)

    manifest: list[dict] = []
    ok, fail, skip = 0, 0, 0
    for src, dest in pairs:
        manifest.append({"source": str(src), "local_path": str(dest)})
        if dest.exists() and dest.stat().st_size > 0:
            print(f"SKIP {dest.relative_to(REPO)} (exists)")
            skip += 1
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"OK   {dest.relative_to(REPO)}")
            ok += 1
        except OSError as exc:
            print(f"ERR  {dest.name}: {exc}")
            fail += 1

    manifest_path = OUT_ROOT / "building_data_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest: {len(manifest)} archivos -> {manifest_path}")
    print(f"\nCopiados: {ok} OK, {skip} skip, {fail} errores")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
