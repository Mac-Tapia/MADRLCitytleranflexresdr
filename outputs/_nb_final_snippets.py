# -*- coding: utf-8 -*-
"""Extract key cleaned cells for final review."""
import json
from pathlib import Path

nb = json.loads(Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
cells = nb["cells"]
out = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_final_snippets.txt")
parts = []
for i in [1, 32, 33, 40, 41, 42, 49, 53, 62, 67, 71]:
    if i >= len(cells):
        continue
    s = "".join(cells[i].get("source", []))
    parts.append(f"\n{'='*60}\nCELL {i:03d} [{cells[i]['cell_type']}]\n{'='*60}\n")
    # truncate large code cells
    if cells[i]["cell_type"] == "code" and len(s) > 2500:
        lines = s.splitlines()
        # show head + HYPERPARAMS-related + EXECUTION
        head = "\n".join(lines[:45])
        mid = "\n".join(ln for ln in lines if any(k in ln for k in (
            "SCHEMA_PATH", "QUICK_TEST", "N_EPISODES", "EXECUTION_MODE",
            "SIX_JOB_MASAC_BUF", "replay_buffer_size", "n_rollout_threads",
            "SIX_JOB_MATD3", "SIX_JOB_MAAC", "HAPPO_KPI_MODE"
        )))
        parts.append(head + "\n...\n" + mid + "\n...")
    else:
        parts.append(s)
out.write_text("".join(parts), encoding="utf-8")
print(f"wrote {out} cells={len(cells)}")
