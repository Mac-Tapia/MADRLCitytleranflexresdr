"""Extract Tabla 3.4 numeric KPIs from canonical 50-ep Drive results (read-only sources)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRIVE = ROOT / "outputs" / "_drive_madrl"
OUT = Path(__file__).resolve().parent / "tabla_3_4_kpis_numericos_50ep.csv"


def calc_autosuf(av: dict) -> tuple[float, float]:
    gen = float(av["pv_generation_total"])
    exp = float(av["pv_export_total"])
    imp = float(av["grid_import_control"])
    used = gen - exp
    denom = used + imp
    return (used / denom if denom else float("nan"), used)


def main() -> None:
    ep_counts: dict[tuple[str, str], int] = {}
    ep_path = DRIVE / "full_data" / "analysis_real_drive" / "tables" / "district_episode_kpis.csv"
    with ep_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["algorithm"], r["scenario"])
            ep_counts[key] = ep_counts.get(key, 0) + 1
    print("Episode counts from district_episode_kpis:", ep_counts)

    rows: list[dict] = []

    def add(
        *,
        axis: str,
        algo: str,
        sc: str,
        seed: int,
        kpi: str,
        value,
        unit: str,
        how: str,
        fuente: str,
        interpret: str,
        notes: str = "",
    ) -> None:
        rows.append(
            {
                "axis": axis,
                "algorithm": algo,
                "scenario": sc,
                "seed": seed,
                "district_timeseries_episodes": ep_counts.get((algo, sc), ""),
                "kpi": kpi,
                "valor": value,
                "unidad": unit,
                "metodo": how,
                "fuente": fuente,
                "interpretacion": interpret,
                "notas": notes,
            }
        )

    for algo in ["MASAC", "MATD3", "MAAC"]:
        for sc in ["E1", "E2", "E3"]:
            ts = DRIVE / "full_data" / algo / sc / "data" / "training_summary.json"
            j = json.loads(ts.read_text(encoding="utf-8"))
            av = j["citylearn_v3_report"]["all_values"]
            src_sum = str(ts).replace("\\", "/")
            src_core = str(
                (DRIVE / "kpis" / f"{algo.lower()}_{sc}_core_kpis.csv").resolve()
            ).replace("\\", "/")
            seed = j.get("seed", 0)
            rs = j["citylearn_v3_report"].get("report_source")
            print(
                f"{algo} {sc}: seed={seed} report_source={rs} "
                f"district_eps={ep_counts.get((algo, sc))}"
            )

            peak = float(av["peak_average"])
            ramp = float(av["ramping_average"])
            omlf = float(av["one_minus_load_factor_average"])
            autoc = float(av["pv_self_consumption_ratio"])
            autosuf, pv_used = calc_autosuf(av)
            ce_ratio = float(av["carbon_emissions"])
            ce_ctrl = float(av["carbon_emissions_control"])
            ce_base = float(av["carbon_emissions_baseline"])
            ce_delta = float(av["carbon_emissions_delta"])
            evitadas = ce_base - ce_ctrl
            cost_r = float(av["electricity_cost"])
            cost_c = float(av["electricity_cost_control"])
            cost_b = float(av["electricity_cost_baseline"])
            cost_d = float(av["electricity_cost_delta"])
            cost_peak = float(av["cost_peak_average"])
            demanda_red_pct = (1.0 - cost_peak) * 100.0
            psd = av.get("price_signal_deviation")
            psd_b = av.get("price_signal_deviation_baseline")
            psd_d = av.get("price_signal_deviation_delta")

            add(
                axis="OE.1",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="peak_average",
                value=peak,
                unit="ratio vs baseline",
                how="extraido",
                fuente=f"{src_core} | {src_sum}::citylearn_v3_report.all_values.peak_average",
                interpret=f"baseline=1.0; delta={peak-1:.6f}; {'peor' if peak > 1 else 'mejor'} pico",
            )
            add(
                axis="OE.1",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="ramping_average",
                value=ramp,
                unit="ratio vs baseline",
                how="extraido",
                fuente=f"{src_core} | all_values.ramping_average",
                interpret=f"baseline=1.0; delta={ramp-1:.6f}",
            )
            add(
                axis="OE.1",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="one_minus_load_factor_average",
                value=omlf,
                unit="ratio vs baseline",
                how="extraido",
                fuente=f"{src_core} | all_values.one_minus_load_factor_average",
                interpret=f"baseline=1.0; delta={omlf-1:.6f}; {'mejor' if omlf < 1 else 'peor'} load factor penalty",
            )
            add(
                axis="OE.1",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="autoconsumo (pv_self_consumption_ratio)",
                value=autoc,
                unit="ratio [0-1]",
                how="extraido",
                fuente=f"{src_core} | all_values.pv_self_consumption_ratio",
                interpret=(
                    f"PV used={pv_used:.2f} kWh de gen={float(av['pv_generation_total']):.2f} kWh; "
                    f"export={float(av['pv_export_total']):.2f} kWh"
                ),
            )
            add(
                axis="OE.1",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="autosuficiencia (derivada)",
                value=autosuf,
                unit="ratio [0-1]",
                how="calculado:(pv_gen-pv_export)/(pv_gen-pv_export+grid_import_control)",
                fuente=src_sum + "::all_values[pv_generation_total,pv_export_total,grid_import_control]",
                interpret=f"cobertura local aprox; import_control={float(av['grid_import_control']):.2f} kWh",
                notes="No hay KPI self_sufficiency nativo en evaluate_v2/madrl_kpis",
            )

            add(
                axis="OE.2",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="carbon_emissions (ratio)",
                value=ce_ratio,
                unit="ratio vs baseline",
                how="extraido",
                fuente=f"{src_core} | all_values.carbon_emissions",
                interpret=f"baseline=1.0; delta_ratio={ce_ratio-1:.6f}",
            )
            add(
                axis="OE.2",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="consumo_ponderado_CI (=carbon_emissions_control)",
                value=ce_ctrl,
                unit="kgCO2",
                how="extraido",
                fuente=f"{src_core} | all_values.carbon_emissions_control",
                interpret=f"absoluto control; baseline={ce_base:.4f} kgCO2",
            )
            add(
                axis="OE.2",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="carbon_emissions_delta",
                value=ce_delta,
                unit="kgCO2",
                how="extraido",
                fuente=f"{src_core} | all_values.carbon_emissions_delta",
                interpret="control - baseline; positivo = más emisiones que baseline",
            )
            add(
                axis="OE.2",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="emisiones_evitadas",
                value=evitadas,
                unit="kgCO2",
                how="calculado:carbon_emissions_baseline - carbon_emissions_control",
                fuente=src_sum + "::all_values",
                interpret=(
                    f"{'evitadas' if evitadas > 0 else 'exceso (sin evitacion)'}: {abs(evitadas):.4f} kgCO2"
                ),
            )

            add(
                axis="OE.3",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="electricity_cost (ratio)",
                value=cost_r,
                unit="ratio vs baseline",
                how="extraido",
                fuente=f"{src_core} | all_values.electricity_cost",
                interpret=f"baseline=1.0; delta_ratio={cost_r-1:.6f}",
            )
            add(
                axis="OE.3",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="electricity_cost_control",
                value=cost_c,
                unit="EUR (etiqueta CityLearn)",
                how="extraido",
                fuente=f"{src_core} | all_values.electricity_cost_control",
                interpret=f"absoluto control; baseline={cost_b:.4f}",
            )
            add(
                axis="OE.3",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="electricity_cost_delta",
                value=cost_d,
                unit="EUR",
                how="extraido",
                fuente=f"{src_core} | all_values.electricity_cost_delta",
                interpret="control - baseline; positivo = mayor costo",
            )
            add(
                axis="OE.3",
                algo=algo,
                sc=sc,
                seed=seed,
                kpi="reduccion_cargo_demanda (proxy cost_peak_average)",
                value=cost_peak,
                unit=f"ratio peak; %reduccion={demanda_red_pct:.4f}",
                how="extraido+proxy",
                fuente=f"{src_core} | all_values.cost_peak_average (=peak_average)",
                interpret=(
                    f"% reduccion vs baseline peak={(1-cost_peak)*100:.4f}% "
                    f"(negativo=aumento de pico/cargo)"
                ),
                notes="No hay campo demand_charge_reduction; se usa cost_peak_average",
            )
            if psd is None:
                add(
                    axis="OE.3",
                    algo=algo,
                    sc=sc,
                    seed=seed,
                    kpi="price_signal_deviation",
                    value="",
                    unit="",
                    how="ausente",
                    fuente=src_core,
                    interpret="no hay numero en datos",
                    notes="campo vacio en core_kpis / all_values para E2",
                )
            else:
                add(
                    axis="OE.3",
                    algo=algo,
                    sc=sc,
                    seed=seed,
                    kpi="price_signal_deviation",
                    value=float(psd),
                    unit="ratio",
                    how="extraido",
                    fuente=f"{src_core} | all_values.price_signal_deviation",
                    interpret=f"baseline={psd_b}; delta={psd_d}",
                )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("Wrote", OUT, "rows", len(rows))

    print("\n======== TABLA 3.4 ALINEADA (OE1@E1, OE2@E2, OE3@E3) ========")
    for r in rows:
        aligned = (
            (r["axis"] == "OE.1" and r["scenario"] == "E1")
            or (r["axis"] == "OE.2" and r["scenario"] == "E2")
            or (r["axis"] == "OE.3" and r["scenario"] == "E3")
        )
        if aligned:
            print(
                f"{r['algorithm']}|{r['scenario']}|{r['kpi']}|{r['valor']}|{r['unidad']}|{r['metodo']}"
            )


if __name__ == "__main__":
    main()
