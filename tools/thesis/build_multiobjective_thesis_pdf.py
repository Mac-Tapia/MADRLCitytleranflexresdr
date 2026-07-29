"""PDF resumen multiobjetivo Colab/Drive para tesis (Pillow, sin pandoc)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
RUN_ID = "madrl_v3_20260627_164047"
MO_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "multiobjetivo"
OUT_PDF = MO_DIR / "RESUMEN_MULTIOBJETIVO_TESIS.pdf"

A4_L_PX = (3508, 2480)
WHITE = (255, 255, 255)
DARK_BLUE = (30, 58, 95)
LIGHT_BLUE = (219, 234, 254)
DARK_TEXT = (28, 25, 23)
ACCENT = (234, 88, 12)


def try_font(size: int):
    for name in (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def try_bold(size: int):
    for name in (
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return try_font(size)


def make_cover() -> Image.Image:
    w, h = A4_L_PX
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (w, 120)], fill=DARK_BLUE)
    d.text(
        (w // 2, 60),
        "Resultados multiobjetivo MADRL — Iquitos",
        fill=WHITE,
        font=try_bold(58),
        anchor="mm",
    )
    d.text(
        (w // 2, 240),
        "Flexibilidad (OE1) · Emisiones CO₂ (OE2) · Costo energético (OE3)",
        fill=DARK_BLUE,
        font=try_bold(44),
        anchor="mm",
    )
    d.text(
        (w // 2, 310),
        f"Corrida canónica: {RUN_ID}",
        fill=ACCENT,
        font=try_font(36),
        anchor="mm",
    )
    d.text(
        (w // 2, 370),
        "17 edificios · 185 cargadores EV · MASAC / MATD3 / MAAC",
        fill=(71, 85, 105),
        font=try_font(32),
        anchor="mm",
    )

    box_y, box_h = 480, 520
    d.rectangle([(160, box_y), (w - 160, box_y + box_h)], fill=LIGHT_BLUE, outline=DARK_BLUE, width=3)
    d.text(
        (w // 2, box_y + 40),
        "Mejor algoritmo por objetivo (distrito)",
        fill=DARK_BLUE,
        font=try_bold(38),
        anchor="mm",
    )
    rows = [
        ("OE1 Flexibilidad (E1)", "MATD3", "flex_composite = 1.001"),
        ("OE2 Emisiones CO₂ (E2)", "MATD3", "ΔCO₂ = 23,070 kg"),
        ("OE3 Costo energético (E3)", "MAAC", "Δcosto = 9,515 EUR"),
        ("Éxito salida EV (distrito)", "MATD3", "tasa ≈ 36–48 % según escenario"),
        ("Inventario EV", "—", "185 tomas controlables (96 equipos Modo 3)"),
    ]
    y = box_y + 100
    for title, algo, detail in rows:
        d.text((220, y), f"• {title}", fill=DARK_TEXT, font=try_bold(30))
        d.text((240, y + 42), f"{algo}: {detail}", fill=DARK_TEXT, font=try_font(26))
        y += 95

    d.rectangle([(0, h - 80), (w, h)], fill=DARK_BLUE)
    d.text(
        (w // 2, h - 40),
        "Tesis doctoral MADRL CityLearn v3 · Fuente: Google Drive Colab · 2026",
        fill=WHITE,
        font=try_font(28),
        anchor="mm",
    )
    return img


def make_figure_page(title: str, png_path: Path, page_no: int) -> Image.Image:
    w, h = A4_L_PX
    page = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(page)
    d.rectangle([(0, 0), (w, 100)], fill=DARK_BLUE)
    d.text((w // 2, 50), title, fill=WHITE, font=try_bold(46), anchor="mm")

    diag = Image.open(png_path).convert("RGB")
    dw, dh = diag.size
    avail_w, avail_h = w - 80, h - 180
    scale = min(avail_w / dw, avail_h / dh)
    new_w, new_h = int(dw * scale), int(dh * scale)
    diag = diag.resize((new_w, new_h), Image.LANCZOS)
    page.paste(diag, ((w - new_w) // 2, 110 + (avail_h - new_h) // 2))

    d.rectangle([(0, h - 70), (w, h)], fill=DARK_BLUE)
    d.text(
        (w // 2, h - 35),
        f"Resumen multiobjetivo · Página {page_no}",
        fill=WHITE,
        font=try_font(26),
        anchor="mm",
    )
    return page


def build(out_pdf: Path = OUT_PDF) -> Path:
    pages: list[Image.Image] = [make_cover()]
    page_no = 2

    main_figs = [
        ("KPIs multiobjetivo — distrito", MO_DIR / "drive_district_objectives.png"),
        ("OE1 Flexibilidad por edificio", MO_DIR / "drive_building_E1_flex_composite_proxy.png"),
        ("OE2 Δ CO₂ por edificio (kg)", MO_DIR / "drive_building_E2_carbon_emissions_delta_kgco2.png"),
        ("OE3 Δ costo por edificio (EUR)", MO_DIR / "drive_building_E3_electricity_cost_delta_eur.png"),
        ("Inventario EV por edificio", MO_DIR / "drive_building_ev_inventory.png"),
        ("Desempeño EV — MATD3 / E2", MO_DIR / "drive_building_ev_success_matd3_e2.png"),
    ]
    for title, path in main_figs:
        if not path.is_file():
            raise FileNotFoundError(path)
        pages.append(make_figure_page(title, path, page_no))
        page_no += 1

    per_dir = MO_DIR / "por_edificio"
    for png in sorted(per_dir.glob("drive_building_B*_objectives.png")):
        bid = png.stem.replace("drive_building_", "").replace("_objectives", "")
        pages.append(make_figure_page(f"Detalle {bid} — tres objetivos × algoritmo", png, page_no))
        page_no += 1

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(
        str(out_pdf),
        format="PDF",
        resolution=300,
        save_all=True,
        append_images=pages[1:],
    )
    size_mb = out_pdf.stat().st_size / 1024 / 1024
    print(f"PDF generado ({len(pages)} páginas): {out_pdf}")
    print(f"Tamaño: {size_mb:.1f} MB")
    return out_pdf


if __name__ == "__main__":
    build()
