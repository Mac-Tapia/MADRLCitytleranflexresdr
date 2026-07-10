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

FIGURE_INTERPRETATIONS = {
    "5.1": "La Figura 5.1 muestra la evolucion de reward_mean en E1. MATD3 y MAAC convergen "
    "hacia valores estables tras ~20 episodios; MASAC presenta mayor varianza inter-episodio. "
    "El patron respalda OE.1 al evidenciar aprendizaje de flexibilidad bajo pesos [0,70; 0,15; 0,15].",
    "5.2": "En E2 (Figura 5.2), las curvas de reward_mean reflejan el eje de emisiones. MATD3 "
    "mantiene la trayectoria mas alta al cierre (50 ep), coherente con su liderazgo en delta CO2 "
    "de distrito (Tabla 5.3).",
    "5.3": "La Figura 5.3 (E3) exhibe convergencia mas lenta en costos; MAAC alcanza reward "
    "competitivo, alineado con su menor delta de costo energetico (9 515 EUR).",
    "5.4": "La Figura 5.4 sintetiza el ranking global por eje OE1/OE2/OE3. MATD3 lidera dos ejes "
    "y obtiene score global 0,6667 (Tabla 5.2); la dispersion entre algoritmos es visible pero "
    "no alcanza significancia inferencial global (KW p=0,155).",
    "5.5": "La Figura 5.5 contrasta el mejor y peor MADRL por escenario. En E2 y E3 MATD3 "
    "aparece como mejor; en E1 MAAC supera a MASAC, evidenciando sensibilidad al vector de pesos.",
    "5.6": "La Figura 5.6 detalla KPI de flexibilidad en E1. MATD3 presenta flex_composite "
    "superior en la corrida canonica, aunque el baseline CityLearn v2 conserva ventaja global "
    "(seccion 5.4).",
    "5.7": "La Figura 5.7 muestra emisiones CO2 en E2. MATD3 reduce delta de carbono a "
    "23 070 kg en distrito, el mejor valor MADRL auditado en Drive.",
    "5.8": "La Figura 5.8 reporta costos en E3. MAAC minimiza delta de costo frente a MATD3 "
    "(9 515 vs 44 399 EUR), matizando la seleccion global hacia MATD3.",
    "5.9": "La Figura 5.9 presenta trazas de control MADRL por edificio (trace.csv, E2). "
    "Se observa heterogeneidad entre B06 (32 EV) y edificios con menor flota, coherente con "
    "la variabilidad estructural del SEAI.",
    "5.10": "La Figura 5.10 agrega objetivos multiobjetivo a nivel distrito. MATD3 domina "
    "flexibilidad y CO2; MAAC destaca en costo, confirmando trade-offs entre ejes.",
    "5.11": "La Figura 5.11 desagrega flexibilidad por edificio (E1). Edificios con mayor "
    "capacidad BESS/PV muestran mayor margen de mejora relativa.",
    "5.12": "La Figura 5.12 muestra delta CO2 por edificio (E2). La reduccion no es uniforme: "
    "hospitales y malls concentran mayor impacto absoluto.",
    "5.13": "La Figura 5.13 presenta delta de costo por edificio (E3). MAAC obtiene valores "
    "inferiores en varios edificios institucionales con perfil diurno estable.",
    "5.14": "La Figura 5.14 inventaria 185 cargadores EV. B07 (UNAP, 42) y B06 (Mall, 32) "
    "concentran la complejidad de accion del entorno multiagente.",
    "5.15": "La Figura 5.15 reporta exito de carga EV con MATD3/E2. Las tasas varian entre "
    "3,9% y 48,2% segun edificio (descriptivo_distrito_colab.csv), indicando margen de mejora "
    "en cumplimiento de restricciones de salida.",
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


def add_figure(doc, path: Path, caption: str, width_cm: float = 15.5, interpretation: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    doc.add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(caption)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = GREY
    if interpretation:
        p_fn = doc.add_paragraph()
        p_fn.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_fn.add_run(interpretation)
    doc.add_paragraph()


def add_chapter_5_doctoral(doc, p, heading, add_table, status_note) -> None:
    report = _read_json(BEST_REPORT)
    district = _read_csv(DISTRICT_CSV)

    heading(doc, "Capitulo 5. Resultados y contrastacion de hipotesis", 1)
    p(
        doc,
        f"Este capitulo reporta la corrida canonica Colab/Drive ({RUN_ID}) como evidencia principal "
        "y la corrida local v4 (5 episodios) como referencia historica. Los KPIs por edificio provienen "
        "del analisis multiobjetivo integrado (17 edificios × 3 algoritmos × 3 escenarios).",
    )

    heading(doc, "5.1 Experimentos realizados", 2)
    add_table(
        doc,
        ["Algoritmo", "E1 ep.", "E2 ep.", "E3 ep.", "KPIs finales"],
        [
            ["MATD3", "50", "50", "50", "Si"],
            ["MAAC", "50", "50", "50", "Si"],
            ["MASAC", "50", "50", "50", "Si"],
            ["HAPPO", "49", "49", "49", "No (error VecEnvWrapper)"],
        ],
        caption="Tabla 5.1. Cobertura de episodios auditada (episodes_recorded).",
        col_widths=[3.0, 2.2, 2.2, 2.2, 5.4],
    )

    heading(doc, "5.2 Seleccion del mejor MADRL (distrito)", 2)
    p(doc, "Mejor algoritmo MADRL seleccionado: MATD3.", bold=True)
    rows = []
    for item in report.get("ranking_with_kpis", []):
        rows.append(
            [
                str(item.get("rank", "")),
                item["algorithm"],
                f"{item.get('score_global', 0):.4f}",
                f"{item.get('score_oe1_flex', 0):.4f}",
                f"{item.get('score_oe2_co2', 0):.4f}",
                f"{item.get('score_oe3_cost', 0):.4f}",
                "Si" if item.get("selected") else "No",
            ]
        )
    add_table(
        doc,
        ["Rango", "Algoritmo", "Score global", "OE1", "OE2", "OE3", "Seleccionado"],
        rows,
        caption="Tabla 5.2. Ranking global Colab/Drive (best_madrl_report.json).",
        col_widths=[1.5, 2.5, 2.5, 1.8, 1.8, 1.8, 2.5],
    )

    heading(doc, "5.3 KPIs fisicos por objetivo (distrito)", 2)
    phys_rows = []
    for row in district:
        phys_rows.append(
            [
                row["algorithm"],
                row["scenario"],
                f"{float(row['flex_composite']):.4f}",
                f"{float(row['carbon_emissions_delta_kg']):,.0f}",
                f"{float(row['electricity_cost_delta_eur']):,.0f}",
                f"{float(row['ev_departure_success_rate']) * 100:.1f}%",
            ]
        )
    add_table(
        doc,
        ["Algoritmo", "Esc.", "Flex comp.", "Delta CO2 (kg)", "Delta costo (EUR)", "EV exito"],
        phys_rows,
        caption="Tabla 5.3. KPIs fisicos agregados de distrito.",
        col_widths=[2.5, 1.5, 2.5, 3.0, 3.0, 2.5],
    )

    heading(doc, "5.4 Comparacion con linea base CityLearn v2", 2)
    p(
        doc,
        "Se contrastan los MADRL seleccionados (MATD3, MAAC, MASAC) frente a los agentes "
        "baseline y hour_rbc de CityLearn v2 original, con los 54 KPI normalizados y score "
        "global HPHI ponderado (pesos 0,34/0,33/0,33 por eje). Fuente: "
        f"outputs/{RUN_ID}/resumen_comparativo/citylearn_v2_baseline/. "
        "Hallazgo central: el baseline RBC supera a todos los MADRL en score global en E1, E2 "
        "y E3; esto no invalida el benchmark metodologico, pero matiza las conclusiones causales.",
    )
    add_table(
        doc,
        ["Escenario", "1.o global", "Score", "2.o", "Score", "Mejor MADRL", "Score MADRL"],
        [
            ["E1", "baseline v2", "0,7289", "hour_rbc", "0,6821", "MAAC", "0,4481"],
            ["E2", "baseline v2", "0,7866", "hour_rbc", "0,6551", "MATD3", "0,3813"],
            ["E3", "baseline v2", "0,7293", "hour_rbc", "0,6823", "MAAC", "0,4085"],
        ],
        caption="Tabla 5.4. Ranking global HPHI: CityLearn v2 vs MADRL (ranking_global_weighted.csv).",
        col_widths=[1.5, 2.5, 2.0, 2.5, 2.0, 2.5, 2.5],
    )
    p(
        doc,
        "En los tres escenarios, baseline y hour_rbc ocupan los dos primeros puestos. "
        "Entre MADRL, MATD3 lidera en E2 y MAAC en E1/E3 segun score global, coherente con "
        "Tabla 5.2 pero por debajo de controles basados en reglas. Nweye et al. (2024) reportan "
        "que politicas RBC bien calibradas son competidoras fuertes con presupuestos de "
        "entrenamiento limitados.",
    )
    for scenario in ("E1", "E2", "E3"):
        heatmap = BL_DIR / scenario / "baseline_gain_heatmap.png"
        if heatmap.is_file():
            add_figure(
                doc,
                heatmap,
                f"Mapa de ganancia vs baseline — escenario {scenario} "
                f"(citylearn_v2_baseline/{scenario}/baseline_gain_heatmap.png).",
                width_cm=14.0,
            )

    heading(doc, "5.5 Figuras de entrenamiento (artefactos Drive reales)", 2)
    p(
        doc,
        "Las siguientes figuras se generan exclusivamente desde timeseries.csv, trace.csv y "
        "results.json descargados de la corrida Colab/Drive (carpeta 1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX). "
        "No se utilizan datos sinteticos ni regeneracion desde episode_summaries.",
    )
    drive_figs = [
        (FD_DIR / "comparativo_E1_convergence_reward_mean.png", "Figura 5.1. Convergencia E1 (reward_mean) — datos reales Drive.", "5.1"),
        (FD_DIR / "comparativo_E2_convergence_reward_mean.png", "Figura 5.2. Convergencia E2 (reward_mean) — datos reales Drive.", "5.2"),
        (FD_DIR / "comparativo_E3_convergence_reward_mean.png", "Figura 5.3. Convergencia E3 (reward_mean) — datos reales Drive.", "5.3"),
        (FD_DIR / "comparativo_global_ranking_oe.png", "Figura 5.4. Ranking global OE1/OE2/OE3 (KPIs Drive).", "5.4"),
        (FD_DIR / "comparativo_best_worst_por_escenario.png", "Figura 5.5. Mejor y peor MADRL por escenario.", "5.5"),
        (FD_DIR / "comparativo_E1_OE1_kpi.png", "Figura 5.6. KPI OE1 flexibilidad — comparativa E1.", "5.6"),
        (FD_DIR / "comparativo_E2_OE2_kpi.png", "Figura 5.7. KPI OE2 emisiones CO2 — comparativa E2.", "5.7"),
        (FD_DIR / "comparativo_E3_OE3_kpi.png", "Figura 5.8. KPI OE3 costo energetico — comparativa E3.", "5.8"),
        (FD_DIR / "comparativo_E2_control_trace.png", "Figura 5.9. Control MADRL por edificio (trace.csv) — E2.", "5.9"),
    ]
    for path, caption, fig_id in drive_figs:
        doc.add_page_break()
        add_figure(doc, path, caption, interpretation=FIGURE_INTERPRETATIONS.get(fig_id))

    heading(doc, "5.6 Analisis multiobjetivo por edificio", 2)
    p(
        doc,
        "Se analizan 17 edificios institucionales/comerciales con inventario de 185 cargadores EV "
        "controlables (96 equipos Modo 3 doble toma). Elementos controlados: BESS, cargadores EV "
        "y carga desplazable; no controlados: carga base, refrigeracion/ACS modeladas y FV fija.",
    )
    inv = _read_csv(INVENTORY_CSV)
    inv_rows = [
        [
            f"B{int(r['building_id']):02d}",
            r["nombre"][:35],
            r["ev_total"],
            r["elementos_controlados"][:45] + "…",
        ]
        for r in inv[:8]
    ]
    add_table(
        doc,
        ["ID", "Edificio", "EV", "Controlados"],
        inv_rows,
        caption="Tabla 5.5. Inventario multiobjetivo (extracto B01–B08; completo en anexo CSV).",
        col_widths=[1.5, 5.5, 1.5, 6.5],
    )

    heading(doc, "5.7 Figuras multiobjetivo (distrito y edificio)", 2)
    figs = [
        (MO_DIR / "drive_district_objectives.png", "Figura 5.10. KPIs multiobjetivo — distrito.", "5.10"),
        (MO_DIR / "drive_building_E1_flex_composite_proxy.png", "Figura 5.11. OE1 flexibilidad por edificio.", "5.11"),
        (MO_DIR / "drive_building_E2_carbon_emissions_delta_kgco2.png", "Figura 5.12. OE2 delta CO2 por edificio.", "5.12"),
        (MO_DIR / "drive_building_E3_electricity_cost_delta_eur.png", "Figura 5.13. OE3 delta costo por edificio.", "5.13"),
        (MO_DIR / "drive_building_ev_inventory.png", "Figura 5.14. Inventario EV por edificio.", "5.14"),
        (MO_DIR / "drive_building_ev_success_matd3_e2.png", "Figura 5.15. Desempeno EV — MATD3/E2.", "5.15"),
    ]
    for path, caption, fig_id in figs:
        doc.add_page_break()
        add_figure(doc, path, caption, interpretation=FIGURE_INTERPRETATIONS.get(fig_id))

    heading(doc, "5.8 Pruebas estadisticas", 2)
    p(
        doc,
        "La bateria inferencial se ejecuto localmente sobre KPIs auditados de la corrida "
        f"Colab/Drive ({RUN_ID}) con tools/run_colab_drive_statistical_analysis.py "
        "(231 filas signed_relative_gain; MATD3, MAAC, MASAC; HAPPO excluido sin KPIs). "
        "La corrida local v4 (5 ep, 4 algoritmos) se conserva solo como referencia historica.",
    )
    add_table(
        doc,
        ["Alcance", "Prueba", "Estadistico / p", "Decision alpha=0.05"],
        [
            ["Colab ALL (KPI-level)", "Shapiro-Wilk", "MASAC/MATD3/MAAC: p<1e-11", "No normal → no parametricos"],
            ["Colab ALL (KPI-level)", "Kruskal-Wallis", "H=3.72, p=0.155", "No rechaza H0 global"],
            ["Colab ALL (KPI-level)", "Wilcoxon SR", "MASAC vs MATD3: p=0.0049", "Significativo (pareado)"],
            ["Colab ALL (KPI-level)", "Mann-Whitney U", "MASAC vs MATD3: p=0.070", "No significativo (0.05)"],
            ["Colab OE1", "Kruskal-Wallis", "p=0.281", "No significativo"],
            ["Colab OE2", "Kruskal-Wallis", "p=0.546", "No significativo"],
            ["Colab OE3", "Kruskal-Wallis", "p=0.388", "No significativo"],
            ["Score escenario (3x3)", "Kruskal-Wallis", "H=4.36, p=0.113", "No significativo"],
            ["Local v4 (referencia)", "Kruskal-Wallis", "p=0.0459", "Significativo (5 ep, exploratorio)"],
        ],
        caption="Tabla 5.6. Contrastacion inferencial Colab vs referencia local v4.",
        col_widths=[3.5, 3.0, 3.5, 4.0],
    )
    p(
        doc,
        "Interpretacion: el ranking descriptivo Colab (MATD3 score global 0.6667) se sostiene "
        "por KPIs de distrito y edificio; la significancia global KW sobre KPI-gains no alcanza "
        "alpha=0.05 con una semilla y sin HAPPO. Wilcoxon pareado detecta diferencia MASAC-MATD3 "
        "en el agregado ALL. Se requiere multi-semilla para elevar conclusiones causales (Colas et al., 2019).",
    )

    heading(doc, "5.9 Discusion", 2)
    p(
        doc,
        "La evidencia descriptiva de la corrida canonica identifica a MATD3 como el MADRL de "
        "mayor efecto coordinado (score 0,6667), con liderazgo en flexibilidad y CO2 y MAAC "
        "competitivo en costos. Sin embargo, tres matices condicionan la lectura doctoral. "
        "Primero, Kruskal-Wallis global no alcanza significancia (p=0,155), por lo que HG no "
        "se confirma inferencialmente con una semilla; Wilcoxon MASAC vs MATD3 (p=0,0049) es "
        "exploratorio y no sustituye el contraste factorial completo. Segundo, la seccion 5.4 "
        "demuestra que baseline y hour_rbc de CityLearn v2 superan a los MADRL en score global "
        "HPHI en los tres escenarios, coherente con Nweye et al. (2024) sobre la competitividad "
        "de controles basados en reglas. Tercero, HAPPO queda excluido de inferencia por ausencia "
        "de KPIs finales (49/50 ep, error VecEnvWrapper). El aporte vigente es metodologico: "
        "benchmark unificado, trazable y reproducible sobre datos reales del SEAI, con protocolo "
        "estadistico documentado para extension multi-semilla (Colas et al., 2019).",
    )


def add_chapter_6_doctoral(doc, p, heading, bullet, add_table) -> None:
    heading(doc, "Capitulo 6. Conclusiones y trabajo futuro", 1)
    heading(doc, "6.1 Conclusiones", 2)
    p(
        doc,
        "En respuesta al objetivo general, la tesis determina que el algoritmo MADRL produce "
        "efectos diferenciados sobre flexibilidad, emisiones y costos en la simulacion del SEAI "
        "Iquitos, identificando descriptivamente a MATD3 como el de mayor efecto coordinado "
        "(score global 0,6667, corrida madrl_v3_20260627_164047). El objetivo OE.1 se atiende "
        "con MATD3 liderando flexibilidad compuesta; OE.2 con menor delta de CO2 (23 070 kg); "
        "y OE.3 con MAAC presentando el menor delta de costo (9 515 EUR frente a 44 399 EUR "
        "de MATD3-E3). La hipotesis general no se confirma inferencialmente (KW p=0,155), aunque "
        "la evidencia descriptiva respalda la seleccion de MATD3 dentro de la familia MADRL.",
    )
    p(
        doc,
        "La contrastacion con baseline CityLearn v2 (seccion 5.4) revela que los agentes RBC "
        "baseline y hour_rbc superan globalmente a los MADRL entrenados, lo cual constituye un "
        "hallazgo honesto y relevante: el marco experimental es valido para comparacion "
        "inter-algoritmica, pero las politicas aprendidas requieren mayor presupuesto de "
        "entrenamiento, hiperparametrizacion u operacionalizacion multi-semilla para superar "
        "controles clasicos. Los cuatro aportes al motor CityLearn (BESS Arrhenius, PV tropical, "
        "KPI pico OSINERGMIN, CarbonIntensityModel SEAI) y el dataset auditado de 17 edificios "
        "constituyen contribuciones metodologicas transferibles a otros sistemas aislados peruanos.",
    )
    heading(doc, "6.2 Limitaciones", 2)
    p(
        doc,
        "Las limitaciones principales son: (i) semilla unica (seed 0), insuficiente para "
        "conclusiones causales robustas segun Colas et al. (2019); (ii) HAPPO sin KPIs finales "
        "(49/50 episodios, error VecEnvWrapper), lo que reduce el diseno factorial efectivo a "
        "3×3 en inferencia; (iii) simulacion sin validacion en red fisica; (iv) CityLearn v3 "
        "propuesto como extension experimental de tesis; (v) MADRL por debajo del baseline RBC "
        "en score global HPHI. La inferencia Colab ya fue ejecutada (Tabla 5.6); no permanece "
        "pendiente.",
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
