"""Agrega KPIs descargados de Google Drive (corrida Colab) y genera resumen comparativo."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KPIS_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
RUN_ID = "madrl_v3_20260627_164047"
OUT_RUN = REPO / "outputs" / RUN_ID / "resumen_comparativo"
ALGOS = ("happo", "masac", "matd3", "maac")
SCENARIOS = ("E1", "E2", "E3")


def read_core_kpis(algo: str, scen: str) -> dict[str, float] | None:
    path = KPIS_DIR / f"{algo}_{scen.lower()}_core_kpis.csv"
    if not path.exists():
        return None
    data: dict[str, float] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            val = (row.get("value") or "").strip()
            if not val:
                continue
            data[row["kpi"]] = float(val)
    return data


def read_episodes(algo: str, scen: str) -> int | None:
    path = resolve_results_path(algo, scen)
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    recorded = payload.get("episodes_recorded")
    if recorded is not None:
        return int(recorded)
    hp = payload.get("hyperparameters") or {}
    jr = hp.get("job_resume") or {}
    if jr.get("completed_episodes") is not None:
        return int(jr["completed_episodes"])
    ep = payload.get("episodes")
    return int(ep) if ep else None


def resolve_results_path(algo: str, scen: str) -> Path | None:
    """Busca results.json por output_dir/scenario interno (nombres locales pueden estar cruzados)."""
    for path in KPIS_DIR.glob(f"{algo}_*_results.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        out = (payload.get("output_dir") or "").rstrip("/")
        if out.endswith(f"/{scen}") and payload.get("algorithm", "").upper() == algo.upper():
            return path
    return None


def flex_composite(kpis: dict[str, float]) -> float:
    return (
        kpis["peak_average"]
        + kpis["ramping_average"]
        + kpis["one_minus_load_factor_average"]
    ) / 3.0


def norm_lower_better(values: dict[str, float]) -> dict[str, float]:
    lo, hi = min(values.values()), max(values.values())
    if hi <= lo:
        return {k: 0.5 for k in values}
    return {k: 1.0 - (v - lo) / (hi - lo) for k, v in values.items()}


def main() -> int:
    flex_raw: dict[str, float] = {}
    co2_raw: dict[str, float] = {}
    cost_raw: dict[str, float] = {}
    rows: list[dict] = []

    for algo in ALGOS:
        e1, e2, e3 = (read_core_kpis(algo, s) for s in SCENARIOS)
        ep = {s: read_episodes(algo, s) for s in SCENARIOS}
        if e1:
            flex_raw[algo.upper()] = flex_composite(e1)
        if e2 and "carbon_emissions_delta" in e2:
            co2_raw[algo.upper()] = e2["carbon_emissions_delta"]
        if e3 and "electricity_cost_delta" in e3:
            cost_raw[algo.upper()] = e3["electricity_cost_delta"]

        for scen, kpis in zip(SCENARIOS, (e1, e2, e3)):
            if not kpis:
                continue
            rows.append(
                {
                    "run_id": RUN_ID,
                    "algorithm": algo.upper(),
                    "scenario": scen,
                    "episodes": ep.get(scen),
                    **{k: kpis.get(k) for k in kpis},
                }
            )

    nf = norm_lower_better(flex_raw)
    nc = norm_lower_better(co2_raw)
    nt = norm_lower_better(cost_raw)

    ranking = []
    for algo in sorted(set(nf) | set(nc) | set(nt)):
        s1 = nf.get(algo, 0.0)
        s2 = nc.get(algo, 0.0)
        s3 = nt.get(algo, 0.0)
        mean = (s1 + s2 + s3) / 3.0
        ranking.append(
            {
                "algorithm": algo,
                "score_oe1_flex": round(s1, 4),
                "score_oe2_co2": round(s2, 4),
                "score_oe3_cost": round(s3, 4),
                "score_global": round(mean, 4),
                "episodes_e1": read_episodes(algo.lower(), "E1"),
                "episodes_e2": read_episodes(algo.lower(), "E2"),
                "episodes_e3": read_episodes(algo.lower(), "E3"),
            }
        )
    ranking.sort(key=lambda x: -x["score_global"])
    for i, item in enumerate(ranking, 1):
        item["rank"] = i
        item["selected"] = i == 1

    best = ranking[0]["algorithm"] if ranking else None

    report = {
        "mejor_madrl": best,
        "fuente": "colab_drive",
        "run_id": RUN_ID,
        "drive_folder": "https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX",
        "target_episodes": 50,
        "gpu": "NVIDIA RTX PRO 6000 Blackwell Server Edition (Colab)",
        "nota_episodios": (
            "Episodios = episodes_recorded en results.json (no el campo episodes del último resume). "
            "MATD3/MAAC/MASAC: 50 ep registrados en E1/E2 (y E3 MATD3); MAAC E3 y MASAC E3 sin results.json local; "
            "HAPPO: 49/50 entrenados, sin KPIs (error VecEnvWrapper). "
            "Varios archivos kpis/ tienen nombre de escenario cruzado — validar por output_dir."
        ),
        "ranking": ranking,
        "kpis_primarios": {
            "flex_composite_e1": flex_raw,
            "co2_delta_kg_e2": co2_raw,
            "cost_delta_eur_e3": cost_raw,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    OUT_RUN.mkdir(parents=True, exist_ok=True)
    (OUT_RUN / "best_madrl_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    csv_path = OUT_RUN / "comparison_metrics_colab.csv"
    if rows:
        fields = sorted({k for r in rows for k in r})
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    sel_path = OUT_RUN / "best_madrl_selection.csv"
    with sel_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "algorithm",
                "score_global",
                "score_oe1_flex",
                "score_oe2_co2",
                "score_oe3_cost",
                "selected",
            ],
        )
        writer.writeheader()
        for item in ranking:
            writer.writerow(
                {
                    "rank": item["rank"],
                    "algorithm": item["algorithm"],
                    "score_global": item["score_global"],
                    "score_oe1_flex": item["score_oe1_flex"],
                    "score_oe2_co2": item["score_oe2_co2"],
                    "score_oe3_cost": item["score_oe3_cost"],
                    "selected": item["selected"],
                }
            )

    latest = REPO / "outputs" / "latest_colab_output_root.txt"
    latest.write_text(f"outputs/{RUN_ID}\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
