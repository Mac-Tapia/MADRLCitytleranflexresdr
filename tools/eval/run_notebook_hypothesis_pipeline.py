"""Pipeline notebook → evidencia OE + Capa A (HE/H0G) desde un OUTPUT_ROOT.

Orquesta:
1) ``generate_thesis_objective_evidence.py`` → scores KPI vs baseline evaluate_v2
2) tablas auxiliares (scenario_scores / descriptivo mínimo)
3) ``run_problem_objective_hypothesis_statistical_analysis.py`` →
   ``resumen_comparativo/estadistica/problemas_objetivos_hipotesis/``

Uso (desde notebook o CLI)::

    python tools/eval/run_notebook_hypothesis_pipeline.py \\
        --output-root outputs/madrl_v3_YYYYMMDD_HHMMSS \\
        --seed 0
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
EVIDENCE_SCRIPT = REPO / "CityLearn" / "scripts" / "generate_thesis_objective_evidence.py"
CAPA_A_SCRIPT = (
    REPO / "tools" / "eval" / "run_problem_objective_hypothesis_statistical_analysis.py"
)


def _resolve_python() -> str:
    candidates = [
        REPO / ".venv39-citylearn-v3" / "Scripts" / "python.exe",
        REPO / ".venv39-citylearn-v3" / "bin" / "python",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return sys.executable


def _run_evidence(output_root: Path, stats_dir: Path, seed: int, python_bin: str) -> None:
    stats_dir.mkdir(parents=True, exist_ok=True)
    rel_out = stats_dir.relative_to(REPO).as_posix()
    cmd = [
        python_bin,
        "-B",
        str(EVIDENCE_SCRIPT),
        f"--output-root=notebook={output_root}",
        f"--output-dir={rel_out}",
        f"--seed={int(seed)}",
    ]
    subprocess.run(cmd, cwd=str(REPO), check=True)


def _ensure_scenario_scores(stats_dir: Path) -> Path:
    path = stats_dir / "scenario_scores_colab.csv"
    if path.is_file() and path.stat().st_size > 0:
        return path

    scores_path = stats_dir / "scores_kpi_algoritmo_madrl.csv"
    if not scores_path.is_file():
        raise FileNotFoundError(scores_path)

    df = pd.read_csv(scores_path)
    # Cap A filtra OE.k ↔ Ek; el score de escenario = media signed_relative_gain
    # en el eje emparejado (misma unidad que ranking OE del notebook).
    axis_to_scen = {"OE1": "E1", "OE2": "E2", "OE3": "E3"}
    rows: list[dict] = []
    for axis, scen in axis_to_scen.items():
        sub = df[(df["axis"] == axis) & (df["scenario"] == scen)].copy()
        if sub.empty:
            continue
        for algo, grp in sub.groupby("algorithm"):
            vals = pd.to_numeric(grp["signed_relative_gain"], errors="coerce").dropna()
            if vals.empty:
                continue
            rows.append(
                {
                    "algorithm": str(algo),
                    "scenario": scen,
                    "scenario_score": round(float(vals.mean()), 6),
                }
            )
    if not rows:
        raise RuntimeError(
            "No se pudieron derivar scenario_scores desde scores_kpi_algoritmo_madrl.csv"
        )
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["algorithm", "scenario", "scenario_score"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def _ensure_descriptivo(stats_dir: Path) -> Path:
    path = stats_dir / "descriptivo_distrito_colab.csv"
    if path.is_file() and path.stat().st_size > 0:
        return path

    # Contexto mínimo: Cap A solo lo copia; no fundamenta HE.
    scores_path = stats_dir / "scores_kpi_algoritmo_madrl.csv"
    df = pd.read_csv(scores_path)
    rows: list[dict] = []
    for (algo, scen), grp in df.groupby(["algorithm", "scenario"]):
        vals = pd.to_numeric(grp["signed_relative_gain"], errors="coerce").dropna()
        if vals.empty:
            continue
        rows.append(
            {
                "algorithm": algo,
                "scenario": scen,
                "metric": "signed_relative_gain_mean",
                "n": int(len(vals)),
                "mean": float(vals.mean()),
                "median": float(vals.median()),
                "std": float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                "min": float(vals.min()),
                "max": float(vals.max()),
                "note": "derived_from_kpi_gains_notebook_pipeline",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "algorithm",
                "scenario",
                "metric",
                "n",
                "mean",
                "median",
                "std",
                "min",
                "max",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def _run_capa_a(output_root: Path, python_bin: str) -> Path:
    cmd = [
        python_bin,
        "-B",
        str(CAPA_A_SCRIPT),
        f"--run-root={output_root}",
    ]
    subprocess.run(cmd, cwd=str(REPO), check=True)
    return (
        output_root
        / "resumen_comparativo"
        / "estadistica"
        / "problemas_objetivos_hipotesis"
    )


def _write_pe_answers_stub(capa_dir: Path, output_root: Path) -> Path:
    """Resumen PE/OE/HE legible desde decisiones Capa A (sin acoplar thesis_doctoral)."""
    decisions_csv = capa_dir / "decisiones_problemas_objetivos_hipotesis.csv"
    if not decisions_csv.is_file():
        raise FileNotFoundError(decisions_csv)
    decisions = pd.read_csv(decisions_csv)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": output_root.name,
        "verdict": "structured_from_capa_a",
        "source": str(decisions_csv),
        "protocol": (
            "Shapiro → Friedman+Kendall W + Wilcoxon/Holm (principal); "
            "Kruskal-Wallis / Mann-Whitney exploratorio"
        ),
        "answers": {},
    }
    scope_map = {
        "OE1": "PE.1",
        "OE2": "PE.2",
        "OE3": "PE.3",
        "GLOBAL": "PG",
    }
    for _, row in decisions.iterrows():
        scope = str(row.get("scope", ""))
        pe_id = scope_map.get(scope, scope)
        payload["answers"][pe_id] = {
            "scope": scope,
            "problem": row.get("problem"),
            "objective": row.get("objective"),
            "null_hypothesis": row.get("null_hypothesis"),
            "alternative_hypothesis": row.get("alternative_hypothesis"),
            "descriptive_best_algorithm": row.get("descriptive_best_algorithm"),
            "friedman_p": row.get("friedman_p"),
            "kruskal_p": row.get("kruskal_p"),
            "hypothesis_decision": row.get("hypothesis_decision"),
            "objective_compliance": row.get("objective_compliance"),
            "coverage_limitation": row.get("coverage_limitation"),
        }
    out = (
        output_root
        / "resumen_comparativo"
        / "estadistica"
        / "pe_answers_audit.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def run_pipeline(output_root: Path, seed: int = 0, skip_evidence: bool = False) -> dict:
    output_root = output_root.resolve()
    if not output_root.is_dir():
        raise FileNotFoundError(f"OUTPUT_ROOT no existe: {output_root}")

    stats_dir = output_root / "resumen_comparativo" / "estadistica"
    python_bin = _resolve_python()

    if not skip_evidence:
        _run_evidence(output_root, stats_dir, seed=seed, python_bin=python_bin)

    scores = stats_dir / "scores_kpi_algoritmo_madrl.csv"
    if not scores.is_file():
        raise FileNotFoundError(
            f"Falta {scores}. Ejecuta generate_thesis_objective_evidence o quita --skip-evidence."
        )

    scenario_scores = _ensure_scenario_scores(stats_dir)
    descriptivo = _ensure_descriptivo(stats_dir)
    capa_dir = _run_capa_a(output_root, python_bin=python_bin)
    pe_answers = _write_pe_answers_stub(capa_dir, output_root)

    summary = {
        "output_root": str(output_root),
        "stats_dir": str(stats_dir),
        "scores_csv": str(scores),
        "scenario_scores_csv": str(scenario_scores),
        "descriptivo_csv": str(descriptivo),
        "capa_a_dir": str(capa_dir),
        "pe_answers_audit": str(pe_answers),
        "decisions_csv": str(capa_dir / "decisiones_problemas_objetivos_hipotesis.csv"),
        "seed": int(seed),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = stats_dir / "notebook_hypothesis_pipeline_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary["summary_json"] = str(summary_path)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera evidencia OE + Capa A HE/H0G desde un OUTPUT_ROOT MADRL."
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Ruta al run (p.ej. outputs/madrl_v3_YYYYMMDD_HHMMSS)",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--skip-evidence",
        action="store_true",
        help="Reutiliza scores_kpi_algoritmo_madrl.csv ya generado en estadistica/",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.output_root)
    if not root.is_absolute():
        root = (REPO / root).resolve()
    summary = run_pipeline(root, seed=int(args.seed), skip_evidence=bool(args.skip_evidence))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
