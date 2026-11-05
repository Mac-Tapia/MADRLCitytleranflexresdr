#!/usr/bin/env python
"""Aggregate multi-seed MADRL KPIs (unit = seed) and bridge to stats batteries.

Scans a campaign ``output_root`` for completed jobs under
``{ALGO}/{E}`` (seed 0) and ``{ALGO}/{E}_sk`` (seed k>0), extracts a primary
score per (algorithm, scenario, seed), and writes:

  - ``seed_level_scores.csv``          (long table; sample_unit=seed)
  - ``seed_coverage_manifest.json``    (coverage vs expected N_SEEDS)
  - ``seed_level_battery_bridge.csv``  (optional; wide metrics for nonparametric battery)
  - optional call into ``scripts/run_madrl_nonparametric_battery.py``
  - optional seed-unit POH under ``.../problemas_objetivos_hipotesis_seed/``

``seed_level_scores.csv`` columns:
  algorithm, scenario, seed, sample_unit, results_path, score, score_source,
  has_kpis, status

Does **not** invent scores: missing jobs are reported as incomplete coverage
(empty/temp roots still write CSV + manifest with ``has_kpis=False``).

Usage (repo root)::

  python tools/eval/aggregate_multiseed_seed_kpis.py \\
      --output-root outputs/_tmp_multiseed_dryrun --n-seeds 12
  python tools/eval/aggregate_multiseed_seed_kpis.py \\
      --output-root outputs/madrl_v3_multiseed --n-seeds 12 --write-seed-poh
  python tools/eval/aggregate_multiseed_seed_kpis.py \\
      --output-root outputs/madrl_v3_multiseed --n-seeds 12 \\
      --run-nonparametric-battery

Nonparametric battery notes:
  - Prefer ``--run-root`` after training (reads ``results.json``; supports
    ``E`` / ``E_sk`` / legacy ``E_seed_k`` layouts via this aggregator bridge).
  - Battery ``--episodes-csv`` needs ``algorithm,scenario,seed`` plus metric
    columns ``reward_mean`` (E1), ``district_emission`` (E2), ``district_cost``
    (E3). This script writes ``seed_level_battery_bridge.csv`` in that shape
    from real scores only (blank metric cells when missing — never fabricated).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
SCRIPTS = REPO / "CityLearn" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from citylearn_v3_training_common import (  # noqa: E402
    iter_job_run_dir_candidates,
    normalize_algorithm_dir,
)

ALGORITHMS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")
N_SEEDS_DEFAULT = 12

# Scenario → preferred numeric keys in results.json / project_axis_metrics.
SCENARIO_SCORE_KEYS: Dict[str, Tuple[str, ...]] = {
    "E1": ("OE1", "flex_score", "flexibility_score", "reward_mean", "score"),
    "E2": ("OE2", "carbon_score", "emission_score", "district_emission", "score"),
    "E3": ("OE3", "cost_score", "district_cost", "score"),
}


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _finite(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def _extract_score(results: Dict[str, Any], scenario: str) -> Tuple[Optional[float], str]:
    scen = scenario.upper()
    keys = SCENARIO_SCORE_KEYS.get(scen, ("score",))
    candidates: List[Tuple[str, Any]] = []

    pam = results.get("project_axis_metrics") or results.get("axis_metrics") or {}
    if isinstance(pam, dict):
        for k in keys:
            if k in pam:
                candidates.append((f"project_axis_metrics.{k}", pam[k]))

    kpis = results.get("kpis") or results.get("all_values") or {}
    if isinstance(kpis, dict):
        for k in keys:
            if k in kpis:
                candidates.append((f"kpis.{k}", kpis[k]))

    for k in keys:
        if k in results:
            candidates.append((k, results[k]))

    nested = results.get("summary") or {}
    if isinstance(nested, dict):
        for k in keys:
            if k in nested:
                candidates.append((f"summary.{k}", nested[k]))

    for label, raw in candidates:
        val = raw
        if isinstance(raw, dict):
            for nested_key in ("value", "mean", "median", "score"):
                if nested_key in raw:
                    val = raw[nested_key]
                    break
        num = _finite(val)
        if num is not None:
            return num, label
    return None, ""


def _job_results_path(output_root: Path, algorithm: str, scenario: str, seed: int) -> Optional[Path]:
    for cand in iter_job_run_dir_candidates(output_root, algorithm, scenario, seed):
        for rel in ("data/results.json", "results.json"):
            path = cand / rel
            if path.is_file():
                return path
    return None


def collect_seed_scores(
    output_root: Path,
    *,
    seeds: Sequence[int],
    algorithms: Sequence[str] = ALGORITHMS,
    scenarios: Sequence[str] = SCENARIOS,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        for algo in algorithms:
            for scen in scenarios:
                path = _job_results_path(output_root, algo, scen, int(seed))
                row: Dict[str, Any] = {
                    "algorithm": normalize_algorithm_dir(algo),
                    "scenario": scen.upper(),
                    "seed": int(seed),
                    "sample_unit": "seed",
                    "results_path": str(path) if path else "",
                    "score": "",
                    "score_source": "",
                    "has_kpis": False,
                    "status": "missing",
                }
                if path is None:
                    rows.append(row)
                    continue
                payload = _read_json(path)
                score, source = _extract_score(payload, scen)
                row["status"] = str(payload.get("status") or "present")
                row["has_kpis"] = score is not None
                if score is not None:
                    row["score"] = score
                    row["score_source"] = source
                rows.append(row)
    return rows


def coverage_report(rows: List[Dict[str, Any]], expected_n_seeds: int) -> Dict[str, Any]:
    by_key: Dict[str, List[int]] = {}
    for row in rows:
        if not row.get("has_kpis"):
            continue
        key = f"{row['algorithm']}|{row['scenario']}"
        by_key.setdefault(key, []).append(int(row["seed"]))
    coverage = {}
    complete = True
    for algo in ALGORITHMS:
        for scen in SCENARIOS:
            key = f"{normalize_algorithm_dir(algo)}|{scen}"
            seeds = sorted(set(by_key.get(key, [])))
            ok = len(seeds) >= int(expected_n_seeds)
            if not ok:
                complete = False
            coverage[key] = {
                "n": len(seeds),
                "expected": int(expected_n_seeds),
                "complete": ok,
                "seeds": seeds,
            }
    return {
        "expected_n_seeds": int(expected_n_seeds),
        "sample_unit": "seed",
        "complete": complete,
        "groups": coverage,
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_seed_unit_poh(
    out_dir: Path,
    rows: List[Dict[str, Any]],
    *,
    min_seeds: int = 3,
) -> Dict[str, Any]:
    """Lightweight seed-unit omnibus (Friedman/KW) when >= min_seeds comparable scores.

    Writes a parallel POH folder; does not overwrite KPI-gain Capa A.
    """
    try:
        import numpy as np
        from scipy import stats
    except Exception as exc:  # pragma: no cover
        return {"status": "skipped", "reason": f"scipy/numpy unavailable: {exc}"}

    out_dir.mkdir(parents=True, exist_ok=True)
    usable = [r for r in rows if r.get("has_kpis") and r.get("score") != ""]
    by_scope: Dict[str, Dict[str, List[float]]] = {"E1": {}, "E2": {}, "E3": {}}
    by_seed: Dict[str, Dict[str, Dict[int, float]]] = {"E1": {}, "E2": {}, "E3": {}}
    for row in usable:
        scen = str(row["scenario"]).upper()
        algo = str(row["algorithm"]).upper()
        by_seed.setdefault(scen, {}).setdefault(algo, {})[int(row["seed"])] = float(row["score"])
    for scen, algo_map in by_seed.items():
        # Friedman pairs blocks: keep only seeds measured by every algorithm, in seed order.
        common = set.intersection(*(set(s) for s in algo_map.values())) if algo_map else set()
        by_scope[scen] = {algo: [scores[s] for s in sorted(common)] for algo, scores in algo_map.items()}

    omnibus_rows: List[Dict[str, Any]] = []
    decision_rows: List[Dict[str, Any]] = []
    for scen, algo_map in by_scope.items():
        algos = sorted(algo_map.keys())
        if len(algos) < 2:
            continue
        lengths = [len(algo_map[a]) for a in algos]
        if min(lengths) < int(min_seeds):
            decision_rows.append(
                {
                    "scope": scen.replace("E", "OE") if scen.startswith("E") else scen,
                    "scenario": scen,
                    "sample_unit": "seed",
                    "hypothesis_decision": "cobertura insuficiente (>=3 seeds requeridos)",
                    "n_seeds_min": min(lengths),
                }
            )
            continue
        n = min(lengths)
        groups = [np.asarray(algo_map[a], dtype=float) for a in algos]
        try:
            kw_h, kw_p = stats.kruskal(*groups)
        except Exception:
            kw_h, kw_p = float("nan"), float("nan")
        try:
            fried = stats.friedmanchisquare(*groups)
            fried_chi2, fried_p = float(fried.statistic), float(fried.pvalue)
        except Exception:
            fried_chi2, fried_p = float("nan"), float("nan")
        scope = {"E1": "OE1", "E2": "OE2", "E3": "OE3"}.get(scen, scen)
        for method, stat, p in (
            ("Kruskal-Wallis", kw_h, kw_p),
            ("Friedman", fried_chi2, fried_p),
        ):
            omnibus_rows.append(
                {
                    "scope": scope,
                    "scenario": scen,
                    "method": method,
                    "algorithms": ", ".join(algos),
                    "n_total": n * len(algos),
                    "group_n": json.dumps({a: n for a in algos}),
                    "statistic": stat,
                    "p_value": p,
                    "sample_unit": "seed",
                    "significant": bool(p < 0.05) if p == p else False,
                    "decision": (
                        "se rechaza igualdad global"
                        if (p == p and p < 0.05)
                        else "no se rechaza igualdad global"
                    ),
                }
            )
        medians = {a: float(np.median(algo_map[a][:n])) for a in algos}
        best = max(medians, key=medians.get)
        decision_rows.append(
            {
                "scope": scope,
                "scenario": scen,
                "sample_unit": "seed",
                "descriptive_best_algorithm": best,
                "best_median_gain": medians[best],
                "kruskal_h": kw_h,
                "kruskal_p": kw_p,
                "friedman_chi2": fried_chi2,
                "friedman_p": fried_p,
                "n_seeds": n,
                "hypothesis_decision": (
                    "seed-unit omnibus (exploratorio); no sustituye Capa A KPI-gains "
                    "hasta campaña completa auditada"
                ),
            }
        )

    write_csv(out_dir / "pruebas_omnibus_problemas_objetivos_seed.csv", omnibus_rows)
    write_csv(out_dir / "decisiones_problemas_objetivos_hipotesis_seed.csv", decision_rows)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_unit": "seed",
        "min_seeds": int(min_seeds),
        "note": "Parallel to Capa A KPI-gains; do not mix as HE until campaign complete.",
        "n_omnibus_rows": len(omnibus_rows),
        "n_decision_rows": len(decision_rows),
    }
    (out_dir / "seed_unit_poh_manifest.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, help="Multi-seed campaign root")
    parser.add_argument("--n-seeds", type=int, default=N_SEEDS_DEFAULT)
    parser.add_argument("--seeds", default=None, help="Comma list; default 0..n_seeds-1")
    parser.add_argument("--out-dir", default=None, help="Stats output dir (default: output-root/resumen_comparativo/estadistica)")
    parser.add_argument("--run-nonparametric-battery", action="store_true")
    parser.add_argument("--write-seed-poh", action="store_true")
    parser.add_argument("--min-seeds-for-poh", type=int, default=3)
    args = parser.parse_args(argv)

    output_root = Path(args.output_root).resolve()
    if args.seeds:
        seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    else:
        seeds = list(range(int(args.n_seeds)))

    rows = collect_seed_scores(output_root, seeds=seeds)
    cov = coverage_report(rows, expected_n_seeds=len(seeds))

    out_dir = Path(args.out_dir).resolve() if args.out_dir else (output_root / "resumen_comparativo" / "estadistica")
    out_dir.mkdir(parents=True, exist_ok=True)
    scores_csv = out_dir / "seed_level_scores.csv"
    write_csv(scores_csv, rows)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_root),
        "scores_csv": str(scores_csv),
        "coverage": cov,
        "n_rows": len(rows),
        "n_with_kpis": sum(1 for r in rows if r.get("has_kpis")),
    }
    (out_dir / "seed_coverage_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[seed-agg] wrote {scores_csv} ({manifest['n_with_kpis']}/{manifest['n_rows']} with scores)")
    print(f"[seed-agg] coverage complete={cov['complete']} expected_n_seeds={cov['expected_n_seeds']}")

    if args.write_seed_poh:
        poh_dir = out_dir / "problemas_objetivos_hipotesis_seed"
        meta = write_seed_unit_poh(poh_dir, rows, min_seeds=args.min_seeds_for_poh)
        print(f"[seed-agg] seed-unit POH -> {poh_dir} status={meta.get('status', 'ok')}")

    if args.run_nonparametric_battery:
        battery = REPO / "scripts" / "run_madrl_nonparametric_battery.py"
        cmd = [
            sys.executable,
            str(battery),
            "--run-root",
            str(output_root),
            "--n-seeds",
            str(len(seeds)),
        ]
        print("[seed-agg] invoking", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=str(REPO))
        return int(proc.returncode)

    return 0 if cov["complete"] or manifest["n_with_kpis"] >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
