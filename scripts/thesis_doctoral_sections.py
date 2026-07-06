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
        "KPIs finales por error de evaluacion (VecEnvWrapper). La evidencia inferencial preliminar local "
        "(5 ep, Kruskal-Wallis p = 0,0459) anticipa la direccion del ranking Colab.",
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
        "Results are grounded in audited Drive artifacts; inferential tests on the canonical run "
        "remain pending.",
        italic=True,
    )
    doc.add_page_break()


def add_figure(doc, path: Path, caption: str, width_cm: float = 15.5) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    doc.add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(caption)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = GREY
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

    heading(doc, "5.5 Figuras de entrenamiento (artefactos Drive reales)", 2)
    p(
        doc,
        "Las siguientes figuras se generan exclusivamente desde timeseries.csv, trace.csv y "
        "results.json descargados de la corrida Colab/Drive (carpeta 1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX). "
        "No se utilizan datos sinteticos ni regeneracion desde episode_summaries.",
    )
    drive_figs = [
        (FD_DIR / "comparativo_E1_convergence_reward_mean.png", "Figura 5.1. Convergencia E1 (reward_mean) — datos reales Drive."),
        (FD_DIR / "comparativo_E2_convergence_reward_mean.png", "Figura 5.2. Convergencia E2 (reward_mean) — datos reales Drive."),
        (FD_DIR / "comparativo_E3_convergence_reward_mean.png", "Figura 5.3. Convergencia E3 (reward_mean) — datos reales Drive."),
        (FD_DIR / "comparativo_global_ranking_oe.png", "Figura 5.4. Ranking global OE1/OE2/OE3 (KPIs Drive)."),
        (FD_DIR / "comparativo_best_worst_por_escenario.png", "Figura 5.5. Mejor y peor MADRL por escenario."),
        (FD_DIR / "comparativo_E1_OE1_kpi.png", "Figura 5.6. KPI OE1 flexibilidad — comparativa E1."),
        (FD_DIR / "comparativo_E2_OE2_kpi.png", "Figura 5.7. KPI OE2 emisiones CO2 — comparativa E2."),
        (FD_DIR / "comparativo_E3_OE3_kpi.png", "Figura 5.8. KPI OE3 costo energetico — comparativa E3."),
        (FD_DIR / "comparativo_E2_control_trace.png", "Figura 5.9. Control MADRL por edificio (trace.csv) — E2."),
    ]
    for path, caption in drive_figs:
        doc.add_page_break()
        add_figure(doc, path, caption)

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
        caption="Tabla 5.4. Inventario multiobjetivo (extracto B01–B08; completo en anexo CSV).",
        col_widths=[1.5, 5.5, 1.5, 6.5],
    )

    heading(doc, "5.7 Figuras multiobjetivo (distrito y edificio)", 2)
    figs = [
        (MO_DIR / "drive_district_objectives.png", "Figura 5.10. KPIs multiobjetivo — distrito."),
        (MO_DIR / "drive_building_E1_flex_composite_proxy.png", "Figura 5.11. OE1 flexibilidad por edificio."),
        (MO_DIR / "drive_building_E2_carbon_emissions_delta_kgco2.png", "Figura 5.12. OE2 delta CO2 por edificio."),
        (MO_DIR / "drive_building_E3_electricity_cost_delta_eur.png", "Figura 5.13. OE3 delta costo por edificio."),
        (MO_DIR / "drive_building_ev_inventory.png", "Figura 5.14. Inventario EV por edificio."),
        (MO_DIR / "drive_building_ev_success_matd3_e2.png", "Figura 5.15. Desempeno EV — MATD3/E2."),
    ]
    for path, caption in figs:
        doc.add_page_break()
        add_figure(doc, path, caption)

    heading(doc, "5.8 Pruebas estadisticas", 2)
    add_table(
        doc,
        ["Fuente", "Prueba", "p-valor", "Estado"],
        [
            ["Local v4 (5 ep)", "Kruskal-Wallis", "0.0459", "Significativo"],
            ["Local v4 (5 ep)", "Mann-Whitney MATD3 vs HAPPO", "0.0182", "Significativo"],
            ["Colab canonica (50 ep)", "Kruskal-Wallis / post-hoc", "[Pendiente]", "Celda 9.1 notebook"],
        ],
        caption="Tabla 5.5. Contrastacion inferencial (local vs canonica).",
        col_widths=[4.0, 4.5, 2.5, 4.0],
    )

    heading(doc, "5.9 Discusion", 2)
    p(
        doc,
        "MATD3 domina flexibilidad y emisiones en la corrida canonica, con mayor tasa de exito EV "
        "que MASAC/MAAC. MAAC es competitivo en costo energetico del distrito. El analisis por "
        "edificio revela heterogeneidad estructural (B06 Mall: 32 EV; B07 UNAP: 42 EV). La "
        "interpretacion exige frontera de Pareto por eje, no solo score global. HAPPO requiere "
        "re-evaluacion tras corregir VecEnvWrapper.",
    )


def add_chapter_6_doctoral(doc, p, heading, bullet, add_table) -> None:
    heading(doc, "Capitulo 6. Conclusiones y trabajo futuro", 1)
    heading(doc, "6.1 Conclusiones", 2)
    bullet(doc, "El OG se responde identificando a MATD3 como el MADRL de mayor efecto coordinado en Colab (score 0,6667).")
    bullet(doc, "OE.1 y OE.2: MATD3 lidera flexibilidad compuesta y delta de CO2 en la corrida canonica.")
    bullet(doc, "OE.3: MAAC presenta el menor delta de costo energetico (9 515 EUR vs 44 399 EUR de MATD3-E3).")
    bullet(doc, "El benchmark unificado Dec-POMDP/CTDE sobre 17 edificios reales es reproducible y auditado.")
    heading(doc, "6.2 Limitaciones", 2)
    bullet(doc, "Semilla unica (seed 0); inferencia Colab pendiente; HAPPO sin KPIs finales.")
    bullet(doc, "Simulacion sin validacion en red fisica; CityLearn v3 propuesto es extension experimental.")
    heading(doc, "6.3 Trabajo futuro", 2)
    bullet(doc, "Multi-semilla, re-evaluacion HAPPO, pruebas Dunn/Wilcoxon con correccion Bonferroni.")
    bullet(doc, "HPO Optuna y transferencia a otros sistemas aislados peruanos.")


def verify_doctoral_docx(path: Path) -> dict:
    from docx import Document

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

    doc = Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text)
    styles = [p.style.name if p.style else "" for p in doc.paragraphs]
    headings = [p.text for p in doc.paragraphs if p.style and p.style.name.startswith("Heading")]

    section_ok = {s: any(s.lower() in h.lower() for h in headings) or s.lower() in text.lower() for s in required_sections}
    n_tables = len(doc.tables)
    n_images = sum(1 for rel in doc.part.rels.values() if "image" in rel.target_ref)

    checks = {
        "sections": section_ok,
        "tables_count": n_tables,
        "tables_ok": n_tables >= required_tables_min,
        "images_count": n_images,
        "images_ok": n_images >= required_figures_min,
        "has_matd3_selection": "MATD3" in text and "0.6667" in text or "0,6667" in text,
        "has_multiobjetivo": "multiobjetivo" in text.lower() or "185" in text,
        "has_drive_figures": "timeseries.csv" in text.lower() or "artefactos drive" in text.lower(),
        "complete": all(section_ok.values()) and n_tables >= required_tables_min and n_images >= required_figures_min,
    }
    return checks
