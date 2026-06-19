"""Assemble defense PDF using only Pillow (no external deps beyond what's in venv).

Each diagram gets its own A4-landscape page. A simple cover page is synthesized
by drawing text on a white image with ImageDraw.
"""
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

A4_L_PX = (3508, 2480)  # A4 landscape at 300 dpi
WHITE = (255, 255, 255)
DARK_BLUE = (30, 58, 95)
LIGHT_BLUE = (219, 234, 254)
DARK_TEXT = (28, 25, 23)
ACCENT = (234, 88, 12)


def try_font(size: int):
    for name in [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def try_bold(size: int):
    for name in [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return try_font(size)


def make_cover() -> Image.Image:
    W, H = A4_L_PX
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    # Header bar
    d.rectangle([(0, 0), (W, 120)], fill=DARK_BLUE)
    d.text((W // 2, 60), "MADRL CityLearn v3 — Arquitectura y Flujo de Trabajo",
           fill=WHITE, font=try_bold(60), anchor="mm")

    # Subtitle
    d.text((W // 2, 260),
           "Multi-Agente de Aprendizaje por Refuerzo Profundo",
           fill=DARK_BLUE, font=try_bold(50), anchor="mm")
    d.text((W // 2, 330),
           "Gestion Coordinada de Flexibilidad Energetica, Emisiones de Carbono y Eficiencia Economica",
           fill=DARK_BLUE, font=try_font(40), anchor="mm")
    d.text((W // 2, 390),
           "en Comunidades Inteligentes",
           fill=DARK_BLUE, font=try_font(40), anchor="mm")

    d.text((W // 2, 470),
           "Caso de estudio: 17 edificios reales de Iquitos, Peru (2023-2025)",
           fill=ACCENT, font=try_font(36), anchor="mm")
    d.text((W // 2, 520),
           "Universidad Nacional Mayor de San Marcos  |  mac.tapia@unmsm.edu.pe",
           fill=(71, 85, 105), font=try_font(30), anchor="mm")

    # Result box
    box_y, box_h = 600, 160
    d.rectangle([(200, box_y), (W - 200, box_y + box_h)], fill=LIGHT_BLUE, outline=DARK_BLUE, width=3)
    d.text((W // 2, box_y + 35),
           "Resultado principal — Corrida v4 (definitiva)",
           fill=DARK_BLUE, font=try_bold(36), anchor="mm")
    d.text((W // 2, box_y + 90),
           "MATD3 es el mejor MADRL global",
           fill=DARK_BLUE, font=try_bold(42), anchor="mm")
    d.text((W // 2, box_y + 140),
           "Kruskal-Wallis p = 0.0459  |  Mann-Whitney MATD3 vs HAPPO p = 0.0182",
           fill=DARK_TEXT, font=try_font(32), anchor="mm")

    # TOC table
    toc = [
        ("1", "Vision General",       "Problema → Dataset → CityLearn v3 → MADRL → MATD3"),
        ("2", "Pipeline Dataset",     "Facturas/meteo → destilacion → 222 CSV + schema.json"),
        ("3", "Dec-POMDP / CTDE",     "17 agentes, obs 19D, critico centralizado, exec local"),
        ("4", "4 Algoritmos MADRL",   "HAPPO/MASAC/MATD3/MAAC: tipo, backend, parametros v4"),
        ("5", "Flujo 12 Corridas",    "4 algos x 3 escenarios, tiempos, artefactos por job"),
        ("6", "Recompensa Multi-obj", "5 componentes, pesos por escenario, team_ratio=0.70"),
        ("7", "Evaluacion Estadist.", "4 tests → KW p=0.0459 → MATD3 ganador"),
        ("8", "Infra Docker/AWS",     "Dev→Git→AWS, bind mount, restart unless-stopped"),
        ("9", "Capas del Software",   "6 niveles: CityLearn v2→v3→UC3M→backends→eval"),
    ]
    row_h = 64
    toc_y0 = 820
    col_x = [100, 220, 760, 1400]
    headers = ["#", "Diagrama", "Contenido"]
    d.rectangle([(80, toc_y0 - row_h), (W - 80, toc_y0)], fill=DARK_BLUE)
    for ci, hdr in enumerate(headers):
        d.text((col_x[ci] + 10, toc_y0 - row_h // 2),
               hdr, fill=WHITE, font=try_bold(28), anchor="lm")
    for ri, (num, name, desc) in enumerate(toc):
        y0 = toc_y0 + ri * row_h
        bg = (248, 250, 252) if ri % 2 == 0 else (226, 232, 240)
        d.rectangle([(80, y0), (W - 80, y0 + row_h)], fill=bg)
        d.text((col_x[0] + 10, y0 + row_h // 2), num, fill=DARK_TEXT, font=try_bold(26), anchor="lm")
        d.text((col_x[1] + 10, y0 + row_h // 2), name, fill=DARK_BLUE, font=try_bold(24), anchor="lm")
        d.text((col_x[2] + 10, y0 + row_h // 2), desc, fill=DARK_TEXT, font=try_font(22), anchor="lm")

    # Footer bar
    d.rectangle([(0, H - 80), (W, H)], fill=DARK_BLUE)
    d.text((W // 2, H - 40),
           "Sustentacion de Tesis  |  MADRL CityLearn v3  |  2026",
           fill=WHITE, font=try_font(28), anchor="mm")

    return img


def make_results_page() -> Image.Image:
    W, H = A4_L_PX
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (W, 120)], fill=DARK_BLUE)
    d.text((W // 2, 60), "Resultados v4 — Corrida Definitiva",
           fill=WHITE, font=try_bold(56), anchor="mm")

    # KPI table
    kpi_hdr = ["Algoritmo", "OE1 Flex Score", "OE2 CO2 Score", "OE3 Costo Score", "Score Global", "Rango"]
    kpi_rows = [
        ["MATD3 ★ (ganador)", "0.7486", "0.7515", "0.7333", "0.7445", "1"],
        ["MASAC",             "0.74",   "0.74",   "0.72",   "~0.73",  "2"],
        ["MAAC",              "0.72",   "0.72",   "0.73",   "~0.72",  "3"],
        ["HAPPO",             "0.70",   "0.70",   "0.70",   "~0.70",  "4"],
    ]
    row_h, col_ws = 72, [800, 440, 440, 440, 440, 220]
    col_xs = [200]
    for cw in col_ws[:-1]:
        col_xs.append(col_xs[-1] + cw)

    table_y = 180
    d.rectangle([(180, table_y), (W - 180, table_y + row_h)], fill=DARK_BLUE)
    for ci, hdr in enumerate(kpi_hdr):
        d.text((col_xs[ci] + 10, table_y + row_h // 2),
               hdr, fill=WHITE, font=try_bold(26), anchor="lm")

    for ri, row in enumerate(kpi_rows):
        y0 = table_y + (ri + 1) * row_h
        bg = (220, 252, 231) if ri == 0 else ((248, 250, 252) if ri % 2 == 0 else (226, 232, 240))
        d.rectangle([(180, y0), (W - 180, y0 + row_h)], fill=bg)
        for ci, val in enumerate(row):
            fnt = try_bold(28) if ri == 0 else try_font(26)
            d.text((col_xs[ci] + 10, y0 + row_h // 2), val, fill=DARK_TEXT, font=fnt, anchor="lm")

    # Stat table
    stat_y = table_y + (len(kpi_rows) + 2) * row_h + 60
    d.text((W // 2, stat_y - 40), "Pruebas Estadisticas", fill=DARK_BLUE, font=try_bold(44), anchor="mm")

    stat_hdr = ["Test", "Resultado", "p-valor", "Conclusion"]
    stat_rows = [
        ["Shapiro-Wilk",                "Algunos grupos no normales", "—",       "Justifica tests no parametricos"],
        ["Kruskal-Wallis",              "Diferencia entre algoritmos", "0.0459",  "Significativo α=0.05 ✓"],
        ["Mann-Whitney U (MATD3/HAPPO)","MATD3 superior",             "0.0182",  "Significativo ✓"],
        ["Wilcoxon SR (MATD3/HAPPO)",   "Diferencia sistematica",     "2.62e-6", "Muy significativo ✓"],
    ]
    scol_ws = [820, 820, 340, 820]
    scol_xs = [180]
    for cw in scol_ws[:-1]:
        scol_xs.append(scol_xs[-1] + cw)

    d.rectangle([(180, stat_y), (180 + sum(scol_ws), stat_y + row_h)], fill=DARK_BLUE)
    for ci, hdr in enumerate(stat_hdr):
        d.text((scol_xs[ci] + 10, stat_y + row_h // 2),
               hdr, fill=WHITE, font=try_bold(26), anchor="lm")

    for ri, row in enumerate(stat_rows):
        y0 = stat_y + (ri + 1) * row_h
        bg = (220, 252, 231) if ri in (1, 2, 3) else (248, 250, 252)
        d.rectangle([(180, y0), (180 + sum(scol_ws), y0 + row_h)], fill=bg)
        for ci, val in enumerate(row):
            d.text((scol_xs[ci] + 10, y0 + row_h // 2), val, fill=DARK_TEXT, font=try_font(24), anchor="lm")

    d.rectangle([(0, H - 80), (W, H)], fill=DARK_BLUE)
    d.text((W // 2, H - 40), "Sustentacion de Tesis  |  MADRL CityLearn v3  |  2026",
           fill=WHITE, font=try_font(28), anchor="mm")
    return img


def build(png_dir: Path, out_pdf: Path):
    DIAGRAM_TITLES = {
        1: "Diagrama 1 — Vision General del Proyecto",
        2: "Diagrama 2 — Pipeline del Dataset Iquitos 2023-2025",
        3: "Diagrama 3 — Arquitectura Dec-POMDP y CTDE (17 Agentes)",
        4: "Diagrama 4 — Los 4 Algoritmos MADRL",
        5: "Diagrama 5 — Flujo de Entrenamiento (12 Corridas)",
        6: "Diagrama 6 — Recompensa Multiobjetivo por Escenario",
        7: "Diagrama 7 — Pipeline de Evaluacion Estadistica",
        8: "Diagrama 8 — Infraestructura Docker / AWS EC2",
        9: "Diagrama 9 — Estructura de Capas del Software",
    }
    W, H = A4_L_PX

    pages = [make_cover()]

    pngs = sorted(png_dir.glob("ARQUITECTURA_PROYECTO_DEFENSA-*.png"))
    for png in pngs:
        m = re.search(r"-(\d+)\.png$", png.name)
        idx = int(m.group(1)) if m else 0
        title = DIAGRAM_TITLES.get(idx, f"Diagrama {idx}")

        page = Image.new("RGB", (W, H), WHITE)
        d = ImageDraw.Draw(page)

        # Header
        d.rectangle([(0, 0), (W, 100)], fill=DARK_BLUE)
        d.text((W // 2, 50), title, fill=WHITE, font=try_bold(50), anchor="mm")

        # Diagram image
        diag = Image.open(png).convert("RGB")
        dw, dh = diag.size
        avail_w = W - 80
        avail_h = H - 180
        scale = min(avail_w / dw, avail_h / dh)
        new_w, new_h = int(dw * scale), int(dh * scale)
        diag = diag.resize((new_w, new_h), Image.LANCZOS)
        x = (W - new_w) // 2
        y = 110 + (avail_h - new_h) // 2
        page.paste(diag, (x, y))

        # Footer
        d.rectangle([(0, H - 70), (W, H)], fill=DARK_BLUE)
        d.text((W // 2, H - 35),
               f"MADRL CityLearn v3 — Sustentacion de Tesis  |  Pagina {idx + 1}",
               fill=WHITE, font=try_font(26), anchor="mm")

        pages.append(page)

    pages.append(make_results_page())

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(
        str(out_pdf),
        format="PDF",
        resolution=300,
        save_all=True,
        append_images=pages[1:],
    )
    size_mb = out_pdf.stat().st_size / 1024 / 1024
    print(f"PDF generado ({len(pages)} paginas): {out_pdf}")
    print(f"Tamano: {size_mb:.1f} MB")


if __name__ == "__main__":
    png_dir = Path("outputs/defensa_pdf/png")
    out_pdf = Path("outputs/defensa_pdf/ARQUITECTURA_MADRL_DEFENSA.pdf")
    build(png_dir, out_pdf)
