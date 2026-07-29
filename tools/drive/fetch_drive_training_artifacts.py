"""Descarga selectiva timeseries/trace/checkpoints desde Drive via conector OAuth.

Usa tools/skills/google-drive-mcp (DriveClient). No usa gdown ni datos sinteticos.

Carpeta Drive: https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_SCRIPTS = REPO / "tools" / "skills" / "google-drive-mcp" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from auth_manager import AuthManager  # noqa: E402
from config import CREDENTIALS_FILE, TOKEN_FILE  # noqa: E402
from drive_client import DriveClient  # noqa: E402

DRIVE_FOLDER_ID = "1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX"
RUN_ID = "madrl_v3_20260627_164047"
OUT_ROOT = REPO / "outputs" / "_drive_madrl" / "full_data"

WANTED = frozenset(
    {
        "timeseries.csv",
        "trace.csv",
        "checkpoint_manifest.json",
        "results.json",
        "training_summary.json",
        "building_kpis.csv",
        "building_behavior_summary.csv",
        "building_observation_action_schema.csv",
    }
)

JOB_RE = re.compile(
    r"(?:^|/)(?P<run>madrl_v3_\d+_?\d*)/(?P<algo>HAPPO|MASAC|MATD3|MAAC)/(?P<scen>E[123])/data/(?P<fname>[^/]+)$",
    re.IGNORECASE,
)


def auth_status() -> dict:
    return {
        "credentials": CREDENTIALS_FILE.exists(),
        "token": TOKEN_FILE.exists(),
        "authenticated": AuthManager().validate_auth() if TOKEN_FILE.exists() else False,
    }


def resolve_run_folder_id(client: DriveClient, folder_id: str, run_id: str) -> str:
    info = client.get_file_info(folder_id)
    if info.get("name") == run_id:
        return folder_id
    children = client.list_files(folder_id=folder_id, page_size=100)
    for child in children:
        if child.get("is_folder") and child.get("name") == run_id:
            return child["id"]
    raise FileNotFoundError(f"No se encontro carpeta de corrida '{run_id}' bajo {folder_id}")


def local_dest(drive_path: str) -> Path | None:
    m = JOB_RE.search(drive_path.replace("\\", "/"))
    if not m:
        return None
    algo, scen, fname = m.group("algo").upper(), m.group("scen").upper(), m.group("fname")
    if fname not in WANTED:
        return None
    return OUT_ROOT / algo / scen / "data" / fname


def fetch(
    *,
    folder_id: str = DRIVE_FOLDER_ID,
    run_id: str = RUN_ID,
    skip_existing: bool = True,
    dry_run: bool = False,
) -> dict:
    status = auth_status()
    if not status["credentials"]:
        raise RuntimeError(
            "Falta credentials.json. Ejecuta: "
            "powershell -ExecutionPolicy Bypass -File scripts\\setup_google_drive_oauth.ps1"
        )
    if not status["authenticated"]:
        raise RuntimeError(
            "OAuth no autenticado. Ejecuta scripts\\setup_google_drive_oauth.ps1 "
            "o setup_auth en el MCP google-drive."
        )

    client = DriveClient()
    run_folder_id = resolve_run_folder_id(client, folder_id, run_id)
    print(f"Buscando archivos en Drive run_id={run_id} folder_id={run_folder_id} ...")

    matches = client.find_files_recursive(run_folder_id, set(WANTED))
    manifest: list[dict] = []
    ok, skip, fail = 0, 0, 0

    for item in sorted(matches, key=lambda x: x.get("drive_path", "")):
        drive_path = item["drive_path"]
        dest = local_dest(drive_path)
        if dest is None:
            continue
        entry = {
            "drive_path": drive_path,
            "file_id": item["id"],
            "size_bytes": int(item.get("size") or 0),
            "local_path": str(dest),
            "modifiedTime": item.get("modifiedTime"),
        }
        if dest.exists() and skip_existing and dest.stat().st_size > 0:
            entry["status"] = "skip_exists"
            skip += 1
            manifest.append(entry)
            print(f"SKIP {dest.relative_to(REPO)}")
            continue
        if dry_run:
            entry["status"] = "dry_run"
            manifest.append(entry)
            print(f"DRY  {dest.relative_to(REPO)} ({entry['size_bytes']:,} bytes)")
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(item["id"], str(dest))
            entry["status"] = "ok"
            entry["local_bytes"] = dest.stat().st_size
            ok += 1
            print(f"OK   {dest.relative_to(REPO)} ({entry['local_bytes']:,} bytes)")
        except OSError as exc:
            entry["status"] = f"error:{exc}"
            fail += 1
            print(f"ERR  {dest.name}: {exc}")
        manifest.append(entry)

    out = {
        "drive_folder_id": folder_id,
        "run_id": run_id,
        "run_folder_id": run_folder_id,
        "wanted": sorted(WANTED),
        "found_on_drive": len(matches),
        "mapped_jobs": len(manifest),
        "ok": ok,
        "skip": skip,
        "fail": fail,
        "entries": manifest,
    }
    manifest_path = OUT_ROOT / "drive_fetch_manifest.json"
    manifest_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nManifest: {manifest_path}")
    print(f"Descarga: {ok} OK, {skip} skip, {fail} errores")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch MADRL training CSVs from Drive (OAuth).")
    parser.add_argument("--folder-id", default=DRIVE_FOLDER_ID)
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--force", action="store_true", help="Re-descargar aunque exista local")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-auth", action="store_true")
    args = parser.parse_args()

    if args.check_auth:
        print(json.dumps(auth_status(), indent=2))
        return 0 if auth_status()["authenticated"] else 2

    try:
        fetch(
            folder_id=args.folder_id,
            run_id=args.run_id,
            skip_existing=not args.force,
            dry_run=args.dry_run,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
