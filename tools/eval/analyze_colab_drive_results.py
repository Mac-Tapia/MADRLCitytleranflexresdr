"""Generate local analysis artifacts from the Colab/Drive canonical MADRL run."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt


REPO = Path(__file__).resolve().parents[2]
KPIS_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
RUN_ID = "madrl_v3_20260627_164047"
RUN_OUT = REPO / "outputs" / RUN_ID / "resumen_comparativo"
BEST_REPORT = RUN_OUT / "best_madrl_report.json"
EPISODE_AUDIT = RUN_OUT / "episode_audit.json"

ALGOS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")


@dataclass
class ObjectiveRow:
    algorithm: str
    flex_e1: float | None
    co2_delta_e2: float | None
    cost_delta_e3: float | None
    episodes_e1: int | None
    episodes_e2: int | None
    episodes_e3: int | None
    has_kpis: bool
    status: str
    notes: str


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_core_kpis(algo: str, scen: str) -> dict[str, float] | None:
    path = KPIS_DIR / f"{algo.lower()}_{scen}_core_kpis.csv"
    if not path.exists():
        return None
    data: dict[str, float] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("value"):
                continue
            data[row["kpi"]] = float(row["value"])
    return data


def build_rows() -> list[ObjectiveRow]:
    best = read_json(BEST_REPORT)
    audit = read_json(EPISODE_AUDIT)
    matrix = audit["matrix"]
    pending = {item["scenario"]: item for item in best["happo_pending"]}

    rows: list[ObjectiveRow] = []
    for algo in ALGOS:
        e1 = read_core_kpis(algo, "E1")
        e2 = read_core_kpis(algo, "E2")
        e3 = read_core_kpis(algo, "E3")

        if algo == "HAPPO":
            episodes = {sc: pending[sc]["episodes_recorded"] for sc in SCENARIOS}
            status = "completed_with_salvage"
            notes = "49/50 episodios; sin KPIs; pendiente resume celda 2.3 por VecEnvWrapper."
        else:
            algo_matrix = matrix[algo]
            episodes = {
                sc: algo_matrix[sc].get("episodes_recorded") or algo_matrix[sc].get("resume_done")
                for sc in SCENARIOS
            }
            status = "ok"
            notes = "KPIs auditados desde Drive y reconciliados por output_dir."

        rows.append(
            ObjectiveRow(
                algorithm=algo,
                flex_e1=((e1["peak_average"] + e1["ramping_average"] + e1["one_minus_load_factor_average"]) / 3.0) if e1 else None,
                co2_delta_e2=e2["carbon_emissions_delta"] if e2 else None,
                cost_delta_e3=e3["electricity_cost_delta"] if e3 else None,
                episodes_e1=episodes["E1"],
                episodes_e2=episodes["E2"],
                episodes_e3=episodes["E3"],
                has_kpis=all(v is not None for v in (e1, e2, e3)),
                status=status,
                notes=notes,
            )
        )
    return rows


def write_objective_summary(rows: list[ObjectiveRow]) -> Path:
    out = RUN_OUT / "drive_objective_summary.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "algorithm",
                "flex_composite_e1",
                "co2_delta_kg_e2",
                "cost_delta_eur_e3",
                "episodes_e1",
                "episodes_e2",
                "episodes_e3",
                "has_kpis",
                "status",
                "notes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.algorithm,
                    row.flex_e1,
                    row.co2_delta_e2,
                    row.cost_delta_e3,
                    row.episodes_e1,
                    row.episodes_e2,
                    row.episodes_e3,
                    row.has_kpis,
                    row.status,
                    row.notes,
                ]
            )
    return out


def write_thesis_mapping(best: dict, rows: list[ObjectiveRow]) -> Path:
    out = RUN_OUT / "drive_thesis_mapping.md"
    best_algo = best["mejor_madrl"]
    content = f"""# Análisis Colab/Drive — {RUN_ID}

## Conclusiones

- La corrida canónica en Drive fue localizada usando el conector de Google Drive en la carpeta compartida del usuario.
- La estructura real en Drive sigue el layout del proyecto: `outputs/{RUN_ID}/{{HAPPO,MASAC,MATD3,MAAC}}/{{E1,E2,E3}}/`.
- El análisis local correcto se apoya en `outputs/_drive_madrl/kpis/` y `outputs/{RUN_ID}/resumen_comparativo/`.
- El mejor MADRL global entre algoritmos con KPIs auditados es **{best_algo}**.
- `HAPPO` no debe entrar al ranking final todavía: quedó en `completed_with_salvage`, 49/50 episodios y sin KPIs post-evaluación.

## Qué corresponde a cada artefacto

- `best_madrl_report.json`: selección global del mejor MADRL, ranking y KPIs primarios.
  Ubicación: Capítulo 5.3 y Capítulo 6.
- `episode_audit.json`: evidencia de completitud real por `episodes_recorded`.
  Ubicación: Capítulo 5.1.
- `comparison_metrics_colab.csv`: base larga comparativa por algoritmo/escenario.
  Ubicación: tablas auxiliares del Capítulo 5.
