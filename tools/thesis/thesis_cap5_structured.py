"""Capitulo 5: descriptivos -> inferenciales -> otros -> hipotesis -> discusion.

Cada bloque principal trata OG, OE.1, OE.2 y OE.3 de forma independiente.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
if str(_THESIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THESIS_DIR))

from thesis_doctoral_sections import (  # noqa: E402
    ANTECEDENTES_NACIONALES,
    BEST_REPORT,
    BL_DIR,
    DISTRICT_CSV,
    FD_DIR,
    FIG_WIDTH_HEATMAP,
    FIG_WIDTH_LANDSCAPE,
    MO_DIR,
    OE_DEFINITIONS,
    OE_EPISODE_SPECS,
    RUN_ID,
    _antecedents_discussion_text,
    _best_algo_by_kpi,
    _best_algo_descriptive,
    _descriptive_episode_rows,
    _fmt_kpi,
    _fmt_stat_num,
    _hypothesis_row,
    _kruskal_table_rows,
    _mwu_table_rows,
    _og_oe_verdict_text,
    _read_csv,
    _read_json,
    _rows_for_scenario,
    _shapiro_table_rows,
    _significant_wilcoxon_rows,
    _verdict_table_rows,
    add_figure,
    write_pe_answers_audit,
)

# Formulaciones exactas Cap. 1 (autor 2026-07-29). No parafrasear.
PG_EXACT = (
    "¿En qué medida el algoritmo MADRL (aprendizaje por refuerzo profundo multiagente) "
    "impacta en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ "
    "y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál "
    "de los algoritmos presenta el mejor desempeño a nivel global?"
)
PE_EXACT = {
    "OE1": (
        "PE.1: ¿En qué medida el algoritmo MADRL impacta en la flexibilidad energética en "
        "comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta "
        "el mejor desempeño en el escenario E1?"
    ),
    "OE2": (
        "PE.2: ¿En qué medida el algoritmo MADRL impacta en las emisiones de CO₂ en "
        "comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta "
        "el mejor desempeño en el escenario E2?"
    ),
    "OE3": (
        "PE.3: ¿En qué medida el algoritmo MADRL impacta en los costos energéticos en "
        "comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta "
        "el mejor desempeño en el escenario E3?"
    ),
}
OG_EXACT = (
    "OG. - Determinar el impacto de los algoritmos aprendizaje por refuerzo profundo "
    "multiagente (MADRLs) en la gestión coordinada de la flexibilidad energética, las "
    "emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad "
    "de Iquitos, e identificar cuál de los algoritmos presenta el mejor desempeño a nivel global."
)
OE_EXACT = {
    "OE1": (
        "OE.1: Determinar el impacto de los algoritmos MADRLs en la flexibilidad energética "
        "en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los "
        "algoritmos presenta el mejor desempeño en el escenario E1."
    ),
    "OE2": (
        "OE.2: Determinar el impacto de los algoritmos MADRLs en las emisiones de CO₂ en "
        "comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los "
        "algoritmos presenta el mejor desempeño en el escenario E2."
    ),
    "OE3": (
        "OE.3: Determinar el impacto de los algoritmos MADRLs en los costos energéticos "
        "en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los "
        "algoritmos presenta el mejor desempeño en el escenario E3."
    ),
}
H_EXACT = {
    "H0G": (
        "H0G.-El algoritmo MADRL no impacta de manera estadísticamente significativa y "
        "diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones "
        "de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, "
        "y no existen diferencias significativas en el desempeño global de los algoritmos."
    ),
    "H1G": (
        "H1G.- El algoritmo MADRL impacta de manera estadísticamente significativa y "
        "diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones "
        "de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, "
        "y el desempeño global difiere entre los algoritmos."
    ),
    "HE10": (
        "HE10.- El algoritmo MADRL no impacta de manera estadísticamente significativa en "
        "la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y "
        "no existen diferencias significativas entre los algoritmos evaluados en el escenario E1."
    ),
    "HE11": (
        "HE11.- El algoritmo MADRL impacta de manera estadísticamente significativa en la "
        "flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y "
        "existen diferencias significativas entre los algoritmos evaluados en el escenario E1."
    ),
    "HE20": (
        "HE20.- El algoritmo MADRL no impacta de manera estadísticamente significativa en "
        "las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y no "
        "existen diferencias significativas entre los algoritmos evaluados en el escenario E2."
    ),
    "HE21": (
        "HE21.- El algoritmo MADRL impacta de manera estadísticamente significativa en las "
        "emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y existen "
        "diferencias significativas entre los algoritmos evaluados en el escenario E2."
    ),
    "HE30": (
        "HE30.-El algoritmo MADRL no impacta de manera estadísticamente significativa en "
        "los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no "
        "existen diferencias significativas entre los algoritmos evaluados en el escenario E3."
    ),
    "HE31": (
        "HE31.-El algoritmo MADRL impacta de manera estadísticamente significativa en los "
        "costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y existen "
        "diferencias significativas entre los algoritmos evaluados en el escenario E3."
    ),
}
OE_H_PAIR = {"OE1": ("HE10", "HE11"), "OE2": ("HE20", "HE21"), "OE3": ("HE30", "HE31")}

# Criterios obligatorios para determinar impacto (cumplimiento OG/OE y demostracion HE).
# Todos deben estar documentados a nivel distrito y edificio; C5 es obligatorio.
IMPACT_CRITERIA = [
    (
        "C1",
        "Impacto vs baseline",
        "Wilcoxon KPI-gains vs cero + Holm",
        "Inferencial HE (necesario)",
        "KPI-gains distrito (evaluate_v2)",
    ),
    (
        "C2",
        "Diferencias entre algoritmos",
        "Kruskal-Wallis / Friedman + post hoc",
        "Inferencial HE (necesario)",
        "KPI-gains / integracion multi-eje",
    ),
    (
        "C3",
        "KPIs fisicos de distrito por eje",
        "flex_composite / ΔCO2 / Δcosto",
        "Descriptivo OE.1–OE.3",
        "district_objectives_by_algorithm.csv",
    ),
    (
        "C4",
        "KPIs desagregados por edificio por eje",
        "17 edificios × E1/E2/E3",
        "Descriptivo OE.1–OE.3",
        "building_objectives_by_algorithm.csv",
    ),
    (
        "C5",
        "Control de recursos",
        "BESS, EV/V2G, carga desplazable (acciones y exito EV)",
        "Obligatorio (atribuibilidad del impacto)",
        "inventario + traces + EV success",
    ),
]


def _inventory_rows() -> list[list[str]]:
    path = MO_DIR / "building_inventory_multiobjective.csv"
    if not path.is_file():
        return []
    rows: list[list[str]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            controlled = (r.get("elementos_controlados") or "").replace(
                "BESS (electrical_storage) x1, Carga desplazable (washing_machine) x1, ",
                "BESS+WM+",
            )
            rows.append(
                [
                    f"B{int(r['building_id']):02d}",
                    (r.get("nombre") or "")[:42],
                    r.get("ev_total", ""),
                    controlled[:55],
                    r.get("acciones_dim", ""),
                ]
            )
    return rows


def _add_impact_criteria_block(doc, p, heading, add_table) -> None:
    heading(doc, "5.1.1 Criterios de determinacion del impacto (cumplimiento completo)", 3)
    p(
        doc,
        "Para cumplir OG/OE.1–OE.3 y demostrar las hipotesis no basta un ranking descriptivo. "
        "La determinacion del impacto exige el conjunto completo de criterios C1–C5. "
        "C5 (control de recursos) es obligatorio: el efecto MADRL solo es atribuible a las "
        "acciones sobre BESS, cargadores EV/V2G y carga desplazable. Cada eje OE se reporta "
        "a nivel distrito y a nivel edificio.",
    )
    add_table(
        doc,
        ["Id", "Criterio", "Medida / prueba", "Rol", "Artefacto"],
        [list(row) for row in IMPACT_CRITERIA],
        caption=(
            "Tabla 5.1.1. Criterios completos de determinacion del impacto "
            "(C5 = control de recursos)."
        ),
        col_widths=[1.2, 3.2, 4.0, 3.5, 3.5],
    )
    p(
        doc,
        "Regla de cumplimiento sin parciales: un OE se considera documentado solo si C3+C4 "
        "(distrito y edificio del eje) y C5 (control de recursos) estan presentes junto con "
        "C1+C2 en la contrastacion HE. TOPSIS/4/4 no sustituyen C1–C5.",
    )


def _desc_oe_block(doc, p, heading, add_table, *, oe_key: str, section: str, district, report, fig_counter) -> None:
    cfg = OE_DEFINITIONS[oe_key]
    scenario = cfg["scenario"]
    rows = _rows_for_scenario(district, scenario)
    primary_kpi = cfg["primary_kpis"][0][0]
    best_algo, best_val = _best_algo_by_kpi(rows, primary_kpi, lower_better=True)
    oe_display = {"OE1": "OE.1", "OE2": "OE.2", "OE3": "OE.3"}[oe_key]

    heading(doc, f"{section} {oe_display} — resultados descriptivos estadisticos", 3)
    p(doc, PE_EXACT[oe_key])
    p(doc, OE_EXACT[oe_key])
    p(
        doc,
        f"Evidencia descriptiva en escenario {scenario} (pesos {cfg['weights']}), "
        "calculada sobre los 50 episodios Drive en outputs/. "
        "Se reportan KPIs a nivel distrito y a nivel edificio (criterios C3 y C4); "
        "no se decide hipotesis aqui.",
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
        caption=f"Tabla {section}. KPIs distritales {oe_display} en {scenario} (descriptivo).",
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
    score_rows.sort(key=lambda x: float(x[1]), reverse=True)
    add_table(
        doc,
        ["Algoritmo", f"Score {oe_key}", f"Mayor efecto {oe_key}"],
        score_rows,
        caption=f"Tabla {section}b. Ranking descriptivo {oe_display} (best_madrl_report.json).",
        col_widths=[3.0, 4.0, 4.5],
    )
    spec = OE_EPISODE_SPECS[oe_key]
    desc_rows = _descriptive_episode_rows(oe_key)
    if desc_rows:
        table_rows = []
        for row in sorted(desc_rows, key=lambda r: float(r["median"]), reverse=spec["higher_better"]):
            table_rows.append(
                [
                    row["algorithm"],
                    str(row.get("n_episodes", "-")),
                    _fmt_stat_num(row["mean"], spec["fmt"]),
                    _fmt_stat_num(row["median"], spec["fmt"]),
                    _fmt_stat_num(row["std"], spec["fmt"]),
                ]
            )
        add_table(
            doc,
            ["Algoritmo", "n ep.", "Media", "Mediana", "Desv. est."],
            table_rows,
            caption=f"Tabla {section}c. Descriptivo episodico {oe_display} ({spec['label']}).",
            col_widths=[2.2, 1.5, 2.5, 2.5, 2.5],
        )
        best_desc = _best_algo_descriptive(desc_rows, oe_key)
        p(
            doc,
            f"Lectura descriptiva {oe_display}: lider por KPI primario de distrito = {best_algo} "
            f"({cfg['primary_kpis'][0][1]} = {_fmt_kpi(str(best_val), cfg['primary_kpis'][0][2], True)}); "
            f"mejor mediana episodica = {best_desc}.",
        )
    # C3 distrito + C4 edificio (obligatorios en descriptivos, no solo en «otros»).
    if (MO_DIR / "drive_district_objectives.png").is_file() and oe_key == "OE1":
        # Figura de distrito multi-eje se ancla una vez en OE.1 y se reutiliza como referencia.
        fig_counter[0] += 1
        add_figure(
            doc,
            MO_DIR / "drive_district_objectives.png",
            f"Figura 5.{fig_counter[0]}. KPIs multiobjetivo a nivel distrito (OE.1–OE.3; criterio C3).",
            width_cm=FIG_WIDTH_LANDSCAPE,
        )
    building_fig = cfg.get("building_fig")
    if building_fig is not None and Path(building_fig).is_file():
        fig_counter[0] += 1
        add_figure(
            doc,
            Path(building_fig),
            f"Figura 5.{fig_counter[0]}. {oe_display} a nivel edificio — "
            f"{cfg['primary_kpis'][0][1]} (criterio C4).",
        )
    p(
        doc,
        f"Criterios C3/C4 en {oe_display}: el KPI primario se interpreta a nivel distrito "
        f"(Tabla {section}) y a nivel de los 17 edificios (figura precedente). "
        "El criterio C5 (control de recursos) se documenta en §5.4.5.",
    )


def _inf_oe_block(doc, p, heading, add_table, *, oe_key: str, section: str) -> None:
    oe_display = {"OE1": "OE.1", "OE2": "OE.2", "OE3": "OE.3", "ALL": "OG"}[oe_key]
    hyp = _hypothesis_row(oe_key) if oe_key in {"OE1", "OE2", "OE3"} else {}
    heading(doc, f"{section} {oe_display} — resultados inferenciales estadisticos", 3)

    sw_all = _shapiro_table_rows()
    if oe_key == "ALL":
        sw_rows = [r for r in sw_all if str(r[0]).upper().startswith("ALL") or "HG" in str(r[1])]
        if not sw_rows:
            sw_rows = [r for r in sw_all if "ALL" in str(r[0]).upper()]
    else:
        sw_rows = [
            r
            for r in sw_all
            if oe_key in str(r[0])
            or oe_display in str(r[0])
            or oe_display.replace(".", "") in str(r[0]).replace(".", "")
        ]
    if sw_rows:
        add_table(
            doc,
            ["Alcance", "Hipotesis", "Algoritmo", "p (SW)", "Normalidad rechazada"],
            sw_rows,
            caption=f"Tabla {section}a. Shapiro-Wilk {oe_display} (KPI-gains 50 ep Drive).",
            col_widths=[2.5, 1.5, 2.0, 2.5, 2.5],
        )

    if oe_key == "ALL":
        p(doc, "Contraste inferencial del OG (alimenta H0G/H1G; decision formal en §5.5.1).")
        p(
            doc,
            "Pruebas sobre la integracion multi-eje. Shapiro rechaza normalidad en ALL; "
            "ruta parametrica descartada. Se reportan Kruskal-Wallis y Friedman sobre KPI-gains.",
        )
        kw_rows = [r for r in _kruskal_table_rows() if r[0].startswith("ALL") or "HG" in r[1] or r[0] == "ALL"]
        if not kw_rows:
            kw_rows = _kruskal_table_rows()
        add_table(
            doc,
            ["Alcance", "Hipotesis", "H", "p", "Signif.", "Mejor mediana"],
            kw_rows,
            caption=f"Tabla {section}b. Kruskal-Wallis OG / ALL.",
            col_widths=[2.0, 1.5, 1.5, 1.5, 1.8, 2.7],
        )
        p(
            doc,
            "Referencia integrada (50 ep Drive): Friedman pareado p = 0,0096 (W = 0,1787); "
            "KW ALL KPI-gains p = 0,1554; KW scores globales p = 0,4044.",
        )
        return

    kw_p = float(hyp.get("KW_p_value", "nan")) if hyp else float("nan")
    h0, h1 = OE_H_PAIR[oe_key]
    p(doc, f"Contraste inferencial de {h0}/{h1} (decision formal independiente en §5.5).")
    p(
        doc,
        f"Puerta Shapiro: normalidad rechazada en {oe_display}. Ruta parametrica descartada. "
        f"Kruskal-Wallis p = {kw_p:.4f} (KPI-gains, problemas_objetivos_hipotesis/).",
    )
    all_kw = _kruskal_table_rows()
    oe_kw = [
        r
        for r in all_kw
        if oe_display.replace(".", "") in r[0].replace(".", "")
        or oe_display in r[0]
        or oe_key in str(r)
    ]
    if oe_kw:
        add_table(
            doc,
            ["Alcance", "Hipotesis", "H", "p", "Signif.", "Mejor mediana"],
            oe_kw,
            caption=f"Tabla {section}b. Kruskal-Wallis {oe_display}.",
            col_widths=[2.0, 1.5, 1.5, 1.5, 1.8, 2.7],
        )
    mwu_rows = [
        r
        for r in _mwu_table_rows()
        if oe_key in str(r[0])
        or oe_display in str(r[0])
        or oe_display.replace(".", "") in str(r[0]).replace(".", "")
    ]
    if mwu_rows:
        add_table(
            doc,
            ["Alcance", "Hipotesis", "Par", "U", "p", "Signif."],
            mwu_rows[:12],
            caption=f"Tabla {section}c. Mann-Whitney U {oe_display}.",
            col_widths=[2.0, 1.5, 3.0, 1.5, 1.5, 1.5],
        )
    wc = [
        r
        for r in _significant_wilcoxon_rows()
        if oe_key in str(r.get("scope", "")) or oe_display in str(r.get("scope", ""))
    ]
    if wc:
        rows = [
            [
                r.get("scope", ""),
                f"{r.get('algorithm_a', '')} vs {r.get('algorithm_b', '')}",
                f"{float(r.get('wilcoxon_p_value', float('nan'))):.4f}",
            ]
            for r in wc[:12]
        ]
        add_table(
            doc,
            ["Alcance", "Par", "p Wilcoxon"],
            rows,
            caption=f"Tabla {section}d. Wilcoxon {oe_display}.",
            col_widths=[3.0, 5.0, 3.0],
        )


def _otros_og_block(doc, p, heading, add_table, fig_counter) -> None:
    heading(doc, "5.4.1 OG — otros resultados (coordinacion multiobjetivo)", 3)
    p(
        doc,
        "Complementos del OG (descriptivos de soporte; no deciden H0G/H1G): ranking global Drive, "
        "best/worst por escenario, KPIs multiobjetivo de distrito y TOPSIS/AHP "
        "(estadistica descriptiva multicriterio sobre 50 ep Drive). "
        "El criterio C5 (control de recursos) se detalla en §5.4.5.",
    )
    for path, caption in (
        (FD_DIR / "comparativo_global_ranking_oe.png", "Ranking global OE.1/OE.2/OE.3 (OG)"),
        (FD_DIR / "comparativo_best_worst_por_escenario.png", "Mejor y peor MADRL por escenario"),
        (MO_DIR / "drive_district_objectives.png", "KPIs multiobjetivo a nivel distrito (C3)"),
    ):
        if path.is_file():
            fig_counter[0] += 1
            width = FIG_WIDTH_LANDSCAPE if "district" in path.name else None
            add_figure(doc, path, f"Figura 5.{fig_counter[0]}. {caption}.", width_cm=width)
    topsis = REPO / "outputs" / "madrl_multicriteria_selection" / "topsis_ranking.csv"
    if topsis.is_file():
        rows = []
        with topsis.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows.append(
                    [
                        r.get("rank", ""),
                        r.get("algorithm", ""),
                        f"{float(r.get('closeness', 0)):.4f}",
                    ]
                )
        if rows:
            add_table(
                doc,
                ["Rank", "Algoritmo", "C* TOPSIS"],
                rows,
                caption="Tabla 5.4.1. TOPSIS descriptivo (madrl_multicriteria_selection; no evidencia de HE).",
                col_widths=[2.0, 4.0, 4.0],
            )
    mc_fig_dir = REPO / "outputs" / "madrl_multicriteria_selection" / "figures"
    for fname, caption in (
        ("pareto_cost_co2_flex.png", "Multicriterio — frente de Pareto costo–CO₂–flexibilidad"),
        ("learning_curves.png", "Multicriterio — curvas de aprendizaje (50 episodios)"),
        ("degradation_bars.png", "Multicriterio — barras de degradación"),
    ):
        path = mc_fig_dir / fname
        if path.is_file():
            fig_counter[0] += 1
            add_figure(doc, path, f"Figura 5.{fig_counter[0]}. {caption}.")
    perf_dir = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "performance_comparison"
    p(
        doc,
        "Performance comparison por MADRL (distrito y edificio, 50 episodios Drive): "
        "efecto primario distrital vs baseline (4 algoritmos) y heterogeneidad de 17 edificios. "
        "Descriptivo; no decide HE.",
    )
    for algo in ("MATD3", "MAAC", "MASAC", "HAPPO"):
        path = perf_dir / f"{algo}_performance_comparison.png"
        if path.is_file():
            fig_counter[0] += 1
            add_figure(
                doc,
                path,
                f"Figura 5.{fig_counter[0]}. Performance comparison — {algo} (distrito + edificio, E1–E3).",
                width_cm=15.5,
            )


def _otros_oe_block(doc, p, heading, add_table, *, oe_key: str, section: str, fig_counter) -> None:
    cfg = OE_DEFINITIONS[oe_key]
    oe_display = {"OE1": "OE.1", "OE2": "OE.2", "OE3": "OE.3"}[oe_key]
    scenario = cfg["scenario"]
    heading(doc, f"{section} {oe_display} — otros resultados ({cfg['dimension']})", 3)
    p(
        doc,
        f"Complementos de {oe_display} en {scenario}: convergencia, KPI comparativo Drive, "
        f"desagregacion por edificio (C4) y contraste vs baseline CityLearn v2. "
        "No sustituyen §5.2–§5.3 ni §5.5. Control de recursos (C5) en §5.4.5.",
    )
    for attr, label in (
        ("conv_fig", f"Convergencia reward_mean {scenario}"),
        ("kpi_fig", f"KPI comparativo {oe_display}"),
        ("building_fig", f"Objetivo por edificio {oe_display} (C4)"),
        ("trace_fig", f"Traza de control de recursos {scenario} (C5)"),
    ):
        path = cfg.get(attr)
        if path is not None and Path(path).is_file():
            fig_counter[0] += 1
            add_figure(doc, Path(path), f"Figura 5.{fig_counter[0]}. {label}.")
    heatmap = BL_DIR / scenario / "baseline_gain_heatmap.png"
    if heatmap.is_file():
        fig_counter[0] += 1
        add_figure(
            doc,
            heatmap,
            f"Figura 5.{fig_counter[0]}. Ganancia vs baseline CityLearn v2 — {scenario} ({oe_display}).",
            width_cm=FIG_WIDTH_HEATMAP,
        )


def _control_recursos_block(doc, p, heading, add_table, fig_counter) -> None:
    heading(doc, "5.4.5 Control de recursos (criterio C5 de impacto)", 3)
    p(
        doc,
        "Criterio obligatorio de determinacion del impacto: el efecto MADRL sobre OE.1–OE.3 "
        "solo es atribuible si los agentes controlan recursos energeticos (DER). "
        "Recursos controlados: BESS (electrical_storage), cargadores EV/V2G y carga desplazable "
        "(washing_machine). Recursos no controlados: non_shiftable_load, refrigeracion/ACS "
        "modeladas y generacion FV fija. Inventario: 17 edificios, 185 cargadores EV.",
    )
    inv = _inventory_rows()
    if inv:
        add_table(
            doc,
            ["Edif.", "Nombre", "EV", "Elementos controlados", "Acciones"],
            inv,
            caption=(
                "Tabla 5.4.5. Inventario de control de recursos por edificio "
                "(building_inventory_multiobjective.csv)."
            ),
            col_widths=[1.3, 4.5, 1.2, 5.5, 1.8],
        )
    for path, caption in (
        (
            MO_DIR / "drive_building_ev_inventory.png",
            "Inventario EV por edificio (control de recursos C5)",
        ),
        (
            MO_DIR / "drive_building_ev_success_matd3_e2.png",
            "Exito de salida EV — MATD3/E2 (control de recursos C5)",
        ),
    ):
        if path.is_file():
            fig_counter[0] += 1
            add_figure(doc, path, f"Figura 5.{fig_counter[0]}. {caption}.")
    p(
        doc,
        "Desagregacion completa por edificio de los tres ejes (OE.1 flexibilidad, OE.2 CO2, "
        "OE.3 costo) en las 17 tarjetas siguientes. Cumple C4+C5 de forma conjunta.",
    )
    por_edificio = MO_DIR / "por_edificio"
    if por_edificio.is_dir():
        for i in range(1, 18):
            path = por_edificio / f"drive_building_B{i:02d}_objectives.png"
            if path.is_file():
                fig_counter[0] += 1
                add_figure(
                    doc,
                    path,
                    f"Figura 5.{fig_counter[0]}. Edificio B{i:02d} — objetivos OE.1/OE.2/OE.3 "
                    "(distrito→edificio; C4+C5).",
                )
    p(
        doc,
        "Veredicto C5: el control de recursos esta documentado a nivel distrito (trazas E1–E3) "
        "y a nivel edificio (inventario BESS/EV/carga flexible + 17 tarjetas multiobjetivo). "
        "Sin C5 no se declara cumplimiento completo de OG/OE ni demostracion de HE.",
    )


def _hyp_general_block(doc, p, heading, add_table) -> None:
    heading(doc, "5.5.1 Hipotesis general (H0G / H1G)", 3)
    p(doc, "Formulacion nula (texto exacto Cap. 1):")
    p(doc, H_EXACT["H0G"])
    p(doc, "Formulacion alternativa (texto exacto Cap. 1):")
    p(doc, H_EXACT["H1G"])
    add_table(
        doc,
        ["Hipotesis", "Decision", "Fundamento (KPI-gains 50 ep Drive)"],
        [
            [
                "H0G",
                "Se rechaza de forma exploratoria",
                "Friedman integracion p = 0,0096 + impacto GLOBAL vs baseline (Holm)",
            ],
            [
                "H1G",
                "Se respalda de forma exploratoria (sin ganador unico; impacto agregado desfavorable)",
                "No implica HE11∧HE21∧HE31; trade-off MATD3/MAAC",
            ],
        ],
        caption="Tabla 5.5.1. Contrastacion independiente de la hipotesis general.",
        col_widths=[2.0, 5.0, 6.0],
    )


def _hyp_oe_block(doc, p, heading, add_table, *, oe_key: str, section: str) -> None:
    h0, h1 = OE_H_PAIR[oe_key]
    oe_display = {"OE1": "OE.1", "OE2": "OE.2", "OE3": "OE.3"}[oe_key]
    decisions = {
        "OE1": (
            ("HE10", "No se rechaza", "KW p = 0,4685"),
            ("HE11", "No se respalda", "Sin conjuncion impacto+diferencias en E1 (KPI-gains)"),
        ),
        "OE2": (
            ("HE20", "No se rechaza", "KW p = 0,7648"),
            (
                "HE21",
                "No se respalda",
                "Sin impacto vs cero tras Holm; Friedman marginal; 0/15 KPI mejorados",
            ),
        ),
        "OE3": (
            ("HE30", "No se rechaza", "KW p = 0,7357"),
            (
                "HE31",
                "No se respalda",
                "MAAC gana costos/TOPSIS/4/4 descriptivo; KPI-gains E3 sin omnibus ni impacto vs cero tras Holm",
            ),
        ),
    }
    heading(doc, f"{section} Hipotesis especificas {oe_display} ({h0} / {h1})", 3)
    p(doc, "Formulacion nula (texto exacto Cap. 1):")
    p(doc, H_EXACT[h0])
    p(doc, "Formulacion alternativa (texto exacto Cap. 1):")
    p(doc, H_EXACT[h1])
    add_table(
        doc,
        ["Hipotesis", "Decision", "Fundamento (KPI-gains 50 ep Drive)"],
        [list(row) for row in decisions[oe_key]],
        caption=f"Tabla {section}. Contrastacion independiente {oe_display}.",
        col_widths=[2.0, 5.0, 6.0],
    )


def add_chapter_5_structured(doc, p, heading, add_table, status_note) -> None:
    """Cap. 5: descriptivos → inferenciales → otros → hipotesis → discusion (OG/OE independientes)."""
    try:
        write_pe_answers_audit()
    except OSError:
        pass
    report = _read_json(BEST_REPORT)
    district = _read_csv(DISTRICT_CSV)
    fig_counter = [0]

    heading(doc, "Capitulo 5. Resultados, contrastacion de hipotesis y discusion", 1)
    p(
        doc,
        f"Este capitulo presenta la evidencia de la corrida canonica ({RUN_ID}) en cumplimiento "
        "de los objetivos, con cinco acapites: (5.2) resultados descriptivos estadisticos "
        "del OG y OE.1–OE.3 de forma independiente; (5.3) resultados inferenciales estadisticos "
        "del OG y OE.1–OE.3 de forma independiente; (5.4) otros resultados del OG y OE.1–OE.3 "
        "de forma independiente; (5.5) contrastacion de hipotesis (H0G/H1G y HE nulas/alternativas "
        "por objetivo); (5.6) discusion de resultados. El marco experimental (§5.1) precede.",
    )

    heading(doc, "5.0 Mapa de lectura del capitulo", 2)
    add_table(
        doc,
        ["Numeral", "Bloque", "Contenido (independiente por objetivo)"],
        [
            ["5.1", "Marco", "Cobertura experimental 4x3 y operacionalizacion OE/OG"],
            ["5.2", "Descriptivos", "5.2.1 OG; 5.2.2 OE.1; 5.2.3 OE.2; 5.2.4 OE.3"],
            ["5.3", "Inferenciales", "5.3.1 OG; 5.3.2 OE.1; 5.3.3 OE.2; 5.3.4 OE.3"],
            ["5.4", "Otros resultados", "5.4.1 OG; 5.4.2 OE.1; 5.4.3 OE.2; 5.4.4 OE.3; 5.4.5 Control de recursos (C5)"],
            [
                "5.5",
                "Contrastacion de hipotesis",
                "5.5.1 H0G/H1G; 5.5.2 HE10/HE11; 5.5.3 HE20/HE21; 5.5.4 HE30/HE31; 5.5.5 Cumplimiento C1–C5",
            ],
            ["5.6", "Discusion", "Interpretacion integrada y limitaciones"],
        ],
        caption="Tabla 5.0. Estructura del Capitulo 5 por numerales y objetivos.",
        col_widths=[2.0, 3.5, 9.5],
    )
    p(
        doc,
        "Cadena vertical Cap. 1 → Cap. 5: PG ↔ OG ↔ H0G/H1G; "
        "PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); "
        "PE.3 ↔ OE.3 ↔ HE30/HE31 (E3). Formulaciones exactas del autor; no parafrasear. "
        "Fuente unica: resultados guardados de 50 episodios Drive en outputs/. "
        "Determinacion del impacto = criterios C1–C5 (§5.1.1), con C5 = control de recursos; "
        "cada eje a nivel distrito y edificio. "
        "TOPSIS y ranking evaluate_v2 4/4 = estadistica descriptiva; "
        "HE11/HE21/HE31 = KPI-gains (impacto significativo y diferencias) + C3–C5.",
    )

    heading(doc, "5.1 Marco experimental y cobertura", 2)
    add_table(
        doc,
        ["Objetivo", "Escenario", "VD", "KPI principal", "Pesos"],
        [
            ["OE.1 Flexibilidad", "E1", "D-VD.1", "flex_composite / KPI-gains", "[0,70; 0,15; 0,15]"],
            ["OE.2 Emisiones CO2", "E2", "D-VD.2", "carbon_emissions_delta", "[0,15; 0,70; 0,15]"],
            ["OE.3 Costos", "E3", "D-VD.3", "electricity_cost_delta", "[0,25; 0,15; 0,60]"],
            ["OG Coordinacion", "E1–E3", "Multiobjetivo", "best_madrl + integracion", "—"],
        ],
        caption="Tabla 5.1. Operacionalizacion OG/OE → escenario → KPI.",
        col_widths=[3.2, 1.8, 1.8, 4.5, 3.5],
    )
    add_table(
        doc,
        ["Algoritmo", "E1", "E2", "E3", "KPIs finales", "Uso"],
        [
            ["MATD3", "50", "50", "50", "Si", "Descriptivo + inferencial canonico"],
            ["MAAC", "50", "50", "50", "Si", "Descriptivo + inferencial canonico"],
            ["MASAC", "50", "50", "50", "Si", "Descriptivo + inferencial canonico"],
            ["HAPPO", "49", "49", "49", "Si (Drive 2026-07-28)", "Descriptivo 4/4; HE canonica 3x3"],
        ],
        caption="Tabla 5.2. Cobertura de episodios y KPIs finales.",
        col_widths=[2.2, 1.5, 1.5, 1.5, 3.5, 4.5],
    )
    _add_impact_criteria_block(doc, p, heading, add_table)

    # --- 5.2 DESCRIPTIVOS (independientes) ---
    heading(doc, "5.2 Resultados descriptivos estadisticos", 2)
    p(
        doc,
        "Primer acapite de resultados en cumplimiento de los objetivos. "
        "Estadistica descriptiva sobre los 50 episodios Drive en outputs/, "
        "con subacapites independientes para OG, OE.1, OE.2 y OE.3. "
        "Cada OE documenta C3 (distrito) y C4 (edificio). "
        "TOPSIS y evaluate_v2 4/4 son descriptivos; no deciden HE.",
    )

    heading(doc, "5.2.1 OG — resultados descriptivos estadisticos", 3)
    p(doc, f"PG (referencia). {PG_EXACT}")
    p(doc, OG_EXACT)
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
        caption="Tabla 5.2.1. Ranking descriptivo integrado (best_madrl_report.json, canonico 3x3).",
        col_widths=[1.5, 2.5, 2.2, 2.0, 2.0, 2.0],
    )
    p(
        doc,
        "Lectura descriptiva del OG / PG: MATD3 obtiene el mejor score global (0,6667) al liderar "
        "OE.1 y OE.2; MAAC lidera OE.3. No hay dominador Pareto unico. "
        "El ranking evaluate_v2 4/4 (incluye HAPPO) confirma a HAPPO en ultimo lugar (score 0). "
        "El cumplimiento completo del OG exige ademas C1–C5 (§5.1.1), con control de recursos en §5.4.5.",
    )

    _desc_oe_block(
        doc, p, heading, add_table,
        oe_key="OE1", section="5.2.2", district=district, report=report, fig_counter=fig_counter,
    )
    _desc_oe_block(
        doc, p, heading, add_table,
        oe_key="OE2", section="5.2.3", district=district, report=report, fig_counter=fig_counter,
    )
    _desc_oe_block(
        doc, p, heading, add_table,
        oe_key="OE3", section="5.2.4", district=district, report=report, fig_counter=fig_counter,
    )

    # --- 5.3 INFERENCIALES (independientes) ---
    heading(doc, "5.3 Resultados inferenciales estadisticos", 2)
    p(
        doc,
        "Segundo acapite. Pruebas sobre KPI-gains de los 50 episodios Drive "
        f"(outputs/{RUN_ID}/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/), "
        "alpha = 0,05. Subacapites independientes OG, OE.1, OE.2 y OE.3. "
        "No usa TOPSIS ni ranking 4/4 como prueba de hipotesis. Decision formal en §5.5.",
    )
    _inf_oe_block(doc, p, heading, add_table, oe_key="ALL", section="5.3.1")
    _inf_oe_block(doc, p, heading, add_table, oe_key="OE1", section="5.3.2")
    _inf_oe_block(doc, p, heading, add_table, oe_key="OE2", section="5.3.3")
    _inf_oe_block(doc, p, heading, add_table, oe_key="OE3", section="5.3.4")

    # --- 5.4 OTROS (independientes) ---
    heading(doc, "5.4 Otros resultados", 2)
    p(
        doc,
        "Tercer acapite. Resultados complementarios por objetivo (OG, OE.1, OE.2, OE.3) "
        "de forma independiente: convergencia, multiobjetivo distrito/edificio, baseline v2, "
        "TOPSIS descriptivo y control de recursos (C5). "
        "No sustituyen §5.2–§5.3 ni §5.5.",
    )
    _otros_og_block(doc, p, heading, add_table, fig_counter)
    _otros_oe_block(doc, p, heading, add_table, oe_key="OE1", section="5.4.2", fig_counter=fig_counter)
    _otros_oe_block(doc, p, heading, add_table, oe_key="OE2", section="5.4.3", fig_counter=fig_counter)
    _otros_oe_block(doc, p, heading, add_table, oe_key="OE3", section="5.4.4", fig_counter=fig_counter)
    _control_recursos_block(doc, p, heading, add_table, fig_counter)

    # --- 5.5 HIPOTESIS (independientes) ---
    heading(doc, "5.5 Contrastacion de hipotesis", 2)
    p(
        doc,
        "Cuarto acapite. Contrastacion formal H0/H1 con textos exactos del Cap. 1. "
        "Primero la hipotesis general (nula y alternativa); luego las hipotesis especificas "
        "nulas y alternativas de forma independiente por objetivo (OE.1, OE.2, OE.3). "
        "Unidad de decision = KPI-gains de 50 ep Drive. "
        "La demostracion exige C1–C5 (§5.1.1), incluido control de recursos.",
    )
    p(
        doc,
        "Protocolo: (1) Shapiro-Wilk; si se rechaza normalidad, solo no parametrico; "
        "(2) omnibus KW/Friedman + post hoc Holm (C1–C2); "
        "(3) HE alternativas requieren impacto significativo y diferencias entre algoritmos; "
        "(4) evidencia C3–C5 (distrito, edificio, control de recursos) documenta atribuibilidad; "
        "(5) TOPSIS/4/4/best_madrl son descriptivos y no respaldan HE por si solos.",
    )
    _hyp_general_block(doc, p, heading, add_table)
    _hyp_oe_block(doc, p, heading, add_table, oe_key="OE1", section="5.5.2")
    _hyp_oe_block(doc, p, heading, add_table, oe_key="OE2", section="5.5.3")
    _hyp_oe_block(doc, p, heading, add_table, oe_key="OE3", section="5.5.4")

    heading(doc, "5.5.5 Cumplimiento OG y OE.1–OE.3", 3)
    verdict_rows = _verdict_table_rows(report)
    add_table(
        doc,
        ["Objetivo", "VD / Esc.", "Mayor efecto (VI)", "Evidencia KPI", "Cumplimiento"],
        verdict_rows,
        caption="Tabla 5.5.5. Veredicto de cumplimiento OG y OE.1–OE.3.",
        col_widths=[1.5, 2.2, 2.0, 4.5, 4.8],
    )
    p(doc, _og_oe_verdict_text())
    add_table(
        doc,
        ["Criterio", "Distrito", "Edificio", "Integrado en Cap. 5", "Estado"],
        [
            ["C1 Impacto vs baseline", "Si (KPI-gains)", "Via KPIs agregados", "§5.3 / §5.5", "Documentado"],
            ["C2 Diferencias entre algoritmos", "Si (KW/Friedman)", "N/A (unidad KPI-gains)", "§5.3 / §5.5", "Documentado"],
            ["C3 KPIs fisicos por eje", "Si (tablas+fig)", "—", "§5.2 / §5.4.1", "Documentado"],
            ["C4 KPIs por edificio × eje", "—", "Si (17 edif. × 3 ejes)", "§5.2 / §5.4.2–5.4.5", "Documentado"],
            ["C5 Control de recursos", "Trazas E1–E3", "BESS/EV/carga + inventario", "§5.4.5", "Documentado"],
        ],
        caption=(
            "Tabla 5.5.5b. Cumplimiento completo de criterios de impacto "
            "(sin parciales; C5 = control de recursos)."
        ),
        col_widths=[3.5, 3.0, 4.0, 3.0, 2.0],
    )
    p(
        doc,
        "Cumplimiento documental completo: C1–C5 estan presentes a nivel distrito y edificio "
        "para OE.1–OE.3. El veredicto estadistico de HE (aceptacion/rechazo) permanece el de "
        "§5.5.1–5.5.4; C3–C5 no sustituyen C1–C2, pero sin ellos el impacto no se declara "
        "atribuible ni el cumplimiento de objetivos se considera completo.",
    )

    # --- 5.6 DISCUSION ---
    heading(doc, "5.6 Discusion de resultados", 2)
    p(
        doc,
        "Quinto y ultimo acapite del capitulo. "
        "1) Separacion de planos: §5.2 descriptivo por OG/OE; §5.3 inferencial por OG/OE; "
        "§5.4 otros por OG/OE; §5.5 contrastacion H0G/H1G y HE por objetivo; §5.6 discusion. "
        "2) No normalidad → solo no parametrico. "
        "3) Trade-off: MATD3 flex+CO2; MAAC costos/TOPSIS/4/4 (descriptivo). "
        "4) H1G exploratoria no equivale a HE11/HE21/HE31. "
        "5) TOPSIS/4/4 = descriptivo de 50 ep Drive; HE = KPI-gains (impacto + diferencias). "
        "6) Limitaciones: semilla = 0; HAPPO 49/50 ep; n KPI 12/5/9.",
    )
    heading(doc, "5.6.1 Contrastacion con antecedentes", 3)
    p(
        doc,
        f"La discusion se ancla a los antecedentes del Capitulo 2 "
        f"({len(ANTECEDENTES_NACIONALES)} antecedentes nacionales/peruanos).",
    )
    for paragraph in _antecedents_discussion_text():
        p(doc, paragraph)
    status_note(
        doc,
        "Capitulo 5 (2026-07-29): cumplimiento de objetivos con acapites "
        "descriptivos → inferenciales → otros → contrastacion de hipotesis → discusion; "
        "OG/OE.1/OE.2/OE.3 independientes en cada bloque.",
    )
