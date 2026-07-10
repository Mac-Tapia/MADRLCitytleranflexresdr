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

BL_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "citylearn_v2_baseline"
STAT_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "estadistica"
HYP_CSV = STAT_DIR / "hipotesis_estadisticas_madrl.csv"

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
        add_figure(
            doc,
            path,
            f"Figura 5.{n}. {desc.capitalize()} — escenario {scenario}, datos reales Drive (300 dpi).",
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
    fig_counter = [0]

    heading(doc, "Capitulo 5. Resultados y contrastacion de hipotesis", 1)
    p(
        doc,
        f"Este capitulo organiza la evidencia experimental de la corrida canonica Colab/Drive "
        f"({RUN_ID}, 50 episodios) objetivo por objetivo, siguiendo la cadena VI→VD del "
        "diseno factorial: cada objetivo especifico (OE.1, OE.2, OE.3) se contrasta en su "
        "escenario dominante (E1, E2, E3) con KPIs de distrito y desagregacion por edificio. "
        "La sintesis integrada, la comparacion con baseline CityLearn v2 y la inferencia "
        "estadistica cierran el capitulo.",
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

    _add_oe_results_section(
        doc, p, heading, add_table,
        oe_key="OE1", oe_num=1, section_num="5.2",
        district=district, report=report, fig_counter=fig_counter,
    )
    _add_oe_results_section(
        doc, p, heading, add_table,
        oe_key="OE2", oe_num=2, section_num="5.3",
        district=district, report=report, fig_counter=fig_counter,
    )
    _add_oe_results_section(
        doc, p, heading, add_table,
        oe_key="OE3", oe_num=3, section_num="5.4",
        district=district, report=report, fig_counter=fig_counter,
    )

    heading(doc, "5.5 Sintesis integrada por objetivo especifico", 2)
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

    heading(doc, "5.6 Comparacion con linea base CityLearn v2 por objetivo", 2)
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

    heading(doc, "5.7 Pruebas estadisticas por objetivo especifico", 2)
    p(
        doc,
        "La bateria inferencial (tools/run_colab_drive_statistical_analysis.py) se reporta "
        "por eje OE y en agregado ALL. HAPPO excluido; semilla unica (seed 0).",
    )
    hyp_rows = _read_csv(HYP_CSV)
    stat_table = []
    for row in hyp_rows:
        if row["axis"] not in ("OE1", "OE2", "OE3", "OG"):
            continue
        label = {"OE1": "OE.1 / E1", "OE2": "OE.2 / E2", "OE3": "OE.3 / E3", "OG": "Global (ALL)"}[row["axis"]]
        stat_table.append(
            [
                label,
                "Kruskal-Wallis",
                f"H={float(row['KW_H_statistic']):.2f}, p={float(row['KW_p_value']):.3f}",
                "Si" if float(row["KW_p_value"]) < 0.05 else "No",
                row.get("statistical_best_algorithm_by_median_gain", "-"),
            ]
        )
    stat_table.append(["ALL (pareado)", "Wilcoxon", "MASAC vs MATD3: p=0,0049", "Si", "MATD3"])
    add_table(
        doc,
        ["Alcance OE", "Prueba", "Estadistico / p", "Signif. alpha=0,05", "Mejor (mediana KPI-gain)"],
        stat_table,
        caption="Tabla 5.13. Inferencia por objetivo especifico (hipotesis_estadisticas_madrl.csv).",
        col_widths=[2.5, 2.5, 3.5, 2.5, 3.0],
    )
    p(
        doc,
        "Interpretacion por OE: ningun Kruskal-Wallis por eje alcanza alpha=0,05 con una semilla; "
        "por tanto, las respuestas a OE.1–OE.3 en las secciones 5.2–5.4 se sustentan en evidencia "
        "descriptiva de KPIs de distrito y edificio. El Wilcoxon global MASAC–MATD3 (p=0,0049) "
        "es exploratorio y no reemplaza el contraste factorial completo.",
    )

    heading(doc, "5.8 Discusion integrada alineada a objetivos", 2)
    p(
        doc,
        "La lectura doctoral exige separar tres niveles. Nivel 1 (respuesta OE): MATD3 es el "
        "de mayor efecto en OE.1 (flexibilidad, E1) y OE.2 (CO2, E2); MAAC en OE.3 (costos, E3). "
        "Nivel 2 (integracion): MATD3 obtiene score global 0,6667 por liderar dos ejes, pero "
        "no domina costos. Nivel 3 (contraste externo): baseline RBC de CityLearn v2 supera "
        "globalmente a MADRL (seccion 5.6), coherente con Nweye et al. (2024). La coherencia "
        "vertical PG→OE→VD se cumple en estructura y evidencia descriptiva; la inferencia causal "
        "robusta requiere multi-semilla. HAPPO (49/50 ep) reduce el diseno factorial efectivo "
        "a 3×3 en inferencia.",
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
        "Ningun Kruskal-Wallis por eje alcanza alpha=0,05 (Tabla 5.13); las respuestas OE se "
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
        "en score global HPHI. La inferencia Colab por OE se reporta en Tabla 5.13.",
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
