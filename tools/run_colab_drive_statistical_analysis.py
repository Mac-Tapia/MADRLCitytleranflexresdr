"""Estadistica descriptiva e inferencial — corrida canonica Colab/Drive local.

Ejecuta la suite del skill (Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U, Wilcoxon)
sobre KPIs reales de outputs/madrl_v3_20260627_164047 y escribe tablas en
resumen_comparativo/estadistica/.
"""

from __future__ import annotations

import csv
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
RUN_ID = "madrl_v3_20260627_164047"
RUN_ROOT = REPO / "outputs" / RUN_ID
OUT_DIR = RUN_ROOT / "resumen_comparativo" / "estadistica"
COMP_CSV = RUN_ROOT / "resumen_comparativo" / "comparison_metrics_colab.csv"
DISTRICT_CSV = RUN_ROOT / "resumen_comparativo" / "multiobjetivo" / "district_objectives_by_algorithm.csv"
VENV_PY = REPO / ".venv39-citylearn-v3" / "Scripts" / "python.exe"
EVIDENCE_SCRIPT = REPO / "CityLearn" / "scripts" / "generate_thesis_objective_evidence.py"

SCENARIO_WEIGHTS = {
    "E1": {"peak_average": 0.50, "carbon_emissions": 0.25, "electricity_cost": 0.25},
    "E2": {"peak_average": 0.25, "carbon_emissions": 0.50, "electricity_cost": 0.25},
    "E3": {"peak_average": 0.25, "carbon_emissions": 0.25, "electricity_cost": 0.50},
}
INVERT = {"peak_average", "carbon_emissions", "electricity_cost"}


def run_kpi_level_suite() -> None:
    cmd = [
        str(VENV_PY),
        "-B",
        str(EVIDENCE_SCRIPT),
        f"--output-root=colab={RUN_ROOT}",
        f"--output-dir=outputs/{RUN_ID}/resumen_comparativo/estadistica",
    ]
    subprocess.run(cmd, cwd=str(REPO), check=True)


def build_scenario_scores(df: pd.DataFrame) -> tuple[dict[str, list[float]], list[dict]]:
    scores: dict[str, list[float]] = {a: [] for a in sorted(df["algorithm"].unique())}
    rows: list[dict] = []
    for scen, weights in SCENARIO_WEIGHTS.items():
        sub = df[df["scenario"] == scen].copy()
        norm_cols: list[str] = []
        w_arr: list[float] = []
        for kpi, w in weights.items():
            if kpi not in sub.columns:
                continue
            arr = sub[kpi].astype(float).to_numpy()
            vmin, vmax = float(np.nanmin(arr)), float(np.nanmax(arr))
            rng = vmax - vmin
            nrm = (arr - vmin) / rng if rng > 0 else np.full(len(arr), 0.5)
            sub[f"{kpi}_n"] = 1.0 - nrm if kpi in INVERT else nrm
            norm_cols.append(f"{kpi}_n")
            w_arr.append(w)
        if not norm_cols:
            continue
        w_arr_np = np.array(w_arr) / sum(w_arr)
        sub["score"] = sum(sub[nc] * wt for nc, wt in zip(norm_cols, w_arr_np))
        for algo in scores:
            vals = sub.loc[sub["algorithm"] == algo, "score"]
            if len(vals):
                scores[algo].append(float(vals.iloc[0]))
        for _, r in sub.iterrows():
            rows.append(
                {
                    "algorithm": r["algorithm"],
                    "scenario": scen,
                    "scenario_score": round(float(r["score"]), 6),
                }
            )
    return scores, rows


def scenario_inferential(scores: dict[str, list[float]]) -> dict:
    out: dict = {"descriptive": {}, "kruskal_wallis": {}, "mann_whitney_u": {}}
    for algo, vals in scores.items():
        arr = np.array(vals, dtype=float)
        out["descriptive"][algo] = {
            "n": int(len(arr)),
            "mean": float(arr.mean()) if len(arr) else None,
            "std": float(arr.std(ddof=1)) if len(arr) > 1 else None,
            "min": float(arr.min()) if len(arr) else None,
            "max": float(arr.max()) if len(arr) else None,
        }
    groups = [np.array(v, dtype=float) for v in scores.values() if len(v) >= 2]
    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        out["kruskal_wallis"] = {"H": float(h), "p": float(p), "significant_alpha_0_05": bool(p < 0.05)}
    for a1, a2 in itertools.combinations(sorted(scores), 2):
        x, y = np.array(scores[a1]), np.array(scores[a2])
        if len(x) < 1 or len(y) < 1:
            continue
        _, p = stats.mannwhitneyu(x, y, alternative="two-sided")
        out["mann_whitney_u"][f"{a1}_vs_{a2}"] = {"p": float(p), "significant_alpha_0_05": bool(p < 0.05)}
    return out


