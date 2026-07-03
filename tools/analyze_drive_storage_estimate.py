"""Estimate Drive storage breakdown for MADRL Colab run from KPI exports + code defaults."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KPIS = REPO / "outputs" / "_drive_madrl" / "kpis"
RUN_ID = "madrl_v3_20260627_164047"

# Checkpoint MB per scenario (order-of-magnitude from hidden sizes + agent count)
CKPT_MB_PER_JOB = {
    "HAPPO": 150,  # 17 actors + critic + value_norm x ~50 saves + heavy TensorBoard logs
    "MAAC": 90,    # 52 checkpoint files reported
    "MASAC": 70,   # 12 bundles but large replay-related artifacts
    "MATD3": 110,  # 17 policies x actor+critic x 34 saves
}
BYTES_PER_TS_ROW = 140
BYTES_PER_TRACE_ROW = 900  # compact trace @ interval 8760 still has building cols


def load_jobs() -> list[dict]:
    jobs: list[dict] = []
    for path in sorted(KPIS.glob("*_results.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out = (data.get("output_dir") or "").rstrip("/")
        if RUN_ID not in out and not out.endswith(("/E1", "/E2", "/E3")):
            continue
        audit = data.get("artifact_audit") or {}
        layout = data.get("artifact_layout") or {}
        hp = data.get("hyperparameters") or {}
        jobs.append(
            {
                "file": path.name,
                "algo": str(data.get("algorithm", "?")).upper(),
                "scenario": str(data.get("scenario", "?")).upper(),
                "episodes_recorded": int(data.get("episodes_recorded") or 0),
                "checkpoint_count": int(data.get("checkpoint_count") or 0),
                "timeseries_rows": int(data.get("timeseries_rows") or audit.get("timeseries_rows") or 0),
                "trace_rows": int(data.get("trace_rows") or audit.get("trace_rows") or 0),
                "root_timeseries": bool(layout.get("root_timeseries_csv")),
                "root_trace": bool(layout.get("root_trace_csv")),
                "trace_detail": layout.get("trace_detail") or hp.get("trace_detail"),
                "trace_interval": layout.get("trace_record_interval") or hp.get("trace_record_interval"),
                "n_rollout": int(hp.get("n_rollout_threads") or 1),
                "status": data.get("status"),
            }
        )
    return jobs


def mirror_stats() -> dict:
    mirror = REPO / "outputs" / "_drive_madrl" / "outputs" / RUN_ID
    if not mirror.is_dir():
        return {"path": str(mirror), "exists": False}
    by_algo: dict[str, int] = defaultdict(int)
    total = 0
    n_files = 0
    for f in mirror.rglob("*"):
        if not f.is_file():
            continue
        sz = f.stat().st_size
        total += sz
        n_files += 1
        parts = f.parts
        for i, p in enumerate(parts):
            if p in {"HAPPO", "MASAC", "MATD3", "MAAC"} and i + 1 < len(parts):
                by_algo[p] += sz
                break
    return {
        "path": str(mirror),
        "exists": True,
        "files": n_files,
        "total_mb": total / 1e6,
        "by_algo_mb": {k: v / 1e6 for k, v in sorted(by_algo.items())},
    }


def local_outputs_scan() -> list[dict]:
    """Scan any local madrl_v3_* or training output folders for size reference."""
    rows: list[dict] = []
    out_root = REPO / "outputs"
    for d in sorted(out_root.glob("madrl_v3_*")):
        if not d.is_dir():
            continue
        total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        rows.append({"name": d.name, "gb": total / 1e9, "kind": "madrl_v3"})
    return rows


def main() -> None:
    jobs = load_jobs()
    print(f"Run analizado: {RUN_ID}")
    print(f"Jobs con results.json exportado: {len(jobs)}\n")

    print("=== POR JOB (filas reales en results.json) ===")
    print(f"{'Algo':6} {'Scen':4} {'Ep':>3} {'ckpt':>5} {'ts_rows':>10} {'tr_rows':>8} {'roll':>4} status")
    for j in jobs:
        print(
            f"{j['algo']:6} {j['scenario']:4} {j['episodes_recorded']:3d} "
            f"{j['checkpoint_count']:5d} {j['timeseries_rows']:10,d} {j['trace_rows']:8,d} "
            f"{j['n_rollout']:4d} {j['status'] or 'ok'}"
        )

    print("\n=== ESTIMACION POR MADRL (12 jobs = 4 algos x 3 escenarios) ===")
    by_algo: dict[str, dict] = defaultdict(lambda: {"jobs": 0, "ts_rows": 0, "tr_rows": 0, "ckpt": 0})
    for j in jobs:
        a = by_algo[j["algo"]]
        a["jobs"] += 1
        a["ts_rows"] += j["timeseries_rows"]
        a["tr_rows"] += j["trace_rows"]
        a["ckpt"] += j["checkpoint_count"]

    grand = {"csv_gb": 0.0, "ckpt_gb": 0.0, "tb_gb": 0.0, "fig_gb": 0.0}
    for algo in ("HAPPO", "MASAC", "MATD3", "MAAC"):
        v = by_algo.get(algo, {})
        ts_gb = v.get("ts_rows", 0) * BYTES_PER_TS_ROW / 1e9
        tr_gb = v.get("tr_rows", 0) * BYTES_PER_TRACE_ROW / 1e9
        csv_gb = ts_gb + tr_gb
        ckpt_gb = v["jobs"] * CKPT_MB_PER_JOB.get(algo, 80) / 1024
        tb_gb = (150 if algo == "HAPPO" else 20) * v["jobs"] / 1024  # TensorBoard events
        fig_gb = 0.05 * v["jobs"]
        total_gb = csv_gb + ckpt_gb + tb_gb + fig_gb
        grand["csv_gb"] += csv_gb
        grand["ckpt_gb"] += ckpt_gb
        grand["tb_gb"] += tb_gb
        grand["fig_gb"] += fig_gb
        print(
            f"\n{algo} ({v.get('jobs',0)} escenarios):"
            f"\n  timeseries.csv  ~{ts_gb:6.2f} GB  ({v.get('ts_rows',0):,} filas)"
            f"\n  trace.csv       ~{tr_gb:6.2f} GB  ({v.get('tr_rows',0):,} filas)"
            f"\n  checkpoints     ~{ckpt_gb:6.2f} GB  ({v.get('ckpt',0)} archivos contados)"
            f"\n  TensorBoard     ~{tb_gb:6.2f} GB  (logs HAPPO muy pesados)"
            f"\n  figuras/tablas  ~{fig_gb:6.2f} GB"
            f"\n  SUBTOTAL        ~{total_gb:6.2f} GB"
        )

    run_total = sum(grand.values())
    print(f"\n=== TOTAL RUN CANONICO {RUN_ID} (1 carpeta) ===")
    print(f"  CSV (ts+trace)     ~{grand['csv_gb']:.1f} GB")
    print(f"  Checkpoints        ~{grand['ckpt_gb']:.1f} GB")
    print(f"  TensorBoard        ~{grand['tb_gb']:.1f} GB")
    print(f"  Figuras            ~{grand['fig_gb']:.1f} GB")
    print(f"  ESTIMADO RUN       ~{run_total:.1f} GB")

    print("\n=== CAUSA PROBABLE >130 GB EN DRIVE ===")
    print("  1. Varias carpetas madrl_v3_* (reintentos Colab) — celda 2.1c lista duplicados")
    print("  2. HAPPO: checkpoint cada ep + 12 rollouts + logs TB por 17 agentes")
    print("  3. MATD3: timeseries inflado (437k+ filas/job vs ~350k esperadas)")
    print("  4. Repo git + dataset Iquitos + outputs/_archive si tambien estan en Drive")

    mirror = mirror_stats()
    if mirror.get("exists"):
        print(f"\n=== ESPEJO LOCAL PARCIAL (solo fragmento descargado) ===")
        print(f"  {mirror['path']}: {mirror['files']} archivos, {mirror['total_mb']:.1f} MB")
        for algo, mb in mirror.get("by_algo_mb", {}).items():
            print(f"    {algo}: {mb:.1f} MB")

    local = local_outputs_scan()
    if local:
        print("\n=== CARPETAS madrl_v3_* LOCALES (referencia) ===")
        for row in local:
            print(f"  {row['name']}: {row['gb']:.2f} GB")


if __name__ == "__main__":
    main()
