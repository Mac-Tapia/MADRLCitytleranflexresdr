"""Clear stale outputs and apply canonical text fixes to the Colab tutorial notebook."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "CityLearn" / "examples" / "madrl_citylearn_v3_tutorial.ipynb"

REPLACEMENTS = [
    (
        "| Ejecucion | Secuencial, recuperable, con monitor visible y reintento OOM |",
        "| Ejecucion | two_phase_happo_masac (6+6 paralelo), recuperable, monitor y reintento OOM |",
    ),
    (
        "# 2. RAM — hard fail en Colab si < 60 GiB; advertencia local",
        "# 2. RAM — hard fail en Colab si < 120 GiB (A100 High-RAM); advertencia local",
    ),
    (
        "Re-ejecuta 1.2 (git reset --hard) o espera sync GitHub.",
        "Re-ejecuta celda 1.2 (checkout -B CityLearn) o espera sync GitHub.",
    ),
    (
        "Ejecuta celda 1.2 (git reset --hard) y re-ejecuta 6.1 -> 7.0 -> 7.1.",
        "Ejecuta celda 1.2 (checkout -B CityLearn) y re-ejecuta 6.1 -> 7.0 -> 7.1.",
    ),
    (
        "Ejecuta celda 1.2 (hard reset).",
        "Ejecuta celda 1.2 (checkout -B CityLearn).",
    ),
    (
        "#   CityLearn        → github.com/Mac-Tapia/CityLearn           (codex/iquitos-distillation-madrl-docs)",
        "#   CityLearn        → Mac-Tapia/CityLearn (Colab rama viva: codex/iquitos-distillation-madrl-docs; .gitmodules pin: citylearn-v3-madrl)",
    ),
]


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cleared = 0
    fixed = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            if cell.get("execution_count") is not None or cell.get("outputs"):
                cell["execution_count"] = None
                cell["outputs"] = []
                cleared += 1
        src = cell.get("source", [])
        if isinstance(src, str):
            src = [src]
        new_src = []
        for line in src:
            new_line = line
            for old, new in REPLACEMENTS:
                if old in new_line:
                    new_line = new_line.replace(old, new)
                    fixed += 1
            new_src.append(new_line)
        cell["source"] = new_src

    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[OK] {NB_PATH.relative_to(ROOT)}")
    print(f"     cells={len(nb['cells'])} cleared_outputs={cleared} text_fixes={fixed}")


if __name__ == "__main__":
    main()
