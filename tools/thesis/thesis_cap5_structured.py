"""Capitulo 5 reestructurado por objetivos: 5.1 marco; 5.2 OE.1; 5.3 OE.2; 5.4 OE.3;
5.5 OG; 5.6 contrastacion consolidada; 5.7 discusion. Inferencia canónica = Capa A
(problemas_objetivos_hipotesis/); Friedman principal; KW/MWU exploratorio.
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
        "Friedman + Kendall W + Wilcoxon/Holm (principal); KW/MWU exploratorio",
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
        sw_rows = [
            r
            for r in sw_all
            if "GLOBAL" in str(r[0]).upper()
            or str(r[0]).upper().startswith("ALL")
            or "HG" in str(r[1])
        ]
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
            caption=f"Tabla {section}a. Shapiro-Wilk {oe_display} (KPI-gains Capa A).",
            col_widths=[2.5, 1.5, 2.0, 2.5, 2.5],
        )

    if oe_key == "ALL":
        p(doc, "Contraste inferencial del OG (alimenta H0G/H1G; decision formal en §5.5 / §5.6).")
        p(
            doc,
            "Pruebas sobre la integracion multi-eje (Capa A). Shapiro rechaza normalidad en GLOBAL; "
            "ruta parametrica descartada. Prueba global principal = Friedman pareado; "
            "Kruskal-Wallis solo exploratorio.",
        )
        kw_rows = [
            r
            for r in _kruskal_table_rows()
            if "GLOBAL" in str(r[0]).upper() or "HG" in str(r[1]) or "ALL" in str(r[0]).upper()
        ]
        if not kw_rows:
            kw_rows = _kruskal_table_rows()
        add_table(
            doc,
            ["Alcance", "Hipotesis", "Friedman χ²", "p", "Signif.", "KW exploratorio"],
            kw_rows,
            caption=f"Tabla {section}b. Omnibus OG / GLOBAL (Friedman principal).",
            col_widths=[2.0, 1.5, 2.0, 1.5, 1.5, 3.5],
        )
        p(
            doc,
            "Referencia integrada (50 ep Drive, problemas_objetivos_hipotesis/): Friedman pareado "
            "χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; KW GLOBAL exploratorio H = 1,8108, "
            "p = 0,4044. No citar KW ALL p = 0,1554 (Capa B poolada) como decision HG/HE.",
        )
        return

    h0, h1 = OE_H_PAIR[oe_key]
    p(doc, f"Contraste inferencial de {h0}/{h1} (decision formal en el mismo objetivo / §5.6).")
    p(
        doc,
        f"Puerta Shapiro: normalidad rechazada en {oe_display}. Ruta parametrica descartada. "
        "Prueba global principal = Friedman pareado + Kendall W; KW/MWU = exploratorio "
        "(problemas_objetivos_hipotesis/).",
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
            ["Alcance", "Hipotesis", "Friedman χ²", "p", "Signif.", "KW exploratorio"],
            oe_kw,
            caption=f"Tabla {section}b. Omnibus {oe_display} (Friedman principal).",
            col_widths=[2.0, 1.5, 2.0, 1.5, 1.5, 3.5],
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
            caption=f"Tabla {section}c. Mann-Whitney U exploratorio {oe_display}.",
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


# Valores exactos desde problemas_objetivos_hipotesis/ (no mezclar con analisis_estadistico_madrl.csv).
STATS_EXACT_BLOCK = [
    "[[STATS_EXACTAS_KPI_GAINS_50EP]]",
    (
        "Síntesis de pruebas estadísticas con valores exactos (KPI-gains, 50 episodios Drive, "
        "carpeta problemas_objetivos_hipotesis/; α = 0,05; MAAC, MASAC y MATD3; HAPPO sin "
        "KPI-gains finales comparables). Los números siguientes son la referencia obligatoria "
        "para HG/HE1–HE3."
    ),
    (
        "Shapiro–Wilk (W y p) por objetivo. OE.1/E1: MAAC W = 0,7152, p = 0,001184; "
        "MASAC W = 0,5997, p = 1,066e-04; MATD3 W = 0,7160, p = 0,001208. "
        "OE.2/E2: MAAC W = 0,6993, p = 0,009419; MASAC W = 0,6999, p = 0,009548; "
        "MATD3 W = 0,7012, p = 0,009848. "
        "OE.3/E3: MAAC W = 0,5575, p = 3,029e-05; MASAC W = 0,5879, p = 6,905e-05; "
        "MATD3 W = 0,5464, p = 2,246e-05. "
        "GLOBAL: MAAC W = 0,6772, p = 2,628e-06; MASAC W = 0,6011, p = 3,047e-07; "
        "MATD3 W = 0,6734, p = 2,343e-06. Normalidad rechazada en todos los grupos calculables."
    ),
    (
        "Kruskal–Wallis exploratorio (H y p; no prueba principal HE). OE.1: H = 1,5164, p = 0,4685; "
        "OE.2: H = 0,5364, p = 0,7648; OE.3: H = 0,6138, p = 0,7357; GLOBAL: H = 1,8108, p = 0,4044."
    ),
    (
        "Friedman principal (χ², p) y Kendall's W. OE.1: χ² = 5,5897, p = 0,0611, W = 0,2329; "
        "OE.2: χ² = 6,0000, p = 0,0498, W = 0,6000; OE.3: χ² = 3,4286, p = 0,1801, W = 0,1905; "
        "GLOBAL: χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787."
    ),
    (
        "Mann–Whitney U exploratorio (U, p-Holm, Cliff's δ). OE.1: MAAC–MASAC U = 89,0, p-Holm = 0,8498, δ = 0,2361; "
        "MAAC–MATD3 U = 67,5, p-Holm = 0,8498, δ = −0,0625; MASAC–MATD3 U = 53,0, p-Holm = 0,8498, "
        "δ = −0,2639. OE.2: U ∈ {15,0; 10,0; 10,0}, p-Holm = 1,0000. OE.3: U ∈ {49,0; 44,0; 35,0}, "
        "p-Holm = 1,0000. GLOBAL: MAAC–MASAC U = 393,0, p-Holm = 0,6294, δ = 0,1627; "
        "MAAC–MATD3 U = 325,5, p-Holm = 0,8251, δ = −0,0370; MASAC–MATD3 U = 269,0, "
        "p-Holm = 0,6191, δ = −0,2041. Ningún par significativo tras Holm."
    ),
    (
        "Wilcoxon signed-rank pareado (W, p-Holm). OE.1: W ∈ {7,0; 17,0; 14,0}, p-Holm ∈ {0,1100; 0,5143; 0,3376}. "
        "OE.2: W = 0,0, p-Holm = 0,3074 (tres pares). OE.3: W ∈ {6,0; 13,0; 11,0}, "
        "p-Holm ∈ {0,5266; 1,0000; 1,0000}. GLOBAL: MAAC–MASAC W = 31,0, p-Holm = 0,0172 "
        "(único significativo); MAAC–MATD3 W = 69,0, p-Holm = 0,2953; MASAC–MATD3 W = 54,0, "
        "p-Holm = 0,1137."
    ),
    (
        "Decisión HG/HE1/HE2/HE3. HG (H0G/H1G): se rechaza H0G y se respalda H1G "
        "(Friedman p = 0,0096; Kendall's W = 0,1787), sin ganador único. "
        "HE1 (HE10/HE11): no se rechaza HE10; no se respalda HE11. "
        "HE2 (HE20/HE21): no se rechaza HE20; no se respalda HE21. "
        "HE3 (HE30/HE31): no se rechaza HE30; no se respalda HE31. "
        "TOPSIS C* MAAC = 0,9827 (descriptivo; no sustituye HE). "
        "Limitación metodológica (aparte del veredicto): semilla única seed = 0."
    ),
]


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
                "Se rechaza",
                "Friedman χ² = 9,2911, p = 0,0096, Kendall's W = 0,1787; impacto GLOBAL vs baseline "
                "Holm (MAAC/MASAC/MATD3); KW GLOBAL H = 1,8108, p = 0,4044",
            ],
            [
                "H1G",
                "Se respalda (sin ganador unico; impacto agregado desfavorable)",
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
            (
                "HE10",
                "No se rechaza",
                "Friedman χ² = 5,5897, p = 0,0611, Kendall's W = 0,2329 (principal); "
                "KW exploratorio H = 1,5164, p = 0,4685; MWU/Wilcoxon pares n.s. tras Holm",
            ),
            ("HE11", "No se respalda", "Sin conjuncion impacto+diferencias en E1 (KPI-gains)"),
        ),
        "OE2": (
            (
                "HE20",
                "No se rechaza",
                "Friedman χ² = 6,0000, p = 0,0498, Kendall's W = 0,6000 (principal) sin impacto "
                "vs cero tras Holm ni post hoc; KW exploratorio H = 0,5364, p = 0,7648",
            ),
            (
                "HE21",
                "No se respalda",
                "Sin impacto vs cero tras Holm; Friedman marginal; post hoc n.s.; 0/5 KPI mejorados",
            ),
        ),
        "OE3": (
            (
                "HE30",
                "No se rechaza",
                "Friedman χ² = 3,4286, p = 0,1801, Kendall's W = 0,1905 (principal); "
                "KW exploratorio H = 0,6138, p = 0,7357; sin impacto vs cero tras Holm",
            ),
            (
                "HE31",
                "No se respalda",
                "MAAC gana costos/TOPSIS C*=0,9827/4/4 descriptivo; KPI-gains E3 sin omnibus "
                "ni impacto vs cero tras Holm",
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
    """Cap. 5 por objetivos: 5.1 marco; 5.2–5.4 OE; 5.5 OG; 5.6 hipotesis; 5.7 discusion."""
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
        f"Este capitulo determina el efecto de HAPPO, MASAC, MATD3 y MAAC e identifica el "
        f"algoritmo de mejor desempeno para el OG y OE.1–OE.3 sobre la corrida canonica "
        f"({RUN_ID}). Estructura por objetivos: §5.1 marco y C1–C5; §5.2 OE.1; §5.3 OE.2; "
        "§5.4 OE.3; §5.5 OG (Pareto/TOPSIS complementario); §5.6 contrastacion consolidada "
        "HG/HE; §5.7 discusion y auditoria de coherencia. Inferencia canónica = Capa A "
        "(problemas_objetivos_hipotesis/); Friedman principal; KW/MWU exploratorio. "
        "No se confunde mejor desempeno descriptivo con superioridad estadisticamente "
        "significativa. Resumen/Abstract/Cap. VI se alinean en fase posterior.",
    )

    heading(doc, "5.0 Mapa de lectura del capitulo", 2)
    add_table(
        doc,
        ["Numeral", "Bloque", "Contenido"],
        [
            ["5.1", "Marco", "Diseno 4x3, C1–C5, artefactos canonicos, semilla unica"],
            ["5.2", "OE.1 Flexibilidad", "Descriptivo + Shapiro + C1–C5 + HE10/HE11"],
            ["5.3", "OE.2 Emisiones CO2", "Misma secuencia + HE20/HE21"],
            ["5.4", "OE.3 Costos", "Misma secuencia + HE30/HE31"],
            ["5.5", "OG Integrado", "Trade-offs, Pareto, TOPSIS C*=0,9827, H0G/H1G"],
            ["5.6", "Contrastacion", "Tabla consolidada HG/HE"],
            ["5.7", "Discusion", "Literatura + auditoria PG–OE–HE"],
        ],
        caption="Tabla 5.0. Estructura del Capitulo 5 por objetivos.",
        col_widths=[2.0, 3.5, 9.5],
    )
    p(
        doc,
        "Cadena vertical Cap. 1 → Cap. 5: PG ↔ OG ↔ H0G/H1G; "
        "PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); "
        "PE.3 ↔ OE.3 ↔ HE30/HE31 (E3). Fuente unica HE: KPI-gains Capa A. "
        "TOPSIS y evaluate_v2 4/4 = descriptivos. HAPPO excluido de HE "
        "(sin KPI-gains finales comparables). Episodios de una corrida no son "
        "replicas experimentales independientes.",
    )

    heading(doc, "5.1 Marco experimental y criterios de determinacion del efecto", 2)
    add_table(
        doc,
        ["Objetivo", "Escenario", "VD", "KPI principal", "Pesos"],
        [
            ["OE.1 Flexibilidad", "E1", "D-VD.1", "flex_composite / KPI-gains (n=12)", "[0,70; 0,15; 0,15]"],
            ["OE.2 Emisiones CO2", "E2", "D-VD.2", "carbon_emissions_delta / gains (n=5)", "[0,15; 0,70; 0,15]"],
            ["OE.3 Costos", "E3", "D-VD.3", "electricity_cost_delta / gains (n=9)", "[0,25; 0,15; 0,60]"],
            ["OG Coordinacion", "E1–E3", "Multiobjetivo", "best_madrl + GLOBAL (n=26)", "—"],
        ],
        caption="Tabla 5.1. Operacionalizacion OG/OE → escenario → KPI.",
        col_widths=[3.2, 1.8, 1.8, 4.5, 3.5],
    )
    add_table(
        doc,
        ["Algoritmo", "E1", "E2", "E3", "KPI-gains finales", "Uso"],
        [
            ["MATD3", "50", "50", "50", "Si", "Descriptivo + inferencial canonico"],
            ["MAAC", "50", "50", "50", "Si", "Descriptivo + inferencial canonico"],
            ["MASAC", "50", "50", "50", "Si", "Descriptivo + inferencial canonico"],
            ["HAPPO", "49", "49", "49", "No comparables", "Solo descriptivo 4/4; excluido de HE"],
        ],
        caption="Tabla 5.2. Cobertura de episodios y uso inferencial (seed = 0).",
        col_widths=[2.2, 1.5, 1.5, 1.5, 3.5, 4.5],
    )
    p(
        doc,
        "Unidad de observacion HE: KPI-gain orientado por KPI (escenario filtrado). "
        "Unidad experimental: tratamiento algoritmo x escenario, seed = 0. "
        "Baseline: CityLearn v2. alpha = 0,05. Capas B (poolada), C (episodica) y D "
        "(primary/building) no sustituyen la Capa A para HE "
        "(docs/AUDITORIA_CAP5_CONTRADICCIONES_STATS_2026-08-06.md).",
    )
    _add_impact_criteria_block(doc, p, heading, add_table)

    # --- 5.2 OE.1 ---
    heading(doc, "5.2 OE.1 — Efecto sobre la flexibilidad energetica", 2)
    _desc_oe_block(
        doc, p, heading, add_table,
        oe_key="OE1", section="5.2.1", district=district, report=report, fig_counter=fig_counter,
    )
    _inf_oe_block(doc, p, heading, add_table, oe_key="OE1", section="5.2.2")
    _hyp_oe_block(doc, p, heading, add_table, oe_key="OE1", section="5.2.3")
    p(
        doc,
        "Respuesta OE.1: mejor desempeno descriptivo = MAAC (mediana KPI-gain) / MATD3 "
        "(flex_composite distrito). Nivel de evidencia: descriptivo; HE10 no se rechaza; "
        "HE11 no se respalda (sin superioridad estadistica conjunta).",
    )

    # --- 5.3 OE.2 ---
    heading(doc, "5.3 OE.2 — Efecto sobre las emisiones de CO2", 2)
    _desc_oe_block(
        doc, p, heading, add_table,
        oe_key="OE2", section="5.3.1", district=district, report=report, fig_counter=fig_counter,
    )
    _inf_oe_block(doc, p, heading, add_table, oe_key="OE2", section="5.3.2")
    _hyp_oe_block(doc, p, heading, add_table, oe_key="OE2", section="5.3.3")
    p(
        doc,
        "Respuesta OE.2: mejor MADRL descriptivo = MATD3 (mediana gain, Delta CO2, score OE2). "
        "Friedman p = 0,0498 es senal pareada debil; sin impacto vs cero ni post hoc Holm "
        "no habilita HE21. HE20 no se rechaza; HE21 no se respalda.",
    )

    # --- 5.4 OE.3 ---
    heading(doc, "5.4 OE.3 — Efecto sobre los costos energeticos", 2)
    _desc_oe_block(
        doc, p, heading, add_table,
        oe_key="OE3", section="5.4.1", district=district, report=report, fig_counter=fig_counter,
    )
    _inf_oe_block(doc, p, heading, add_table, oe_key="OE3", section="5.4.2")
    _hyp_oe_block(doc, p, heading, add_table, oe_key="OE3", section="5.4.3")
    p(
        doc,
        "Respuesta OE.3: mejor MADRL descriptivo = MAAC (KPI-gain, Delta costo, score 4/4, "
        "TOPSIS C* = 0,9827). Ventaja descriptiva sin omnibus ni impacto Holm. "
        "HE30 no se rechaza; HE31 no se respalda.",
    )

    # --- 5.5 OG ---
    heading(doc, "5.5 OG — Efecto integrado y mejor desempeno global", 2)
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
        caption="Tabla 5.5. Ranking descriptivo best_madrl 3x3 (MATD3 = 0,6667).",
        col_widths=[1.5, 2.5, 2.2, 2.0, 2.0, 2.0],
    )
    p(
        doc,
        "Trade-off: MATD3 lidera flex fisica y CO2; MAAC lidera costos, evaluate_v2 4/4 "
        "(score 0,9538) y TOPSIS (C* = 0,9827). Frente de Pareto = {MAAC, MASAC, MATD3}. "
        "TOPSIS es herramienta multicriterio complementaria y no sustituye la contrastacion "
        "estadistica. Sin dominador Pareto unico ni superioridad estadistica global de un "
        "unico MADRL.",
    )
    _inf_oe_block(doc, p, heading, add_table, oe_key="ALL", section="5.5.1")
    _hyp_general_block(doc, p, heading, add_table)
    _otros_og_block(doc, p, heading, add_table, fig_counter)
    _control_recursos_block(doc, p, heading, add_table, fig_counter)

    # --- 5.6 Contrastacion consolidada ---
    heading(doc, "5.6 Contrastacion consolidada de hipotesis", 2)
    p(
        doc,
        "Tabla consolidada HG/HE desde problemas_objetivos_hipotesis/ (Capa A). "
        "Se usa «se rechaza / no se rechaza H0»; no se utiliza «se acepta H0».",
    )
    for line in STATS_EXACT_BLOCK:
        p(doc, line)
    add_table(
        doc,
        ["Hipotesis", "Decision", "Mejor descriptivo", "Fundamento Friedman (principal)"],
        [
            [
                "H0G / H1G",
                "Se rechaza H0G; se respalda H1G; sin ganador unico",
                "MAAC score / MATD3 mediana",
                "χ² = 9,2911; p = 0,0096; W = 0,1787",
            ],
            [
                "HE10 / HE11",
                "No se rechaza HE10; no se respalda HE11",
                "MAAC (gain) / MATD3 (flex)",
                "χ² = 5,5897; p = 0,0611; W = 0,2329",
            ],
            [
                "HE20 / HE21",
                "No se rechaza HE20; no se respalda HE21",
                "MATD3",
                "χ² = 6,0000; p = 0,0498; W = 0,6000 (sin post hoc/impacto)",
            ],
            [
                "HE30 / HE31",
                "No se rechaza HE30; no se respalda HE31",
                "MAAC",
                "χ² = 3,4286; p = 0,1801; W = 0,1905",
            ],
        ],
        caption="Tabla 5.6. Contrastacion consolidada HG/HE (Capa A, alpha = 0,05).",
        col_widths=[2.5, 4.5, 3.5, 4.5],
    )

    heading(doc, "5.6.1 Cumplimiento OG y OE.1–OE.3", 3)
    add_table(
        doc,
        ["Objetivo", "VD / Esc.", "Mayor efecto (VI)", "Evidencia KPI", "Cumplimiento"],
        _verdict_table_rows(report),
        caption="Tabla 5.6.1. Cumplimiento de objetivos (efecto + identificacion MADRL).",
        col_widths=[1.5, 2.2, 2.0, 4.5, 4.8],
    )

    # --- 5.7 Discusion ---
    heading(doc, "5.7 Discusion de resultados", 2)
    p(
        doc,
        "1) Separacion descriptivo/inferencial: lideres MAAC/MATD3 no equivalen a HE11/HE21/HE31. "
        "2) CityLearn y flexibilidad comunitaria (Nweye et al., 2022, 2023b, 2024): la coordinacion "
        "DER no garantiza mejoras univocas en todos los KPI bajo semilla unica. "
        "3) Familias MADRL (Iqbal y Sha, 2019; Kuba et al., 2021; Zhong et al., 2023; Haarnoja et al., "
        "2018; Gao et al., 2023): trade-offs tipicos actor-critico multiagente. "
        "4) Carbon-aware y precios (Nweye et al., 2024; Nweye y Nagy, 2024b): disociacion Delta CO2 "
        "vs Delta costo. "
        "5) Rigor estadistico RL (Agarwal et al., 2021; Demsar, 2006; Colas et al., 2019; "
        "Patterson et al., 2024): no tratar episodios como replicas independientes; reportar "
        "incertidumbre y tamanos de efecto. "
        "6) Limitaciones metodologicas (no alteran la formula del veredicto H): seed = 0 "
        "(semilla unica); HAPPO sin KPI-gains HE; n KPI 12/5/9; impacto GLOBAL desfavorable.",
    )
    heading(doc, "5.7.1 Contrastacion con antecedentes nacionales", 3)
    p(
        doc,
        f"Anclaje adicional a antecedentes del Capitulo 2 "
        f"({len(ANTECEDENTES_NACIONALES)} antecedentes nacionales/peruanos).",
    )
    for paragraph in _antecedents_discussion_text():
        p(doc, paragraph)

    heading(doc, "5.7.2 Auditoria de coherencia PG–OG–HG / PE–OE–HE", 3)
    add_table(
        doc,
        ["Cadena", "Efecto respondido", "Mejor MADRL", "Nivel de evidencia"],
        [
            [
                "PG → OG → H0G/H1G",
                "Si (H0G rechazada / H1G respaldada)",
                "Parcial: sin ganador unico",
                "Descriptivo + inferencial (limitacion: semilla unica)",
            ],
            [
                "PE.1 → OE.1 → HE10/HE11",
                "Si (HE10 no rechazada)",
                "MAAC gain / MATD3 flex (solo descriptivo)",
                "Descriptivo",
            ],
            [
                "PE.2 → OE.2 → HE20/HE21",
                "Si (HE20 no rechazada)",
                "MATD3 (solo descriptivo)",
                "Descriptivo",
            ],
            [
                "PE.3 → OE.3 → HE30/HE31",
                "Si (HE30 no rechazada)",
                "MAAC (solo descriptivo)",
                "Descriptivo",
            ],
        ],
        caption="Tabla 5.7.2. Auditoria de coherencia vertical Cap. 1 ↔ Cap. 5.",
        col_widths=[3.5, 4.0, 4.0, 3.5],
    )
    p(
        doc,
        "Veredicto de cierre Cap. V: los objetivos quedan respondidos en cuanto a determinacion "
        "del efecto y a identificacion del MADRL de mejor desempeno descriptivo por eje; "
        "la superioridad estadisticamente significativa por eje no se establece. "
        "Resumen, Abstract y Cap. VI se alinearan a este cierre en fase posterior.",
    )
    status_note(
        doc,
        "Capitulo 5 (2026-08-06): reestructurado por objetivos OE.1–OE.3/OG; Capa A canónica; "
        "Friedman principal; TOPSIS C*=0,9827; auditoria de coherencia PG–OE–HE.",
    )
