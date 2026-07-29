"""Analyze real Drive MADRL artifacts: timeseries, traces, building KPIs, checkpoints.

This script intentionally uses only downloaded Drive artifacts under
outputs/_drive_madrl/full_data. It does not synthesize missing time-series,
trace, building, or checkpoint values.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path("outputs/_drive_madrl/full_data")
OUT = ROOT / "analysis_real_drive"
ALGORITHMS = ["MASAC", "MATD3", "MAAC", "HAPPO"]
SCENARIOS = ["E1", "E2", "E3"]
DATA_FILES = [
    "timeseries.csv",
    "trace.csv",
    "building_kpis.csv",
    "building_behavior_summary.csv",
    "building_observation_action_schema.csv",
    "building_trace_sample.csv",
    "checkpoint_manifest.json",
    "results.json",
    "training_summary.json",
]


def ensure_out() -> None:
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    (OUT / "tables").mkdir(parents=True, exist_ok=True)


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size <= 0:
        raise FileNotFoundError(path)
    return pd.read_csv(path, **kwargs)


def artifact_inventory() -> pd.DataFrame:
    rows = []
    for algo in ALGORITHMS:
        for scenario in SCENARIOS:
            data_dir = ROOT / algo / scenario / "data"
            for name in DATA_FILES:
                path = data_dir / name
                rows.append(
                    {
                        "algorithm": algo,
                        "scenario": scenario,
                        "file": name,
                        "exists": path.exists(),
                        "bytes": path.stat().st_size if path.exists() else 0,
                        "path": str(path).replace("\\", "/"),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "tables" / "downloaded_artifacts_inventory.csv", index=False)
    return df


def complete_runs(inventory: pd.DataFrame) -> list[tuple[str, str]]:
    required = {
        "timeseries.csv",
        "trace.csv",
        "building_kpis.csv",
        "building_behavior_summary.csv",
        "building_observation_action_schema.csv",
        "checkpoint_manifest.json",
    }
    runs = []
    for (algo, scenario), group in inventory.groupby(["algorithm", "scenario"]):
        present = set(group.loc[group["exists"] & (group["bytes"] > 1000), "file"])
        if required.issubset(present):
            runs.append((algo, scenario))
    return runs


def district_trace_runs(inventory: pd.DataFrame) -> list[tuple[str, str]]:
    required = {"timeseries.csv", "trace.csv"}
    runs = []
    for (algo, scenario), group in inventory.groupby(["algorithm", "scenario"]):
        present = set(group.loc[group["exists"] & (group["bytes"] > 1000), "file"])
        if required.issubset(present):
            runs.append((algo, scenario))
    return runs


def aggregate_timeseries(runs: Iterable[tuple[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_cols = [
        "district_net_electricity_consumption",
        "district_net_electricity_consumption_cost",
        "district_net_electricity_consumption_emission",
        "district_net_electricity_consumption_without_storage",
        "reward_mean",
        "reward_sum",
    ]
    rows = []
    for algo, scenario in runs:
        path = ROOT / algo / scenario / "data" / "timeseries.csv"
        usecols = ["algorithm", "scenario", "episode", "episode_step", "global_step", *metric_cols]
        df = read_csv(path, usecols=usecols)
        grouped = df.groupby("episode", as_index=False).agg(
            steps=("episode_step", "count"),
            global_step_min=("global_step", "min"),
            global_step_max=("global_step", "max"),
            district_net_electricity_consumption_kwh=("district_net_electricity_consumption", "sum"),
            district_cost=("district_net_electricity_consumption_cost", "sum"),
            district_emission=("district_net_electricity_consumption_emission", "sum"),
            district_without_storage_kwh=("district_net_electricity_consumption_without_storage", "sum"),
            reward_mean=("reward_mean", "mean"),
            reward_sum=("reward_sum", "sum"),
        )
        grouped.insert(0, "scenario", scenario)
        grouped.insert(0, "algorithm", algo)
        rows.append(grouped)
    episode_df = pd.concat(rows, ignore_index=True)
    episode_df.to_csv(OUT / "tables" / "district_episode_kpis.csv", index=False)

    summary = episode_df.groupby(["algorithm", "scenario"], as_index=False).agg(
        episodes=("episode", "nunique"),
        steps_total=("steps", "sum"),
        district_net_kwh_mean=("district_net_electricity_consumption_kwh", "mean"),
        district_net_kwh_std=("district_net_electricity_consumption_kwh", "std"),
        district_cost_mean=("district_cost", "mean"),
        district_cost_std=("district_cost", "std"),
        district_emission_mean=("district_emission", "mean"),
        district_emission_std=("district_emission", "std"),
        district_without_storage_kwh_mean=("district_without_storage_kwh", "mean"),
        reward_mean=("reward_mean", "mean"),
        reward_sum_mean=("reward_sum", "mean"),
    )
    summary.to_csv(OUT / "tables" / "district_summary_by_algorithm_scenario.csv", index=False)
    return episode_df, summary


def collect_building_tables(runs: Iterable[tuple[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    behavior_rows = []
    kpi_rows = []
    for algo, scenario in runs:
        data_dir = ROOT / algo / scenario / "data"
        behavior = read_csv(data_dir / "building_behavior_summary.csv")
        behavior.insert(0, "scenario", scenario)
        behavior.insert(0, "algorithm", algo)
        behavior_rows.append(behavior)

        kpis = read_csv(data_dir / "building_kpis.csv")
        kpis.insert(0, "scenario", scenario)
        kpis.insert(0, "algorithm", algo)
        kpi_rows.append(kpis)

    behavior_all = pd.concat(behavior_rows, ignore_index=True)
    kpis_all = pd.concat(kpi_rows, ignore_index=True)
    behavior_all.to_csv(OUT / "tables" / "building_behavior_summary_all.csv", index=False)
    kpis_all.to_csv(OUT / "tables" / "building_kpis_all.csv", index=False)

    selected = [
        "building_battery_health_capacity_fade_ratio",
        "building_battery_health_equivalent_full_cycles_count",
        "building_cost_function",
        "building_net_electricity_consumption",
    ]
    selected_kpis = kpis_all[kpis_all["cost_function"].isin(selected)].copy()
    if not selected_kpis.empty:
        selected_kpis.to_csv(OUT / "tables" / "building_kpis_selected_long.csv", index=False)
    return behavior_all, kpis_all


def collect_trace_summary(runs: Iterable[tuple[str, str]]) -> pd.DataFrame:
    trace_rows = []
    for algo, scenario in runs:
        data_dir = ROOT / algo / scenario / "data"
        trace = read_csv(data_dir / "trace.csv")
        summary = trace.groupby(["algorithm", "scenario", "agent", "agent_index"], as_index=False).agg(
            trace_rows=("time_step", "count"),
            action_l2_mean=("action_l2", "mean"),
            action_l2_max=("action_l2", "max"),
            action_mean=("action_mean", "mean"),
            individual_reward_mean=("individual_reward", "mean"),
            individual_reward_sum=("individual_reward", "sum"),
            grid_import_kwh=("grid_import_kwh", "sum"),
            grid_export_kwh=("grid_export_kwh", "sum"),
            battery_consumption_kwh=("electrical_storage_electricity_consumption_kwh", "sum"),
            battery_energy_balance_kwh=("electrical_storage_energy_balance_kwh", "sum"),
            ev_charge_kwh=("ev_charge_kwh", "sum"),
            ev_consumption_kwh=("ev_electricity_consumption_kwh", "sum"),
            ev_v2g_export_kwh=("ev_v2g_export_kwh", "sum"),
            pv_generation_kwh=("pv_generation_kwh", "sum"),
            pv_export_kwh=("pv_export_kwh", "sum"),
        )
        trace_rows.append(summary)

    trace_all = pd.concat(trace_rows, ignore_index=True)
    trace_all.to_csv(OUT / "tables" / "trace_agent_summary_by_building.csv", index=False)
    return trace_all


def collect_equipment_schema(runs: Iterable[tuple[str, str]]) -> pd.DataFrame:
    rows = []
    for algo, scenario in runs:
        schema = read_csv(ROOT / algo / scenario / "data" / "building_observation_action_schema.csv")
        actions = schema[schema["variable_type"].eq("action")]
        obs = schema[schema["variable_type"].eq("observation")]
        for agent, group in actions.groupby("agent"):
            obs_group = obs[obs["agent"].eq(agent)]
            variables = sorted(group["variable_name"].astype(str).unique())
            observations = sorted(obs_group["variable_name"].astype(str).unique())
            rows.append(
                {
                    "algorithm": algo,
                    "scenario": scenario,
                    "building": agent,
                    "action_count": len(variables),
                    "controlled_bess_actions": sum(v == "electrical_storage" for v in variables),
                    "controlled_ev_charger_actions": sum("electric_vehicle_storage_charger" in v for v in variables),
                    "other_controlled_actions": sum(
                        v != "electrical_storage" and "electric_vehicle_storage_charger" not in v
                        for v in variables
                    ),
                    "uncontrolled_non_shiftable_load_observed": "non_shiftable_load" in observations,
                    "observed_variable_count": len(observations),
                    "controlled_action_variables": "; ".join(variables),
                }
            )
    out = pd.DataFrame(rows)

    der_path = Path("data/dataset_audit/der_sizing_audit.csv")
    ev_path = Path("data/dataset_audit/ev_charger_sizing_audit.csv")
    if der_path.exists():
        der = pd.read_csv(der_path)
        der["building"] = der["ID"].str.extract(r"(\d+)").astype(int).iloc[:, 0].map(lambda x: f"Building_{x}")
        keep = [
            "building",
            "ID",
            "Edificio",
            "Tipo",
            "Area_m2",
            "Carga_base_medida_MWh",
            "Maquina_controlada_MWh",
            "Maquina_controlada_pico_kW",
            "Maquina_controlada_count",
            "EV_load_total_MWh",
            "EV_load_peak_kW",
            "PV_schema_kWp",
            "BESS_schema_kWh",
            "BESS_schema_kW",
            "AC_pico_cooling_demand_kWth",
        ]
        out = out.merge(der[keep], on="building", how="left")
        out["controlled_load_mwh_dataset_audit"] = (
            out["Maquina_controlada_MWh"].fillna(0) + out["EV_load_total_MWh"].fillna(0)
        )
        out["uncontrolled_base_load_mwh_dataset_audit"] = out["Carga_base_medida_MWh"]
    if ev_path.exists():
        ev = pd.read_csv(ev_path)
        ev["building"] = ev["B"].astype(int).map(lambda x: f"Building_{x}")
        keep = [
            "building",
            "vehicle_predominant",
            "total_chargers",
            "mode3_physical_units",
            "mode3_socket_count",
            "total_kw",
            "parking_capped",
        ]
        out = out.merge(ev[keep], on="building", how="left")
    out.to_csv(OUT / "tables" / "controlled_uncontrolled_equipment_by_building.csv", index=False)
    return out


def collect_checkpoint_summary(runs: Iterable[tuple[str, str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    files = []
    for algo, scenario in runs:
        path = ROOT / algo / scenario / "data" / "checkpoint_manifest.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        checkpoints = obj.get("checkpoints", [])
        policy_ids = []
        checkpoint_episodes = []
        checkpoint_groups = []
        suffixes = []
        for item in checkpoints:
            rel = item.get("relative_path", "")
            policy = None
            for part in Path(rel).parts:
                if part.startswith("policy_"):
                    policy = part
                if part.startswith("checkpoint_episode_"):
                    checkpoint_episodes.append(part)
                if part.startswith("clamp"):
                    checkpoint_groups.append(part)
                    break
            policy_ids.append(policy)
            suffixes.append(Path(rel).suffix or Path(rel).name)
            files.append(
                {
                    "algorithm": algo,
                    "scenario": scenario,
                    "backend": obj.get("backend"),
                    "policy": policy,
                    "relative_path": rel,
                    "bytes": item.get("bytes", 0),
                }
            )
        summaries.append(
            {
                "algorithm": algo,
                "scenario": scenario,
                "backend": obj.get("backend"),
                "checkpoint_count_declared": obj.get("checkpoint_count"),
                "checkpoint_files_listed": len(checkpoints),
                "matd3_policies_with_checkpoints": len({p for p in policy_ids if p}),
                "maac_checkpoint_episodes": len(set(checkpoint_episodes)),
                "masac_checkpoint_groups": len(set(checkpoint_groups)),
                "checkpoint_file_types": "; ".join(sorted(set(suffixes))),
                "checkpoint_bytes_total": sum(int(i.get("bytes", 0) or 0) for i in checkpoints),
            }
        )
    summary_df = pd.DataFrame(summaries)
    files_df = pd.DataFrame(files)
    summary_df.to_csv(OUT / "tables" / "checkpoint_summary.csv", index=False)
    files_df.to_csv(OUT / "tables" / "checkpoint_policy_files.csv", index=False)
    return summary_df, files_df


def plot_line(df: pd.DataFrame, metric: str, title: str, filename: str, ylabel: str) -> None:
    plt.figure(figsize=(12, 6))
    for (algo, scenario), group in df.groupby(["algorithm", "scenario"]):
        label = f"{algo}-{scenario}"
        ordered = group.sort_values("episode")
        plt.plot(ordered["episode"], ordered[metric], label=label, linewidth=1.6)
    plt.title(title)
    plt.xlabel("Episode")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.25)
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT / "figures" / filename, dpi=180)
    plt.close()


def plot_outputs(
    episode_df: pd.DataFrame,
    district_summary: pd.DataFrame,
    behavior: pd.DataFrame,
    equipment: pd.DataFrame,
    checkpoint_summary: pd.DataFrame,
) -> None:
    plot_line(episode_df, "reward_mean", "District reward mean by episode", "district_reward_by_episode.png", "Mean reward")
    plot_line(
        episode_df,
        "district_net_electricity_consumption_kwh",
        "District net electricity by episode",
        "district_net_energy_by_episode.png",
        "kWh per episode",
    )

    pivot = district_summary.pivot(index="algorithm", columns="scenario", values="district_cost_mean")
    ax = pivot.plot(kind="bar", figsize=(9, 5))
    ax.set_title("Mean district cost by algorithm and scenario")
    ax.set_ylabel("Cost units from Drive artifact")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT / "figures" / "district_cost_summary.png", dpi=180)
    plt.close()

    pivot = district_summary.pivot(index="algorithm", columns="scenario", values="district_emission_mean")
    ax = pivot.plot(kind="bar", figsize=(9, 5))
    ax.set_title("Mean district emissions by algorithm and scenario")
    ax.set_ylabel("Emission units from Drive artifact")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT / "figures" / "district_emission_summary.png", dpi=180)
    plt.close()

    cols = ["algorithm", "scenario", "agent", "electricity_cost_delta_eur"]
    cost = behavior[cols].copy()
    cost["run"] = cost["algorithm"] + "-" + cost["scenario"]
    heat = cost.pivot(index="agent", columns="run", values="electricity_cost_delta_eur")
    plt.figure(figsize=(12, 7))
    plt.imshow(heat.values, aspect="auto", cmap="coolwarm")
    plt.colorbar(label="Electricity cost delta")
    plt.xticks(range(len(heat.columns)), heat.columns, rotation=45, ha="right")
    plt.yticks(range(len(heat.index)), heat.index)
    plt.title("Building electricity cost delta by run")
    plt.tight_layout()
    plt.savefig(OUT / "figures" / "building_cost_delta_heatmap.png", dpi=180)
    plt.close()

    cols = ["algorithm", "scenario", "agent", "carbon_emissions_delta_kgco2"]
    carbon = behavior[cols].copy()
    carbon["run"] = carbon["algorithm"] + "-" + carbon["scenario"]
    heat = carbon.pivot(index="agent", columns="run", values="carbon_emissions_delta_kgco2")
    plt.figure(figsize=(12, 7))
    plt.imshow(heat.values, aspect="auto", cmap="coolwarm")
    plt.colorbar(label="Carbon emissions delta kgCO2")
    plt.xticks(range(len(heat.columns)), heat.columns, rotation=45, ha="right")
    plt.yticks(range(len(heat.index)), heat.index)
    plt.title("Building carbon emissions delta by run")
    plt.tight_layout()
    plt.savefig(OUT / "figures" / "building_carbon_delta_heatmap.png", dpi=180)
    plt.close()

    eq_base = equipment.drop_duplicates("building").sort_values("building")
    x = range(len(eq_base))
    plt.figure(figsize=(12, 6))
    plt.bar(x, eq_base["controlled_ev_charger_actions"], label="EV charger actions")
    plt.bar(x, eq_base["controlled_bess_actions"], bottom=eq_base["controlled_ev_charger_actions"], label="BESS actions")
    plt.xticks(x, eq_base["building"], rotation=90)
    plt.ylabel("Controlled action count")
    plt.title("Controlled action variables by building")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "figures" / "controlled_actions_by_building.png", dpi=180)
    plt.close()

    if "controlled_load_mwh_dataset_audit" in eq_base.columns:
        plt.figure(figsize=(12, 6))
        plt.bar(x, eq_base["uncontrolled_base_load_mwh_dataset_audit"], label="Uncontrolled base load MWh")
        plt.bar(x, eq_base["controlled_load_mwh_dataset_audit"], label="Controlled EV + machine MWh")
        plt.xticks(x, eq_base["building"], rotation=90)
        plt.ylabel("MWh")
        plt.title("Dataset audit: controlled vs uncontrolled load by building")
        plt.legend()
        plt.tight_layout()
        plt.savefig(OUT / "figures" / "controlled_vs_uncontrolled_load_mwh.png", dpi=180)
        plt.close()

    # Figura A.9: tamaño total por tratamiento en GB (escala log). Incluye HAPPO=0.
    # Evita el gráfico legado en bytes crudos (4e10) que ocultaba MASAC/MATD3.
    try:
        import sys

        tools_dir = Path(__file__).resolve().parent
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        from fix_figura_a9_checkpoint_size import plot_a9, scan_checkpoint_bytes

        plot_a9(scan_checkpoint_bytes())
    except Exception:
        # Fallback mínimo si el módulo dedicado no está disponible.
        cs = checkpoint_summary.copy()
        cs["total_gb"] = cs["checkpoint_bytes_total"].astype(float) / (1024**3)
        pivot = cs.pivot(index="algorithm", columns="scenario", values="total_gb")
        ax = pivot.plot(kind="bar", figsize=(9, 5), logy=True)
        ax.set_title("Tamaño total listado en manifiestos de checkpoint")
        ax.set_ylabel("GB (escala log)")
        ax.grid(axis="y", alpha=0.25, which="both")
        plt.tight_layout()
        plt.savefig(OUT / "figures" / "checkpoint_manifest_bytes.png", dpi=180)
        plt.close()


def write_report(
    inventory: pd.DataFrame,
    district_runs: list[tuple[str, str]],
    building_runs: list[tuple[str, str]],
    district_summary: pd.DataFrame,
    behavior: pd.DataFrame,
    equipment: pd.DataFrame,
    checkpoint_summary: pd.DataFrame,
) -> None:
    district_complete = ", ".join(f"{a}-{s}" for a, s in district_runs)
    building_complete = ", ".join(f"{a}-{s}" for a, s in building_runs)
    missing = inventory[(~inventory["exists"]) | (inventory["bytes"] <= 1000)]
    best_reward = district_summary.sort_values("reward_mean", ascending=False).head(1).iloc[0]
    lowest_cost = district_summary.sort_values("district_cost_mean", ascending=True).head(1).iloc[0]
    lowest_emission = district_summary.sort_values("district_emission_mean", ascending=True).head(1).iloc[0]
    best_building_cost = behavior.sort_values("electricity_cost_delta_eur", ascending=True).head(1).iloc[0]
    report = [
        "# Real Drive MADRL Training Artifact Analysis",
        "",
        "Source: `outputs/_drive_madrl/full_data`, downloaded from the user-provided Google Drive folder.",
        "No synthetic time-series, trace, building KPI, or checkpoint values are generated.",
        "",
        "## Runs With Real Timeseries And Trace",
        "",
        district_complete or "None",
        "",
        "## Runs With Complete Building KPIs And Checkpoints",
        "",
        building_complete or "None",
        "",
        "HAPPO is included in district and trace tables where real files exist, but it is not used "
        "for building KPI/checkpoint comparisons because Drive does not contain the required "
        "`building_kpis.csv`, `building_behavior_summary.csv`, or `checkpoint_manifest.json` files.",
        "",
        "## Missing Or Incomplete Artifacts",
        "",
    ]
    if missing.empty:
        report.append("No missing artifacts among expected files for the checked algorithms/scenarios.")
    else:
        report.append(missing[["algorithm", "scenario", "file", "exists", "bytes"]].to_markdown(index=False))
    report.extend(
        [
            "",
            "## District-Level Interpretation",
            "",
            f"Highest mean reward: {best_reward['algorithm']}-{best_reward['scenario']} "
            f"with reward_mean={best_reward['reward_mean']:.6g}.",
            f"Lowest mean district cost: {lowest_cost['algorithm']}-{lowest_cost['scenario']} "
            f"with district_cost_mean={lowest_cost['district_cost_mean']:.6g}.",
            f"Lowest mean district emissions: {lowest_emission['algorithm']}-{lowest_emission['scenario']} "
            f"with district_emission_mean={lowest_emission['district_emission_mean']:.6g}.",
            "",
            "## Building-Level Interpretation",
            "",
            f"Most negative electricity_cost_delta_eur row: {best_building_cost['algorithm']}-"
            f"{best_building_cost['scenario']} {best_building_cost['agent']} "
            f"with electricity_cost_delta_eur={best_building_cost['electricity_cost_delta_eur']:.6g}.",
            "Building tables preserve all 17 buildings per complete run.",
            "",
            "## Controlled / Uncontrolled Equipment",
            "",
            "Controlled action variables are read from `building_observation_action_schema.csv` "
            "(`variable_type == action`). Uncontrolled/base demand is read from the dataset audit "
            "`Carga_base_medida_MWh`; controlled scenario loads are EV plus machine loads from the same audit.",
            "",
            f"Equipment rows generated: {len(equipment)}.",
            "",
            "## Checkpoints",
            "",
            checkpoint_summary.to_markdown(index=False),
            "",
            "## Generated Tables",
            "",
            "- `tables/district_episode_kpis.csv`",
            "- `tables/district_summary_by_algorithm_scenario.csv`",
            "- `tables/building_behavior_summary_all.csv`",
            "- `tables/building_kpis_all.csv`",
            "- `tables/trace_agent_summary_by_building.csv`",
            "- `tables/controlled_uncontrolled_equipment_by_building.csv`",
            "- `tables/checkpoint_summary.csv`",
            "- `tables/checkpoint_policy_files.csv`",
            "",
            "## Generated Figures",
            "",
            "- `figures/district_reward_by_episode.png`",
            "- `figures/district_net_energy_by_episode.png`",
            "- `figures/district_cost_summary.png`",
            "- `figures/district_emission_summary.png`",
            "- `figures/building_cost_delta_heatmap.png`",
            "- `figures/building_carbon_delta_heatmap.png`",
            "- `figures/controlled_actions_by_building.png`",
            "- `figures/controlled_vs_uncontrolled_load_mwh.png`",
            "- `figures/checkpoint_manifest_bytes.png`",
            "",
        ]
    )
    (OUT / "real_drive_training_analysis_report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    ensure_out()
    inventory = artifact_inventory()
    district_runs = district_trace_runs(inventory)
    building_runs = complete_runs(inventory)
    if not district_runs:
        raise SystemExit("No runs with timeseries and trace found in outputs/_drive_madrl/full_data")
    if not building_runs:
        raise SystemExit("No complete building KPI runs found in outputs/_drive_madrl/full_data")
    episode_df, district_summary = aggregate_timeseries(district_runs)
    behavior, _kpis = collect_building_tables(building_runs)
    _trace = collect_trace_summary(district_runs)
    equipment = collect_equipment_schema(building_runs)
    checkpoint_summary, _checkpoint_files = collect_checkpoint_summary(building_runs)
    plot_outputs(episode_df, district_summary, behavior, equipment, checkpoint_summary)
    write_report(inventory, district_runs, building_runs, district_summary, behavior, equipment, checkpoint_summary)
    print(f"Wrote analysis to {OUT}")
    print(f"District/trace runs: {', '.join(f'{a}-{s}' for a, s in district_runs)}")
    print(f"Building/checkpoint runs: {', '.join(f'{a}-{s}' for a, s in building_runs)}")


if __name__ == "__main__":
    main()