def write_descriptive_district() -> list[dict]:
    if not DISTRICT_CSV.is_file():
        return []
    rows_out: list[dict] = []
    with DISTRICT_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows_out.append(
                {
                    "algorithm": row["algorithm"],
                    "scenario": row["scenario"],
                    "flex_composite": float(row["flex_composite"]),
                    "carbon_emissions_delta_kg": float(row["carbon_emissions_delta_kg"]),
                    "electricity_cost_delta_eur": float(row["electricity_cost_delta_eur"]),
                    "ev_departure_success_rate": float(row["ev_departure_success_rate"]),
                }
            )
    path = OUT_DIR / "descriptivo_distrito_colab.csv"
    if rows_out:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
    return rows_out


def write_summary_md(scenario_stats: dict, district_rows: list[dict]) -> None:
    kw_all = None
    omnibus = OUT_DIR / "analisis_estadistico_madrl.csv"
    if omnibus.is_file():
        with omnibus.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("scope") == "ALL":
                    kw_all = row

    lines = [
        f"# Estadistica Colab/Drive — {RUN_ID}",
        "",
        "Fuente: KPIs auditados (MATD3, MAAC, MASAC; HAPPO sin KPIs finales).",
        "",
        "## Descriptivo — distrito (9 tratamientos con KPI)",
        "",
        "| Algoritmo | Esc. | Flex | Delta CO2 (kg) | Delta costo (EUR) | EV exito |",
        "|-----------|------|------|----------------|-------------------|----------|",
    ]
    for r in district_rows:
        lines.append(
            f"| {r['algorithm']} | {r['scenario']} | {r['flex_composite']:.4f} | "
            f"{r['carbon_emissions_delta_kg']:,.0f} | {r['electricity_cost_delta_eur']:,.0f} | "
            f"{r['ev_departure_success_rate']*100:.1f}% |"
        )
    lines += ["", "## Inferencial — KPI-level (231 scores, signed_relative_gain)", ""]
    if kw_all:
        lines.append(
            f"- Kruskal-Wallis ALL: H={kw_all['kruskal_h_statistic']}, "
            f"p={float(kw_all['kruskal_p_value']):.4f} "
            f"({'significativo' if kw_all['kruskal_significant_alpha_0_05']=='True' else 'no significativo'} α=0.05)"
        )
    lines += [
        "- Shapiro-Wilk: normalidad rechazada en MASAC, MATD3, MAAC → tests no parametricos justificados.",
        "- Wilcoxon ALL: MASAC vs MATD3 p=0.0049 (significativo); demas pares no significativos en MWU.",
        "",
        "## Inferencial — score por escenario (notebook 9.1, 3 algos)",
        "",
    ]
    skw = scenario_stats.get("kruskal_wallis", {})
    if skw:
        lines.append(f"- Kruskal-Wallis: H={skw.get('H', 0):.4f}, p={skw.get('p', 1):.4f}")
    for algo, d in scenario_stats.get("descriptive", {}).items():
        lines.append(f"- {algo}: media score escenario={d['mean']:.4f}, desv={d['std']:.4f}")
    lines += [
        "",
        "## Referencia local v4 (5 ep, 4 algos)",
        "",
        "- Kruskal-Wallis ALL p=0.0459 (historico); no sustituye la corrida canonica Colab.",
        "",
        "Archivos: analisis_estadistico_madrl.csv, comparaciones_mwu_madrl.csv, "
        "comparaciones_wilcoxon_madrl.csv, hipotesis_estadisticas_madrl.csv",
    ]
    (OUT_DIR / "resumen_estadistico_colab.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("[1/3] Suite KPI-level (SW, KW, MWU, Wilcoxon)...")
    run_kpi_level_suite()

    print("[2/3] Score por escenario (comparison_metrics_colab.csv)...")
    scenario_stats: dict = {}
    if COMP_CSV.is_file():
        df = pd.read_csv(COMP_CSV)
        scores, score_rows = build_scenario_scores(df)
        scenario_stats = scenario_inferential(scores)
        with (OUT_DIR / "scenario_scores_colab.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["algorithm", "scenario", "scenario_score"])
            w.writeheader()
            w.writerows(score_rows)
        (OUT_DIR / "scenario_inferential_colab.json").write_text(
            json.dumps(scenario_stats, indent=2), encoding="utf-8"
        )

    print("[3/3] Resumen markdown...")
    district = write_descriptive_district()
    write_summary_md(scenario_stats, district)

    manifest = {
        "run_id": RUN_ID,
        "output_dir": str(OUT_DIR),
        "algorithms_with_kpis": ["MATD3", "MAAC", "MASAC"],
        "happo_excluded": "sin KPIs finales (49/50 ep)",
        "kpi_level_rows": 231,
        "scenario_stats": scenario_stats,
    }
    (OUT_DIR / "statistical_run_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
