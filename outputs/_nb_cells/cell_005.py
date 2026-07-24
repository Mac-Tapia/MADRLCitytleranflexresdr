# ── 0.0  Helper Mermaid — renderiza los 9 diagramas de arquitectura ──────────
# Estrategia: mermaid.ink API (SVG estatico guardado en notebook) con fallback CDN
import json
import base64
import urllib.request
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
