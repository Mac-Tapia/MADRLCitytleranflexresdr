"""Audit inferential statistics: CSV sources vs thesis protocol (Cap 5.9).

Writes outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/inferential_audit_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN_ID = "madrl_v3_20260627_164047"
STAT_DIR = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "estadistica"
DRIVE_EPISODE_CSV = (
    REPO
    / "outputs"
    / "_drive_madrl"
    / "full_data"
    / "analysis_real_drive"
    / "tables"
    / "district_episode_kpis.csv"
)
V4_KW_ALL_P = 0.0459
CANONICAL_ALGOS = ("MASAC", "MATD3", "MAAC")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _episode_counts() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {a: {} for a in ("HAPPO", *CANONICAL_ALGOS)}
    if not DRIVE_EPISODE_CSV.is_file():
        return out
    rows = _read_csv(DRIVE_EPISODE_CSV)
    for algo in out:
        for scen in ("E1", "E2", "E3"):
            n = sum(1 for r in rows if r.get("algorithm") == algo and r.get("scenario") == scen)
            if n:
                out[algo][scen] = n
    return out


def _kw_summary() -> dict[str, dict]:
    hyp = {r["axis"]: r for r in _read_csv(STAT_DIR / "hipotesis_estadisticas_madrl.csv")}
    analysis = {r["scope"]: r for r in _read_csv(STAT_DIR / "analisis_estadistico_madrl.csv")}
    result = {}
    for scope, axis in [("OE1", "OE1"), ("OE2", "OE2"), ("OE3", "OE3"), ("ALL", "OG")]:
        h = hyp.get(axis, {})
        a = analysis.get(scope, {})
        group_n = json.loads(a.get("group_n_json", "{}")) if a.get("group_n_json") else {}
        result[scope] = {
            "kw_h": float(h.get("KW_H_statistic", "nan")) if h.get("KW_H_statistic") else None,
            "kw_p": float(h.get("KW_p_value", "nan")) if h.get("KW_p_value") else None,
            "kw_significant": h.get("KW_significant_alpha_0_05") == "True",
            "best_median_kpi_gain": h.get("statistical_best_algorithm_by_median_gain"),
            "n_total_kpi_gains": int(a.get("n_total", 0) or 0),
            "group_n": {k: v for k, v in group_n.items() if k in CANONICAL_ALGOS},
            "happo_excluded": int(group_n.get("HAPPO", 0)) == 0,
        }
    return result


def _wilcoxon_significant() -> list[dict]:
    rows = _read_csv(STAT_DIR / "comparaciones_wilcoxon_madrl.csv")
    out = []
    for r in rows:
        if r.get("wilcoxon_significant_alpha_0_05") != "True":
            continue
        if not str(r.get("wilcoxon_status", "")).startswith("ok"):
            continue
        out.append(
            {
                "scope": r["scope"],
                "pair": f"{r['algorithm_a']} vs {r['algorithm_b']}",
                "p": float(r["wilcoxon_p_value"]),
                "better": r.get("better_by_median_difference"),
            }
        )
    return out


def _mwu_significant() -> list[dict]:
    rows = _read_csv(STAT_DIR / "comparaciones_mwu_madrl.csv")
    out = []
    for r in rows:
        if r.get("mann_whitney_significant_alpha_0_05") != "True":
            continue
        if r.get("mann_whitney_status") != "ok":
            continue
        out.append(
            {
                "scope": r["scope"],
                "pair": f"{r['algorithm_a']} vs {r['algorithm_b']}",
                "p": float(r["mann_whitney_p_value"]),
            }
        )
    return out


def _checklist(kw: dict, episode_counts: dict) -> list[dict]:
    checks = []

    # Population: 50ep canonical, not v4
    score_rows = _read_csv(STAT_DIR / "scores_kpi_algoritmo_madrl.csv")
    algos_in_scores = {r["algorithm"] for r in score_rows}
    checks.append(
        {
            "id": "population_50ep_kpi_gains",
            "status": "pass" if len(score_rows) == 231 and algos_in_scores == set(CANONICAL_ALGOS) else "fail",
            "detail": f"{len(score_rows)} KPI-gain rows; algorithms={sorted(algos_in_scores)}",
        }
    )

    # Sample sizes per group
    for scope, data in kw.items():
        expected = {"OE1": 36, "OE2": 15, "OE3": 26, "ALL": 77}[scope]
        ok = all(n == expected for n in data["group_n"].values()) and len(data["group_n"]) == 3
        checks.append(
            {
                "id": f"sample_sizes_{scope}",
                "status": "pass" if ok else "fail",
                "detail": data["group_n"],
            }
        )

    # HAPPO excluded from inferential
    happo_in_mwu = any(
        r.get("algorithm_a") == "HAPPO" or r.get("algorithm_b") == "HAPPO"
        for r in _read_csv(STAT_DIR / "comparaciones_mwu_madrl.csv")
        if r.get("mann_whitney_status") == "ok"
    )
    checks.append(
        {
            "id": "happo_excluded_inferential",
            "status": "pass" if kw["ALL"]["happo_excluded"] and not happo_in_mwu else "fail",
            "detail": "HAPPO has 0 KPI-gains; MWU ok-rows exclude HAPPO",
        }
    )

    # Descriptive from episode timeseries
    desc = _read_csv(STAT_DIR / "descriptivo_distrito_colab.csv")
    ep_ok = all(
        int(r.get("n_episodes", 0)) >= 49
        for r in desc
        if r.get("algorithm") in CANONICAL_ALGOS
    )
    checks.append(
        {
            "id": "descriptive_episode_timeseries",
            "status": "pass" if ep_ok and DRIVE_EPISODE_CSV.is_file() else "fail",
            "detail": f"episode_csv={DRIVE_EPISODE_CSV.is_file()}; n_rows={len(desc)}",
        }
    )

    # Not using v4 p=0.0459 as canonical
    checks.append(
        {
            "id": "not_v4_canonical_kw",
            "status": "pass" if abs(kw["ALL"]["kw_p"] - V4_KW_ALL_P) > 0.05 else "fail",
            "detail": f"canonical ALL p={kw['ALL']['kw_p']:.4f} vs v4 p={V4_KW_ALL_P}",
        }
    )

    return checks


def _hypothesis_decisions(kw: dict, wilcoxon_sig: list[dict]) -> dict:
    decisions = {}
    for code, scope in [("HG", "ALL"), ("HE.1", "OE1"), ("HE.2", "OE2"), ("HE.3", "OE3")]:
        k = kw[scope]
        wc_scope = [w for w in wilcoxon_sig if w["scope"] == scope]
        decisions[code] = {
            "kw_p": k["kw_p"],
            "kw_h0_rejected": k["kw_significant"],
            "best_median_kpi_gain": k["best_median_kpi_gain"],
            "wilcoxon_significant_pairs": len(wc_scope),
            "decision_omnibus": "no_rechaza_H0" if not k["kw_significant"] else "rechaza_H0",
            "decision_support": (
                "evidencia_descriptiva_primaria; inferencia_omnibus_no_confirmatoria; "
                f"Wilcoxon_exploratorio={len(wc_scope)}_pares_significativos"
            ),
        }
    return decisions


def build_report() -> dict:
    kw = _kw_summary()
    wilcoxon_sig = _wilcoxon_significant()
    mwu_sig = _mwu_significant()
    checks = _checklist(kw, _episode_counts())
    failed = [c for c in checks if c["status"] == "fail"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "verdict": "correct" if not failed else "had_errors",
        "errors": failed,
        "checks": checks,
        "kruskal_wallis": {s: {"p": v["kw_p"], "significant": v["kw_significant"]} for s, v in kw.items()},
        "mann_whitney_significant_count": len(mwu_sig),
        "wilcoxon_significant": wilcoxon_sig,
        "hypothesis_decisions": _hypothesis_decisions(kw, wilcoxon_sig),
        "episode_counts_drive": _episode_counts(),
        "reproduce_command": "powershell -ExecutionPolicy Bypass -File scripts\\verify_project_context.ps1; "
        ".venv39-citylearn-v3\\Scripts\\python.exe tools\\run_colab_drive_statistical_analysis.py; "
        ".venv39-citylearn-v3\\Scripts\\python.exe tools\\inferential_audit_report.py",
        "sources": {
            "analisis_estadistico_madrl": str(STAT_DIR / "analisis_estadistico_madrl.csv"),
            "hipotesis_estadisticas_madrl": str(STAT_DIR / "hipotesis_estadisticas_madrl.csv"),
            "comparaciones_wilcoxon_madrl": str(STAT_DIR / "comparaciones_wilcoxon_madrl.csv"),
            "comparaciones_mwu_madrl": str(STAT_DIR / "comparaciones_mwu_madrl.csv"),
            "descriptivo_distrito_colab": str(STAT_DIR / "descriptivo_distrito_colab.csv"),
            "district_episode_kpis": str(DRIVE_EPISODE_CSV),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inferential statistics audit report")
    parser.add_argument("--output", type=Path, default=STAT_DIR / "inferential_audit_report.json")
    args = parser.parse_args()

    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "errors": len(report["errors"]), "output": str(args.output)}, indent=2))
    return 1 if report["verdict"] == "had_errors" else 0


if __name__ == "__main__":
    raise SystemExit(main())
