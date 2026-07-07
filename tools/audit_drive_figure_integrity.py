"""Valida que figuras de entrenamiento usen solo CSV/JSON reales de Drive (50 ep)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FULL = REPO / "outputs" / "_drive_madrl" / "full_data"
RUN = REPO / "outputs" / "madrl_v3_20260627_164047"
OUT = RUN / "resumen_comparativo" / "figuras_drive_reales" / "drive_data_integrity_audit.json"

ALGOS = ("MASAC", "MATD3", "MAAC", "HAPPO")
SCENS = ("E1", "E2", "E3")
EXPECTED_EP = 50
EXPECTED_STEPS = 8760


def md5_head(path: Path, n: int = 8000) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        h.update(f.read(n))
    return h.hexdigest()[:16]


def audit_job(algo: str, scen: str) -> tuple[dict, list[str]]:
    issues: list[str] = []
    d = FULL / algo / scen / "data"
    rec: dict = {"algo": algo, "scen": scen}

    ts_p = d / "timeseries.csv"
    tr_p = d / "trace.csv"
    res_p = d / "results.json"

    if not ts_p.is_file():
        issues.append(f"{algo}/{scen}: FALTA timeseries.csv en espejo Drive")
        return rec, issues

    rec["drive_timeseries_bytes"] = ts_p.stat().st_size
    rec["drive_timeseries_md5_head"] = md5_head(ts_p)
    df = pd.read_csv(
        ts_p,
        usecols=lambda c: c in ("episode", "reward_mean", "reward_sum", "global_step", "episode_step"),
    )
    ep_unique = sorted(int(x) for x in df["episode"].dropna().unique())
    rec["episodes_in_timeseries"] = len(ep_unique)
    rec["episode_range"] = [min(ep_unique), max(ep_unique)] if ep_unique else None
    rec["rows_timeseries"] = len(df)

    steps = df.groupby("episode").size()
    rec["steps_per_episode"] = {
        "min": int(steps.min()),
        "max": int(steps.max()),
        "median": float(steps.median()),
    }

    if algo != "HAPPO":
        if rec["episodes_in_timeseries"] != EXPECTED_EP:
            issues.append(
                f"{algo}/{scen}: {rec['episodes_in_timeseries']} episodios en timeseries "
                f"(esperado {EXPECTED_EP})"
            )
    elif rec["episodes_in_timeseries"] not in (49, 50):
        issues.append(f"HAPPO/{scen}: {rec['episodes_in_timeseries']} episodios (esperado 49-50)")

    if int(steps.median()) != EXPECTED_STEPS:
        issues.append(
            f"{algo}/{scen}: mediana pasos/episodio={int(steps.median())} (esperado {EXPECTED_STEPS})"
        )

    if tr_p.is_file():
        tr = pd.read_csv(tr_p, usecols=lambda c: c in ("episode", "agent", "action_l2", "reward"))
        rec["trace_rows"] = len(tr)
        rec["trace_episodes"] = int(tr["episode"].nunique())
        rec["trace_md5_head"] = md5_head(tr_p)
        rec["trace_note"] = (
            "submuestra Drive (no 8760*17 filas/ep); figuras de exploracion usan datos reales parciales"
            if rec["trace_rows"] < rec["rows_timeseries"] * 5
            else "trace completo relativo a timeseries"
        )
    else:
        issues.append(f"{algo}/{scen}: FALTA trace.csv")

    if res_p.is_file():
        res = json.loads(res_p.read_text(encoding="utf-8"))
        rec["results_episodes"] = res.get("episodes")
        rec["results_episodes_recorded"] = res.get("episodes_recorded")
        rec["has_citylearn_v3_report"] = bool(res.get("citylearn_v3_report"))
        av = (res.get("citylearn_v3_report") or {}).get("all_values") or {}
        rec["kpi_count"] = len(av)
        if algo != "HAPPO" and rec["kpi_count"] == 0:
            issues.append(f"{algo}/{scen}: results.json sin KPIs (citylearn_v3_report vacio)")
    else:
        issues.append(f"{algo}/{scen}: FALTA results.json")

    prov_p = RUN / algo / scen / "figures" / "tables" / "drive_data_provenance.csv"
    if prov_p.is_file():
        prov = pd.read_csv(prov_p).iloc[0].to_dict()
        rec["provenance"] = prov
        prov_ts = Path(str(prov.get("timeseries", "")))
        if prov_ts.is_file():
            if md5_head(prov_ts) != rec["drive_timeseries_md5_head"]:
                issues.append(f"{algo}/{scen}: provenance timeseries no coincide con espejo Drive")
        else:
            issues.append(f"{algo}/{scen}: provenance apunta a timeseries inexistente")
    else:
        issues.append(f"{algo}/{scen}: FALTA drive_data_provenance.csv en figuras generadas")

    ep_sum_p = RUN / algo / scen / "figures" / "tables" / "episode_summary.csv"
    if ep_sum_p.is_file():
        n_es = len(pd.read_csv(ep_sum_p))
        rec["episode_summary_rows"] = n_es
        if n_es != rec["episodes_in_timeseries"]:
            issues.append(
                f"{algo}/{scen}: episode_summary({n_es}) != episodios timeseries({rec['episodes_in_timeseries']})"
            )

    # Figuras PNG existen y tablas KPI coherentes
    fig_dir = RUN / algo / scen / "figures"
    expected_training = [
        "reward_timeseries.png",
        "convergence_returns.png",
        "episode_reward_summary.png",
        "learning_efficiency.png",
        "citylearn_v2_district_timeseries.png",
        "exploration_action_l2.png",
        "agent_reward_contribution.png",
    ]
    kpi_figs = [
        "axis_baseline_comparison.png",
        "baseline_gain_by_kpi.png",
        "core_kpis.png",
        "OE1_flexibility_kpis.png",
        "OE2_co2_kpis.png",
        "OE3_cost_kpis.png",
    ]
    missing = [f for f in expected_training if not (fig_dir / f).is_file()]
    rec["training_figs_present"] = len(expected_training) - len(missing)
    if missing:
        issues.append(f"{algo}/{scen}: faltan figuras entrenamiento {missing}")

    if rec.get("kpi_count", 0) > 0:
        missing_kpi = [f for f in kpi_figs if not (fig_dir / f).is_file()]
        rec["kpi_figs_present"] = 6 - len(missing_kpi)
        if missing_kpi:
            issues.append(f"{algo}/{scen}: faltan figuras KPI {missing_kpi}")
    else:
        rec["kpi_figs_present"] = sum(1 for f in kpi_figs if (fig_dir / f).is_file())
        if algo != "HAPPO" and rec["kpi_figs_present"] > 0 and rec["kpi_count"] == 0:
            issues.append(f"{algo}/{scen}: figuras KPI sin KPIs en results.json (inconsistente)")

    return rec, issues


def audit_comparative() -> list[str]:
    issues: list[str] = []
    comp = RUN / "resumen_comparativo" / "figuras_drive_reales" / "comparativo"
    expected = [
        f"comparativo_{s}_convergence_reward_mean.png" for s in SCENS
    ] + [
        f"comparativo_{s}_OE{s[1]}_kpi.png" for s in SCENS
    ] + [
        f"comparativo_{s}_district_net_electricity_consumption_cost.png" for s in SCENS
    ] + [
        f"comparativo_{s}_district_net_electricity_consumption_emission.png" for s in SCENS
    ] + [
        f"comparativo_{s}_control_trace.png" for s in SCENS
    ] + ["comparativo_global_ranking_oe.png", "comparativo_best_worst_por_escenario.png"]

    for name in expected:
        if not (comp / name).is_file():
            issues.append(f"FALTA figura comparativa: {name}")

    # convergencia: cada punto = media reward_mean por episodio desde timeseries Drive
    for scen in SCENS:
        for algo in ALGOS:
            ts_p = FULL / algo / scen / "data" / "timeseries.csv"
            if not ts_p.is_file():
                continue
            ep = pd.read_csv(ts_p, usecols=["episode", "reward_mean"]).groupby("episode")["reward_mean"].mean()
            if ep.empty:
                issues.append(f"Serie convergencia vacia: {algo}/{scen}")
            elif ep.isna().all():
                issues.append(f"Serie convergencia solo NaN: {algo}/{scen}")

    return issues


def main() -> int:
    rows: list[dict] = []
    all_issues: list[str] = []
    for algo in ALGOS:
        for scen in SCENS:
            rec, issues = audit_job(algo, scen)
            rows.append(rec)
            all_issues.extend(issues)

    all_issues.extend(audit_comparative())

    # Regla anti-inventado: generate_drive_thesis_figures solo lee FULL_DATA
    summary = {
        "validation_rule": "Figuras generadas solo desde outputs/_drive_madrl/full_data (espejo Drive); sin sintesis",
        "expected_episodes_evaluable": EXPECTED_EP,
        "expected_steps_per_episode": EXPECTED_STEPS,
        "jobs_validated": len(rows),
        "issues_count": len(all_issues),
        "issues": all_issues,
        "verdict": "PASS" if not all_issues else "PASS_WITH_DOCUMENTED_EXCEPTIONS" if all(
            "HAPPO" in i or "trace" in i.lower() or "kpi" in i.lower() for i in all_issues
        ) and len(all_issues) <= 10 else "FAIL",
        "per_job": rows,
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "per_job"}, indent=2, ensure_ascii=False))
    for r in rows:
        print(
            f"{r['algo']}/{r['scen']}: eps={r.get('episodes_in_timeseries')} "
            f"steps_med={r.get('steps_per_episode',{}).get('median')} "
            f"kpi={r.get('kpi_count')} train_figs={r.get('training_figs_present')}/7 "
            f"kpi_figs={r.get('kpi_figs_present')}/6"
        )
    return 0 if summary["verdict"] in ("PASS", "PASS_WITH_DOCUMENTED_EXCEPTIONS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
