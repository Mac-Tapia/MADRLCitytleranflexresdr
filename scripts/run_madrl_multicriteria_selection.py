#!/usr/bin/env python
"""CLI demo for the multicriteria MADRL selection methodology.

Usage (from repo root, with project venv):

    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_multicriteria_selection.py
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_multicriteria_selection.py --illustrative-only
    .\\.venv39-citylearn-v3\\Scripts\\python.exe scripts\\run_madrl_multicriteria_selection.py --plots
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Optional MADRL outputs run directory with resumen_comparativo/",
    )
    parser.add_argument(
        "--scenario",
        default="E1",
        help="Scenario label used when mapping district OE KPIs (default: E1)",
    )
    parser.add_argument(
        "--illustrative-only",
        action="store_true",
        help="Ignore real artefacts and use the methodology illustrative matrix",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO / "outputs" / "madrl_multicriteria_selection",
        help="Directory for CSV/JSON/figure artefacts",
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Generate learning-curve / Pareto / degradation figures",
    )
    parser.add_argument(
        "--sensitivity-samples",
        type=int,
        default=48,
        help="Weight-sweep samples for ±20%% sensitivity",
    )
    args = parser.parse_args(argv)

    from uc3m.multicriteria.pipeline import run_selection_pipeline

    result = run_selection_pipeline(
        repo=REPO,
        run_dir=args.run_dir,
        scenario=args.scenario,
        prefer_real=not args.illustrative_only,
        output_dir=args.output_dir,
        make_plots=args.plots,
        sensitivity_samples=args.sensitivity_samples,
    )

    ranking = result["topsis"]["ranking"]
    print("=== Multicriteria MADRL selection (TOPSIS + AHP) ===")
    print(f"source: {result['source']}")
    print(f"AHP CR: {result['ahp']['consistency_ratio']:.4f} "
          f"(consistent={result['ahp']['consistent']})")
    print("weights:", json.dumps(result["weights"], indent=2))
    print("\nTOPSIS ranking:")
    for row in ranking:
        print(
            f"  #{row['rank']} {row['algorithm']:<6}  "
            f"C*={row['closeness']:.4f}  "
            f"D+={row['distance_positive']:.4f}  D-={row['distance_negative']:.4f}"
        )
    print("\nConsistency checks:")
    for key, value in result["ranking_consistency"].items():
        print(f"  {key}: {value}")
    if result.get("stats"):
        gate = result["stats"].get("significance_gate", {})
        print(
            f"\nSignificance gate (C1/C2, 1st vs 2nd): "
            f"defensible={gate.get('defensible')}"
        )
    print(f"\nArtefacts: {args.output_dir}")
    for name, path in result.get("saved_paths", {}).items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
