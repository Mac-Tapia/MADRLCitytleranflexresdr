#!/usr/bin/env python3
"""
Genera PDFs de los archivos Markdown de arquitectura usando Chrome headless.
Requiere: Python 3.x con 'markdown' instalado + Google Chrome.
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

ARCH_DIR = Path(__file__).parent.parent / "docs" / "architecture"

# Mapeo: markdown fuente -> pdf destino
FILES = [
    (
        "ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md",
        "ARQUITECTURA_FLUJO_CITYLEARN_V3_MADRL.pdf",
    ),
    (
        "FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md",
        "FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.pdf",
    ),
    (
        "ARQUITECTURA_OPERATIVA_ENTRENAMIENTO_VISIBLE_CITYLEARN_V3_MADRL.md",
        "ARQUITECTURA_OPERATIVA_ENTRENAMIENTO_VISIBLE_CITYLEARN_V3_MADRL.pdf",
    ),
    (
        "COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.md",
        "COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.pdf",
    ),
    (
        "dataset_construction_pipeline.md",
        "DATASET_CONSTRUCTION_PIPELINE.pdf",
    ),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a1a2e;
    max-width: 960px;
    margin: 0 auto;
    padding: 20px 32px 40px 32px;
  }}
  h1 {{ font-size: 1.7em; color: #0f172a; border-bottom: 2px solid #0891b2; padding-bottom: 6px; margin-top: 1.2em; }}
  h2 {{ font-size: 1.3em; color: #1e3a5f; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 1.4em; }}
  h3 {{ font-size: 1.1em; color: #334155; margin-top: 1.2em; }}
  h4 {{ font-size: 1em; color: #475569; margin-top: 1em; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 10pt;
    page-break-inside: avoid;
  }}
  th {{
    background: #1e3a5f;
    color: #ffffff;
    padding: 7px 10px;
    text-align: left;
    font-weight: 600;
  }}
  td {{
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
  }}
  tr:nth-child(even) td {{ background: #f1f5f9; }}
  pre {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    font-size: 9pt;
    page-break-inside: avoid;
  }}
  code {{
    background: #f1f5f9;
    border-radius: 3px;
    padding: 1px 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9.5pt;
  }}
  pre code {{
    background: none;
    padding: 0;
  }}
  .mermaid {{
    background: #fafafa;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 16px;
    margin: 14px 0;
    text-align: center;
    page-break-inside: avoid;
  }}
  blockquote {{
    border-left: 4px solid #0891b2;
    margin: 8px 0;
    padding: 4px 16px;
    color: #475569;
    background: #f0f9ff;
  }}
  hr {{
    border: none;
    border-top: 1px solid #cbd5e1;
    margin: 18px 0;
  }}
  a {{ color: #0369a1; }}
  p {{ margin: 6px 0 10px 0; }}
  ul, ol {{ margin: 6px 0 10px 20px; }}
  li {{ margin: 2px 0; }}
  .status-ok   {{ color: #15803d; font-weight: bold; }}
  .status-run  {{ color: #b45309; font-weight: bold; }}
  .status-pend {{ color: #6b7280; }}
  @media print {{
    body {{ padding: 10px 20px; }}
    h1 {{ page-break-before: auto; }}
    h2 {{ page-break-after: avoid; }}
    table {{ page-break-inside: auto; }}
    tr {{ page-break-inside: avoid; page-break-after: auto; }}
    .mermaid {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
{body}
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose',
    flowchart: {{ curve: 'linear', useMaxWidth: true }},
    sequence: {{ useMaxWidth: true }}
  }});
</script>
</body>
</html>"""


def find_chrome():
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    return None


def extract_mermaid_blocks(md_text):
    """Extrae bloques mermaid del markdown y los reemplaza con placeholders."""
    blocks = []
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

    def replacer(m):
        idx = len(blocks)
        blocks.append(m.group(1).strip())
        return f"MERMAID_PLACEHOLDER_{idx}"

    processed = pattern.sub(replacer, md_text)
    return processed, blocks


def md_to_html_body(md_text):
    """Convierte markdown a HTML con soporte de tablas y mermaid."""
    import markdown as md_lib

    text, mermaid_blocks = extract_mermaid_blocks(md_text)

    html = md_lib.markdown(
        text,
        extensions=["tables", "fenced_code", "toc"],
    )

    for idx, block in enumerate(mermaid_blocks):
        escaped = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        mermaid_div = f'<div class="mermaid">{escaped}</div>'
        html = html.replace(f"<p>MERMAID_PLACEHOLDER_{idx}</p>", mermaid_div)
        html = html.replace(f"MERMAID_PLACEHOLDER_{idx}", mermaid_div)

    return html


def generate_pdf(md_path: Path, pdf_path: Path, chrome_exe: str):
    print(f"  Procesando: {md_path.name}")

    md_text = md_path.read_text(encoding="utf-8")
    title = md_path.stem.replace("_", " ")

    body = md_to_html_body(md_text)
    html_content = HTML_TEMPLATE.format(title=title, body=body)

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False, dir=ARCH_DIR
    ) as f:
        f.write(html_content)
        html_tmp = f.name

    try:
        cmd = [
            chrome_exe,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--run-all-compositor-stages-before-draw",
            "--disable-extensions",
            "--virtual-time-budget=10000",
            f"--print-to-pdf={str(pdf_path.resolve())}",
            f"file:///{html_tmp.replace(chr(92), '/')}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"    ADVERTENCIA Chrome stderr: {result.stderr[:200]}")
        if pdf_path.exists() and pdf_path.stat().st_size > 1000:
            print(f"  OK -> {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)")
            return True
        else:
            print(f"  ERROR: PDF no generado o muy pequeno para {pdf_path.name}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ERROR: timeout al generar {pdf_path.name}")
        return False
    finally:
        try:
            os.unlink(html_tmp)
        except Exception:
            pass


def main():
    chrome = find_chrome()
    if not chrome:
        print("ERROR: Google Chrome no encontrado en rutas esperadas.")
        sys.exit(1)
    print(f"Chrome: {chrome}")

    ok = 0
    fail = 0
    for md_name, pdf_name in FILES:
        md_path = ARCH_DIR / md_name
        pdf_path = ARCH_DIR / pdf_name
        if not md_path.exists():
            print(f"  OMITIDO (no existe): {md_name}")
            continue
        if generate_pdf(md_path, pdf_path, chrome):
            ok += 1
        else:
            fail += 1

    print(f"\nResumen: {ok} PDFs generados, {fail} fallidos.")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
