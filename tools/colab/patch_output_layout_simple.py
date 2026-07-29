"""Patch Colab tutorial notebook paths to the simple output layout."""
from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK = Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb")

REPLACEMENTS = [
    ("{algo}/E{1,2,3}_seed_0/", "{MADRL}/E{1,2,3}/"),
    ("happo/E1_seed_0/data/results.json", "HAPPO/E1/data/results.json"),
    ("happo/E1_seed_0/data/timeseries.csv", "HAPPO/E1/data/timeseries.csv"),
    ("happo/E1_seed_0/checkpoints/ep_*.pt", "HAPPO/E1/checkpoints/models/*.pt"),
    ("happo/E1_seed_0/figures/*.png", "HAPPO/E1/figures/*.png"),
    ("masac/E1_seed_0/...", "MASAC/E1/..."),
    ("matd3/E1_seed_0/...", "MATD3/E1/..."),
    ("maac/E1_seed_0/...", "MAAC/E1/..."),
    ("outputs/<ts>/<algo>/<Escenario>_seed_0/", "outputs/<ts>/<MADRL>/<Escenario>/"),
    ("f'{esc}_seed_0'", "f'{esc}'"),
    ("f\"{sc}_seed_0\"", "f\"{sc}\""),
    ("f'{sc_short}_seed_{_seed}'", "f'{sc_short}'"),
    ("f'{scenario}_seed_0'", "f'{scenario}'"),
    ("{OUTPUT_ROOT}/{algo}/{scenario}_seed_0/", "{OUTPUT_ROOT}/{MADRL}/{scenario}/"),
    ("algo.lower() / f'{esc}_seed_0'", "algo.upper() / f'{esc}'"),
    ("out / algo / f'{scen}_seed_0'", "out / algo.upper() / f'{scen}'"),
    ("out / algo.lower() / f'{sc_short}_seed_{_seed}'", "out / algo.upper() / f'{sc_short}'"),
    ("assert parts[1] in {f'{sc}_seed_{SEED}' for sc in SCENARIOS}",
     "assert parts[1] in set(SCENARIOS)"),
    ("SCENARIO_MAP = {'E1': 'escenario_1', 'E2': 'escenario_2', 'E3': 'escenario_3'}",
     "SCENARIO_MAP = {'E1': 'E1', 'E2': 'E2', 'E3': 'E3'}"),
    ("# El launcher escribe: {OUTPUT_ROOT}/happo/E1_seed_0/data/results.json",
     "# Layout simple: {OUTPUT_ROOT}/HAPPO/E1/data/results.json"),
    ("# Formato requerido:   {OUTPUT_ROOT}/HAPPO/escenario_1/metrics.csv  etc.",
     "# Export opcional:     {OUTPUT_ROOT}/HAPPO/E1/metrics.csv  etc."),
    ("E1_seed_0 / E2_seed_0 / E3_seed_0 /", "E1 / E2 / E3 /"),
    ("_required_scenarios = ['escenario_1', 'escenario_2', 'escenario_3']",
     "_required_scenarios = ['E1', 'E2', 'E3']"),
    ("escenario_1/  metrics.csv", "E1/  metrics.csv"),
    ("(`happo/E1_seed_0/data/`) al formato canónico",
     "(`HAPPO/E1/data/`) con nombres simples"),
    ("# Layout algorithm-first: {output_root}/{algo}/{scenario}_seed_0/data/results.json",
     "# Layout simple: {output_root}/{MADRL}/{scenario}/data/results.json"),
]


def main() -> None:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    changed = 0
    for cell in nb.get("cells", []):
        src = cell.get("source", [])
        if not src:
            continue
        text = "".join(src)
        new_text = text
        for old, new in REPLACEMENTS:
            if old in new_text:
                new_text = new_text.replace(old, new)
        if new_text != text:
            cell["source"] = [line + ("\n" if not line.endswith("\n") else "") for line in new_text.splitlines()]
            if cell["source"] and not cell["source"][-1].endswith("\n"):
                cell["source"][-1] += "\n"
            changed += 1
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Patched {changed} cells in {NOTEBOOK}")


if __name__ == "__main__":
    main()
