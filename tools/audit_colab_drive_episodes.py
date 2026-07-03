"""Audita episodios y mapeo de artefactos Colab/Drive en outputs/_drive_madrl/kpis/."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KPIS = REPO / "outputs" / "_drive_madrl" / "kpis"
ALGOS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")


def load_results(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def scenario_from_output_dir(output_dir: str) -> str | None:
    for scen in SCENARIOS:
        if output_dir.rstrip("/").endswith(f"/{scen}"):
            return scen
    return None


def audit_results_files() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(KPIS.glob("*_results.json")):
        data = load_results(path)
        hp = data.get("hyperparameters") or {}
        jr = hp.get("job_resume") or {}
        audit = data.get("artifact_audit") or {}
        out = data.get("output_dir") or ""
        true_scen = scenario_from_output_dir(out) or data.get("scenario", "?")
        name_parts = path.stem.replace("_results", "").rsplit("_", 1)
        name_scen = name_parts[-1].upper() if len(name_parts) == 2 else "?"
        rows.append(
            {
                "file": path.name,
                "algorithm": data.get("algorithm", "?"),
                "filename_scenario": name_scen,
                "true_scenario": true_scen,
                "name_mismatch": name_scen != true_scen,
                "episodes_field": data.get("episodes"),
                "episodes_recorded": data.get("episodes_recorded"),
                "episode_summaries": len(audit.get("episode_summaries") or []),
                "resume_done": jr.get("completed_episodes"),
                "resume_target": jr.get("target_episodes"),
                "status": data.get("status", "ok"),
                "has_kpis": bool(data.get("project_axis_metrics")),
                "salvage": data.get("salvage_reason"),
                "output_dir": out,
            }
        )
    return rows


def build_matrix(rows: list[dict]) -> dict[str, dict[str, dict]]:
    matrix: dict[str, dict[str, dict]] = {a: {} for a in ALGOS}
    for row in rows:
        algo = row["algorithm"]
        scen = row["true_scenario"]
        if algo in matrix and scen in SCENARIOS:
            prev = matrix[algo].get(scen)
            if prev is None or (row.get("episodes_recorded") or 0) >= (prev.get("episodes_recorded") or 0):
                matrix[algo][scen] = row
    return matrix


def kpi_files() -> dict[tuple[str, str], list[str]]:
    found: dict[tuple[str, str], list[str]] = {}
    for path in KPIS.glob("*_core_kpis.csv"):
        parts = path.stem.split("_")
        if len(parts) >= 3:
            algo, scen = parts[0].upper(), parts[1].upper()
            found.setdefault((algo, scen), []).append(path.name)
    return found


def main() -> int:
    rows = audit_results_files()
    matrix = build_matrix(rows)
    kpis = kpi_files()

    print("=== results.json por archivo ===")
    for r in rows:
        flag = " MISMATCH" if r["name_mismatch"] else ""
        ep = r["episodes_recorded"] if r["episodes_recorded"] is not None else r["resume_done"]
        print(
            f"{r['file']:28} {r['algorithm']:6} true={r['true_scenario']} "
            f"episodes_field={r['episodes_field']} recorded={r['episodes_recorded']} "
            f"summaries={r['episode_summaries']} resume={r['resume_done']}/{r['resume_target']} "
            f"status={r['status']}{flag}"
        )

    print("\n=== Matriz por algoritmo × escenario (output_dir) ===")
    for algo in ALGOS:
        for scen in SCENARIOS:
            r = matrix[algo].get(scen)
            kpi = kpis.get((algo, scen), [])
            if r:
                ep = r["episodes_recorded"] if r["episodes_recorded"] is not None else r["resume_done"]
                print(
                    f"{algo:6} {scen}: recorded={ep} episodes_field={r['episodes_field']} "
                    f"status={r['status']} kpis_csv={kpi or 'NO'}"
                )
            else:
                print(f"{algo:6} {scen}: SIN results.json")

    out = REPO / "outputs" / "madrl_v3_20260627_164047" / "resumen_comparativo" / "episode_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"files": rows, "matrix": {a: matrix[a] for a in ALGOS}, "core_kpis": {f"{k[0]}_{k[1]}": v for k, v in kpis.items()}}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGuardado: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
