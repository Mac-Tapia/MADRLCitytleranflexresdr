"""Statistical report of a fresh campaign, read from its verified analysis (SPEC-005 FR-005.5, SPEC-009).

    python tools/eval/build_campaign_statistical_report.py \
        --manifest outputs/campaigns/<alias>/campaign_manifest.json --stage confirm --split test_2025

Inputs
    The explicit campaign manifest and the analysis ``python -m uc3m.application.pipeline
    analyze`` registered in it. No folder is searched for runs. The attempts are listed by
    ``uc3m.application.evaluation.results_catalog`` and the analysis is read through
    ``uc3m.application.pipeline.read_verified_analysis``, which re-verifies its digests,
    rebuilds the seed table from the attempts through the trust rule and recomputes the
    statistics.

Single statistical truth
    This tool computes no estimator, interval or test. Every figure is a value of
    ``scientific_report.json``, written by ``uc3m.application.evaluation.fresh_analysis``:
    mean, standard deviation and IQM per seed, percentile bootstrap interval of the mean
    over whole seeds, Friedman omnibus, paired Wilcoxon post hoc, each with Holm inside its
    family. The tool only derives the separation FR-005.5 asks for: ``descriptive_leader``
    is the best IQM (gains are oriented to maximize) and ``inferential_decision`` names a
    ``superior_algorithm`` only if the omnibus is significant after Holm and the leader
    wins a confirmatory pair against every other algorithm.

Fail closed
    Exit code 2, a message on stderr and no output files when there is no registered
    analysis, the analysis or any attempt no longer verifies, the analysis is incomplete,
    fewer than 2 seeds are declared, or a report already exists there. Every attempt that
    does not count is named with its reason. The report never sets
    ``scientific_acceptance`` to true.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from uc3m.application.evaluation.results_catalog import audit_stage_evaluations  # noqa: E402
from uc3m.application.pipeline import (  # noqa: E402
    VerifiedAnalysis,
    describe_exclusions,
    dominates,
    read_verified_analysis,
    requires_full_split,
)

SCHEMA_VERSION = "2.0"
DEFAULT_OUTPUT_SUBDIR = "reports"
REPORT_JSON = "campaign_statistical_report.json"
SEED_TABLE_CSV = "seed_table.csv"
TREATMENTS_CSV = "treatment_statistics.csv"
COMPARISONS_CSV = "scenario_comparisons.csv"
MIN_SEEDS = 2


class IncompleteCampaign(ValueError):
    """The stage has no complete analysis that still verifies against its attempts."""


def treatment_rows(table_rows: Sequence[Mapping], report: Mapping) -> List[dict]:
    """The seed statistics of the report, next to the seed values they describe."""
    rows = []
    for item in report.get("seed_statistics") or []:
        values = {
            int(r["seed"]): r["value"]
            for r in table_rows
            if r["algorithm"] == item["algorithm"] and r["scenario"] == item["scenario"]
            and r["endpoint"] == item["endpoint"]
        }
        seeds = sorted(values)
        low, high = item["ci95_mean"]
        rows.append(
            {
                "family": item["family"],
                "algorithm": item["algorithm"],
                "scenario": item["scenario"],
                "endpoint": item["endpoint"],
                "seeds": seeds,
                "values": [values[seed] for seed in seeds],
                "n_seeds": item["n"],
                "mean": item["mean"],
                "std": item["std"],
                "median": item["median"],
                "iqm": item["iqm"],
                "ci_low": low,
                "ci_high": high,
            }
        )
    return rows


def _descriptive_leader(iqms: Mapping[str, float]) -> dict:
    best = max(iqms.values())
    tied = sorted(name for name, value in iqms.items() if math.isclose(value, best, rel_tol=0.0, abs_tol=1e-12))
    return {
        "algorithm": tied[0] if len(tied) == 1 else None,
        "tied": tied,
        "iqm": best,
        "basis": "best IQM over seeds; gains are oriented to maximize (descriptive only)",
    }


def _inferential_decision(family: Mapping, omnibus: Mapping, leader: Optional[str], algorithms: Sequence[str],
                          alpha: float) -> dict:
    scenario, endpoint = omnibus["scenario"], omnibus["endpoint"]
    decision = {
        "alpha": alpha,
        "omnibus": {
            "test": "friedman",
            "p_value": omnibus["p_value"],
            "p_holm": omnibus["p_holm"],
            "kendall_w": omnibus["kendall_w"],
        },
        "posthoc": [r for r in family["pairwise"] if r["scenario"] == scenario and r["endpoint"] == endpoint],
        "superior_algorithm": None,
    }
    if omnibus["p_holm"] >= alpha:
        decision.update(
            status="no_significant_difference",
            rationale=f"Friedman Holm p={omnibus['p_holm']:.4g} >= alpha={alpha}; no superiority claim.",
        )
    elif leader is not None and dominates(family, scenario, endpoint, leader,
                                           [name for name in algorithms if name != leader]):
        decision.update(
            status="superior",
            superior_algorithm=leader,
            rationale=f"Friedman and Wilcoxon-Holm p<{alpha} for {leader} against every other algorithm.",
        )
    else:
        decision.update(
            status="omnibus_significant_no_unique_superior",
            rationale=f"Friedman Holm p<{alpha}, but no algorithm wins every confirmatory pair.",
        )
    return decision


def comparison_rows(report: Mapping, algorithms: Sequence[str], alpha: float) -> List[dict]:
    """Descriptive leader and inferential decision of every endpoint with its own test family."""
    statistics: Dict[tuple, Dict[str, float]] = {}
    for item in report.get("seed_statistics") or []:
        statistics.setdefault((item["scenario"], item["endpoint"]), {})[item["algorithm"]] = item["iqm"]
    families = [report.get("test_families") or {}, *(report.get("kpi_families") or {}).values()]
    rows = []
    for family in families:
        for omnibus in family.get("omnibus") or []:
            scenario, endpoint = omnibus["scenario"], omnibus["endpoint"]
            leader = _descriptive_leader(statistics[(scenario, endpoint)])
            rows.append(
                {
                    "scenario": scenario,
                    "endpoint": endpoint,
                    "descriptive_leader": leader,
                    "inferential_decision": _inferential_decision(family, omnibus, leader["algorithm"], algorithms,
                                                                  alpha),
                }
            )
    return rows


def compose_report(verified: VerifiedAnalysis, campaign_id: str, excluded: Sequence[Mapping]) -> dict:
    protocol, report = verified.protocol, verified.report
    rows = [dict(row) for row in verified.table.rows]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "campaign_id": campaign_id,
        "stage": verified.stage,
        "split": verified.split,
        "status": report.get("status"),
        "source_analysis": {
            "command": "python -m uc3m.application.pipeline analyze",
            "folder": str(verified.folder),
            "sha256": verified.manifest_sha256,
        },
        "declared": {"algorithms": list(protocol.algorithms), "seeds": list(protocol.seeds)},
        "alpha": protocol.alpha,
        "bootstrap": {
            "method": "percentile; whole seeds resampled with replacement",
            "statistic": "mean",
            "n_resamples": protocol.resamples,
            "seed": protocol.bootstrap_seed,
        },
        "iqm_definition": "fractional interquartile mean (uc3m.application.evaluation.fresh_analysis.iqm)",
        "coverage": report.get("coverage"),
        "excluded_attempts": list(excluded),
        "seed_rows": rows,
        "treatments": treatment_rows(rows, report),
        "comparisons": comparison_rows(report, protocol.algorithms, protocol.alpha),
        "decisions": report.get("decisions"),
        "limitations": report.get("limitations"),
        "scientific_acceptance": False,
    }


def build_report(manifest_path: Path, stage: str, split: str) -> dict:
    """The report of one stage and split, or IncompleteCampaign with every attempt that does not count."""
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"no campaign manifest at {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    audit = audit_stage_evaluations(
        manifest_path, stage=stage, split=split, require_full_split=requires_full_split(stage, split)
    )
    excluded = [attempt for attempt in audit if not attempt.included]
    detail = f" Attempts excluded: {describe_exclusions(excluded)}." if excluded else ""
    try:
        verified = read_verified_analysis(manifest_path, stage, split)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise IncompleteCampaign(f"analysis of {stage}:{split} not usable: {exc}.{detail}") from exc
    coverage = verified.report.get("coverage") or {}
    if coverage.get("complete") is not True:
        raise IncompleteCampaign(
            f"analysis of {stage}:{split} is incomplete, missing {coverage.get('missing')}.{detail}"
        )
    if len(set(verified.protocol.seeds)) < MIN_SEEDS:
        raise IncompleteCampaign(
            f"{stage} declares {len(set(verified.protocol.seeds))} seed(s); "
            f"at least {MIN_SEEDS} seeds are required for multiseed statistics"
        )
    return compose_report(verified, str(manifest["campaign_id"]), [a.as_dict() for a in excluded])


def write_report(report: Mapping, output_dir: Path) -> List[Path]:
    output_dir = Path(output_dir)
    json_path = output_dir / REPORT_JSON
    if json_path.exists():
        raise FileExistsError(f"{json_path} exists; a report is never overwritten")
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_path = output_dir / SEED_TABLE_CSV
    fields = ["campaign_id", "algorithm", "scenario", "seed", "split", "endpoint", "value", "kpi_report_sha256"]
    with seed_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["seed_rows"])

    treatments_path = output_dir / TREATMENTS_CSV
    fields = ["family", "algorithm", "scenario", "endpoint", "n_seeds", "seeds", "mean", "std", "median", "iqm",
              "ci_low", "ci_high"]
    with treatments_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["treatments"]:
            writer.writerow({**{k: row[k] for k in fields}, "seeds": ";".join(str(s) for s in row["seeds"])})

    comparisons_path = output_dir / COMPARISONS_CSV
    fields = [
        "scenario", "endpoint", "descriptive_leader", "tied", "leader_iqm", "inferential_status",
        "superior_algorithm", "p_value", "p_holm", "alpha",
    ]
    with comparisons_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["comparisons"]:
            leader, decision = row["descriptive_leader"], row["inferential_decision"]
            writer.writerow(
                {
                    "scenario": row["scenario"],
                    "endpoint": row["endpoint"],
                    "descriptive_leader": leader["algorithm"] or "",
                    "tied": ";".join(leader["tied"]),
                    "leader_iqm": leader["iqm"],
                    "inferential_status": decision["status"],
                    "superior_algorithm": decision["superior_algorithm"] or "",
                    "p_value": decision["omnibus"]["p_value"],
                    "p_holm": decision["omnibus"]["p_holm"],
                    "alpha": decision["alpha"],
                }
            )
    # Written last: its presence marks a complete report.
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return [json_path, seed_path, treatments_path, comparisons_path]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--manifest", type=Path, required=True, help="campaign_manifest.json of the fresh campaign")
    parser.add_argument("--stage", required=True, help="Stage whose analysis is read, for example confirm")
    parser.add_argument("--split", required=True, help="Split whose analysis is read, for example test_2025")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help=f"Default: <campaign>/{DEFAULT_OUTPUT_SUBDIR}/<stage>_<split>")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir or args.manifest.parent / DEFAULT_OUTPUT_SUBDIR / f"{args.stage}_{args.split}"
    try:
        written = write_report(build_report(args.manifest, args.stage, args.split), output_dir)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"ERROR: campaign statistical report not written: {exc}", file=sys.stderr)
        return 2
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
