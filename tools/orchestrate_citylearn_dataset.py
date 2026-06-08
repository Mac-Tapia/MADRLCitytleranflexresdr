"""Orchestrate the full Iquitos mixed dataset build for CityLearn v3 training.

The resulting dataset is a synchronized mix of supplied/measured building inputs
and reproducible simulation layers: controlled/uncontrolled loads, pricing
costs, carbon emissions, weather, PV, EV chargers, controlled washing machine
and BESS. The final gate runs before MADRL observation normalization.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
DEFAULT_MANIFEST = ROOT / "outputs" / "dataset_audit" / "dataset_orchestration_manifest.json"


def _rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def _project_path(path: Path | str) -> Path:
    p = Path(path)
    return (ROOT / p).resolve() if not p.is_absolute() else p.resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cmd_text(cmd: list[str]) -> str:
    return " ".join(str(part) for part in cmd)


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def run_stage(
    manifest: dict[str, Any],
    manifest_path: Path,
    label: str,
    cmd: list[str],
    *,
    dry_run: bool,
) -> None:
    stage = {
        "label": label,
        "command": _cmd_text(cmd),
        "started_at": _utc_now(),
        "completed_at": None,
        "return_code": None,
        "status": "planned" if dry_run else "running",
    }
    manifest["stages"].append(stage)
    _write_manifest(manifest_path, manifest)

    print(f"\n[{len(manifest['stages']):02d}] {label}")
    print(f"     {_cmd_text(cmd)}")

    if dry_run:
        stage["completed_at"] = _utc_now()
        stage["return_code"] = 0
        stage["status"] = "dry_run"
        _write_manifest(manifest_path, manifest)
        return

    started = time.perf_counter()
    try:
        completed = subprocess.run(cmd, cwd=ROOT, check=False)
        stage["return_code"] = int(completed.returncode)
        stage["duration_seconds"] = round(time.perf_counter() - started, 3)
        stage["completed_at"] = _utc_now()
        stage["status"] = "ok" if completed.returncode == 0 else "failed"
        _write_manifest(manifest_path, manifest)
        if completed.returncode != 0:
            raise subprocess.CalledProcessError(completed.returncode, cmd)
    except Exception:
        manifest["status"] = "failed"
        manifest["completed_at"] = _utc_now()
        _write_manifest(manifest_path, manifest)
        raise


def build_base_generation_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        "-B",
        "tools/generate_iquitos_dataset.py",
        "--output-dir",
        str(args.dataset_dir),
        "--no-sync-der",
        "--no-validate",
    ]

    if args.skip_cache:
        cmd.append("--skip-cache")
    if args.verbose:
        cmd.append("--verbose")
    if args.buildings:
        cmd.append("--buildings")
        cmd.extend(str(bid) for bid in args.buildings)

    return cmd


def synchronization_commands(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    py = sys.executable
    dataset_dir = str(args.dataset_dir)
    ready_cmd = [
        py,
        "-B",
        "tools/check_training_dataset_ready.py",
        "--dataset-dir",
        dataset_dir,
        "--buildingcsv-dir",
        "CityLearn/data/buildingcsv",
        "--audit-dir",
        "outputs/dataset_audit",
        "--manifest-out",
        "outputs/dataset_audit/training_dataset_ready_manifest.json",
    ]
    if args.skip_citylearn_load:
        ready_cmd.append("--skip-citylearn-load")

    commands = [
        (
            "Destilar cargas reales: no controlada + cooling/DHW controlados desde buildingcsv",
            [
                py,
                "-B",
                "tools/distill_building_loads.py",
                "--dataset-dir",
                dataset_dir,
                "--buildingcsv-dir",
                "CityLearn/data/buildingcsv",
                "--report-out",
                "tools/dataset_docs/distillation_report.csv",
            ],
        ),
        (
            "Sincronizar costos horarios desde facturacion y soporte de red",
            [
                py,
                "-B",
                "tools/distill_building_loads.py",
                "--dataset-dir",
                dataset_dir,
                "--buildingcsv-dir",
                "CityLearn/data/buildingcsv",
                "--report-out",
                "tools/dataset_docs/distillation_report.csv",
            ],
        ),
        (
            "Aplicar PV pvlib/TMY por edificio y potencia nominal en schema",
            [
                py,
                "-B",
                "tools/fix_solar_pvlib.py",
                "--weather-source",
                "tmy",
                "--capacity-method",
                "power-density",
                "--power-density-kwp-m2",
                "0.24",
                "--parking-factor",
                "0.0",
            ],
        ),
        (
            "Dimensionar y cargar EV controlados en charger_*.csv/schema",
            [py, "-B", "tools/dimension_ev_chargers.py"],
        ),
        (
            "Cargar maquinas/controlables por edificio en Washing_Machine_X.csv/schema",
            [py, "-B", "tools/sync_controlled_machines.py"],
        ),
        (
            "Aplicar margen numerico de cooling autosize en schema",
            [py, "-B", "tools/fix_schema_cooling.py"],
        ),
        (
            "Dimensionar y cargar BESS final con PV, EV, red publica y cargas",
            [py, "-B", "tools/size_bess_optimal.py", "--write"],
        ),
        (
            "Auditar DER sincronizados: PV, EV, BESS, red, cargas y picos",
            [py, "-B", "tools/audit_der_sizing.py"],
        ),
        (
            "Auditar procedencia de entrenamiento: reales, simulados, costos y emisiones",
            [py, "-B", "tools/audit_training_dataset_provenance.py"],
        ),
        (
            "Eliminar archivos generados no referenciados por schema.json",
            [py, "-B", "tools/clean_dataset_orphans.py", "--dataset-dir", dataset_dir],
        ),
        (
            "Auditar integridad CSV: NaN, infinitos, columnas y referencias schema",
            [
                py,
                "-B",
                "tools/audit_citylearn_csv_integrity.py",
                "--dataset-dir",
                dataset_dir,
                "--manifest-out",
                "outputs/dataset_audit/csv_integrity_manifest.json",
            ],
        ),
        (
            "Evaluacion exhaustiva del dataset calibrado",
            [py, "-B", "tools/evaluate_dataset.py"],
        ),
        (
            "Analisis profundo de carga CityLearn v3 y normalizacion",
            [py, "-B", "tools/deep_dataset_analysis.py"],
        ),
        (
            "Compuerta final antes de normalizacion MADRL",
            ready_cmd,
        ),
    ]

    # The second distillation command is intentionally omitted at runtime: the
    # first call already writes pricing.csv from the same measured monthly
    # inputs. Keeping costs in the stage name below makes the manifest explicit.
    commands[0] = (
        "Destilar cargas reales y costos horarios desde buildingcsv",
        commands[0][1],
    )
    return [commands[0], *commands[2:]]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build, synchronize, audit and gate the Iquitos CityLearn v3 training dataset."
    )
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--buildings", nargs="+", type=int, default=list(range(1, 18)))
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--skip-base-generation", action="store_true")
    parser.add_argument("--skip-project-context-check", action="store_true")
    parser.add_argument("--skip-citylearn-load", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    args.dataset_dir = _project_path(args.dataset_dir)
    args.manifest_out = _project_path(args.manifest_out)

    manifest = {
        "started_at": _utc_now(),
        "completed_at": None,
        "status": "running" if not args.dry_run else "dry_run",
        "dataset_dir": _rel(args.dataset_dir),
        "purpose": (
            "Construccion sincronizada de dataset mixto CityLearn: datos reales buildingcsv, "
            "cargas controladas/no controladas, costos, emisiones, clima, PV, EV, maquina "
            "controlada, BESS y auditorias antes de normalizacion MADRL."
        ),
        "stages": [],
    }
    _write_manifest(args.manifest_out, manifest)

    try:
        if not args.skip_project_context_check:
            run_stage(
                manifest,
                args.manifest_out,
                "Verificar contexto del proyecto",
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "scripts/verify_project_context.ps1",
                ],
                dry_run=args.dry_run,
            )

        if not args.skip_base_generation:
            run_stage(
                manifest,
                args.manifest_out,
                "Crear dataset base CityLearn sin normalizar",
                build_base_generation_command(args),
                dry_run=args.dry_run,
            )

        for label, cmd in synchronization_commands(args):
            run_stage(manifest, args.manifest_out, label, cmd, dry_run=args.dry_run)

        manifest["status"] = "ready" if not args.dry_run else "dry_run"
        manifest["completed_at"] = _utc_now()
        _write_manifest(args.manifest_out, manifest)
        print(f"\nManifest: {args.manifest_out}")
        print(f"Estado orquestacion: {manifest['status'].upper()}")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\nFallo etapa: {_cmd_text([str(x) for x in exc.cmd])}")
        print(f"Codigo salida: {exc.returncode}")
        return int(exc.returncode) if exc.returncode else 1


if __name__ == "__main__":
    raise SystemExit(main())
