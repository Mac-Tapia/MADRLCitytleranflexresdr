"""Measure real Google Drive folder sizes via the project's Drive API client."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_SCRIPTS = REPO / "tools" / "skills" / "google-drive-mcp" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from auth_manager import AuthManager  # noqa: E402
from config import CREDENTIALS_FILE, TOKEN_FILE  # noqa: E402
from drive_client import DriveClient  # noqa: E402

DEFAULT_OUTPUTS_FOLDER = "MADRLCitytleranflexresdr/outputs"
SHARED_FOLDER_ID = "1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX"


def _auth_status() -> dict:
    return {
        "credentials_present": CREDENTIALS_FILE.exists(),
        "token_present": TOKEN_FILE.exists(),
        "authenticated": AuthManager().validate_auth() if TOKEN_FILE.exists() else False,
    }


def _print_breakdown(label: str, result: dict) -> None:
    print(f"\n=== {label} ===")
    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return
    print(
        f"  {result.get('folder_name') or result.get('folder_path') or result.get('folder_id')}: "
        f"{result.get('total_gb', 0):.3f} GB "
        f"({result.get('file_count', 0):,} archivos, {result.get('folder_count', 0):,} subcarpetas)"
    )
    for row in result.get("by_child", [])[:30]:
        kind = "dir " if row.get("is_folder") else "file"
        print(
            f"    [{kind}] {row.get('name', '?'):40s} "
            f"{row.get('total_gb', 0):8.3f} GB  files={row.get('file_count', 0):,}"
        )


def _madrl_breakdown(client: DriveClient, run_folder_id: str, run_name: str) -> None:
    run = client.folder_size(folder_id=run_folder_id, max_depth=12)
    _print_breakdown(f"RUN {run_name}", run)
    for row in run.get("by_child", []):
        if not row.get("is_folder"):
            continue
        name = str(row.get("name", "")).upper()
        if name not in {"HAPPO", "MAAC", "MASAC", "MATD3"}:
            continue
        algo = client.folder_size(folder_id=row["id"], max_depth=10)
        _print_breakdown(f"  {run_name}/{name}", algo)
        for scen in algo.get("by_child", []):
            if scen.get("is_folder"):
                scen_res = client.folder_size(folder_id=scen["id"], max_depth=8)
                print(
                    f"      {scen.get('name'):6s} "
                    f"{scen_res.get('total_gb', 0):8.3f} GB  "
                    f"files={scen_res.get('file_count', 0):,}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Real Drive folder sizes (OAuth required).")
    parser.add_argument("--folder-id", default=None, help="Drive folder ID")
    parser.add_argument("--folder-path", default=None, help="Path under My Drive")
    parser.add_argument(
        "--scan-outputs",
        action="store_true",
        help="List all madrl_v3_* under MADRLCitytleranflexresdr/outputs with GB",
    )
    parser.add_argument(
        "--run-id",
        default="madrl_v3_20260627_164047",
        help="Canonical run folder name for per-MADRL breakdown",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    status = _auth_status()
    if not status["credentials_present"]:
        msg = (
            "Falta tools/skills/google-drive-mcp/data/credentials.json. "
            "Sigue README del conector y ejecuta setup_auth una vez."
        )
        if args.json:
            print(json.dumps({"error": msg, **status}, indent=2))
        else:
            print(msg)
            print(f"Estado: {status}")
        return 2
    if not status["authenticated"]:
        msg = "Token OAuth ausente o expirado. Ejecuta setup_auth en el MCP google-drive."
        if args.json:
            print(json.dumps({"error": msg, **status}, indent=2))
        else:
            print(msg)
            print(f"Estado: {status}")
        return 2

    client = DriveClient()

    if args.scan_outputs:
        outputs = client.folder_size(folder_path=DEFAULT_OUTPUTS_FOLDER, max_depth=2)
        runs = [
            row
            for row in outputs.get("by_child", [])
            if row.get("is_folder") and str(row.get("name", "")).startswith("madrl_v3_")
        ]
        rows = []
        for run in sorted(runs, key=lambda r: r["name"]):
            detail = client.folder_size(folder_id=run["id"], max_depth=12)
            rows.append(
                {
                    "name": run["name"],
                    "total_gb": detail.get("total_gb", 0),
                    "file_count": detail.get("file_count", 0),
                    "active_canonical": run["name"] == args.run_id,
                }
            )
        if args.json:
            print(json.dumps({"runs": rows, "outputs_parent_gb": outputs.get("total_gb")}, indent=2))
            return 0
        print(f"outputs/ total: {outputs.get('total_gb', 0):.2f} GB")
        for row in rows:
            flag = " <- CANONICO" if row["active_canonical"] else ""
            print(
                f"  {row['name']:32s} {row['total_gb']:8.2f} GB  "
                f"files={row['file_count']:,}{flag}"
            )
        return 0

    if args.folder_id or args.folder_path:
        result = client.folder_size(
            folder_id=args.folder_id,
            folder_path=args.folder_path,
            max_depth=12,
        )
    else:
        result = client.folder_size(folder_id=SHARED_FOLDER_ID, max_depth=2)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    _print_breakdown("CARPETA", result)

    if args.run_id:
        for row in result.get("by_child", []):
            if row.get("is_folder") and row.get("name") == args.run_id:
                _madrl_breakdown(client, row["id"], args.run_id)
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
