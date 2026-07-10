"""Secciones doctorales: Cap. 5 Colab, multiobjetivo, verificación de completitud."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

REPO = Path(__file__).resolve().parents[1]
RUN_ID = "madrl_v3_20260627_164047"
MO_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "multiobjetivo"
FD_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "figuras_drive_reales" / "comparativo"
BEST_REPORT = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "best_madrl_report.json"
DISTRICT_CSV = MO_DIR / "district_objectives_by_algorithm.csv"
INVENTORY_CSV = MO_DIR / "building_inventory_multiobjective.csv"

BL_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "citylearn_v2_baseline"
STAT_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "estadistica"
HYP_CSV = STAT_DIR / "hipotesis_estadisticas_madrl.csv"
ANALYSIS_CSV = STAT_DIR / "analisis_estadistico_madrl.csv"
MWU_CSV = STAT_DIR / "comparaciones_mwu_madrl.csv"
WC_CSV = STAT_DIR / "comparaciones_wilcoxon_madrl.csv"
DESCRIPTIVE_CSV = STAT_DIR / "descriptivo_distrito_colab.csv"
EPISODE_CSV = (
    REPO / "outputs" / "_drive_madrl" / "full_data" / "analysis_real_drive" / "tables" / "district_episode_kpis.csv"
)
BUILDING_CSV = MO_DIR / "building_objectives_by_algorithm.csv"
ALGO_METRICS_JSON = STAT_DIR / "madrl_per_algorithm_metrics.json"
FIG_RUN = REPO / "outputs" / RUN_ID

OE_EPISODE_SPECS = {
    "OE1": {
        "scenario": "E1",
        "metric": "reward_mean",
        "label": "reward_mean por episodio",
        "hypothesis": "HE.1",
        "fmt": ".4f",
        "higher_better": True,
    },
    "OE2": {
        "scenario": "E2",
        "metric": "district_emission",
        "label": "emision distrital por episodio (kgCO2 eq.)",
        "hypothesis": "HE.2",
        "fmt": ",.1f",
        "higher_better": False,
    },
    "OE3": {
        "scenario": "E3",
        "metric": "district_cost",
        "label": "costo distrital por episodio (EUR)",
        "hypothesis": "HE.3",
        "fmt": ",.1f",
        "higher_better": False,
    },
}
HYPOTHESIS_LABELS = {
    "OE1": ("HE.1", "OE.1 / E1"),
    "OE2": ("HE.2", "OE.2 / E2"),
    "OE3": ("HE.3", "OE.3 / E3"),
    "OG": ("HG", "Global (ALL)"),
    "ALL": ("HG", "Global (ALL)"),
}

FIG_WIDTH_LANDSCAPE = 17.5
FIG_WIDTH_PORTRAIT = 16.5
FIG_WIDTH_HEATMAP = 17.0

OE_DEFINITIONS = {
    "OE1": {
        "scenario": "E1",
        "vd": "D-VD.1",
        "dimension": "flexibilidad energetica",
        "weights": "[0,70; 0,15; 0,15]",
        "primary_kpis": [
            ("flex_composite", "Flexibilidad compuesta", ".4f", True),
            ("peak_average", "Pico promedio", ".4f", True),
            ("ramping_average", "Ramping promedio", ".4f", True),
            ("one_minus_load_factor_average", "1 − factor de carga", ".4f", True),
            ("grid_import_delta", "Delta importacion red (kWh)", ",.0f", True),
            ("ev_departure_success_rate", "Exito salida EV", ".1%", False),
        ],
        "kpi_fig": FD_DIR / "comparativo_E1_OE1_kpi.png",
        "conv_fig": FD_DIR / "comparativo_E1_convergence_reward_mean.png",
        "building_fig": MO_DIR / "drive_building_E1_flex_composite_proxy.png",
        "score_key": "score_oe1_flex",
    },
    "OE2": {
        "scenario": "E2",
        "vd": "D-VD.2",
        "dimension": "emisiones de CO2",
        "weights": "[0,15; 0,70; 0,15]",
        "primary_kpis": [
            ("carbon_emissions_delta_kg", "Delta CO2 (kg)", ",.0f", True),
            ("flex_composite", "Flexibilidad compuesta (secundaria)", ".4f", True),
            ("grid_import_delta", "Delta importacion red (kWh)", ",.0f", True),
            ("ev_departure_success_rate", "Exito salida EV", ".1%", False),
        ],
        "kpi_fig": FD_DIR / "comparativo_E2_OE2_kpi.png",
        "conv_fig": FD_DIR / "comparativo_E2_convergence_reward_mean.png",
        "building_fig": MO_DIR / "drive_building_E2_carbon_emissions_delta_kgco2.png",
        "trace_fig": FD_DIR / "comparativo_E2_control_trace.png",
        "score_key": "score_oe2_co2",
    },
    "OE3": {
        "scenario": "E3",
        "vd": "D-VD.3",
        "dimension": "costos energeticos",
        "weights": "[0,15; 0,15; 0,70]",
        "primary_kpis": [
            ("electricity_cost_delta_eur", "Delta costo electrico (EUR)", ",.0f", True),
            ("flex_composite", "Flexibilidad compuesta (secundaria)", ".4f", True),
            ("peak_average", "Pico promedio", ".4f", True),
            ("ev_departure_success_rate", "Exito salida EV", ".1%", False),
        ],
        "kpi_fig": FD_DIR / "comparativo_E3_OE3_kpi.png",
        "conv_fig": FD_DIR / "comparativo_E3_convergence_reward_mean.png",
        "building_fig": MO_DIR / "drive_building_E3_electricity_cost_delta_eur.png",
        "score_key": "score_oe3_cost",
    },
}


GREY = RGBColor(0x59, 0x59, 0x59)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def add_dedicatoria_agradecimientos(doc, p, heading) -> None:
    heading(doc, "Dedicatoria", 1)
    p(
        doc,
        "A mi familia, por el apoyo incondicional durante este camino de formación doctoral; "
        "a los docentes y colegas de la Universidad Nacional de Ingeniería, por impulsar la "
        "investigación aplicada en sistemas eléctricos inteligentes; y a la comunidad académica "
        "de Iquitos, cuyo contexto energético motivó el presente estudio.",
    )
    doc.add_page_break()
    heading(doc, "Agradecimientos", 1)
    p(
        doc,
        "Se agradece a la Escuela de Posgrado de la UNI, al equipo de investigación del proyecto "
        "MADRL CityLearn v3, a Electro Oriente S.A. y a las instituciones que aportaron datos "
        "operativos para el dataset citylearn_iquitos_2023_2025. Asimismo, se reconoce el uso "
        "de recursos computacionales en Google Colab para la corrida canónica de 50 episodios "
        f"({RUN_ID}).",
    )
    doc.add_page_break()


def add_resumen_doctoral(doc, p, heading) -> None:
    heading(doc, "Resumen", 1)
    p(
        doc,
        "Esta tesis doctoral determina, mediante simulación computacional bajo diseño experimental "
        "factorial 4×3, el efecto de cuatro algoritmos Multi-Agente de Aprendizaje por Refuerzo "
        "Profundo (MADRL) —HAPPO, MASAC, MATD3 y MAAC— sobre la gestión coordinada de flexibilidad "
        "energética, emisiones de CO₂ y costos en una comunidad inteligente del Sistema Eléctrico "
        "Aislado de Iquitos (SEAI). La formulación Dec-POMDP con CTDE se implementa sobre CityLearn "
        "v3 propuesto (17 edificios reales, 26 304 h, 185 cargadores EV). La corrida canónica "
        f"Colab/Drive ({RUN_ID}) completó 50 episodios por escenario en MATD3, MAAC y MASAC; "
        "MATD3 obtiene el mejor score global (0,6667) y lidera flexibilidad (OE1) y emisiones (OE2); "
        "MAAC lidera costos (OE3). Las figuras de convergencia, control MADRL y ranking provienen de "
        "timeseries.csv y trace.csv auditados en Drive (sin datos sinteticos). El analisis multiobjetivo "
        "desagrega KPIs por distrito y por edificio (153 registros). HAPPO alcanzo 49/50 episodios sin "
        "KPIs finales por error de evaluacion (VecEnvWrapper). La evidencia inferencial Colab "
        "(Kruskal-Wallis ALL p=0.155; Wilcoxon MASAC vs MATD3 p=0.0049) complementa el ranking "
        "descriptivo; la referencia local v4 (KW p=0.0459) es exploratoria con 5 episodios.",
    )
    p(
        doc,
        "Palabras clave: aprendizaje por refuerzo multiagente, diseño experimental, Dec-POMDP, CTDE, "
        "flexibilidad energética, emisiones de CO₂, microrred aislada, Iquitos.",
        italic=True,
    )
    doc.add_page_break()
    heading(doc, "Abstract", 1)
    p(
        doc,
        "This doctoral thesis evaluates four cooperative Multi-Agent Deep Reinforcement Learning "
        "(MADRL) algorithms under a Dec-POMDP/CTDE framework on a real 17-building dataset from "
        "Iquitos, Peru. A canonical 50-episode Colab run shows MATD3 as the best overall performer "
        "(global score 0.6667), leading flexibility and CO₂ objectives, while MAAC leads energy cost. "
        "Multi-objective KPIs are reported at district and building levels (185 EV chargers). "
        "Training figures use audited Drive timeseries and trace CSVs (no synthetic data). "
        "Inferential tests on the canonical run were executed: Kruskal-Wallis ALL p=0.155 "
        "(not significant at alpha=0.05); Wilcoxon MASAC vs MATD3 p=0.0049. MATD3 leads "
        "descriptively but CityLearn v2 baseline outperforms MADRL on global HPHI score.",
        italic=True,
    )
    doc.add_page_break()


def _fmt_kpi(value: str, fmt: str, lower_better: bool) -> str:
    x = float(value)
    if fmt == ".1%":
        return f"{x * 100:.1f}%"
    if fmt == ",.0f":
        return f"{x:,.0f}"
    if fmt == ".4f":
        return f"{x:.4f}"
    return str(x)


def _rows_for_scenario(district: list[dict[str, str]], scenario: str) -> list[dict[str, str]]:
    return [r for r in district if r["scenario"] == scenario]


def _best_algo_by_kpi(rows: list[dict[str, str]], kpi: str, lower_better: bool = True) -> tuple[str, float]:
    best_algo, best_val = "", float("inf") if lower_better else float("-inf")
    for row in rows:
        val = float(row[kpi])
        if lower_better and val < best_val:
            best_val, best_algo = val, row["algorithm"]
        elif not lower_better and val > best_val:
            best_val, best_algo = val, row["algorithm"]
    return best_algo, best_val


def _hypothesis_row(oe_key: str) -> dict[str, str]:
    rows = _read_csv(HYP_CSV)
    axis = {"OE1": "OE1", "OE2": "OE2", "OE3": "OE3"}[oe_key]
    for row in rows:
        if row.get("axis") == axis:
            return row
    return {}


def _fmt_stat_num(value: float | str | None, fmt: str) -> str:
    if value is None or value == "":
        return "-"
    x = float(value)
    if fmt == ".4f":
        return f"{x:.4f}"
    if fmt == ",.1f":
        return f"{x:,.1f}"
    if fmt == ".3e":
        return f"{x:.3e}"
    return f"{x:.3f}"


def _descriptive_episode_rows(oe_key: str) -> list[dict[str, str | float]]:
    spec = OE_EPISODE_SPECS[oe_key]
    if DESCRIPTIVE_CSV.is_file():
        rows = [r for r in _read_csv(DESCRIPTIVE_CSV) if r.get("axis") == oe_key]
        if rows:
            return rows
    if not EPISODE_CSV.is_file():
        return []
    import pandas as pd

    df = pd.read_csv(EPISODE_CSV)
    sub = df[df["scenario"] == spec["scenario"]]
    out: list[dict[str, str | float]] = []
    for algo, grp in sub.groupby("algorithm"):
        vals = grp[spec["metric"]].dropna().astype(float)
        if vals.empty:
            continue
        out.append(
            {
                "axis": oe_key,
                "scenario": spec["scenario"],
                "algorithm": algo,
                "n_episodes": int(len(vals)),
                "mean": float(vals.mean()),
                "median": float(vals.median()),
                "std": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                "min": float(vals.min()),
                "max": float(vals.max()),
            }
        )
    return out


def _best_algo_descriptive(rows: list[dict], oe_key: str) -> str:
    spec = OE_EPISODE_SPECS[oe_key]
    if not rows:
        return "-"
    key = "median"
    reverse = spec["higher_better"]
    best = sorted(rows, key=lambda r: float(r[key]), reverse=reverse)[0]
    return str(best["algorithm"])


def _analysis_row(scope: str) -> dict[str, str]:
    if not ANALYSIS_CSV.is_file():
        return {}
    for row in _read_csv(ANALYSIS_CSV):
        if row.get("scope") == scope:
            return row
    return {}


def _shapiro_table_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for scope in ("OE1", "OE2", "OE3", "ALL"):
        row = _analysis_row(scope)
        if not row:
            continue
        hyp, label = HYPOTHESIS_LABELS.get(scope, (scope, scope))
        for algo in ("MASAC", "MATD3", "MAAC", "HAPPO"):
            p_key = f"shapiro_wilk_p_value_{algo}"
            status = row.get(f"shapiro_wilk_status_{algo}", "")
            if status == "no_data":
                continue
            p_val = row.get(p_key, "")
            rejected = row.get(f"shapiro_wilk_normality_rejected_{algo}", "")
            rows.append(
                [
                    label,
                    hyp,
                    algo,
                    _fmt_stat_num(p_val, ".3e") if p_val else "-",
                    "Si" if str(rejected).lower() == "true" else "No",
                ]
            )
    return rows


def _kruskal_table_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for axis in ("OE1", "OE2", "OE3", "OG"):
        hyp_row = next((r for r in _read_csv(HYP_CSV) if r.get("axis") == axis), {})
        if not hyp_row:
            continue
        hyp, label = HYPOTHESIS_LABELS.get(axis, (axis, axis))
        p_val = float(hyp_row.get("KW_p_value", "nan"))
        rows.append(
            [
                label,
                hyp,
                _fmt_stat_num(hyp_row.get("KW_H_statistic"), ".3f"),
                _fmt_stat_num(p_val, ".4f"),
                "Si" if p_val < 0.05 else "No",
                hyp_row.get("statistical_best_algorithm_by_median_gain", "-"),
            ]
        )
    return rows


def _mwu_table_rows(scope_filter: str | None = None) -> list[list[str]]:
    if not MWU_CSV.is_file():
        return []
    rows: list[list[str]] = []
    for row in _read_csv(MWU_CSV):
        scope = row.get("scope", "")
        if scope_filter and scope != scope_filter:
            continue
        if row.get("mann_whitney_status") != "ok":
            continue
        p_val = float(row.get("mann_whitney_p_value", "nan"))
        hyp, label = HYPOTHESIS_LABELS.get(scope, (scope, scope))
        rows.append(
            [
                label,
                hyp,
                f"{row.get('algorithm_a')} vs {row.get('algorithm_b')}",
                _fmt_stat_num(row.get("mann_whitney_u"), ".1f"),
                _fmt_stat_num(p_val, ".4f"),
                "Si" if p_val < 0.05 else "No",
            ]
        )
    return rows


def _wilcoxon_table_rows(scope_filter: str | None = None) -> list[list[str]]:
    if not WC_CSV.is_file():
        return []
    rows: list[list[str]] = []
    for row in _read_csv(WC_CSV):
        scope = row.get("scope", "")
        if scope_filter and scope != scope_filter:
            continue
        if not str(row.get("wilcoxon_status", "")).startswith("ok"):
            continue
        p_val = float(row.get("wilcoxon_p_value", "nan"))
        hyp, label = HYPOTHESIS_LABELS.get(scope, (scope, scope))
        rows.append(
            [
                label,
                hyp,
                f"{row.get('algorithm_a')} vs {row.get('algorithm_b')}",
                _fmt_stat_num(row.get("wilcoxon_T_statistic"), ".1f"),
                _fmt_stat_num(p_val, ".4f"),
                "Si" if p_val < 0.05 else "No",
            ]
        )
    return rows


def _load_algo_profiles() -> dict:
    from madrl_algorithm_analysis import build_all_profiles, write_metrics_json

    if not ALGO_METRICS_JSON.is_file():
        write_metrics_json(ALGO_METRICS_JSON)
    return json.loads(ALGO_METRICS_JSON.read_text(encoding="utf-8"))


def _algo_figure(algo: str, scen: str, name: str) -> Path | None:
    path = FIG_RUN / algo / scen / "figures" / f"{name}.png"
    return path if path.is_file() else None


def _fmt_ep(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def _add_per_algorithm_analysis_section(
    doc,
    p,
    heading,
    add_table,
    *,
    profiles: dict,
    fig_counter: list[int],
) -> None:
    heading(doc, "5.2 Analisis de convergencia, aprendizaje y desempeno por algoritmo MADRL", 2)
    p(
        doc,
        "Esta seccion complementa el analisis por objetivo especifico (secciones 5.3–5.5) con una "
        "lectura longitudinal por algoritmo sobre la corrida canonica de 50 episodios. Para cada "
        "MADRL se reportan: (i) trayectoria de reward_mean y episodio de meseta; (ii) estabilidad "
        "(varianza intra-entrenamiento); (iii) KPIs distritales por escenario E1/E2/E3; "
        "(iv) heterogeneidad entre los 17 edificios; y (v) comportamiento EV/BESS cuando los datos "
        "lo permiten. La interpretacion se alinea con la literatura CityLearn: algoritmos off-policy "
        "actor-critico (MASAC, MATD3) y atencion cooperativa (MAAC) exhiben patrones de convergencia "
        "distintos; HAPPO on-policy muestra mayor varianza inter-episodio en entornos multiagente "
        "(Yu et al., 2022; Vazquez-Canteli et al., 2024).",
    )

    algo_specs = [
        (
            "MATD3",
            "5.2.1",
            True,
            "MATD3 (Multi-Agent Twin Delayed DDPG) combina politica determinista con retraso de "
            "actualizacion del actor y ruido de exploracion gaussiano. En CityLearn, TD3 y variantes "
            "multiagente han mostrado convergencia rapida en costos pero sensibilidad a la escala de "
            "recompensa (Fujimoto et al., 2018; Di Savino et al., 2025). En Iquitos, MATD3 lidera "
            "OE.1 y OE.2 descriptivamente y obtiene el mejor score global (0,6667), con la mayor "
            "tasa de exito EV (43,9% en E1) y flex_composite distrital minimo (1,0009).",
        ),
        (
            "MAAC",
            "5.2.2",
            True,
            "MAAC (Multi-Agent Actor-Attention-Critic) usa atencion en el critico centralizado para "
            "ponderar contribuciones de agentes vecinos, lo que mejora escalabilidad en distritos "
            "grandes (Iqbal & Sha, 2019; Di Savino et al., 2025). En esta corrida, MAAC converge "
            "tempranamente (meseta ~episodio 4 en los tres escenarios) con baja varianza de "
            "reward_mean y lidera OE.3 (delta costo = 9 515 EUR). Su debilidad relativa en CO2 "
            "(70 654 kg) refleja trade-off multiobjetivo.",
        ),
        (
            "MASAC",
            "5.2.3",
            True,
            "MASAC (Multi-Agent Soft Actor-Critic) maximiza entropia de politica para exploracion "
            "estable; en benchmarks CityLearn, SAC y variantes multiagente suelen mejorar rapido "
            "al inicio pero pueden plateauar antes que metodos on-policy cooperativos "
            "(Haarnoja et al., 2018; arXiv:2602.19223). Aqui, MASAC muestra convergencia estable "
            "pero KPIs distritales inferiores en flexibilidad y CO2; su score OE.3 intermedio "
            "(0,7054) indica competencia parcial en costos sin liderar el eje.",
        ),
        (
            "HAPPO",
            "5.2.4",
            False,
            "HAPPO (Heterogeneous-Agent PPO) aplica PPO secuencial por agente bajo CTDE "
            "(Yu et al., 2022). La corrida registro 49/50 episodios por escenario sin KPIs finales "
            "(error VecEnvWrapper en evaluacion). El analisis es parcial: convergencia de reward_mean "
            "disponible, pero sin flex_composite, delta CO2 ni delta costo auditados. HAPPO queda "
            "incluido en figuras comparativas de convergencia pero excluido de inferencia KPI-level.",
        ),
    ]

    conv_headers = [
        "Esc.",
        "n ep.",
        "Media reward",
        "Desv. est.",
        "CV",
        "Ep. meseta",
        "Mejora ep.1–10 → ult.10",
    ]

    for algo, sec_num, has_kpis, intro in algo_specs:
        prof = profiles["algorithms"][algo]
        heading(doc, f"{sec_num} {algo}", 3)
        p(doc, intro)

        conv_rows = []
        for scen in ("E1", "E2", "E3"):
            c = prof.get("convergence", {}).get(scen)
            if not c:
                continue
            conv_rows.append(
                [
                    scen,
                    str(c["n_episodes"]),
                    _fmt_ep(c["reward_mean"]),
                    _fmt_ep(c["reward_std"]),
                    _fmt_ep(c["coefficient_of_variation"]),
                    str(c["plateau_episode"]) if c["plateau_episode"] is not None else "-",
                    _fmt_ep(c["improvement_first_to_last"]),
                ]
            )
        if conv_rows:
            add_table(
                doc,
                conv_headers,
                conv_rows,
                caption=f"Tabla 5.3-{algo}. Convergencia y estabilidad de {algo} (reward_mean, timeseries.csv).",
                col_widths=[1.2, 1.2, 2.2, 2.0, 1.5, 1.8, 2.5],
            )

        if has_kpis and prof.get("district_kpis"):
            kpi_rows = []
            for scen in ("E1", "E2", "E3"):
                d = prof["district_kpis"].get(scen, {})
                if not d:
                    continue
                kpi_rows.append(
                    [
                        scen,
                        _fmt_ep(d.get("flex_composite")),
                        f"{d.get('carbon_emissions_delta_kg', 0):,.0f}",
                        f"{d.get('electricity_cost_delta_eur', 0):,.0f}",
                        f"{d.get('ev_departure_success_rate', 0) * 100:.1f}%",
                        f"{d.get('grid_import_delta', 0):,.0f}",
                    ]
                )
            add_table(
                doc,
                ["Esc.", "flex_composite", "Delta CO2 (kg)", "Delta costo (EUR)", "Exito EV", "Delta import."],
                kpi_rows,
                caption=f"Tabla 5.4-{algo}. KPIs distritales por escenario ({algo}, corrida 50 ep).",
                col_widths=[1.2, 2.2, 2.5, 2.5, 1.8, 2.0],
            )

            het_rows = []
            for scen in ("E1", "E2", "E3"):
                h = prof.get("building_heterogeneity", {}).get(scen, {})
                if not h:
                    continue
                het_rows.append(
                    [
                        scen,
                        str(int(h["n_buildings"])),
                        f"{h['mean']:,.2f}",
                        f"{h['std']:,.2f}",
                        _fmt_ep(h["cv"], 3),
                        f"{h['min']:,.2f}",
                        f"{h['max']:,.2f}",
                    ]
                )
            add_table(
                doc,
                ["Esc.", "n edif.", "Media KPI edificio", "Desv. est.", "CV", "Min.", "Max."],
                het_rows,
                caption=(
                    f"Tabla 5.5-{algo}. Heterogeneidad inter-edificio (17 agentes, building_objectives_by_algorithm.csv)."
                ),
                col_widths=[1.2, 1.5, 2.5, 2.0, 1.5, 2.0, 2.0],
            )

        dom_scen = {"MATD3": "E1", "MAAC": "E3", "MASAC": "E2", "HAPPO": "E1"}[algo]
        conv_fig = _algo_figure(algo, dom_scen, "convergence_returns")
        if conv_fig:
            fig_counter[0] += 1
            add_figure(
                doc,
                conv_fig,
                f"Figura 5.{fig_counter[0]}. Convergencia reward_mean — {algo}/{dom_scen} (300 dpi, datos Drive).",
                width_cm=FIG_WIDTH_LANDSCAPE,
                interpretation=(
                    f"La trayectoria de {algo} en {dom_scen} muestra "
                    f"{'mejora sostenida hasta meseta temprana' if prof.get('convergence', {}).get(dom_scen, {}).get('plateau_episode', 99) < 15 else 'varianza inter-episodio elevada'} "
                    f"(CV = {_fmt_ep(prof.get('convergence', {}).get(dom_scen, {}).get('coefficient_of_variation', 0), 3)}). "
                    "Coherente con patrones reportados en benchmarks MARL-CityLearn donde la estabilidad "
                    "depende del algoritmo y del peso de recompensa por escenario."
                ),
            )
        expl_fig = _algo_figure(algo, dom_scen, "exploration_action_l2")
        if expl_fig:
            fig_counter[0] += 1
            add_figure(
                doc,
                expl_fig,
                f"Figura 5.{fig_counter[0]}. Exploracion (action_l2) — {algo}/{dom_scen} (trace.csv).",
                interpretation=(
                    f"La norma L2 de acciones de {algo} refleja intensidad de control sobre BESS, "
                    "cargas desplazables y EV. Reduccion gradual sugiere politica mas determinista; "
                    "picos persistentes indican exploracion activa o inestabilidad de politica."
                ),
            )
        base_fig = _algo_figure(algo, dom_scen, "axis_baseline_comparison")
        if base_fig and has_kpis:
            fig_counter[0] += 1
            add_figure(
                doc,
                base_fig,
                f"Figura 5.{fig_counter[0]}. Comparacion vs baseline CityLearn v2 — {algo}/{dom_scen}.",
                interpretation=(
                    f"El contraste con baseline RBC ubica a {algo} respecto a controles heuristicos "
                    "del eje dominante. Esta lectura matiza la superioridad MADRL frente a reglas "
                    "predefinidas (Nweye et al., 2024)."
                ),
            )


def _figure_width_cm(path: Path) -> float:
    try:
        from PIL import Image

        with Image.open(path) as im:
            w, h = im.size
            return FIG_WIDTH_PORTRAIT if h > w * 1.15 else FIG_WIDTH_LANDSCAPE
    except Exception:
        return FIG_WIDTH_LANDSCAPE


def add_figure(
    doc,
    path: Path,
    caption: str,
    width_cm: float | None = None,
    interpretation: str | None = None,
) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    if width_cm is None:
        width_cm = _figure_width_cm(path)
    doc.add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(caption)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = GREY
    if interpretation:
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        para.add_run(interpretation)
    doc.add_paragraph()


def _add_oe_results_section(
    doc,
    p,
    heading,
    add_table,
    *,
    oe_key: str,
    oe_num: int,
    section_num: str,
    district: list[dict[str, str]],
    report: dict,
    fig_counter: list[int],
) -> None:
    cfg = OE_DEFINITIONS[oe_key]
    scenario = cfg["scenario"]
    rows = _rows_for_scenario(district, scenario)
    primary_kpi = cfg["primary_kpis"][0][0]
    best_algo, best_val = _best_algo_by_kpi(rows, primary_kpi, lower_better=True)
    hyp = _hypothesis_row(oe_key)
    kw_p = float(hyp.get("KW_p_value", "nan")) if hyp else float("nan")

    oe_display = {"OE1": "OE.1", "OE2": "OE.2", "OE3": "OE.3"}[oe_key]

    heading(doc, f"{section_num} {oe_display} — Efecto sobre {cfg['dimension']} ({cfg['vd']})", 2)
    p(
        doc,
        f"{oe_display}. Determinar el efecto del algoritmo MADRL (VI: D-VI.1) sobre "
        f"{cfg['dimension']} ({cfg['vd']}) e identificar el algoritmo de mayor efecto en esta "
        f"dimension. El escenario {scenario} concentra el peso de recompensa en este eje "
        f"({cfg['weights']}). La evidencia proviene de la corrida canonica de 50 episodios "
        f"({RUN_ID}) con MATD3, MAAC y MASAC; HAPPO queda excluido de contrastacion por "
        "ausencia de KPIs finales (49/50 ep).",
    )

    kpi_headers = ["Algoritmo"] + [label for _, label, _, _ in cfg["primary_kpis"]]
    kpi_rows = []
    for row in sorted(rows, key=lambda r: float(r[primary_kpi])):
        cells = [row["algorithm"]]
        for kpi, _, fmt, lower in cfg["primary_kpis"]:
            cells.append(_fmt_kpi(row[kpi], fmt, lower))
        kpi_rows.append(cells)
    add_table(
        doc,
        kpi_headers,
        kpi_rows,
        caption=(
            f"Tabla 5.{3 + oe_num}. KPIs de {cfg['vd']} en escenario {scenario} "
            f"(distrito, corrida Colab 50 ep)."
        ),
        col_widths=[2.2] + [2.4] * (len(kpi_headers) - 1),
    )

    score_rows = []
    for item in report.get("ranking_with_kpis", []):
        score_rows.append(
            [
                item["algorithm"],
                f"{item.get(cfg['score_key'], 0):.4f}",
                "Si" if item["algorithm"] == best_algo else "No",
            ]
        )
    score_rows.sort(key=lambda r: float(r[1]), reverse=True)
    add_table(
        doc,
        ["Algoritmo", f"Score normalizado {oe_key}", f"Mayor efecto en {oe_key}"],
        score_rows,
        caption=f"Tabla 5.{6 + oe_num}. Ranking descriptivo {oe_display} (best_madrl_report.json).",
        col_widths=[3.0, 4.0, 4.5],
    )

    p(
        doc,
        f"Respuesta a {oe_display}: el algoritmo MADRL de mayor efecto sobre {cfg['vd']} "
        f"en {scenario} es {best_algo} "
        f"({cfg['primary_kpis'][0][1]} = {_fmt_kpi(str(best_val), cfg['primary_kpis'][0][2], True)}). "
        f"El contraste inferencial Kruskal-Wallis sobre KPI-gains en {scenario} arroja "
        f"p = {kw_p:.3f} (alpha = 0,05), por lo que la diferencia global entre algoritmos "
        f"{'no alcanza significancia inferencial con una semilla' if kw_p >= 0.05 else 'alcanza significancia inferencial'}. "
        "La evidencia descriptiva de distrito respalda la identificacion del lider por objetivo; "
        "la inferencia confirmatoria requiere replicacion multi-semilla (Colas et al., 2019).",
    )

    fig_specs = [
        (cfg["conv_fig"], f"convergencia de reward_mean en {scenario}"),
        (cfg["kpi_fig"], f"comparativa de KPI {oe_key} en {scenario}"),
        (cfg["building_fig"], f"desagregacion por edificio ({cfg['vd']})"),
    ]
    if cfg.get("trace_fig"):
        fig_specs.append((cfg["trace_fig"], "trazas de control MADRL (trace.csv)"))

    for path, desc in fig_specs:
        fig_counter[0] += 1
        n = fig_counter[0]
        doc.add_page_break()
        width = FIG_WIDTH_LANDSCAPE if "convergencia" in desc else None
        add_figure(
            doc,
            path,
            f"Figura 5.{n}. {desc.capitalize()} — escenario {scenario}, datos reales Drive (300 dpi).",
            width_cm=width,
            interpretation=(
                f"La Figura 5.{n} vincula directamente {oe_display} con {cfg['vd']}: "
                f"en {scenario} se observa que {best_algo} concentra el mejor desempeno "
                f"descriptivo frente a los demas MADRL auditados. La lectura debe hacerse "
                f"exclusivamente en la dimension {cfg['dimension']}, sin extrapolar al "
                "score global ni a los otros objetivos especificos."
            ),
        )


def add_chapter_5_doctoral(doc, p, heading, add_table, status_note) -> None:
    report = _read_json(BEST_REPORT)
    district = _read_csv(DISTRICT_CSV)
    profiles = _load_algo_profiles()
    fig_counter = [0]

    heading(doc, "Capitulo 5. Resultados y contrastacion de hipotesis", 1)
    p(
        doc,
        f"Este capitulo organiza la evidencia experimental de la corrida canonica Colab/Drive "
        f"({RUN_ID}, 50 episodios) en dos niveles complementarios: (A) analisis por algoritmo "
        "MADRL (convergencia, estabilidad, heterogeneidad edificio) y (B) analisis por objetivo "
        "especifico (OE.1, OE.2, OE.3) siguiendo la cadena VI→VD del diseno factorial. "
        "La sintesis integrada, la comparacion con baseline CityLearn v2 y la inferencia "
        "estadistica cierran el capitulo con veredicto explicito de cumplimiento por OE.",
    )

    heading(doc, "5.1 Marco de contrastacion VI→VD y cobertura experimental", 2)
    add_table(
        doc,
        ["Objetivo", "Escenario", "VD", "KPI principal distrito", "Pesos recompensa"],
        [
            ["OE.1 Flexibilidad", "E1", "D-VD.1", "flex_composite, peak, ramping", "[0,70; 0,15; 0,15]"],
            ["OE.2 Emisiones CO2", "E2", "D-VD.2", "carbon_emissions_delta_kg", "[0,15; 0,70; 0,15]"],
            ["OE.3 Costos", "E3", "D-VD.3", "electricity_cost_delta_eur", "[0,15; 0,15; 0,70]"],
        ],
        caption="Tabla 5.1. Operacionalizacion objetivo→escenario→KPI (corrida 50 ep).",
        col_widths=[3.5, 1.5, 1.8, 4.5, 3.7],
    )
    add_table(
        doc,
        ["Algoritmo (VI)", "E1 ep.", "E2 ep.", "E3 ep.", "KPIs finales", "Uso en OE"],
        [
            ["MATD3", "50", "50", "50", "Si", "OE.1, OE.2, OE.3"],
            ["MAAC", "50", "50", "50", "Si", "OE.1, OE.2, OE.3"],
            ["MASAC", "50", "50", "50", "Si", "OE.1, OE.2, OE.3"],
            ["HAPPO", "49", "49", "49", "No", "Excluido (VecEnvWrapper)"],
        ],
        caption="Tabla 5.2. Cobertura de episodios auditada (episodes_recorded).",
        col_widths=[2.5, 1.8, 1.8, 1.8, 2.5, 3.6],
    )

    _add_per_algorithm_analysis_section(
        doc, p, heading, add_table, profiles=profiles, fig_counter=fig_counter
    )

    _add_oe_results_section(
        doc, p, heading, add_table,
        oe_key="OE1", oe_num=1, section_num="5.3",
        district=district, report=report, fig_counter=fig_counter,
    )
    _add_oe_results_section(
        doc, p, heading, add_table,
        oe_key="OE2", oe_num=2, section_num="5.4",
        district=district, report=report, fig_counter=fig_counter,
    )
    _add_oe_results_section(
        doc, p, heading, add_table,
        oe_key="OE3", oe_num=3, section_num="5.5",
        district=district, report=report, fig_counter=fig_counter,
    )

    heading(doc, "5.6 Sintesis integrada por objetivo especifico", 2)
    p(
        doc,
        "La Tabla 5.10 resume la respuesta a cada OE con el algoritmo de mayor efecto "
        "descriptivo, el score normalizado y la significancia inferencial por eje. "
        "Ningun algoritmo domina los tres objetivos: MATD3 lidera OE.1 y OE.2; MAAC lidera OE.3. "
        "El score global 0,6667 de MATD3 refleja su ventaja en dos de tres dimensiones, "
        "no superioridad universal.",
    )
    synth_rows = []
    oe_map = [("OE.1", "OE1", "E1", "score_oe1_flex"), ("OE.2", "OE2", "E2", "score_oe2_co2"), ("OE.3", "OE3", "E3", "score_oe3_cost")]
    for oe_label, oe_key, scen, score_key in oe_map:
        cfg = OE_DEFINITIONS[oe_key]
        rows = _rows_for_scenario(district, scen)
        primary = cfg["primary_kpis"][0][0]
        best, val = _best_algo_by_kpi(rows, primary, lower_better=True)
        score = next(item.get(score_key, 0) for item in report["ranking_with_kpis"] if item["algorithm"] == best)
        hyp = _hypothesis_row(oe_key)
        synth_rows.append(
            [
                oe_label,
                scen,
                cfg["vd"],
                best,
                _fmt_kpi(str(val), cfg["primary_kpis"][0][2], True),
                f"{score:.4f}",
                f"{float(hyp.get('KW_p_value', 0)):.3f}",
            ]
        )
    add_table(
        doc,
        ["OE", "Esc.", "VD", "Mayor efecto (VI)", "KPI principal", "Score norm.", "KW p"],
        synth_rows,
        caption="Tabla 5.10. Matriz de respuesta por objetivo especifico (50 ep Colab).",
        col_widths=[1.5, 1.2, 1.5, 2.5, 2.8, 2.0, 1.5],
    )

    ranking_rows = []
    for item in report.get("ranking_with_kpis", []):
        ranking_rows.append(
            [
                str(item.get("rank", "")),
                item["algorithm"],
                f"{item.get('score_global', 0):.4f}",
                f"{item.get('score_oe1_flex', 0):.4f}",
                f"{item.get('score_oe2_co2', 0):.4f}",
                f"{item.get('score_oe3_cost', 0):.4f}",
            ]
        )
    add_table(
        doc,
        ["Rango", "Algoritmo", "Global", "OE.1", "OE.2", "OE.3"],
        ranking_rows,
        caption="Tabla 5.11. Ranking integrado por score normalizado (best_madrl_report.json).",
        col_widths=[1.5, 2.5, 2.2, 2.0, 2.0, 2.0],
    )

    fig_counter[0] += 1
    doc.add_page_break()
    add_figure(
        doc,
        FD_DIR / "comparativo_global_ranking_oe.png",
        f"Figura 5.{fig_counter[0]}. Ranking global OE.1/OE.2/OE.3 y KPIs fisicos por algoritmo.",
        interpretation=(
            "La figura confirma la no-dominancia unica: MATD3 concentra ventaja en flexibilidad "
            "y CO2; MAAC en costo. Esta visualizacion cierra la lectura integrada de la Tabla 5.10."
        ),
    )
    fig_counter[0] += 1
    add_figure(
        doc,
        FD_DIR / "comparativo_best_worst_por_escenario.png",
        f"Figura 5.{fig_counter[0]}. Mejor y peor MADRL por escenario objetivo.",
        interpretation=(
            "Por escenario, el algoritmo de mayor efecto coincide con OE.1→MATD3 (E1), "
            "OE.2→MATD3 (E2) y OE.3→MAAC (E3), alineado con las tablas 5.4–5.6 y 5.10."
        ),
    )
    fig_counter[0] += 1
    add_figure(
        doc,
        MO_DIR / "drive_district_objectives.png",
        f"Figura 5.{fig_counter[0]}. KPIs multiobjetivo agregados a nivel distrito.",
        width_cm=FIG_WIDTH_LANDSCAPE,
        interpretation=(
            "La agregacion distrital muestra trade-offs entre ejes: mejoras en flexibilidad o CO2 "
            "no implican automaticamente mejor costo, lo que justifica el diseno factorial E1/E2/E3."
        ),
    )

    heading(doc, "5.7 Comparacion con linea base CityLearn v2 por objetivo", 2)
    p(
        doc,
        "Se contrasta cada eje OE frente a baseline y hour_rbc de CityLearn v2 (54 KPI, score HPHI). "
        "Fuente: outputs/{}/resumen_comparativo/citylearn_v2_baseline/. "
        "Hallazgo: los controles RBC superan a MADRL en score global, pero la comparacion por eje "
        "permite ubicar el efecto relativo de cada algoritmo aprendido.".format(RUN_ID),
    )
    add_table(
        doc,
        ["OE / Esc.", "1.o eje", "Score eje", "Mejor MADRL", "Score MADRL", "Posicion MADRL"],
        [
            ["OE.1 / E1", "MATD3", "0,496", "MATD3", "0,496", "1.o / 5 metodos"],
            ["OE.2 / E2", "baseline v2", "1,000", "MATD3", "0,291", "4.o / 5 metodos"],
            ["OE.3 / E3", "hour_rbc", "0,737", "MAAC", "0,531", "3.o / 5 metodos"],
        ],
        caption="Tabla 5.12. Ranking por eje OE (ranking_by_axis.csv, E1–E3).",
        col_widths=[2.0, 2.5, 2.0, 2.5, 2.5, 2.5],
    )
    p(
        doc,
        "Lectura por OE: en OE.1 (flexibilidad) MATD3 supera incluso a baseline y hour_rbc en "
        "score de eje; en OE.2 (CO2) los controles RBC dominan y MATD3 lidera solo entre MADRL; "
        "en OE.3 (costos) MAAC es el mejor MADRL pero hour_rbc y baseline mantienen ventaja absoluta.",
    )
    for scenario in ("E1", "E2", "E3"):
        heatmap = BL_DIR / scenario / "baseline_gain_heatmap.png"
        if heatmap.is_file():
            fig_counter[0] += 1
            add_figure(
                doc,
                heatmap,
                f"Figura 5.{fig_counter[0]}. Mapa de ganancia vs baseline — escenario {scenario}.",
                width_cm=FIG_WIDTH_HEATMAP,
                interpretation=(
                    f"El mapa de {scenario} detalla que KPIs del eje correspondiente favorecen "
                    "a controles RBC frente a MADRL; matiza las respuestas OE sin invalidar "
                    "la identificacion del mayor efecto inter-algoritmico."
                ),
            )

    heading(doc, "5.8 Analisis descriptivo por objetivo (50 episodios reales)", 2)
    p(
        doc,
        "El nivel descriptivo se calcula sobre episodios auditados de timeseries.csv "
        f"({EPISODE_CSV.name}): media, mediana, desviacion estandar, minimo y maximo "
        "por algoritmo en el escenario dominante de cada OE. HAPPO incluye 49 episodios "
        "por escenario; MAAC, MASAC y MATD3 incluyen 50. Los KPI finales de distrito "
        "(Tablas 5.4–5.6) complementan la lectura con valores agregados de simulacion.",
    )
    desc_table_num = 13
    for oe_key, oe_label in (("OE1", "OE.1"), ("OE2", "OE.2"), ("OE3", "OE.3")):
        spec = OE_EPISODE_SPECS[oe_key]
        desc_rows = _descriptive_episode_rows(oe_key)
        if not desc_rows:
            continue
        table_rows = []
        for row in sorted(desc_rows, key=lambda r: float(r["median"]), reverse=spec["higher_better"]):
            table_rows.append(
                [
                    row["algorithm"],
                    str(row.get("n_episodes", "-")),
                    _fmt_stat_num(row["mean"], spec["fmt"]),
                    _fmt_stat_num(row["median"], spec["fmt"]),
                    _fmt_stat_num(row["std"], spec["fmt"]),
                    _fmt_stat_num(row["min"], spec["fmt"]),
                    _fmt_stat_num(row["max"], spec["fmt"]),
                ]
            )
        add_table(
            doc,
            ["Algoritmo", "n ep.", "Media", "Mediana", "Desv. est.", "Min.", "Max."],
            table_rows,
            caption=(
                f"Tabla 5.{desc_table_num}. Estadistica descriptiva {oe_label} — "
                f"{spec['label']} ({spec['scenario']}, corrida {RUN_ID})."
            ),
            col_widths=[2.0, 1.2, 2.0, 2.0, 2.0, 2.0, 2.0],
        )
        desc_table_num += 1
        best_desc = _best_algo_descriptive(desc_rows, oe_key)
        p(
            doc,
            f"Descriptivo {oe_label} ({spec['hypothesis']}): el algoritmo con mejor mediana "
            f"en {spec['scenario']} es {best_desc}. Esta evidencia responde al objetivo "
            f"especifico antes de la contrastacion inferencial (alpha = 0,05).",
        )

    heading(doc, "5.9 Contrastacion inferencial de hipotesis (protocolo no parametrico)", 2)
    p(
        doc,
        "El protocolo inferencial sigue el orden obligatorio del Capitulo 3 y la formulacion "
        "del Capitulo 1: (1) Shapiro-Wilk por grupo de KPI-gains; (2) si se viola normalidad, "
        "solo pruebas no parametricas — Kruskal-Wallis (comparacion global), Mann-Whitney U "
        "(pares independientes) y Wilcoxon signed-rank (pares pareados por KPI); alpha = 0,05. "
        "HAPPO queda excluido de inferencia KPI-level por ausencia de KPIs finales; la inferencia "
        "efectiva opera sobre MASAC, MATD3 y MAAC (semilla unica, seed 0).",
    )

    heading(doc, "5.9.1 Prueba de normalidad (Shapiro-Wilk)", 3)
    sw_rows = _shapiro_table_rows()
    if sw_rows:
        add_table(
            doc,
            ["Alcance", "Hipotesis", "Algoritmo", "p (SW)", "Normalidad rechazada"],
            sw_rows,
            caption="Tabla 5.16. Shapiro-Wilk sobre KPI-gains por grupo (analisis_estadistico_madrl.csv).",
            col_widths=[2.5, 1.5, 2.0, 2.5, 2.5],
        )
    p(
        doc,
        "En todos los alcances OE.1–OE.3 y ALL se rechaza la normalidad en al menos un grupo "
        "(p < 0,05), lo que justifica el uso exclusivo de pruebas no parametricas en las "
        "etapas siguientes (Colas et al., 2019; Agarwal et al., 2021).",
    )

    heading(doc, "5.9.2 Comparacion global (Kruskal-Wallis)", 3)
    kw_rows = _kruskal_table_rows()
    add_table(
        doc,
        ["Alcance", "Hipotesis", "H", "p", "Signif. alpha=0,05", "Mejor (mediana KPI-gain)"],
        kw_rows,
        caption="Tabla 5.17. Kruskal-Wallis por eje OE y agregado OG/HG (hipotesis_estadisticas_madrl.csv).",
        col_widths=[2.3, 1.3, 1.3, 1.5, 2.0, 2.6],
    )
    p(
        doc,
        "Ningun Kruskal-Wallis por eje alcanza alpha = 0,05 con una semilla (OE.1 p=0,281; "
        "OE.2 p=0,546; OE.3 p=0,388; ALL p=0,155). Por tanto, no se rechaza H0 de igualdad "
        "global entre algoritmos en los contrastes omnibus; las respuestas a HE.1–HE.3 y HG "
        "se sustentan principalmente en evidencia descriptiva (seccion 5.8 y Tablas 5.4–5.6).",
    )

    heading(doc, "5.9.3 Comparaciones por pares independientes (Mann-Whitney U)", 3)
    mwu_rows = _mwu_table_rows()
    if mwu_rows:
        add_table(
            doc,
            ["Alcance", "Hipotesis", "Par", "U", "p", "Signif."],
            mwu_rows,
            caption="Tabla 5.18. Mann-Whitney U por par de algoritmos (comparaciones_mwu_madrl.csv).",
            col_widths=[2.2, 1.2, 2.8, 1.5, 1.5, 1.3],
        )
    p(
        doc,
        "Ningun par Mann-Whitney U alcanza significancia global a alpha = 0,05 en los ejes "
        "OE.1–OE.3; en ALL, MASAC vs MATD3 (p = 0,070) tampoco alcanza el umbral. "
        "Estas pruebas complementan el Kruskal-Wallis sin sustituir la evidencia descriptiva.",
    )

    heading(doc, "5.9.4 Comparaciones pareadas (Wilcoxon signed-rank)", 3)
    wc_rows = _wilcoxon_table_rows()
    if wc_rows:
        add_table(
            doc,
            ["Alcance", "Hipotesis", "Par", "T", "p", "Signif."],
            wc_rows,
            caption="Tabla 5.19. Wilcoxon signed-rank por KPI pareado (comparaciones_wilcoxon_madrl.csv).",
            col_widths=[2.2, 1.2, 2.8, 1.5, 1.5, 1.3],
        )
    p(
        doc,
        "Wilcoxon pareado detecta diferencias sistematicas en pares especificos: ALL "
        "MASAC vs MATD3 (p = 0,0049) y MASAC vs MAAC (p < 0,001); en OE.1, MASAC vs MAAC "
        "(p = 0,0013). Estos contrastes son exploratorios sobre KPI-gains pareados y no "
        "reemplazan replicacion multi-semilla ni el diseno factorial 4×3 completo.",
    )

    heading(doc, "5.9.5 Decision por hipotesis (Capitulo 1)", 3)
    hyp_decision_rows = []
    for axis, (hyp_code, label) in (
        ("OE1", ("HE.1", "OE.1 / E1")),
        ("OE2", ("HE.2", "OE.2 / E2")),
        ("OE3", ("HE.3", "OE.3 / E3")),
        ("OG", ("HG", "Global (ALL)")),
    ):
        hyp_row = next((r for r in _read_csv(HYP_CSV) if r.get("axis") == axis), {})
        kw_sig = float(hyp_row.get("KW_p_value", 1)) < 0.05 if hyp_row else False
        hyp_decision_rows.append(
            [
                hyp_code,
                label,
                "Kruskal-Wallis + descriptivo",
                "Si" if kw_sig else "No (omnibus)",
                hyp_row.get("statistical_best_algorithm_by_median_gain", "-"),
                "Evidencia descriptiva + exploratoria KPI-gain",
            ]
        )
    add_table(
        doc,
        ["Hipotesis", "Alcance", "Prueba principal", "H0 rechazada (KW)", "Mejor (mediana gain)", "Decision"],
        hyp_decision_rows,
        caption="Tabla 5.20. Sintesis de contrastacion HG / HE.1–HE.3 (corrida canonica 50 ep).",
        col_widths=[1.5, 2.0, 2.5, 2.0, 2.5, 3.0],
    )

    heading(doc, "5.10 Discusion integrada alineada a objetivos", 2)
    p(
        doc,
        "La lectura doctoral exige separar tres niveles. Nivel 1 (respuesta OE): MATD3 es el "
        "de mayor efecto en OE.1 (flexibilidad, E1) y OE.2 (CO2, E2); MAAC en OE.3 (costos, E3). "
        "Nivel 2 (integracion): MATD3 obtiene score global 0,6667 por liderar dos ejes, pero "
        "no domina costos. Nivel 3 (contraste externo): baseline RBC de CityLearn v2 supera "
        "globalmente a MADRL (seccion 5.6), coherente con Nweye et al. (2024). La coherencia "
        "vertical PG→OE→VD se cumple en estructura y evidencia descriptiva; la inferencia causal "
        "robusta requiere multi-semilla. HAPPO (49/50 ep) reduce el diseno factorial efectivo "
        "a 3×3 en inferencia. Los hallazgos convergen con benchmarks CityLearn que reportan "
        "trade-offs entre algoritmos off-policy y on-policy (arXiv:2602.19223) y la utilidad de "
        "controles RBC como referencia superior en algunos KPIs (Vazquez-Canteli et al., 2024).",
    )

    heading(doc, "5.11 Veredicto de cumplimiento por objetivo especifico", 2)
    p(
        doc,
        "Tabla 5.21 sintetiza el cumplimiento de cada OE en dos planos: descriptivo (KPI distrital "
        "y ranking normalizado) e inferencial (Kruskal-Wallis sobre KPI-gains, alpha = 0,05). "
        "Un OE se considera cumplido descriptivamente cuando se identifica el algoritmo de mayor "
        "efecto con datos auditados; inferencialmente cuando KW rechaza H0 (ninguno alcanza con "
        "una semilla). HE.1–HE.3 y HG se vinculan explicitamente.",
    )
    verdict_rows = [
        [
            "OE.1",
            "D-VD.1 / E1",
            "HE.1",
            "MATD3",
            "flex_composite = 1,0009; score = 1,0000",
            "Si (descriptivo)",
            "No (KW p = 0,281)",
            "Cumplido parcialmente: lider identificado; inferencia no confirmatoria",
        ],
        [
            "OE.2",
            "D-VD.2 / E2",
            "HE.2",
            "MATD3",
            "delta CO2 = 23 070 kg; score = 1,0000",
            "Si (descriptivo)",
            "No (KW p = 0,546)",
            "Cumplido parcialmente: menor emision entre MADRL; RBC supera globalmente",
        ],
        [
            "OE.3",
            "D-VD.3 / E3",
            "HE.3",
            "MAAC",
            "delta costo = 9 515 EUR; score = 1,0000",
            "Si (descriptivo)",
            "No (KW p = 0,388)",
            "Cumplido parcialmente: lider costos identificado; hour_rbc supera en score eje",
        ],
        [
            "OG",
            "ALL",
            "HG",
            "MATD3",
            "score global = 0,6667 (2/3 ejes)",
            "Si (descriptivo)",
            "No (KW p = 0,155)",
            "Cumplido parcialmente: mejor integracion MADRL; sin dominancia universal",
        ],
    ]
    add_table(
        doc,
        ["OE", "VD / Esc.", "Hip.", "Mejor VI", "Evidencia KPI", "Desc.", "Infer.", "Veredicto"],
        verdict_rows,
        caption="Tabla 5.21. Veredicto de cumplimiento OE.1–OE.3 y HG (corrida canonica 50 ep).",
        col_widths=[1.2, 1.8, 1.0, 1.5, 2.8, 1.5, 1.8, 2.5],
    )
    p(
        doc,
        "Conclusion operativa: los tres objetivos especificos se cumplen en el sentido descriptivo "
        "exigido por la tesis (identificacion del algoritmo de mayor efecto por eje), pero ninguno "
        "alcanza significancia inferencial omnibus con una semilla. La hipotesis global HG se "
        "sustenta descriptivamente en MATD3; Wilcoxon ALL (MASAC vs MATD3, p = 0,0049) sugiere "
        "diferencias exploratorias en KPI-gains pareados que requieren replicacion multi-semilla.",
    )


def add_chapter_6_doctoral(doc, p, heading, bullet, add_table) -> None:
    heading(doc, "Capitulo 6. Conclusiones y trabajo futuro", 1)
    heading(doc, "6.1 Conclusiones por objetivo especifico", 2)
    p(
        doc,
        "OE.1 (flexibilidad, D-VD.1, escenario E1): el algoritmo MADRL de mayor efecto es MATD3 "
        "(flex_composite = 1,0009; score normalizado OE.1 = 1,0000; 50 episodios). MATD3 tambien "
        "registra la mayor tasa de exito EV (43,9%), coherente con la operacionalizacion de "
        "flexibilidad mediante BESS, cargadores y cargas desplazables.",
    )
    p(
        doc,
        "OE.2 (emisiones CO2, D-VD.2, escenario E2): el algoritmo de mayor efecto es MATD3 "
        "(delta CO2 = 23 070 kg; score OE.2 = 1,0000). La reduccion distrital es la menor entre "
        "los tres MADRL auditados (MASAC: 77 649 kg; MAAC: 70 654 kg).",
    )
    p(
        doc,
        "OE.3 (costos energeticos, D-VD.3, escenario E3): el algoritmo de mayor efecto es MAAC "
        "(delta costo = 9 515 EUR; score OE.3 = 1,0000), frente a MATD3 (44 399 EUR) y MASAC "
        "(19 793 EUR). Esta conclusion es independiente del score global y confirma trade-offs "
        "entre objetivos.",
    )
    p(
        doc,
        "Integracion: MATD3 obtiene score global 0,6667 por liderar OE.1 y OE.2, pero no OE.3. "
        "Ningun Kruskal-Wallis por eje alcanza alpha=0,05 (Tabla 5.17); las respuestas OE se "
        "sustentan en evidencia descriptiva trazable. La comparacion con baseline CityLearn v2 "
        "(seccion 5.6) muestra que controles RBC superan globalmente a MADRL, matizando la "
        "generalizacion causal pero no invalidando el benchmark inter-algoritmico.",
    )
    heading(doc, "6.2 Limitaciones", 2)
    p(
        doc,
        "Las limitaciones principales son: (i) semilla unica (seed 0), insuficiente para "
        "conclusiones causales robustas segun Colas et al. (2019); (ii) HAPPO sin KPIs finales "
        "(49/50 episodios, error VecEnvWrapper), lo que reduce el diseno factorial efectivo a "
        "3×3 en inferencia; (iii) simulacion sin validacion en red fisica; (iv) CityLearn v3 "
        "propuesto como extension experimental de tesis; (v) MADRL por debajo del baseline RBC "
        "en score global HPHI. La inferencia Colab por OE se reporta en seccion 5.9 y Tabla 5.21.",
    )
    heading(doc, "6.3 Trabajo futuro", 2)
    p(
        doc,
        "Se propone: re-evaluacion de HAPPO tras corregir VecEnvWrapper; corrida multi-semilla "
        "(≥5, ideal ≥20) con post-hoc Dunn y correccion Bonferroni; optimizacion con Optuna; "
        "analisis de frontera de Pareto por eje; y transferencia del benchmark a otros sistemas "
        "aislados de la Amazonia peruana. La comparacion con SB3 (PPO/SAC/A2C) y el benchmark "
        "hour_rbc E2 completado en segundo plano enriqueceran el contraste con literatura.",
    )


def verify_doctoral_docx(path: Path) -> dict:
    import re

    from docx import Document

    from thesis_references_apa import reference_stats

    required_sections = [
        "Dedicatoria",
        "Agradecimientos",
        "Resumen",
        "Abstract",
        "Introduccion",
        "Capitulo 5",
        "Capitulo 6",
        "Referencias bibliograficas",
    ]
    required_tables_min = 15
    required_figures_min = 12
    ref_stats = reference_stats()
    required_refs_min = max(50, ref_stats["total_unique"] - 5)

    doc = Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text)
    headings = [p.text for p in doc.paragraphs if p.style and p.style.name.startswith("Heading")]

    section_ok = {s: any(s.lower() in h.lower() for h in headings) or s.lower() in text.lower() for s in required_sections}
    n_tables = len(doc.tables)
    n_images = sum(1 for rel in doc.part.rels.values() if "image" in rel.target_ref)

    in_refs = False
    n_ref_paras = 0
    for para in doc.paragraphs:
        t = (para.text or "").strip()
        if "Referencias bibliograficas" in t:
            in_refs = True
            continue
        if in_refs and re.match(r"^[A-Za-z]", t) and re.search(r"\(\d{4}", t):
            n_ref_paras += 1

    checks = {
        "sections": section_ok,
        "tables_count": n_tables,
        "tables_ok": n_tables >= required_tables_min,
        "images_count": n_images,
        "images_ok": n_images >= required_figures_min,
        "references_count": n_ref_paras,
        "references_expected": ref_stats["total_unique"],
        "references_ok": n_ref_paras >= required_refs_min,
        "has_matd3_selection": "MATD3" in text and ("0.6667" in text or "0,6667" in text),
        "has_multiobjetivo": "multiobjetivo" in text.lower() or "185" in text,
        "has_drive_figures": "timeseries.csv" in text.lower() or "artefactos drive" in text.lower(),
        "has_referencias_apa": "Referencias_APA.md" in text or "referencias bibliograficas" in text.lower(),
        "complete": (
            all(section_ok.values())
            and n_tables >= required_tables_min
            and n_images >= required_figures_min
            and n_ref_paras >= required_refs_min
        ),
    }
    return checks
