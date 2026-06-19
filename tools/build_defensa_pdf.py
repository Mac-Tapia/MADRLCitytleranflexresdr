"""Assemble the MADRL thesis defense PDF from rendered PNG diagrams + markdown text."""
import re
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

PAGE = landscape(A4)
W, H = PAGE
MARGIN = 1.5 * cm


DIAGRAM_TITLES = {
    1: "Diagrama 1 — Vision General del Proyecto (inicio a fin)",
    2: "Diagrama 2 — Pipeline del Dataset Iquitos 2023-2025",
    3: "Diagrama 3 — Arquitectura Dec-POMDP y CTDE de los 17 Agentes",
    4: "Diagrama 4 — Los 4 Algoritmos MADRL: Taxonomia y Diferencias",
    5: "Diagrama 5 — Flujo de Entrenamiento: 12 Corridas (4 x 3)",
    6: "Diagrama 6 — Recompensa Multiobjetivo por Escenario",
    7: "Diagrama 7 — Pipeline de Evaluacion y Seleccion del Mejor MADRL",
    8: "Diagrama 8 — Infraestructura de Despliegue: Local y AWS EC2",
    9: "Diagrama 9 — Estructura de Capas del Software",
}


def build_styles():
    styles = getSampleStyleSheet()
    cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=28,
        leading=36,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=18,
        alignment=TA_CENTER,
    )
    cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontSize=14,
        leading=20,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10,
        alignment=TA_CENTER,
    )
    cover_body = ParagraphStyle(
        "CoverBody",
        parent=styles["Normal"],
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=8,
        alignment=TA_CENTER,
    )
    diag_title = ParagraphStyle(
        "DiagTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    result_head = ParagraphStyle(
        "ResultHead",
        parent=styles["Heading2"],
        fontSize=14,
        leading=20,
        textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=8,
        spaceAfter=8,
    )
    result_body = ParagraphStyle(
        "ResultBody",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#1c1917"),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    return {
        "cover_title": cover_title,
        "cover_sub": cover_sub,
        "cover_body": cover_body,
        "diag_title": diag_title,
        "result_head": result_head,
        "result_body": result_body,
    }