- `drive_objective_summary.csv`: resumen sintético por objetivo OE1/OE2/OE3 generado en este análisis.
  Ubicación: Tabla operativa de resultados.
- `drive_ranking_scores.png`: figura de ranking global.
  Ubicación: Figura 5.1.
- `drive_objective_kpis.png`: figura comparativa por objetivo.
  Ubicación: apoyo para Figuras 5.2–5.5.
- `drive_episode_completion.png`: figura de cobertura de episodios.
  Ubicación: Sección 5.1, nota metodológica.

## Estado por algoritmo
"""
    for row in rows:
        content += (
            f"\n- `{row.algorithm}`: E1={row.episodes_e1}, E2={row.episodes_e2}, E3={row.episodes_e3}, "
            f"`has_kpis={row.has_kpis}`, `status={row.status}`. {row.notes}"
        )

    content += """

## Interpretación

- `MATD3` gana OE1 flexibilidad y OE2 CO₂ por los criterios usados en el flujo local.
- `MAAC` gana OE3 costo, pero pierde el ranking global.
- `MASAC` queda tercero entre algoritmos con KPIs.
- La narrativa del proyecto debe reportar `episodes_recorded=50` para MATD3/MAAC/MASAC y no el campo `episodes` del último resume.
"""
    out.write_text(content, encoding="utf-8")
    return out


def plot_ranking(best: dict) -> Path:
    ranking = best["ranking"]
    labels = [item["algorithm"] for item in ranking]
    scores = [item["score_global"] for item in ranking]

    plt.figure(figsize=(8, 4.8))
    bars = plt.bar(labels, scores, color=["#2f855a", "#3182ce", "#d69e2e"])
    plt.ylabel("Score global")
    plt.title("Ranking global Colab/Drive por algoritmo con KPIs")
    plt.ylim(0, 1)
    for bar, score in zip(bars, scores):
        plt.text(bar.get_x() + bar.get_width() / 2, score + 0.02, f"{score:.4f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    out = RUN_OUT / "drive_ranking_scores.png"
    plt.savefig(out, dpi=180)
    plt.close()
    return out


def plot_objectives(rows: list[ObjectiveRow]) -> Path:
    labels = [r.algorithm for r in rows if r.algorithm != "HAPPO"]
    flex = [r.flex_e1 for r in rows if r.algorithm != "HAPPO"]
    co2 = [r.co2_delta_e2 for r in rows if r.algorithm != "HAPPO"]
    cost = [r.cost_delta_e3 for r in rows if r.algorithm != "HAPPO"]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    fig.suptitle("KPIs primarios Colab/Drive por objetivo")

    axes[0].bar(labels, flex, color="#2b6cb0")
    axes[0].set_title("OE1 Flex compuesta E1")
    axes[0].set_ylabel("Menor es mejor")

    axes[1].bar(labels, co2, color="#2f855a")
    axes[1].set_title("OE2 Delta CO₂ E2")
    axes[1].set_ylabel("kg")

    axes[2].bar(labels, cost, color="#dd6b20")
    axes[2].set_title("OE3 Delta costo E3")
    axes[2].set_ylabel("EUR")

    for ax in axes:
        ax.tick_params(axis="x", rotation=20)

    plt.tight_layout()
    out = RUN_OUT / "drive_objective_kpis.png"
    plt.savefig(out, dpi=180)
    plt.close()
    return out


def plot_episode_completion(rows: list[ObjectiveRow]) -> Path:
    labels = [r.algorithm for r in rows]
    e1 = [r.episodes_e1 or 0 for r in rows]
    e2 = [r.episodes_e2 or 0 for r in rows]
    e3 = [r.episodes_e3 or 0 for r in rows]

    x = range(len(labels))
    width = 0.22

    plt.figure(figsize=(9, 4.8))
    plt.bar([i - width for i in x], e1, width=width, label="E1")
    plt.bar(list(x), e2, width=width, label="E2")
    plt.bar([i + width for i in x], e3, width=width, label="E3")
    plt.axhline(50, color="black", linestyle="--", linewidth=1, label="Objetivo 50")
    plt.xticks(list(x), labels)
    plt.ylabel("Episodios registrados")
    plt.title("Cobertura de episodios Colab/Drive por algoritmo")
    plt.legend()
    plt.tight_layout()
    out = RUN_OUT / "drive_episode_completion.png"
    plt.savefig(out, dpi=180)
    plt.close()
    return out


def main() -> int:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    best = read_json(BEST_REPORT)
    rows = build_rows()

    generated = {
        "drive_objective_summary_csv": str(write_objective_summary(rows)),
        "drive_thesis_mapping_md": str(write_thesis_mapping(best, rows)),
        "drive_ranking_scores_png": str(plot_ranking(best)),
        "drive_objective_kpis_png": str(plot_objectives(rows)),
        "drive_episode_completion_png": str(plot_episode_completion(rows)),
    }
    print(json.dumps(generated, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
