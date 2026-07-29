"""
embed_mermaid_svgs.py
Fetches SVGs from mermaid.ink for all 9 diagram cells in the tutorial notebook
and embeds them as pre-rendered outputs so they appear without re-running the notebook.
Also rewrites the render_mermaid helper (cell 5) to use mermaid.ink + CDN fallback.
"""
import json, re, base64, urllib.request, time, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb"
BACKUP_PATH = NOTEBOOK_PATH.with_suffix(".ipynb.bak")

# ── New render_mermaid helper (cell 5 replacement) ─────────────────────────
NEW_HELPER_SOURCE = '''\
# ── 0.0  Helper Mermaid — renderiza los 9 diagramas de arquitectura ──────────
# Estrategia: mermaid.ink API (SVG estatico guardado en notebook) con fallback CDN
import json, base64, urllib.request
from IPython.display import display, HTML

_diagram_idx = [0]

def render_mermaid(title, code, height=520):
    """Renderiza diagrama Mermaid via mermaid.ink (estatico) o CDN (fallback)."""
    _diagram_idx[0] += 1
    uid = f"mmd_{_diagram_idx[0]}"

    # ── Intento 1: mermaid.ink API → SVG embebido en el output (offline despues) ──
    try:
        encoded = base64.urlsafe_b64encode(code.strip().encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/svg/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            svg = resp.read().decode("utf-8")
        html = f"""<div style="margin:16px 0;border:1px solid #e2e8f0;border-radius:10px;
padding:20px;background:#f8fafc;font-family:sans-serif;">
  <h4 style="margin:0 0 14px 0;color:#0f172a;font-size:14px;">{title}</h4>
  <div style="overflow:auto;max-height:{height + 80}px;">{svg}</div>
</div>"""
        display(HTML(html))
        return
    except Exception as _e:
        pass  # fallback below

    # ── Intento 2: CDN Mermaid@10 (requiere JS habilitado en el navegador) ──────
    code_js = json.dumps(code, ensure_ascii=False)
    html = f"""<div style="margin:16px 0;border:1px solid #e2e8f0;border-radius:10px;
padding:20px;background:#f8fafc;font-family:sans-serif;">
  <h4 style="margin:0 0 14px 0;color:#0f172a;font-size:14px;">{title}</h4>
  <div id="{uid}" style="min-height:{height}px;"></div>
  <script>
  (function(){{
    var el=document.getElementById("{uid}");
    el.textContent={code_js};
    el.className="mermaid";
    function tryR(){{
      if(window._mermaidReady&&typeof mermaid!=="undefined"){{
        try{{mermaid.run({{nodes:[el]}});}}catch(e){{console.error(e);}}
      }}else{{
        if(!window._mermaidCDNLoading){{
          window._mermaidCDNLoading=true;
          var s=document.createElement("script");
          s.src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
          s.onload=function(){{mermaid.initialize({{startOnLoad:false,theme:"default",securityLevel:"loose"}});window._mermaidReady=true;}};
          document.head.appendChild(s);
        }}
        setTimeout(tryR,400);
      }}
    }}
    tryR();
  }})();
  </script>
</div>"""
    display(HTML(html))

print("✅  Helper Mermaid listo (mermaid.ink + CDN fallback). Ejecuta celdas 0.1-0.9.")
'''


def fetch_svg(code: str, retries: int = 3) -> str:
    encoded = base64.urlsafe_b64encode(code.strip().encode("utf-8")).decode("utf-8")
    url = f"https://mermaid.ink/svg/{encoded}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            if attempt < retries - 1:
                print(f"  Retry {attempt+1}/{retries}: {e}")
                time.sleep(2)
            else:
                raise


def make_html_output(title: str, svg: str, height: int = 520) -> dict:
    html = (
        f'<div style="margin:16px 0;border:1px solid #e2e8f0;border-radius:10px;'
        f'padding:20px;background:#f8fafc;font-family:sans-serif;">'
        f'<h4 style="margin:0 0 14px 0;color:#0f172a;font-size:14px;">{title}</h4>'
        f'<div style="overflow:auto;max-height:{height+80}px;">{svg}</div>'
        f'</div>'
    )
    return {
        "output_type": "display_data",
        "data": {
            "text/html": [html],
            "text/plain": ["<IPython.core.display.HTML object>"]
        },
        "metadata": {}
    }


def main():
    print(f"Loading: {NOTEBOOK_PATH}")
    nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # ── Backup ────────────────────────────────────────────────────────────────
    BACKUP_PATH.write_text(
        json.dumps(nb, ensure_ascii=False, indent=1),
        encoding="utf-8"
    )
    print(f"Backup saved: {BACKUP_PATH.name}")

    # ── Rewrite cell 5: render_mermaid helper ────────────────────────────────
    cells[5]["source"] = [NEW_HELPER_SOURCE]
    cells[5]["outputs"] = [
        {
            "output_type": "stream",
            "name": "stdout",
            "text": ["✅  Helper Mermaid listo (mermaid.ink + CDN fallback). Ejecuta celdas 0.1-0.9.\n"]
        }
    ]
    cells[5]["execution_count"] = 1
    print("Cell 5: helper reescrito.")

    # ── Process diagram cells 6-14 ───────────────────────────────────────────
    exec_count = 2
    for cell_idx in range(6, 15):
        src = "".join(cells[cell_idx]["source"])
        match = re.search(
            r'render_mermaid\((".*?"),\s*r"""(.+?)"""\s*(?:,\s*height=(\d+))?\)',
            src, re.DOTALL
        )
        if not match:
            print(f"Cell {cell_idx}: no match, skipping.")
            continue

        title_raw = match.group(1).strip().strip('"')
        code = match.group(2).strip()
        height = int(match.group(3)) if match.group(3) else 520

        print(f"Cell {cell_idx}: fetching SVG for '{title_raw[:55]}'...", end=" ", flush=True)
        try:
            svg = fetch_svg(code)
            print(f"OK ({len(svg)} chars)")
        except Exception as e:
            print(f"FAILED ({e}) — skipping output for this cell")
            cells[cell_idx]["execution_count"] = exec_count
            exec_count += 1
            continue

        cells[cell_idx]["outputs"] = [make_html_output(title_raw, svg, height)]
        cells[cell_idx]["execution_count"] = exec_count
        exec_count += 1
        time.sleep(0.5)  # be polite to mermaid.ink

    # ── Save updated notebook ─────────────────────────────────────────────────
    NOTEBOOK_PATH.write_text(
        json.dumps(nb, ensure_ascii=False, indent=1),
        encoding="utf-8"
    )
    print(f"\n✅  Notebook guardado: {NOTEBOOK_PATH.name}")
    print("Abre el notebook en Jupyter/VS Code — los diagramas 1-9 ya son visibles.")


if __name__ == "__main__":
    main()
