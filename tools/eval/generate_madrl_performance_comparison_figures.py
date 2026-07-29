#!/usr/bin/env python3
"""Genera performance_comparison.png por MADRL (distrito + edificio, 50 ep Drive).

Salidas:
  - outputs/{RUN}/{ALGO}/{E}/figures/performance_comparison.png  (12 jobs)
  - outputs/{RUN}/resumen_comparativo/performance_comparison/{ALGO}_performance_comparison.png
  - mapping + report JSON con interpretación por figura

Fuente exclusiva: artefactos cuantitativos de madrl_v3_20260627_164047 (sin datos sintéticos).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RUN_ID = "madrl_v3_20260627_164047"
RUN = REPO / "outputs" / RUN_ID
AQ = RUN / "resumen_comparativo" / "estadistica" / "analisis_cuantitativo_completo_50_episodios"
MO = RUN / "resumen_comparativo" / "multiobjetivo"
OUT_SUMMARY = RUN / "resumen_comparativo" / "performance_comparison"
ALGOS = ("MATD3", "MAAC", "MASAC", "HAPPO")
SCENARIOS = ("E1", "E2", "E3")
OE_LABEL = {
    "E1": "OE.1 Flexibilidad (menor ratio = mejor)",
    "E2": "OE.2 CO₂ (menor Δ = mejor)",
    "E3": "OE.3 Costo (menor Δ = mejor)",
}
COLORS = {
    "MATD3": "#1f77b4",
    "MAAC": "#2ca02c",
    "MASAC": "#ff7f0e",
    "HAPPO": "#d62728",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fnum(x: str | None, default: float = float("nan")) -> float:
    if x is None or x == "":
        return default
    try:
        return float(x)
    except ValueError:
        return default


def load_primary() -> list[dict[str, str]]:
    return read_csv(AQ / "primary_objective_values.csv")


def load_building_mo() -> list[dict[str, str]]:
    path = MO / "building_objectives_by_algorithm.csv"
    return read_csv(path) if path.is_file() else []


def load_building_raw() -> list[dict[str, str]]:
    return read_csv(AQ / "building_kpis_raw.csv")


def district_effect(primary: list[dict[str, str]], algo: str, scenario: str) -> float:
    for row in primary:
        if row["algorithm"] == algo and row["scenario"] == scenario:
            return fnum(row["favorable_effect_percent"])
    return float("nan")


def district_metric_label(scenario: str) -> str:
    return {
        "E1": "Efecto flex_composite vs baseline (%)",
        "E2": "Efecto CO₂ total vs baseline (%)",
        "E3": "Efecto costo eléctrico vs baseline (%)",
    }[scenario]


def building_values_for_job(
    algo: str,
    scenario: str,
    building_mo: list[dict[str, str]],
    building_raw: list[dict[str, str]],
) -> tuple[list[str], list[float], str]:
    """Return (building labels, values, ylabel) for the scenario primary KPI."""
    if scenario == "E1":
        key_mo, key_raw, ylabel = (
            "flex_composite_proxy",
            None,
            "Proxy flexibilidad por edificio (adimensional)",
        )
    elif scenario == "E2":
        key_mo, key_raw, ylabel = (
            "carbon_emissions_delta_kgco2",
            "building_emissions_total_delta_kgco2",
            "Δ emisiones por edificio (kgCO₂)",
        )
    else:
        key_mo, key_raw, ylabel = (
            "electricity_cost_delta_eur",
            "building_cost_total_delta_eur",
            "Δ costo por edificio (EUR)",
        )

    mo_rows = [r for r in building_mo if r["algorithm"] == algo and r["scenario"] == scenario]
    if mo_rows:
        mo_rows = sorted(mo_rows, key=lambda r: int(r["building_id"]))
        labels = [f"B{int(r['building_id']):02d}" for r in mo_rows]
        vals = [fnum(r.get(key_mo)) for r in mo_rows]
        return labels, vals, ylabel

    # Fallback HAPPO / missing MO: building_kpis_raw
    if key_raw is None:
        # E1 without flex proxy: use emission delta magnitude as heterogeneity signal
        key_raw = "building_emissions_total_delta_kgco2"
        ylabel = "Δ emisiones por edificio (kgCO₂; proxy heterogeneidad E1)"

    raw_rows = [
        r
        for r in building_raw
        if r["algorithm"] == algo
        and r["scenario"] == scenario
        and r["cost_function"] == key_raw
    ]
    raw_rows = sorted(raw_rows, key=lambda r: r["name"])
    labels = [r["name"].replace("Building_", "B") for r in raw_rows]
    vals = [fnum(r["value"]) for r in raw_rows]
    return labels, vals, ylabel


def style_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linestyle="--")


def plot_job_figure(
    algo: str,
    scenario: str,
    primary: list[dict[str, str]],
    building_mo: list[dict[str, str]],
    building_raw: list[dict[str, str]],
    out_path: Path,
) -> dict:
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.6), constrained_layout=True)
    fig.suptitle(
        f"Performance comparison — {algo} / {scenario} (50 episodios Drive)\n"
        f"{OE_LABEL[scenario]} | corrida {RUN_ID}",
        fontsize=12,
        fontweight="bold",
    )

    # --- Distrito: este algoritmo vs los otros 3 en el escenario ---
    ax = axes[0]
    x = np.arange(len(ALGOS))
    effects = [district_effect(primary, a, scenario) for a in ALGOS]
    colors = [COLORS[a] if a == algo else "#bbbbbb" for a in ALGOS]
    bars = ax.bar(x, effects, color=colors, edgecolor="black", linewidth=0.6)
    for bar, val, a in zip(bars, effects, ALGOS):
        if np.isnan(val):
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.2f}%",
            ha="center",
            va="bottom" if val >= 0 else "top",
            fontsize=8,
            fontweight="bold" if a == algo else "normal",
        )
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(ALGOS)
    ax.set_ylabel(district_metric_label(scenario))
    ax.set_title("Distrito — efecto primario vs baseline (4 MADRL)")
    style_axes(ax)

    # --- Edificio: 17 edificios del algoritmo focal ---
    ax = axes[1]
    labels, vals, ylabel = building_values_for_job(algo, scenario, building_mo, building_raw)
    if labels:
        y = np.arange(len(labels))
        ax.barh(y, vals, color=COLORS[algo], edgecolor="black", linewidth=0.4, alpha=0.9)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=7)
        ax.axvline(0.0, color="black", linewidth=0.8)
        ax.set_xlabel(ylabel)
        ax.set_title(f"Edificio — heterogeneidad local ({algo})")
        style_axes(ax)
        ax.grid(axis="x", alpha=0.25, linestyle="--")
        ax.grid(axis="y", visible=False)
    else:
        ax.text(0.5, 0.5, "Sin KPI por edificio disponible", ha="center", va="center")
        ax.set_axis_off()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)

    focal = district_effect(primary, algo, scenario)
    peers = {a: district_effect(primary, a, scenario) for a in ALGOS}
    # favorable_effect_percent: mayor (menos negativo) = mejor desempeño descriptivo
    best = max(
        peers,
        key=lambda a: peers[a] if not np.isnan(peers[a]) else float("-inf"),
    )
    interpretation = (
        f"En distrito ({scenario}), {algo} obtiene efecto primario {focal:.3f}% "
        f"(valores negativos = empeoramiento vs baseline CityLearn; mayor % = mejor). "
        f"Mejor descriptivo del escenario: {best} ({peers[best]:.3f}%). "
        f"El panel derecho muestra la dispersión entre los 17 edificios: "
        f"en E2/E3, Δ negativo = reducción local; en E1 el proxy/heterogeneidad se lee por edificio."
    )
    return {
        "path": str(out_path.relative_to(REPO)).replace("\\", "/"),
        "algorithm": algo,
        "scenario": scenario,
        "district_effect_percent": focal,
        "district_leader": best,
        "n_buildings": len(labels),
        "interpretation": interpretation,
    }


def plot_algo_summary(
    algo: str,
    primary: list[dict[str, str]],
    building_mo: list[dict[str, str]],
    building_raw: list[dict[str, str]],
    out_path: Path,
) -> dict:
    fig, axes = plt.subplots(2, 3, figsize=(16.5, 8.8), constrained_layout=True)
    fig.suptitle(
        f"Performance comparison — {algo} (distrito + edificio, 50 episodios)\n"
        f"Fuente: {RUN_ID} | descriptivo; no decide HE10–HE31",
        fontsize=13,
        fontweight="bold",
    )

    interpretations: list[str] = []
    for j, scen in enumerate(SCENARIOS):
        # Distrito row
        ax = axes[0, j]
        effects = [district_effect(primary, a, scen) for a in ALGOS]
        colors = [COLORS[a] if a == algo else "#cfcfcf" for a in ALGOS]
        x = np.arange(len(ALGOS))
        bars = ax.bar(x, effects, color=colors, edgecolor="black", linewidth=0.5)
        for bar, val in zip(bars, effects):
            if np.isnan(val):
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:.1f}",
                ha="center",
                va="bottom" if val >= 0 else "top",
                fontsize=7,
            )
        ax.axhline(0.0, color="black", linewidth=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(ALGOS, fontsize=8)
        ax.set_title(f"Distrito {scen}")
        ax.set_ylabel("% vs baseline" if j == 0 else "")
        style_axes(ax)

        # Edificio row
        ax = axes[1, j]
        labels, vals, ylabel = building_values_for_job(algo, scen, building_mo, building_raw)
        if labels:
            y = np.arange(len(labels))
            ax.barh(y, vals, color=COLORS[algo], edgecolor="black", linewidth=0.3, alpha=0.9)
            ax.set_yticks(y)
            ax.set_yticklabels(labels, fontsize=6)
            ax.axvline(0.0, color="black", linewidth=0.7)
            ax.set_title(f"Edificio {scen}")
            ax.set_xlabel(ylabel, fontsize=7)
            style_axes(ax)
            ax.grid(axis="x", alpha=0.25, linestyle="--")
            ax.grid(axis="y", visible=False)
        else:
            ax.text(0.5, 0.5, "N/D", ha="center", va="center")
            ax.set_axis_off()

        focal = district_effect(primary, algo, scen)
        interpretations.append(
            f"{scen}: efecto distrito {focal:.3f}% sobre {district_metric_label(scen)}; "
            f"{len(labels)} edificios en el panel inferior."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)

    return {
        "path": str(out_path.relative_to(REPO)).replace("\\", "/"),
        "algorithm": algo,
        "interpretation": " ".join(interpretations),
    }


def write_mapping(job_meta: list[dict], algo_meta: list[dict]) -> Path:
    lines = [
        f"# Performance comparison — {RUN_ID}",
        "",
        "## Qué es esta figura",
        "",
        "Cada `performance_comparison.png` resume el **desempeño descriptivo** de un MADRL",
        "sobre la corrida canónica de **50 episodios**, en dos escalas:",
        "",
        "1. **Distrito:** efecto primario vs baseline CityLearn (`favorable_effect_percent`)",
        "   en E1 (flexibilidad), E2 (CO₂) y E3 (costo), comparado con los otros tres MADRL.",
        "2. **Edificio:** heterogeneidad de los **17 edificios** Iquitos en el KPI del escenario",
        "   (proxy de flexibilidad / ΔCO₂ / Δcosto).",
        "",
        "Estas figuras son **descriptivas**. No sustituyen Shapiro → Kruskal/Friedman/Wilcoxon",
        "ni las decisiones HE10–HE31 / H0G–H1G del Cap. 5.",
        "",
        "## Archivos por algoritmo (resumen E1–E3)",
        "",
    ]
    for meta in algo_meta:
        lines.append(f"### {meta['algorithm']}")
        lines.append(f"- Archivo: `{meta['path']}`")
        lines.append(f"- Lectura: {meta['interpretation']}")
        lines.append("")

    lines.extend(
        [
            "## Archivos por job (algoritmo × escenario)",
            "",
            "| Algoritmo | Escenario | Archivo | Efecto distrito (%) | Líder escenario | Edificios |",
            "|---|---|---|---:|---|---:|",
        ]
    )
    for m in job_meta:
        lines.append(
            f"| {m['algorithm']} | {m['scenario']} | `{m['path']}` | "
            f"{m['district_effect_percent']:.3f} | {m['district_leader']} | {m['n_buildings']} |"
        )
        lines.append(f"| | | *{m['interpretation']}* | | | |")

    lines.extend(
        [
            "",
            "## Cómo leer los signos",
            "",
            "- En distrito, el `%` es el efecto favorable reportado en `primary_objective_values.csv`.",
            "  Valores **negativos** indican empeoramiento respecto al baseline (=1 o totales baseline).",
            "- En edificio, ΔCO₂/Δcosto **negativo** = reducción local (mejora); **positivo** = aumento.",
            "- HAPPO usa fallback de `building_kpis_raw.csv` cuando no hay fila en multiobjetivo.",
            "",
        ]
    )
    out = OUT_SUMMARY / "performance_comparison_mapping.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    primary = load_primary()
    building_mo = load_building_mo()
    building_raw = load_building_raw()

    job_meta: list[dict] = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            out = RUN / algo / scen / "figures" / "performance_comparison.png"
            meta = plot_job_figure(algo, scen, primary, building_mo, building_raw, out)
            # sidecar explanation
            (out.with_suffix(".md")).write_text(
                f"# {algo} / {scen} — performance_comparison\n\n{meta['interpretation']}\n",
                encoding="utf-8",
            )
            job_meta.append(meta)

    algo_meta: list[dict] = []
    for algo in ALGOS:
        out = OUT_SUMMARY / f"{algo}_performance_comparison.png"
        meta = plot_algo_summary(algo, primary, building_mo, building_raw, out)
        (out.with_suffix(".md")).write_text(
            f"# {algo} — performance_comparison (distrito + edificio)\n\n{meta['interpretation']}\n",
            encoding="utf-8",
        )
        algo_meta.append(meta)

    mapping = write_mapping(job_meta, algo_meta)
    report = {
        "run_id": RUN_ID,
        "n_job_figures": len(job_meta),
        "n_algo_summaries": len(algo_meta),
        "job_figures": job_meta,
        "algo_summaries": algo_meta,
        "mapping": str(mapping.relative_to(REPO)).replace("\\", "/"),
    }
    report_path = OUT_SUMMARY / "generation_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "jobs": len(job_meta), "summaries": len(algo_meta), "mapping": report["mapping"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
