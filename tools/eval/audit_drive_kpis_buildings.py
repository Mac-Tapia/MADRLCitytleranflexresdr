#!/usr/bin/env python3
"""Audit Drive KPI extracts: per MADRL x E1/E2/E3 x 17 buildings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KPI = REPO / "outputs" / "_drive_madrl" / "kpis"
ALGOS = ("happo", "masac", "matd3", "maac")
SCENS = ("E1", "E2", "E3")
EXPECTED_BUILDINGS = 17
EXPECTED_BKPI_ROWS = 1275  # 17 x 75 metrics per run on Drive


def audit_job(algo: str, scen: str) -> dict:
    path = KPI / f"{algo}_{scen}_results.json"
    row = {
        "job": f"{algo.upper()}/{scen}",
        "results_json": path.exists(),
        "core_kpis_csv": (KPI / f"{algo}_{scen}_core_kpis.csv").exists(),
        "training_summary": (KPI / f"{algo}_{scen}_training_summary.json").exists(),
        "axis_baseline": (KPI / f"{algo}_{scen}_axis_baseline.csv").exists(),
    }
    if not path.exists():
        row["status"] = "MISSING"
        return row

    data = json.loads(path.read_text(encoding="utf-8"))
    row["status"] = str(data.get("status") or "ok")
    row["episodes_recorded"] = data.get("episodes_recorded")
    resume = (data.get("hyperparameters") or {}).get("job_resume") or {}
    if row["episodes_recorded"] is None:
        row["episodes_recorded"] = resume.get("completed_episodes")

    report = data.get("citylearn_v3_report") or {}
    all_values = report.get("all_values") or {}
    row["district_kpi_count"] = len(all_values) if isinstance(all_values, dict) else 0
    row["has_audited_kpis"] = row["district_kpi_count"] > 0

    bd = data.get("building_detail") or {}
    row["building_count"] = data.get("building_count")
    bk = bd.get("building_kpis") or {}
    bb = bd.get("building_behavior_summary") or {}
    row["building_kpis_rows"] = int(bk.get("rows") or 0)
    row["building_behavior_rows"] = int(bb.get("rows") or 0)
    row["building_kpis_csv_on_drive"] = bk.get("csv", "")
    row["buildings_ok"] = row["building_behavior_rows"] == EXPECTED_BUILDINGS
    row["building_kpis_ok"] = row["building_kpis_rows"] == EXPECTED_BKPI_ROWS
    row["complete_50ep"] = int(row.get("episodes_recorded") or 0) >= 50
    row["salvage"] = data.get("salvage_reason") or data.get("status") == "completed_with_salvage"
    return row


def main() -> int:
    rows = [audit_job(a, s) for a in ALGOS for s in SCENS]

    print("=" * 100)
    print("  AUDITORIA KPIs en Drive (mirror: outputs/_drive_madrl/kpis/)")
    print("  Run: madrl_v3_20260627_164047")
    print("=" * 100)
    hdr = (
        f"{'Job':<12} {'Ep':>3} {'KPI dist':>8} {'Edif':>4} "
        f"{'b_kpi':>6} {'b_beh':>5} {'core':>4} {'50ep':>4} {'Estado'}"
    )
    print(hdr)
    print("-" * 100)

    ok_jobs = 0
    partial = 0
    missing_kpi = 0
    for r in rows:
        if not r.get("results_json"):
            print(f"{r['job']:<12}  —   MISSING results.json")
            missing_kpi += 1
            continue
        ep = r.get("episodes_recorded", "?")
        kpi_n = r.get("district_kpi_count", 0)
        bc = r.get("building_count", "?")
        bkr = r.get("building_kpis_rows", 0)
        bbr = r.get("building_behavior_rows", 0)
        core = "Y" if r.get("core_kpis_csv") else "N"
        ep50 = "Y" if r.get("complete_50ep") else "N"
        if r.get("has_audited_kpis") and r.get("building_kpis_ok") and r.get("buildings_ok"):
            estado = "OK completo"
            ok_jobs += 1
        elif r.get("salvage"):
            estado = "SALVAGE sin KPI"
            partial += 1
        else:
            estado = "INCOMPLETO"
            missing_kpi += 1
        print(
            f"{r['job']:<12} {str(ep):>3} {kpi_n:>8} {str(bc):>4} "
            f"{bkr:>6} {bbr:>5} {core:>4} {ep50:>4} {estado}"
        )

    print("=" * 100)
    print(f"  Completos (KPI distrito + 17 edificios x 75 metricas): {ok_jobs}/12")
    print(f"  HAPPO salvage sin KPI auditado: {partial}/12")
    print(f"  Incompletos / faltantes: {missing_kpi}/12")
    print()
    print("  En Drive (por job completo), por cada uno de los 17 edificios:")
    print("    - data/building_kpis.csv  (1275 filas = 17 x 75 KPIs)")
    print("    - data/building_behavior_summary.csv  (17 filas)")
    print("    - figures/tables/building_kpis.csv  (copia en tablas)")
    print("  KPIs de distrito (comunidad):")
    print("    - results.json -> citylearn_v3_report.all_values (~50+ metricas)")
    print("    - figures/tables/core_kpis.csv")
    print("  HAPPO E1/E2/E3: entreno 49/50 ep, crash VecEnvWrapper -> NO genero KPIs finales")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