def cover_page(styles):
    elems = []
    elems.append(Spacer(1, 3 * cm))
    elems.append(Paragraph(
        "MADRL CityLearn v3 — Arquitectura y Flujo de Trabajo",
        styles["cover_title"],
    ))
    elems.append(Spacer(1, 0.5 * cm))
    elems.append(Paragraph(
        "Multi-Agente de Aprendizaje por Refuerzo Profundo para Gestion Coordinada<br/>"
        "de Flexibilidad Energetica, Emisiones de Carbono y Eficiencia Economica<br/>"
        "en Comunidades Inteligentes",
        styles["cover_sub"],
    ))
    elems.append(Spacer(1, 1.5 * cm))
    elems.append(Paragraph("Caso de estudio: 17 edificios reales de Iquitos, Peru (2023-2025)", styles["cover_body"]))
    elems.append(Paragraph("Universidad Nacional de Ingenieria - UNI", styles["cover_body"]))
    elems.append(Paragraph("mac.tapia.c@uni.pe", styles["cover_body"]))
    elems.append(Spacer(1, 1.5 * cm))
    elems.append(Paragraph(
        "<b>Resultado principal (corrida v4 — definitiva):</b><br/>"
        "MATD3 es el mejor MADRL global<br/>"
        "Kruskal-Wallis p = 0.0459 · Mann-Whitney MATD3 vs HAPPO p = 0.0182",
        styles["cover_sub"],
    ))
    elems.append(Spacer(1, 1 * cm))
    toc_data = [
        ["#", "Diagrama", "Contenido"],
        ["1", "Vision General", "Problema → Dataset → CityLearn v3 → MADRL → MATD3"],
        ["2", "Pipeline Dataset", "Facturas/meteo → destilacion → 222 CSV + schema.json"],
        ["3", "Dec-POMDP / CTDE", "17 agentes, obs 19D, critico centralizado, exec local"],
        ["4", "4 Algoritmos MADRL", "HAPPO/MASAC/MATD3/MAAC: tipo, backend, parametros v4"],
        ["5", "Flujo 12 Corridas", "4 algos x 3 escenarios, tiempos, artefactos por job"],
        ["6", "Recompensa Multi-obj", "5 componentes, pesos por escenario, team_ratio=0.70"],
        ["7", "Evaluacion Estadist.", "4 tests → KW p=0.0459 → MATD3 ganador"],
        ["8", "Infra Docker/AWS", "Dev→Git→AWS, bind mount, restart unless-stopped"],
        ["9", "Capas del Software", "6 niveles: CityLearn v2→v3→UC3M→backends→eval"],
        ["10", "Resultados v4", "Tabla KPIs + pruebas estadisticas definitivas"],
    ]
    col_widths = [1 * cm, 5.5 * cm, 15 * cm]
    tbl = Table(toc_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elems.append(tbl)
    elems.append(PageBreak())
    return elems


def diagram_page(png_path: Path, idx: int, styles):
    elems = []
    title = DIAGRAM_TITLES.get(idx, f"Diagrama {idx}")
    elems.append(Paragraph(title, styles["diag_title"]))
    elems.append(Spacer(1, 0.3 * cm))
    with Image.open(png_path) as im:
        iw, ih = im.size
    max_w = W - 2 * MARGIN
    max_h = H - 4 * cm
    scale = min(max_w / iw, max_h / ih, 1.0)
    dw, dh = iw * scale, ih * scale
    img = RLImage(str(png_path), width=dw, height=dh)
    img.hAlign = "CENTER"
    elems.append(img)
    elems.append(PageBreak())
    return elems


def results_page(styles):
    elems = []
    elems.append(Paragraph("Tabla de Resultados v4 — Corrida Definitiva", styles["result_head"]))
    elems.append(Spacer(1, 0.3 * cm))

    kpi_data = [
        ["Algoritmo", "OE1 Flex Score", "OE2 CO2 Score", "OE3 Costo Score", "Score Global", "Rango"],
        ["MATD3 ★", "0.7486", "0.7515", "0.7333", "0.7445", "1 (mejor)"],
        ["MASAC", "0.74", "0.74", "0.72", "~0.73", "2"],
        ["MAAC", "0.72", "0.72", "0.73", "~0.72", "3"],
        ["HAPPO", "0.70", "0.70", "0.70", "~0.70", "4"],
    ]
    col_w = [(W - 2 * MARGIN) / 6] * 6
    tbl = Table(kpi_data, colWidths=col_w)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#dcfce7")),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 0.8 * cm))

    elems.append(Paragraph("Pruebas Estadisticas (OE global)", styles["result_head"]))
    stat_data = [
        ["Test", "Resultado", "p-valor", "Conclusion"],
        ["Shapiro-Wilk", "Algunos grupos no normales", "—", "Justifica tests no parametricos"],
        ["Kruskal-Wallis", "Diferencia entre algoritmos", "0.0459", "Significativo α=0.05 ✓"],
        ["Mann-Whitney U: MATD3 vs HAPPO", "MATD3 superior", "0.0182", "Significativo ✓"],
        ["Wilcoxon SR: MATD3 vs HAPPO", "Diferencia sistematica", "2.62e-6", "Muy significativo ✓"],
    ]
    col_w2 = [6 * cm, 6 * cm, 3 * cm, 8 * cm]
    tbl2 = Table(stat_data, colWidths=col_w2)
    tbl2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    elems.append(tbl2)
    elems.append(Spacer(1, 1 * cm))
    elems.append(Paragraph(
        "Corrida definitiva: outputs/citylearn_v3_madrl_full_20260615_074011_v4 — 12/12 jobs completados.",
        styles["result_body"],
    ))
    elems.append(Paragraph(
        "Funcion de recompensa: CityLearnV3MADRLRewardFunction con perfiles *_unified_comparable_v4. "
        "Penalizacion BESS Arrhenius LiFePO4 C-rate + urgencia EV (SOC deficit × 1/horas_restantes). "
        "team_ratio=0.70 (mixed_reward = 0.30×local + 0.70×team).",
        styles["result_body"],
    ))
    return elems


def build(png_dir: Path, out_pdf: Path):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=PAGE,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="MADRL CityLearn v3 — Arquitectura y Flujo de Trabajo",
        author="mac.tapia.c@uni.pe",
        subject="Sustentacion de Tesis — Arquitectura del Proyecto",
    )
    elems = []
    elems += cover_page(styles)
    pngs = sorted(png_dir.glob("ARQUITECTURA_PROYECTO_DEFENSA-*.png"))
    for png in pngs:
        m = re.search(r"-(\d+)\.png$", png.name)
        idx = int(m.group(1)) if m else 0
        elems += diagram_page(png, idx, styles)
    elems += results_page(styles)
    doc.build(elems)
    print(f"PDF generado: {out_pdf}")
    size_mb = out_pdf.stat().st_size / 1024 / 1024
    print(f"Tamaño: {size_mb:.2f} MB")


if __name__ == "__main__":
    png_dir = Path("outputs/defensa_pdf/png")
    out_pdf = Path("outputs/defensa_pdf/ARQUITECTURA_MADRL_DEFENSA.pdf")
    build(png_dir, out_pdf)
