"""Benchmark CityLearn v2 + comparacion vs MADRL seleccionados (notebook 7.6 / compare script)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN_ID = "madrl_v3_20260627_164047"
V3_ROOT = REPO / "outputs" / RUN_ID
V2_ROOT = REPO / "outputs" / "citylearn_v2_original_benchmark"
OUT_ROOT = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "citylearn_v2_baseline"
VENV_PY = REPO / ".venv39-citylearn-v3" / "Scripts" / "python.exe"
BENCH = REPO / "CityLearn" / "scripts" / "benchmark_citylearn_v2_agents.py"
COMPARE = REPO / "CityLearn" / "scripts" / "compare_citylearn_v2_vs_v3_madrl.py"
SELECTED_ALGOS = ("MATD3", "MAAC", "MASAC")
V2_AGENTS = ("baseline", "hour_rbc")
SCENARIOS = ("E1", "E2", "E3")


def run_benchmark(scenario: str) -> None:
    cmd = [
        str(VENV_PY),
        str(BENCH),
        "--scenario",
        scenario,
        "--seed",
        "0",
        "--agents",
        *V2_AGENTS,
        "--output-dir",
        str(V2_ROOT),
        "--continue-on-error",
    ]
    print(f"[benchmark v2] {scenario} ...")
    subprocess.run(cmd, cwd=str(REPO), check=True)


def run_compare(scenario: str) -> Path:
    out_dir = OUT_ROOT / scenario
    cmd = [
        str(VENV_PY),
        str(COMPARE),
        "--v2-root",
        str(V2_ROOT),
        "--v3-root",
        str(V3_ROOT),
        "--output-dir",
        str(out_dir),
        "--scenario",
        scenario,
        "--seed",
        "0",
        "--v3-algorithms",
        *SELECTED_ALGOS,
    ]
    print(f"[compare] {scenario} -> {out_dir}")
    subprocess.run(cmd, cwd=str(REPO), check=True)
    return out_dir


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    summaries = []
    for scen in SCENARIOS:
        run_benchmark(scen)
        out = run_compare(scen)
        summary_path = out / "comparison_summary.json"
        if summary_path.is_file():
            summaries.append(json.loads(summary_path.read_text(encoding="utf-8")))

    manifest = {
        "run_id": RUN_ID,
        "v2_root": str(V2_ROOT),
        "v3_root": str(V3_ROOT),
        "v2_agents": list(V2_AGENTS),
        "v3_selected_algorithms": list(SELECTED_ALGOS),
        "scenarios": list(SCENARIOS),
        "outputs": [str(OUT_ROOT / s) for s in SCENARIOS],
        "summaries": summaries,
    }
    manifest_path = OUT_ROOT / "baseline_comparison_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"OK -> {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
