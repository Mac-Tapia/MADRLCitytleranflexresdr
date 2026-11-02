"""Selección del mejor MADRL a nivel distrito y por edificio.

Alineado al título de tesis: gestión energética multiobjetivo y desempeño
algorítmico (HAPPO, MASAC, MATD3, MAAC) en la comunidad heterogénea de Iquitos.

Entrada preferida (corrida canónica / post-proceso Drive 50 ep):
  <output_root>/resumen_comparativo/multiobjetivo/kpi_rankings_drive50/
    district_ranking_by_scenario.csv
    building_kpis_4madrl.csv

También acepta rutas absolutas a esos CSV, o el directorio kpi_rankings_drive50.

Salida:
  best_madrl_district_building_report.json
  madrl_wins_per_building.csv
  madrl_building_win_counts.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALGOS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")
SCENARIO_OE = {"E1": "OE.1", "E2": "OE.2", "E3": "OE.3"}
PRIMARY_BUILDING = {
    "E1": ("flex_gain_vs_baseline", True),
    "E2": ("co2_reduction_kgco2", True),
    "E3": ("cost_reduction_eur", True),
}


def _f(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        x = float(val)
    except (TypeError, ValueError):
        return None
    if x != x:  # NaN
        return None
    return x


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def resolve_tables(
    output_root: Path | None = None,
    district_csv: Path | None = None,
    building_csv: Path | None = None,
    rankings_dir: Path | None = None,
) -> tuple[Path, Path]:
    if district_csv and building_csv:
        return district_csv, building_csv
    if rankings_dir is None and output_root is not None:
        rankings_dir = (
            output_root
            / "resumen_comparativo"
            / "multiobjetivo"
            / "kpi_rankings_drive50"
        )
    if rankings_dir is None:
        raise FileNotFoundError(
            "Indica --output-root, --rankings-dir o ambos CSV distrito/edificio."
        )
    d = rankings_dir / "district_ranking_by_scenario.csv"
    b = rankings_dir / "building_kpis_4madrl.csv"
    if not d.is_file() or not b.is_file():
        raise FileNotFoundError(
            f"Faltan tablas en {rankings_dir}. "
            "Ejecuta tools/eval/kpi_rankings.py "
            "o completa Sección 8 del notebook."
        )
    return d, b


def district_winners(district_rows: list[dict[str, str]]) -> dict[str, Any]:
    """Ganador distrito por escenario (rank==1) y OG = mayoría + desempate E1."""
    by_sc: dict[str, list[dict[str, Any]]] = {s: [] for s in SCENARIOS}
    for r in district_rows:
        sc = r.get("scenario", "")
        if sc not in by_sc:
            continue
        by_sc[sc].append(
            {
                "rank": int(float(r["rank"])) if r.get("rank") not in (None, "") else 99,
                "algorithm": str(r.get("algorithm", "")).upper(),
                "metric": r.get("metric"),
                "value": _f(r.get("value")),
                "oe": r.get("oe") or SCENARIO_OE.get(sc),
            }
        )
    winners: dict[str, Any] = {}
    for sc in SCENARIOS:
        rows = sorted(by_sc[sc], key=lambda x: x["rank"])
        winners[sc] = {
            "oe": SCENARIO_OE[sc],
            "winner": rows[0]["algorithm"] if rows else None,
            "ranking": rows,
        }
    counts = Counter(winners[sc]["winner"] for sc in SCENARIOS if winners[sc]["winner"])
    if counts:
        # OG descriptivo: más victorias OE; desempate → ganador E1 (flexibilidad núcleo)
        top = counts.most_common()
        best_n = top[0][1]
        tied = [a for a, n in top if n == best_n]
        og = winners["E1"]["winner"] if winners["E1"]["winner"] in tied else tied[0]
    else:
        og = None
    return {
        "by_scenario": winners,
        "oe_win_counts": dict(counts),
        "mejor_madrl_distrito_OG": og,
    }


def building_algo_winners(building_rows: list[dict[str, str]]) -> dict[str, Any]:
    """Por (escenario, edificio) elige el MADRL con mejor KPI primario del OE."""
    per_building: list[dict[str, Any]] = []
    win_counts: dict[str, Counter] = {s: Counter() for s in SCENARIOS}

    # Index: (scenario, building_id) -> algo -> metric value + resource cols
    indexed: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in building_rows:
        sc = r.get("scenario", "")
        if sc not in PRIMARY_BUILDING:
            continue
        bid = r.get("building_id") or ""
        try:
            building_id = int(float(bid))
        except (TypeError, ValueError):
            continue
        algo = str(r.get("algorithm", "")).upper()
        metric, _hib = PRIMARY_BUILDING[sc]
        indexed[(sc, building_id)][algo] = {
            "value": _f(r.get(metric)),
            "nombre": r.get("nombre") or r.get("agent") or f"Building_{building_id}",
            "tipo_uso": r.get("tipo_uso", ""),
            "agent": r.get("agent", f"Building_{building_id}"),
            "battery_throughput_kwh": _f(r.get("battery_throughput_kwh")),
            "ev_charge_kwh": _f(r.get("ev_charge_kwh")),
            "ev_departure_success_ratio": _f(r.get("ev_departure_success_ratio")),
            "grid_role_control": r.get("grid_role_control", ""),
            "metric": metric,
        }

    for sc in SCENARIOS:
        metric, hib = PRIMARY_BUILDING[sc]
        for bid in range(1, 18):
            by_algo = indexed.get((sc, bid), {})
            candidates = [
                (algo, payload)
                for algo, payload in by_algo.items()
                if payload.get("value") is not None
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda t: float(t[1]["value"]), reverse=hib)
            winner_algo, payload = candidates[0]
            win_counts[sc][winner_algo] += 1
            per_building.append(
                {
                    "scenario": sc,
                    "oe": SCENARIO_OE[sc],
                    "building_id": bid,
                    "agent": payload["agent"],
                    "nombre": payload["nombre"],
                    "tipo_uso": payload["tipo_uso"],
                    "primary_metric": metric,
                    "winner_algorithm": winner_algo,
                    "winner_value": payload["value"],
                    "battery_throughput_kwh": payload["battery_throughput_kwh"],
                    "ev_charge_kwh": payload["ev_charge_kwh"],
                    "ev_departure_success_ratio": payload["ev_departure_success_ratio"],
                    "grid_role_control": payload["grid_role_control"],
                    "all_algorithms": {
                        a: by_algo[a]["value"]
                        for a in ALGOS
                        if a in by_algo and by_algo[a]["value"] is not None
                    },
                }
            )

    ranking_building: dict[str, list[dict[str, Any]]] = {}
    overall = Counter()
    for sc in SCENARIOS:
        ranked = sorted(
            [
                {"algorithm": a, "buildings_won": int(win_counts[sc].get(a, 0))}
                for a in ALGOS
            ],
            key=lambda x: -x["buildings_won"],
        )
        ranking_building[sc] = ranked
        for a, n in win_counts[sc].items():
            overall[a] += n

    overall_ranked = sorted(
        [{"algorithm": a, "buildings_won_all_OE": int(overall.get(a, 0))} for a in ALGOS],
        key=lambda x: -x["buildings_won_all_OE"],
    )
    return {
        "per_building_winners": per_building,
        "win_counts_by_scenario": {s: dict(win_counts[s]) for s in SCENARIOS},
        "ranking_by_scenario": ranking_building,
        "ranking_all_OE": overall_ranked,
        "mejor_madrl_edificio": overall_ranked[0]["algorithm"] if overall_ranked else None,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    flat_rows = []
    for r in rows:
        flat = {k: v for k, v in r.items() if k != "all_algorithms"}
        algos = r.get("all_algorithms") or {}
        if isinstance(algos, dict):
            for a, v in algos.items():
                flat[f"value_{a}"] = v
        flat_rows.append(flat)
    fields = fieldnames or list(flat_rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(flat_rows)


def run_selection(
    output_root: Path | None = None,
    district_csv: Path | None = None,
    building_csv: Path | None = None,
    rankings_dir: Path | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    d_path, b_path = resolve_tables(output_root, district_csv, building_csv, rankings_dir)
    district_rows = _read_csv(d_path)
    building_rows = _read_csv(b_path)
    district = district_winners(district_rows)
    building = building_algo_winners(building_rows)

    if out_dir is None:
        if rankings_dir is not None:
            out_dir = rankings_dir
        elif output_root is not None:
            out_dir = (
                output_root
                / "resumen_comparativo"
                / "multiobjetivo"
                / "kpi_rankings_drive50"
            )
        else:
            out_dir = d_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "titulo_tesis_alineacion": (
            "GESTION ENERGETICA MULTIOBJETIVO MEDIANTE APRENDIZAJE POR REFUERZO "
            "PROFUNDO MULTIAGENTE EN UNA COMUNIDAD INTELIGENTE HETEROGENEA DE IQUITOS: "
            "EFECTOS Y DESEMPEÑO ALGORITMICO"
        ),
        "fecha": datetime.now(timezone.utc).isoformat(),
        "fuentes": {
            "district_ranking_csv": str(d_path),
            "building_kpis_csv": str(b_path),
        },
        "algoritmos": list(ALGOS),
        "niveles": ["distrito", "edificio"],
        "distrito": district,
        "edificio": {
            "mejor_madrl_edificio": building["mejor_madrl_edificio"],
            "win_counts_by_scenario": building["win_counts_by_scenario"],
            "ranking_by_scenario": building["ranking_by_scenario"],
            "ranking_all_OE": building["ranking_all_OE"],
            "n_building_decisions": len(building["per_building_winners"]),
            "criterio": (
                "Por edificio y escenario se elige el MADRL con mejor KPI primario "
                "del OE (E1: flex_gain; E2: co2_reduction; E3: cost_reduction). "
                "El ganador edificio global suma victorias en los 17×3 casos."
            ),
        },
        "veredicto": {
            "mejor_madrl_distrito_OG": district["mejor_madrl_distrito_OG"],
            "mejor_madrl_edificio": building["mejor_madrl_edificio"],
            "coherente_distrito_edificio": (
                district["mejor_madrl_distrito_OG"] == building["mejor_madrl_edificio"]
            ),
            "ganadores_OE_distrito": {
                sc: district["by_scenario"][sc]["winner"] for sc in SCENARIOS
            },
        },
    }

    report_path = out_dir / "best_madrl_district_building_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    write_csv(out_dir / "madrl_wins_per_building.csv", building["per_building_winners"])

    count_rows = []
    for sc in SCENARIOS:
        for item in building["ranking_by_scenario"][sc]:
            count_rows.append(
                {
                    "scenario": sc,
                    "oe": SCENARIO_OE[sc],
                    "algorithm": item["algorithm"],
                    "buildings_won": item["buildings_won"],
                }
            )
    write_csv(out_dir / "madrl_building_win_counts.csv", count_rows)

    report["_artifacts"] = {
        "report_json": str(report_path),
        "wins_per_building_csv": str(out_dir / "madrl_wins_per_building.csv"),
        "win_counts_csv": str(out_dir / "madrl_building_win_counts.csv"),
    }
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-root", type=Path, default=None)
    p.add_argument("--rankings-dir", type=Path, default=None)
    p.add_argument("--district-csv", type=Path, default=None)
    p.add_argument("--building-csv", type=Path, default=None)
    p.add_argument("--out-dir", type=Path, default=None)
    args = p.parse_args()
    report = run_selection(
        output_root=args.output_root,
        district_csv=args.district_csv,
        building_csv=args.building_csv,
        rankings_dir=args.rankings_dir,
        out_dir=args.out_dir,
    )
    v = report["veredicto"]
    print("=" * 68)
    print("SELECCIÓN MADRL — DISTRITO Y EDIFICIO")
    print("=" * 68)
    print(f"  Distrito OG : {v['mejor_madrl_distrito_OG']}")
    for sc, w in v["ganadores_OE_distrito"].items():
        print(f"  Distrito {sc}: {w}")
    print(f"  Edificio    : {v['mejor_madrl_edificio']}  "
          f"(victorias 17 edificios × 3 OE)")
    print(f"  Coherente   : {v['coherente_distrito_edificio']}")
    arts = report.get("_artifacts", {})
    print(f"  Report      : {arts.get('report_json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
