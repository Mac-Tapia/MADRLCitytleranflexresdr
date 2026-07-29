#!/usr/bin/env python3
"""Sync Mermaid diagrams from ARQUITECTURA_PROYECTO_DEFENSA.md into the Colab notebook."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "docs" / "architecture" / "ARQUITECTURA_PROYECTO_DEFENSA.md"
NB = ROOT / "CityLearn" / "examples" / "madrl_citylearn_v3_tutorial.ipynb"
MMD_DIR = ROOT / "outputs" / "defensa_pdf" / "mmd"

DIAGRAM_TITLES = [
    "Diagrama 1 — Vision General del Proyecto (inicio a fin)",
    "Diagrama 2 — Pipeline del Dataset Iquitos 2023-2025",
    "Diagrama 3 — Arquitectura Dec-POMDP y CTDE de los 17 Agentes",
    "Diagrama 4 — Los 4 Algoritmos MADRL: Taxonomia y Diferencias",
    "Diagrama 5 — Flujo de Entrenamiento: 12 Corridas (two_phase_happo_masac_v3)",
    "Diagrama 6 — Recompensa Multiobjetivo por Escenario",
    "Diagrama 7 — Pipeline de Evaluacion y Seleccion del Mejor MADRL",
    "Diagrama 8 — Infraestructura de Despliegue: Local, Colab A100 y AWS EC2",
    "Diagrama 9 — Estructura de Capas del Software",
]

HEIGHTS = [520, 700, 720, 640, 780, 620, 700, 720, 700]


def extract_mermaid_blocks(md_text: str) -> list[str]:
    blocks = re.findall(r"```mermaid\n(.*?)```", md_text, flags=re.DOTALL)
    if len(blocks) != 9:
        raise RuntimeError(f"Expected 9 mermaid blocks, found {len(blocks)}")
    return [b.strip() for b in blocks]


def build_cell_source(title: str, code: str, height: int, idx: int) -> list[str]:
    lines = [
        f"# ── 0.{idx}  {title.split(' — ', 1)[0]} ────────────────────────────────────────\n",
        f'render_mermaid("{title}", r"""\n',
        code + "\n",
        f'""", height={height})\n',
    ]
    return lines


def sync_notebook(blocks: list[str]) -> None:
    nb = json.loads(NB.read_text(encoding="utf-8"))
    cell_indices = []
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "render_mermaid(" in src and "Diagrama " in src:
            cell_indices.append(i)
    if len(cell_indices) != 9:
        raise RuntimeError(f"Expected 9 diagram cells in notebook, found {len(cell_indices)}")
    for n, (ci, block) in enumerate(zip(cell_indices, blocks), start=1):
        title = DIAGRAM_TITLES[n - 1]
        nb["cells"][ci]["source"] = build_cell_source(title, block, HEIGHTS[n - 1], n)
        nb["cells"][ci]["outputs"] = []
        nb["cells"][ci]["execution_count"] = None
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Updated notebook: {NB} ({len(cell_indices)} diagram cells)")


def write_mmd_files(blocks: list[str]) -> None:
    MMD_DIR.mkdir(parents=True, exist_ok=True)
    for i, block in enumerate(blocks, start=1):
        path = MMD_DIR / f"diagram_{i:02d}.mmd"
        path.write_text(block + "\n", encoding="utf-8")
        print(f"  [{i:02d}] {path}")


def main() -> int:
    if not MD.is_file():
        print(f"Missing {MD}", file=sys.stderr)
        return 1
    blocks = extract_mermaid_blocks(MD.read_text(encoding="utf-8"))
    write_mmd_files(blocks)
    sync_notebook(blocks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
