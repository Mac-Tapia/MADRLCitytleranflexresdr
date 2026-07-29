"""Extract Mermaid code blocks from a Markdown file into .mmd files."""
import re
import sys
from pathlib import Path

def extract(md_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    text = md_path.read_text(encoding="utf-8")
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    matches = pattern.findall(text)
    if not matches:
        print("No mermaid blocks found.")
        return []
    paths = []
    for i, code in enumerate(matches, 1):
        p = out_dir / f"diagram_{i:02d}.mmd"
        p.write_text(code.strip(), encoding="utf-8")
        print(f"  [{i:02d}] {p}")
        paths.append(p)
    print(f"Extracted {len(paths)} diagrams to {out_dir}")
    return paths

if __name__ == "__main__":
    md = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "docs/architecture/ARQUITECTURA_PROYECTO_DEFENSA.md"
    )
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        "outputs/defensa_pdf/mmd"
    )
    extract(md, out)
