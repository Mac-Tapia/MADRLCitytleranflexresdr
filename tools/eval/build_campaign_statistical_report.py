"""Multiseed statistical report of the modular MADRL campaign (SPEC-005 FR-005.5).

Inputs
    Verified runs found by ``uc3m.application.evaluation.results_catalog``
    (``--results-root``, then ``MADRL_RESULTS_ROOT``, then ``outputs/campaign``)
    and the campaign declared in ``--campaign-config`` (default
    ``configs/experiments/full_campaign_4x3x3.yaml``). For each declared
    algorithm x scenario x seed the final KPIs are read from
    ``<run>/<E*>/figures/tables/core_kpis.csv`` (columns ``kpi,value``).

Fail closed
    Exit code 2, a message on stderr and no output files when the declaration
    has fewer than 2 seeds, when any declared treatment/seed has no single
    verified run with the declared episodes and a KPI table, or when an
    oriented KPI is missing or non-finite in some run. Nothing is imputed.

Statistics
    Per algorithm x scenario x KPI: mean, sample std, IQM and a percentile
    bootstrap confidence interval of the IQM. The IQM and bootstrap CIs follow
    the recommendation of Agarwal, Schwarzer, Castro, Courville and Bellemare
    (2021), "Deep Reinforcement Learning at the Edge of the Statistical
    Precipice", NeurIPS 34, to report robust aggregates with interval
    estimates instead of point estimates over few runs. Here IQM is the
    project's fractional interquartile mean
    (``uc3m.application.evaluation.fresh_analysis.iqm``: the observations cut
    at 25 % and 75 % enter with fractional weight). It equals the 25 % trimmed
    mean of the authors' ``rliable`` library only when the number of seeds is a
    multiple of four; the fractional rule is a project convention, not a value
    prescribed by the literature. Resampling
    unit is the seed (one final KPI per independent run), resampled with
    replacement independently inside each algorithm x scenario stratum, so
    treatments are never pooled. ``N_RESAMPLES`` resamples, confidence
    ``CONFIDENCE``; each stratum uses ``numpy.random.default_rng([BOOTSTRAP_SEED,
    crc32("<ALGO>|<SCENARIO>|<KPI>")])`` so intervals do not depend on
    iteration order.

    With 3 seeds the IQM equals the mean (int(0.75) = 0 values trimmed per
    tail) and the bootstrap has only 10 distinct resamples; each extreme
    resample has probability 1/27 > 2.5 %, so the 95 % interval collapses to
    the sample range [min, max]. It is a coarse description of seed
    variability, not a population guarantee.

Inference
    Per scenario and oriented KPI, the Kruskal-Wallis omnibus test and the
    Dunn post-hoc with Holm correction are reused from
    ``uc3m.multicriteria.stats_tests`` (asymptotic chi-square/normal p-values;
    small-sample p-values are approximate). ``descriptive_leader`` is the best
    IQM. ``inferential_decision`` names a ``superior_algorithm`` only when the
    omnibus p < alpha and the leader is better than every other algorithm in
    mean rank with Holm-adjusted p < alpha. With p >= alpha no superiority is
    declared. KPIs without a declared orientation are reported descriptively
    only. The report never sets ``scientific_acceptance`` to true.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from uc3m.application.evaluation.fresh_analysis import iqm as canonical_iqm  # noqa: E402
from uc3m.application.evaluation.results_catalog import (  # noqa: E402
    discover_runs,
    resolve_results_root,
)
from uc3m.multicriteria.stats_tests import (  # noqa: E402
    dunns_posthoc_holm,
    kruskal_wallis,
)

SCHEMA_VERSION = "1.0"
DEFAULT_CAMPAIGN_CONFIG = REPO / "configs" / "experiments" / "full_campaign_4x3x3.yaml"
DEFAULT_OUTPUT_SUBDIR = "campaign_statistical_report"
KPI_TABLE = Path("figures") / "tables" / "core_kpis.csv"
REPORT_JSON = "campaign_statistical_report.json"
TREATMENTS_CSV = "treatment_statistics.csv"
COMPARISONS_CSV = "scenario_comparisons.csv"

ALPHA = 0.05
BOOTSTRAP_SEED = 20211206  # arbitrary fixed value chosen before any campaign result; never tuned
N_RESAMPLES = 10_000
CONFIDENCE = 0.95
MIN_SEEDS = 2

# Orientation declared by this tool for KPIs of core_kpis.csv. True = higher is
# better. KPIs not listed here (totals, deltas with producer-defined sign) are
# reported descriptively and excluded from leader/inference.
KPI_ORIENTATION: Dict[str, bool] = {
    "peak_average": False,
    "ramping_average": False,
    "one_minus_load_factor_average": False,
    "carbon_emissions_control": False,
    "electricity_cost_control": False,
    "pv_self_consumption_ratio": True,
}


class IncompleteCampaign(ValueError):
    """The declared campaign is not fully covered by verified runs with KPIs."""


@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    algorithms: Tuple[str, ...]
    scenarios: Tuple[str, ...]
    seeds: Tuple[int, ...]
    episodes: int
    source: str


def load_campaign_spec(path: Path) -> CampaignSpec:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    try:
        return CampaignSpec(
            campaign_id=str(payload["campaign_id"]),
            algorithms=tuple(str(a).upper() for a in payload["algorithms"]),
            scenarios=tuple(str(s).upper() for s in payload["scenarios"]),
            seeds=tuple(int(s) for s in payload["seeds"]),
            episodes=int(payload["episodes"]),
            source=str(path),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise IncompleteCampaign(f"{path}: invalid campaign declaration ({exc})") from exc


# --- estimators ---------------------------------------------------------------------------------


def iqm(values: Sequence[float]) -> float:
    return float(canonical_iqm(values))


def bootstrap_ci(
    values: Sequence[float],
    *,
    stream: str,
    n_resamples: int = N_RESAMPLES,
    confidence: float = CONFIDENCE,
    seed: int = BOOTSTRAP_SEED,
) -> Tuple[float, float]:
    """Percentile bootstrap CI of the IQM, resampling seeds with replacement."""
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng([seed, zlib.crc32(stream.encode("utf-8"))])
    indices = rng.integers(0, arr.size, size=(n_resamples, arr.size))
    replicates = np.asarray([canonical_iqm(row) for row in arr[indices]])
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(replicates, [tail, 1.0 - tail])
    return float(low), float(high)


# --- data collection ----------------------------------------------------------------------------

Collected = Dict[Tuple[str, str], Dict[int, Dict[str, float]]]


def _read_kpi_table(path: Path) -> Dict[str, float]:
    kpis: Dict[str, float] = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw = (row.get("value") or "").strip()
            try:
                value = float(raw)
            except ValueError:
                continue
            if math.isfinite(value):
                kpis[str(row["kpi"]).strip()] = value
    return kpis


def collect_campaign_kpis(results_root: Path, spec: CampaignSpec) -> Collected:
    if len(set(spec.seeds)) < MIN_SEEDS:
        raise IncompleteCampaign(
            f"{spec.source}: the campaign declares {len(set(spec.seeds))} seed(s); "
            f"at least {MIN_SEEDS} seeds are required for multiseed statistics"
        )
    verified: Dict[Tuple[str, str, int], List] = {}
    for run in discover_runs(results_root):
        verified.setdefault((run.algorithm, run.scenario, run.seed), []).append(run)
    statuses = {
        (run.algorithm, run.scenario, run.seed): run.status
        for run in discover_runs(results_root, verified_only=False)
        if run.status != "verified"
    }

    missing: List[str] = []
    collected: Collected = {}
    for algorithm in spec.algorithms:
        for scenario in spec.scenarios:
            for seed in spec.seeds:
                key = (algorithm, scenario, seed)
                label = f"{algorithm} {scenario} seed {seed}"
                runs = verified.get(key, [])
                if not runs:
                    status = statuses.get(key)
                    missing.append(label + (f" (status={status})" if status else ""))
                    continue
                if len(runs) > 1:
                    missing.append(f"{label} (ambiguous: {len(runs)} verified runs)")
                    continue
                run = runs[0]
                if run.completed_episodes < spec.episodes:
                    missing.append(f"{label} (completed {run.completed_episodes}/{spec.episodes} episodes)")
                    continue
                table = run.scenario_dir / KPI_TABLE
                if not table.is_file():
                    missing.append(f"{label} (missing {KPI_TABLE.as_posix()})")
                    continue
                collected.setdefault((algorithm, scenario), {})[seed] = _read_kpi_table(table)
    if missing:
        raise IncompleteCampaign(f"{results_root}: missing treatments: " + ", ".join(missing))

    oriented_seen = {k for per_seed in collected.values() for kpis in per_seed.values() for k in kpis} & set(
        KPI_ORIENTATION
    )
    if not oriented_seen:
        raise IncompleteCampaign(f"{results_root}: no oriented KPI ({sorted(KPI_ORIENTATION)}) in any run")
    gaps = [
        f"{algorithm} {scenario} seed {seed} ({kpi})"
        for (algorithm, scenario), per_seed in collected.items()
        for seed, kpis in per_seed.items()
        for kpi in sorted(oriented_seen)
        if kpi not in kpis
    ]
    if gaps:
        raise IncompleteCampaign(f"{results_root}: oriented KPI missing or non-finite: " + ", ".join(gaps))
    return collected


# --- report -------------------------------------------------------------------------------------


def _treatment_rows(collected: Collected, spec: CampaignSpec) -> List[dict]:
    rows = []
    for algorithm in sorted(spec.algorithms):
        for scenario in spec.scenarios:
            per_seed = collected[(algorithm, scenario)]
            seeds = sorted(per_seed)
            common = set.intersection(*(set(per_seed[s]) for s in seeds))
            for kpi in sorted(common):
                values = [per_seed[s][kpi] for s in seeds]
                low, high = bootstrap_ci(values, stream=f"{algorithm}|{scenario}|{kpi}")
                orientation = KPI_ORIENTATION.get(kpi)
                rows.append(
                    {
                        "algorithm": algorithm,
                        "scenario": scenario,
                        "kpi": kpi,
                        "orientation": (
                            "undeclared" if orientation is None
                            else "higher_is_better" if orientation else "lower_is_better"
                        ),
                        "seeds": seeds,
                        "values": values,
                        "n_seeds": len(values),
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values, ddof=1)),
                        "iqm": iqm(values),
                        "ci_low": low,
                        "ci_high": high,
                    }
                )
    return rows


def _descriptive_leader(iqms: Mapping[str, float], higher_is_better: bool) -> dict:
    best = max(iqms.values()) if higher_is_better else min(iqms.values())
    tied = sorted(name for name, value in iqms.items() if math.isclose(value, best, rel_tol=0.0, abs_tol=1e-12))
    return {
        "algorithm": tied[0] if len(tied) == 1 else None,
        "tied": tied,
        "iqm": best,
        "basis": "best IQM over seeds (descriptive only)",
    }


def _inferential_decision(
    groups: Mapping[str, Sequence[float]], leader: Optional[str], higher_is_better: bool, alpha: float
) -> dict:
    omnibus = kruskal_wallis(groups, alpha=alpha, higher_is_better=higher_is_better)
    decision = {
        "alpha": alpha,
        "omnibus": {
            "test": "kruskal_wallis",
            "H": omnibus.get("H"),
            "p_value": omnibus.get("p_value"),
            "status": omnibus.get("status"),
            "mean_ranks": omnibus.get("mean_ranks", {}),
        },
        "posthoc": [],
        "superior_algorithm": None,
    }
    if omnibus.get("status") != "ok" or omnibus.get("p_value") is None:
        decision.update(status="not_testable", rationale="Kruskal-Wallis not computable; no superiority claim.")
        return decision
    if float(omnibus["p_value"]) >= alpha:
        decision.update(
            status="no_significant_difference",
            rationale=f"Kruskal-Wallis p={omnibus['p_value']:.4g} >= alpha={alpha}; no superiority claim.",
        )
        return decision
    posthoc = dunns_posthoc_holm(groups, alpha=alpha, higher_is_better=higher_is_better)
    decision["posthoc"] = posthoc
    if leader is None:
        decision.update(status="omnibus_significant_no_unique_superior", rationale="Descriptive leader is tied.")
        return decision
    beaten = []
    for row in posthoc:
        if leader not in (row["algorithm_a"], row["algorithm_b"]):
            continue
        own, other = (
            (row["mean_rank_a"], row["mean_rank_b"]) if row["algorithm_a"] == leader
            else (row["mean_rank_b"], row["mean_rank_a"])
        )
        beaten.append(bool(row["significant"]) and own > other)
    if beaten and len(beaten) == len(groups) - 1 and all(beaten):
        decision.update(
            status="superior",
            superior_algorithm=leader,
            rationale=f"Kruskal-Wallis p<{alpha} and Dunn-Holm p<{alpha} for {leader} against every other algorithm.",
        )
    else:
        decision.update(
            status="omnibus_significant_no_unique_superior",
            rationale=f"Kruskal-Wallis p<{alpha} but {leader} is not Dunn-Holm better than every other algorithm.",
        )
    return decision


def build_report(
    results_root: Path,
    spec: CampaignSpec,
    *,
    alpha: float = ALPHA,
) -> dict:
    collected = collect_campaign_kpis(results_root, spec)
    treatments = _treatment_rows(collected, spec)
    comparisons = []
    for scenario in spec.scenarios:
        for kpi in sorted(KPI_ORIENTATION):
            rows = [t for t in treatments if t["scenario"] == scenario and t["kpi"] == kpi]
            if len(rows) != len(spec.algorithms):
                continue
            higher = KPI_ORIENTATION[kpi]
            leader = _descriptive_leader({r["algorithm"]: r["iqm"] for r in rows}, higher)
            groups = {r["algorithm"]: r["values"] for r in rows}
            comparisons.append(
                {
                    "scenario": scenario,
                    "kpi": kpi,
                    "higher_is_better": higher,
                    "descriptive_leader": leader,
                    "inferential_decision": _inferential_decision(groups, leader["algorithm"], higher, alpha),
                }
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "campaign_id": spec.campaign_id,
        "campaign_config": spec.source,
        "source_results_root": str(results_root),
        "declared": {
            "algorithms": list(spec.algorithms),
            "scenarios": list(spec.scenarios),
            "seeds": list(spec.seeds),
            "episodes": spec.episodes,
        },
        "alpha": alpha,
        "iqm_definition": "fractional interquartile mean (uc3m.application.evaluation.fresh_analysis.iqm)",
        "bootstrap": {
            "method": "percentile; seeds resampled with replacement within each algorithm x scenario stratum",
            "statistic": "iqm",
            "n_resamples": N_RESAMPLES,
            "confidence": CONFIDENCE,
            "seed": BOOTSTRAP_SEED,
        },
        "kpi_orientation": {k: ("higher_is_better" if v else "lower_is_better") for k, v in KPI_ORIENTATION.items()},
        "reference": (
            "Agarwal et al. (2021), Deep Reinforcement Learning at the Edge of the "
            "Statistical Precipice, NeurIPS 34"
        ),
        "treatments": treatments,
        "comparisons": comparisons,
        "scientific_acceptance": False,
        "limitations": [
            "Few seeds per treatment: bootstrap intervals are coarse (with 3 seeds the 95 % interval is the "
            "sample range) and p-values are asymptotic approximations.",
            "Kruskal-Wallis/Dunn are run per scenario and KPI without correction across KPIs or scenarios.",
            "KPI orientation is declared by this tool and must match the producer of core_kpis.csv.",
        ],
    }


def write_report(report: Mapping, output_dir: Path) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / REPORT_JSON
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    treatments_path = output_dir / TREATMENTS_CSV
    fields = ["algorithm", "scenario", "kpi", "orientation", "n_seeds", "seeds", "mean", "std", "iqm", "ci_low", "ci_high"]
    with treatments_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["treatments"]:
            writer.writerow({**{k: row[k] for k in fields}, "seeds": ";".join(str(s) for s in row["seeds"])})

    comparisons_path = output_dir / COMPARISONS_CSV
    fields = [
        "scenario", "kpi", "higher_is_better", "descriptive_leader", "tied", "leader_iqm",
        "inferential_status", "superior_algorithm", "p_value", "alpha",
    ]
    with comparisons_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["comparisons"]:
            leader, decision = row["descriptive_leader"], row["inferential_decision"]
            writer.writerow(
                {
                    "scenario": row["scenario"],
                    "kpi": row["kpi"],
                    "higher_is_better": row["higher_is_better"],
                    "descriptive_leader": leader["algorithm"] or "",
                    "tied": ";".join(leader["tied"]),
                    "leader_iqm": leader["iqm"],
                    "inferential_status": decision["status"],
                    "superior_algorithm": decision["superior_algorithm"] or "",
                    "p_value": "" if decision["omnibus"]["p_value"] is None else decision["omnibus"]["p_value"],
                    "alpha": decision["alpha"],
                }
            )
    return [json_path, treatments_path, comparisons_path]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--results-root", type=Path, default=None,
                        help="Campaign results root (default: MADRL_RESULTS_ROOT, then outputs/campaign)")
    parser.add_argument("--campaign-config", type=Path, default=DEFAULT_CAMPAIGN_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=None,
                        help=f"Default: <results-root>/{DEFAULT_OUTPUT_SUBDIR}")
    parser.add_argument("--alpha", type=float, default=ALPHA)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    results_root = resolve_results_root(args.results_root)
    output_dir = args.output_dir or results_root / DEFAULT_OUTPUT_SUBDIR
    try:
        spec = load_campaign_spec(args.campaign_config)
        report = build_report(results_root, spec, alpha=args.alpha)
    except (IncompleteCampaign, FileNotFoundError) as exc:
        print(f"ERROR: campaign statistical report not written: {exc}", file=sys.stderr)
        return 2
    for path in write_report(report, output_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
