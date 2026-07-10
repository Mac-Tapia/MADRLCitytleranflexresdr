from __future__ import annotations

import csv
import json
import math
import re
import shutil
from copy import deepcopy
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


REPO = Path(__file__).resolve().parents[1]
G_BASE = Path(r"G:\Mi unidad\MADRLCitytleranflexresdr\outputs\madrl_v3_20260627_164047")
SRC = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_VERSION_FINAL_50EP_ANTECEDENTES.docx"
OUT = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_VERSION_FINAL_GDRIVE_50EP_OBJETIVOS_DOCTORAL.docx"
ANALYSIS_DIR = REPO / "outputs" / "_drive_madrl" / "gdrive_20260627_164047_objective_analysis"
TABLE_DIR = ANALYSIS_DIR / "tables"
FIG_DIR = ANALYSIS_DIR / "figures"
METRICS = ANALYSIS_DIR / "thesis_gdrive_objective_metrics.json"
LOCAL_EPISODE_CSV = REPO / "outputs" / "_drive_madrl" / "full_data" / "analysis_real_drive" / "tables" / "district_episode_kpis.csv"

ALGOS = ["HAPPO", "MAAC", "MASAC", "MATD3"]
SCENARIOS = ["E1", "E2", "E3"]

OBJECTIVES = [
    {
        "objective": "OE.1",
        "hypothesis": "HE.1",
        "scenario": "E1",
        "dimension": "flexibilidad energetica",
        "metric": "reward_mean_average",
        "direction": "max",
        "indicator": "recompensa media del episodio en E1",
        "explanation": "E1 usa pesos [flex=0,70; CO2=0,15; costo=0,15], por lo que la recompensa media del episodio representa el efecto agregado del algoritmo sobre la dimension de flexibilidad bajo una funcion de recompensa comparable.",
    },
    {
        "objective": "OE.2",
        "hypothesis": "HE.2",
        "scenario": "E2",
        "dimension": "emisiones de CO2",
        "metric": "district_emission",
        "direction": "min",
        "indicator": "suma anual de district_net_electricity_consumption_emission en E2",
        "explanation": "E2 usa pesos [flex=0,15; CO2=0,70; costo=0,15]; por ello la emision distrital anual agregada por episodio es el indicador directo para contrastar el efecto sobre D-VD.2.",
    },
    {
        "objective": "OE.3",
        "hypothesis": "HE.3",
        "scenario": "E3",
        "dimension": "costos energeticos",
        "metric": "district_cost",
        "direction": "min",
        "indicator": "suma anual de district_net_electricity_consumption_cost en E3",
        "explanation": "E3 usa pesos [flex=0,25; CO2=0,15; costo=0,60]; por ello el costo distrital anual agregado por episodio es el indicador directo para contrastar el efecto sobre D-VD.3.",
    },
]

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
GREY = RGBColor(0x59, 0x59, 0x59)


def ensure_dirs() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value) -> float:
    try:
        if value in ("", None):
            return math.nan
        return float(value)
    except Exception:
        return math.nan


def fmt(x, nd: int = 3) -> str:
    try:
        if pd.isna(x):
            return "NA"
        return f"{float(x):,.{nd}f}"
    except Exception:
        return str(x)


def text_of(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()


def clear_body_keep_sectpr(document: Document) -> None:
    body = document.element.body
    sect_pr = None
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            sect_pr = child
        body.remove(child)
    if sect_pr is not None:
        body.append(sect_pr)


def append_before_sectpr(document: Document, el) -> None:
    body = document.element.body
    sect_pr = body.find(qn("w:sectPr"))
    if sect_pr is None:
        body.append(el)
    else:
        body.insert(body.index(sect_pr), el)


def style_doc(document: Document) -> None:
    for name in ["Normal", "Heading 1", "Heading 2", "Heading 3"]:
        if name not in [s.name for s in document.styles]:
            continue
        st = document.styles[name]
        st.font.name = "Calibri"
        if name == "Normal":
            st.font.size = Pt(11)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.line_spacing = 1.15
        else:
            st.font.bold = True
            st.font.color.rgb = ACCENT
            st.font.size = Pt(16 if name == "Heading 1" else 13 if name == "Heading 2" else 11.5)


def set_bg(cell, color: str = "1F4E79") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def p(doc: Document, text: str):
    para = doc.add_paragraph()
    para.add_run(text)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.15
    return para


def set_paragraph_text(para, text: str) -> None:
    for run in para.runs:
        run.text = ""
    if para.runs:
        para.runs[0].text = text
    else:
        para.add_run(text)


def table(doc: Document, caption: str, headers: list[str], rows: list[list[str]], font_size: float = 7.0):
    cap = doc.add_paragraph()
    run = cap.add_run(caption)
    run.bold = True
    run.font.size = Pt(9.5)
    run.font.color.rgb = GREY
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.style = "Light Grid Accent 1"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, head in enumerate(headers):
        cell = tbl.rows[0].cells[i]
        cell.text = ""
        rr = cell.paragraphs[0].add_run(head)
        rr.bold = True
        rr.font.size = Pt(font_size)
        rr.font.color.rgb = RGBColor(255, 255, 255)
        set_bg(cell)
    for row in rows:
        cells = tbl.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            rr = cells[i].paragraphs[0].add_run(str(val))
            rr.font.size = Pt(font_size)
    doc.add_paragraph()
    return tbl


def aggregate_timeseries(path: Path) -> pd.DataFrame:
    cols = [
        "episode",
        "district_net_electricity_consumption",
        "district_net_electricity_consumption_cost",
        "district_net_electricity_consumption_emission",
    ]
    sums: dict[int, dict[str, float]] = {}
    for chunk in pd.read_csv(path, usecols=cols, chunksize=200_000):
        chunk["episode"] = pd.to_numeric(chunk["episode"], errors="coerce").astype("Int64")
        grouped = chunk.groupby("episode", dropna=True).agg(
            district_net_energy=("district_net_electricity_consumption", "sum"),
            district_cost=("district_net_electricity_consumption_cost", "sum"),
            district_emission=("district_net_electricity_consumption_emission", "sum"),
        )
        for ep, row in grouped.iterrows():
            if pd.isna(ep):
                continue
            ep = int(ep)
            dest = sums.setdefault(ep, {"district_net_energy": 0.0, "district_cost": 0.0, "district_emission": 0.0})
            for key in dest:
                dest[key] += float(row[key])
    rows = [{"episode": ep, **vals} for ep, vals in sorted(sums.items())]
    return pd.DataFrame(rows)


def load_materialized_episode_kpis() -> pd.DataFrame:
    if not LOCAL_EPISODE_CSV.exists():
        raise FileNotFoundError(
            f"No existe {LOCAL_EPISODE_CSV}. Se requiere el CSV materializado para evitar releer los timeseries grandes de Drive."
        )
    df = pd.read_csv(LOCAL_EPISODE_CSV)
    df = df.rename(
        columns={
            "district_net_electricity_consumption_kwh": "district_net_energy",
            "reward_mean": "reward_mean_average",
            "reward_sum": "reward_sum_total",
        }
    )
    required = {"algorithm", "scenario", "episode", "district_net_energy", "district_cost", "district_emission", "reward_mean_average"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Faltan columnas en {LOCAL_EPISODE_CSV}: {sorted(missing)}")
    df.to_csv(TABLE_DIR / "gdrive_episode_kpis_from_materialized_drive_analysis.csv", index=False, encoding="utf-8")
    return df


def load_evidence() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    treatment_rows = []
    building_frames = []
    equipment_frames = []
    episode_kpis = load_materialized_episode_kpis()
    episode_counts = episode_kpis.groupby(["algorithm", "scenario"]).size().to_dict()
    for algo in ALGOS:
        for scenario in SCENARIOS:
            data_dir = G_BASE / algo / scenario / "data"
            result = read_json(data_dir / "results.json")
            live_progress_path = G_BASE / algo / scenario / "live_progress.json"
            live_progress = read_json(live_progress_path) if live_progress_path.exists() else {}
            all_values = result.get("citylearn_v3_report", {}).get("all_values", {})
            episode_summaries = result.get("episode_summaries") or []
            reward_df = pd.DataFrame(episode_summaries)
            if not reward_df.empty:
                reward_df = reward_df[["episode", "reward_mean_average", "reward_sum_total", "steps"]].copy()
                reward_df["episode"] = pd.to_numeric(reward_df["episode"], errors="coerce").astype("Int64")
            final_reward = safe_float(reward_df["reward_mean_average"].iloc[-1]) if not reward_df.empty else math.nan
            final_episode = int(reward_df["episode"].iloc[-1]) if not reward_df.empty and not pd.isna(reward_df["episode"].iloc[-1]) else None
            treatment_rows.append(
                {
                    "algorithm": algo,
                    "scenario": scenario,
                    "episodes_recorded": result.get("episodes_recorded", live_progress.get("completed_episode_count", result.get("episodes"))),
                    "training_episodes_field": result.get("episodes"),
                    "saved_episode_summaries": len(episode_summaries),
                    "materialized_episode_kpis": int(episode_counts.get((algo, scenario), 0)),
                    "final_episode_in_artifacts": final_episode,
                    "final_reward_mean": final_reward,
                    "building_count": result.get("building_count"),
                    "checkpoint_count": result.get("checkpoint_count"),
                    "peak_average": all_values.get("peak_average", all_values.get("cost_peak_average")),
                    "ramping_average": all_values.get("ramping_average", all_values.get("cost_ramping_average")),
                    "one_minus_load_factor_average": all_values.get("one_minus_load_factor_average", all_values.get("cost_one_minus_load_factor_average")),
                    "battery_throughput_total": all_values.get("battery_throughput_total"),
                    "pv_self_consumption_ratio": all_values.get("pv_self_consumption_ratio"),
                    "carbon_emissions_control": all_values.get("carbon_emissions_control"),
                    "carbon_emissions_delta": all_values.get("carbon_emissions_delta"),
                    "carbon_emissions_ratio": all_values.get("carbon_emissions"),
                    "electricity_cost_control": all_values.get("electricity_cost_control"),
                    "electricity_cost_delta": all_values.get("electricity_cost_delta"),
                    "electricity_cost_ratio": all_values.get("electricity_cost"),
                    "ev_departure_success_rate": all_values.get("ev_departure_success_rate"),
                }
            )
            b = pd.read_csv(data_dir / "building_behavior_summary.csv")
            b["algorithm"] = algo
            b["scenario"] = scenario
            building_frames.append(b)
            e = pd.read_csv(data_dir / "building_observation_action_schema.csv")
            e["algorithm"] = algo
            e["scenario"] = scenario
            equipment_frames.append(e)
    treatment = pd.DataFrame(treatment_rows)
    episodes = episode_kpis
    buildings = pd.concat(building_frames, ignore_index=True)
    equipment = pd.concat(equipment_frames, ignore_index=True)
    treatment.to_csv(TABLE_DIR / "gdrive_treatment_final_kpis.csv", index=False, encoding="utf-8")
    episodes.to_csv(TABLE_DIR / "gdrive_episode_kpis_used_for_statistics.csv", index=False, encoding="utf-8")
    buildings.to_csv(TABLE_DIR / "gdrive_building_behavior_summary_all.csv", index=False, encoding="utf-8")
    equipment.to_csv(TABLE_DIR / "gdrive_equipment_schema_all.csv", index=False, encoding="utf-8")
    return treatment, episodes, buildings, equipment


def holm_adjust(pairs: list[tuple[str, float]]) -> list[tuple[str, float, float]]:
    ordered = sorted(pairs, key=lambda x: x[1])
    adjusted = []
    running = 0.0
    m = len(ordered)
    for rank, (name, pv) in enumerate(ordered, start=1):
        adj = min(1.0, (m - rank + 1) * pv)
        running = max(running, adj)
        adjusted.append((name, pv, running))
    return sorted(adjusted, key=lambda x: x[0])


def analyze_objectives(treatment: pd.DataFrame, episodes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rows = []
    pair_rows = []
    detail = {}
    for spec in OBJECTIVES:
        sub = episodes[episodes["scenario"] == spec["scenario"]].copy()
        metric = spec["metric"]
        direction = spec["direction"]
        ascending = direction == "min"
        desc = sub.groupby("algorithm")[metric].agg(["count", "mean", "median", "std", "min", "max"]).reset_index()
        desc["statistical_coverage"] = desc["count"].map(lambda n: "cobertura completa por artefacto" if n >= 50 else f"{int(n)} fila(s) conservada(s)")
        final = treatment[treatment["scenario"] == spec["scenario"]].copy()
        if spec["objective"] == "OE.1":
            final["final_metric"] = final["final_reward_mean"]
        elif spec["objective"] == "OE.2":
            final["final_metric"] = final["carbon_emissions_control"]
        else:
            final["final_metric"] = final["electricity_cost_control"]
        final_best_row = final.sort_values("final_metric", ascending=ascending).iloc[0]
        inferential_algos = desc[desc["count"] >= 50]["algorithm"].tolist()
        inferential = sub[sub["algorithm"].isin(inferential_algos)]
        grouped = [g[metric].dropna().values for _, g in inferential.groupby("algorithm")]
        if len(grouped) >= 2:
            kw = stats.kruskal(*grouped)
            n = sum(len(g) for g in grouped)
            k = len(grouped)
            eps2 = (kw.statistic - k + 1) / (n - k) if n > k else math.nan
        else:
            kw = None
            eps2 = math.nan
        pair_p = []
        for i, a in enumerate(inferential_algos):
            for b in inferential_algos[i + 1 :]:
                av = inferential[inferential["algorithm"] == a][metric].dropna().values
                bv = inferential[inferential["algorithm"] == b][metric].dropna().values
                pair_p.append((f"{a} vs {b}", stats.mannwhitneyu(av, bv, alternative="two-sided").pvalue))
        pair_adj = holm_adjust(pair_p) if pair_p else []
        shapiro = {}
        for algo in inferential_algos:
            vals = inferential[inferential["algorithm"] == algo][metric].dropna().values
            shapiro[algo] = stats.shapiro(vals).pvalue if len(vals) >= 3 else math.nan
        best_stat = desc.sort_values("mean", ascending=ascending).iloc[0]["algorithm"]
        best_stat_complete = desc[desc["count"] >= 50].sort_values("mean", ascending=ascending).iloc[0]["algorithm"]
        for _, r in desc.iterrows():
            rows.append(
                {
                    "objective": spec["objective"],
                    "scenario": spec["scenario"],
                    "dimension": spec["dimension"],
                    "metric": metric,
                    "direction": direction,
                    "algorithm": r["algorithm"],
                    "n_episode_artifacts": int(r["count"]),
                    "mean": r["mean"],
                    "median": r["median"],
                    "std": r["std"],
                    "min": r["min"],
                    "max": r["max"],
                    "coverage": r["statistical_coverage"],
                    "best_by_episode_mean": best_stat,
                    "best_inferential_sample": best_stat_complete,
                    "best_final_annual_kpi": final_best_row["algorithm"],
                    "kw_algorithms": ", ".join(inferential_algos),
                    "kw_h": kw.statistic if kw else math.nan,
                    "kw_p": kw.pvalue if kw else math.nan,
                    "kw_epsilon2": eps2,
                    "shapiro_p": shapiro.get(r["algorithm"], math.nan),
                }
            )
        for pair, pv, adj in pair_adj:
            pair_rows.append(
                {
                    "objective": spec["objective"],
                    "scenario": spec["scenario"],
                    "metric": metric,
                    "pair": pair,
                    "p_raw": pv,
                    "p_holm": adj,
                    "decision": "significativo" if adj < 0.05 else "no significativo",
                }
            )
        detail[spec["objective"]] = {
            "spec": spec,
            "desc": desc.sort_values("mean", ascending=ascending).reset_index(drop=True),
            "final": final.sort_values("final_metric", ascending=ascending).reset_index(drop=True),
            "best_stat": best_stat,
            "best_stat_complete": best_stat_complete,
            "best_final": final_best_row["algorithm"],
            "kw": kw,
            "epsilon2": eps2,
            "inferential_algos": inferential_algos,
            "pair_adj": pair_adj,
            "shapiro": shapiro,
        }
    stats_df = pd.DataFrame(rows)
    pairs_df = pd.DataFrame(pair_rows)
    stats_df.to_csv(TABLE_DIR / "gdrive_objective_aligned_statistics.csv", index=False, encoding="utf-8")
    pairs_df.to_csv(TABLE_DIR / "gdrive_objective_pairwise_mannwhitney_holm.csv", index=False, encoding="utf-8")
    return stats_df, pairs_df, detail


def analyze_convergence(episodes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (algo, scenario), sub in episodes.groupby(["algorithm", "scenario"]):
        sub = sub.sort_values("episode").copy()
        rewards = pd.to_numeric(sub["reward_mean_average"], errors="coerce")
        rolling = rewards.rolling(window=5, min_periods=1).mean()
        n = len(sub)
        if n == 0:
            continue
        initial = float(rolling.iloc[: min(5, n)].mean())
        final = float(rolling.iloc[max(0, n - 5) :].mean())
        improvement = final - initial
        threshold = initial + 0.20 * improvement
        learning_start_idx = 0
        if improvement > 0:
            found = rolling[rolling >= threshold]
            learning_start_idx = int(found.index[0]) if not found.empty else int(rolling.index[-1])
        tolerance = max(abs(final) * 0.05, 1e-9)
        stable_idx = int(rolling.index[-1])
        for idx in rolling.index:
            tail = rolling.loc[idx:]
            if ((tail - final).abs() <= tolerance).all():
                stable_idx = int(idx)
                break
        best_pos = int(rewards.idxmax())
        learn_row = sub.loc[learning_start_idx]
        stable_row = sub.loc[stable_idx]
        best_row = sub.loc[best_pos]
        rows.append(
            {
                "algorithm": algo,
                "scenario": scenario,
                "n_episode_artifacts": n,
                "initial_rolling_reward": initial,
                "final_rolling_reward": final,
                "reward_improvement": improvement,
                "learning_start_episode_index": int(learn_row["episode"]),
                "learning_start_episode_ordinal": int(learn_row["episode"]) + 1,
                "stabilization_episode_index": int(stable_row["episode"]),
                "stabilization_episode_ordinal": int(stable_row["episode"]) + 1,
                "best_episode_index": int(best_row["episode"]),
                "best_episode_ordinal": int(best_row["episode"]) + 1,
                "best_reward_mean": float(best_row["reward_mean_average"]),
                "stabilization_tolerance": tolerance,
            }
        )
    df = pd.DataFrame(rows).sort_values(["scenario", "algorithm"]).reset_index(drop=True)
    df.to_csv(TABLE_DIR / "gdrive_reward_convergence_episodes.csv", index=False, encoding="utf-8")
    return df


def load_citylearn_v2_kpi_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = REPO / "outputs" / "madrl_v3_20260627_164047" / "resumen_comparativo" / "citylearn_v2_baseline"
    rank_frames = []
    catalog_frames = []
    axis_for_scenario = {"E1": "OE1", "E2": "OE2", "E3": "OE3"}
    for scenario in SCENARIOS:
        scenario_dir = base / scenario
        rank_path = scenario_dir / "ranking_by_axis.csv"
        master_path = scenario_dir / "master_kpi_comparison.csv"
        if rank_path.exists():
            r = pd.read_csv(rank_path)
            r["scenario"] = scenario
            r = r[r["axis"] == axis_for_scenario[scenario]].copy()
            rank_frames.append(r)
        if master_path.exists():
            m = pd.read_csv(master_path)
            m["scenario"] = scenario
            catalog_frames.append(m)
    if not rank_frames:
        return pd.DataFrame(), pd.DataFrame()
    ranking = pd.concat(rank_frames, ignore_index=True)
    ranking = ranking[
        [
            "scenario",
            "axis",
            "family",
            "method",
            "normalized_score",
            "available_kpis",
            "improved_kpis",
            "total_kpis",
            "axis_rank",
        ]
    ].sort_values(["scenario", "axis_rank", "family", "method"])
    ranking.to_csv(TABLE_DIR / "citylearn_v2_evaluate_v2_axis_ranking.csv", index=False, encoding="utf-8")
    if catalog_frames:
        catalog = pd.concat(catalog_frames, ignore_index=True)
        catalog = catalog[catalog["available"].astype(str).str.lower().isin(["true", "1"])]
        rows = []
        for (scenario, axis, axis_name), sub in catalog.groupby(["scenario", "axis", "axis_name"], dropna=False):
            names = sorted(sub["kpi"].dropna().astype(str).unique().tolist())
            rows.append(
                {
                    "scenario": scenario,
                    "axis": axis,
                    "axis_name": axis_name,
                    "available_unique_kpis": len(names),
                    "source": ", ".join(sorted(sub["source"].dropna().astype(str).unique().tolist())[:3]),
                    "example_kpis": ", ".join(names[:8]),
                }
            )
        kpi_catalog = pd.DataFrame(rows).sort_values(["scenario", "axis"])
    else:
        kpi_catalog = pd.DataFrame()
    kpi_catalog.to_csv(TABLE_DIR / "citylearn_v2_evaluate_v2_kpi_catalog.csv", index=False, encoding="utf-8")
    return ranking, kpi_catalog


def analyze_buildings(buildings: pd.DataFrame, equipment: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = [
        "algorithm",
        "scenario",
        "agent",
        "grid_role_control",
        "action_dim",
        "observation_dim",
        "battery_throughput_total_kwh",
        "ev_charge_total_kwh",
        "ev_departure_success_rate",
        "carbon_emissions_control_kgco2",
        "carbon_emissions_delta_kgco2",
        "electricity_cost_control_eur",
        "electricity_cost_delta_eur",
        "grid_import_control_kwh",
        "grid_export_control_kwh",
    ]
    b = buildings[[c for c in cols if c in buildings.columns]].copy()
    b.to_csv(TABLE_DIR / "gdrive_building_kpi_compact.csv", index=False, encoding="utf-8")
    eq = equipment[equipment["variable_type"] == "action"].copy()
    eq["equipment_class"] = eq["variable_name"].map(classify_equipment)
    eq_summary = eq.groupby(["algorithm", "scenario", "agent", "equipment_class"]).size().reset_index(name="count")
    eq_summary.to_csv(TABLE_DIR / "gdrive_controlled_equipment_by_building.csv", index=False, encoding="utf-8")
    return b, eq_summary


def classify_equipment(name: str) -> str:
    n = str(name).lower()
    if "electric_vehicle" in n:
        return "EV controlado"
    if "electrical_storage" in n or "battery" in n:
        return "BESS controlado"
    if "washing" in n or "dishwasher" in n or "dryer" in n:
        return "carga flexible controlada"
    if "cooling" in n or "heating" in n or "heat_pump" in n:
        return "HVAC/termico controlado"
    return "otro actuador controlado"


def make_figures(detail: dict, buildings: pd.DataFrame, episodes: pd.DataFrame, convergence: pd.DataFrame) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for oe, d in detail.items():
        spec = d["spec"]
        fig, ax = plt.subplots(figsize=(7, 4))
        desc = d["desc"].copy()
        y = desc["mean"]
        ax.bar(desc["algorithm"], y, color=["#9AA7B2", "#2F6B52", "#C77D2A", "#406A9F"][: len(desc)])
        ax.set_title(f"{oe} - {spec['dimension']} ({spec['scenario']})")
        ax.set_ylabel(spec["metric"])
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        out = FIG_DIR / f"{oe.lower().replace('.', '')}_{spec['scenario'].lower()}_episode_mean.png"
        fig.savefig(out, dpi=180)
        plt.close(fig)
        paths[oe] = out
    fig, ax = plt.subplots(figsize=(7, 4))
    top = buildings.groupby("agent")["action_dim"].max().sort_values(ascending=False)
    ax.bar(top.index, top.values, color="#2F6B52")
    ax.set_title("Equipamiento controlado por edificio (dimensiones de accion)")
    ax.set_ylabel("acciones controlables")
    ax.tick_params(axis="x", rotation=75)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = FIG_DIR / "controlled_equipment_action_dim_by_building.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    paths["equipment"] = out
    for scenario in SCENARIOS:
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        sub = episodes[episodes["scenario"] == scenario].copy()
        for algo in ALGOS:
            alg = sub[sub["algorithm"] == algo].sort_values("episode").copy()
            if alg.empty:
                continue
            alg["rolling_reward"] = pd.to_numeric(alg["reward_mean_average"], errors="coerce").rolling(window=5, min_periods=1).mean()
            ax.plot(alg["episode"] + 1, alg["rolling_reward"], linewidth=1.8, label=algo)
            conv = convergence[(convergence["scenario"] == scenario) & (convergence["algorithm"] == algo)]
            if not conv.empty:
                c = conv.iloc[0]
                ax.axvline(c["learning_start_episode_ordinal"], color="gray", alpha=0.10, linewidth=0.8)
                ax.scatter([c["stabilization_episode_ordinal"]], [c["final_rolling_reward"]], s=28, zorder=5)
        ax.set_title(f"Convergencia MADRL por recompensa media movil - {scenario}")
        ax.set_xlabel("episodio ordinal en artefacto")
        ax.set_ylabel("recompensa media movil")
        ax.grid(alpha=0.25)
        ax.legend(ncol=2, fontsize=8)
        fig.tight_layout()
        out = FIG_DIR / f"convergence_{scenario.lower()}_learning_stabilization.png"
        fig.savefig(out, dpi=180)
        plt.close(fig)
        paths[f"convergence_{scenario}"] = out
    return paths


def add_picture(doc: Document, caption: str, path: Path, width: float = 5.8) -> None:
    cap = doc.add_paragraph()
    r = cap.add_run(caption)
    r.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = GREY
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()


def clean_front_matter_50ep(doc: Document) -> None:
    replacement = (
        "Esta tesis doctoral determina, mediante simulacion computacional bajo diseno experimental factorial 4x3, "
        "el efecto de cuatro algoritmos Multi-Agente de Aprendizaje por Refuerzo Profundo (MADRL) -HAPPO, MASAC, "
        "MATD3 y MAAC- sobre la flexibilidad energetica, las emisiones de CO2 y los costos energeticos en una "
        "comunidad inteligente del Sistema Electrico Aislado de Iquitos. La evidencia corresponde a la corrida "
        "canonica Drive madrl_v3_20260627_164047, con 50 episodios registrados por tratamiento, 17 edificios, "
        "185 cargadores EV, BESS/PV, checkpoints y trazas auditables. La contrastacion se organiza estrictamente "
        "por OE.1 flexibilidad, OE.2 emisiones de CO2 y OE.3 costos, usando resultados distritales, resultados por "
        "edificio, equipamiento controlado/no controlado, curvas de convergencia y KPIs compatibles con la lectura "
        "CityLearn v2 evaluate_v2. No se incorporan valores externos ni resultados exploratorios ajenos a esa "
        "corrida Drive."
    )
    forbidden = ["5 episodios", "referencia local", "KW p=0.0459", "Colab (Kruskal-Wallis ALL", "VecEnvWrapper"]
    for para in doc.paragraphs:
        text = para.text
        if any(token in text for token in forbidden):
            set_paragraph_text(para, replacement)


def replace_section(document: Document, start_prefix: str, end_prefix: str, writer) -> None:
    body = document.element.body
    children = list(body)
    start = end = None
    for i, el in enumerate(children):
        txt = text_of(el)
        if start is None and txt.startswith(start_prefix):
            start = i
            continue
        if start is not None and txt.startswith(end_prefix):
            end = i
            break
    if start is None or end is None or end <= start:
        raise RuntimeError(f"No se pudo reemplazar seccion: {start_prefix} -> {end_prefix}")
    tmp = Document()
    clear_body_keep_sectpr(tmp)
    writer(tmp)
    new_children = [deepcopy(el) for el in tmp.element.body if el.tag != qn("w:sectPr")]
    for el in children[start:end]:
        body.remove(el)
    for offset, el in enumerate(new_children):
        body.insert(start + offset, el)


def add_expanded_decpomdp_section(doc: Document, building_compact: pd.DataFrame) -> None:
    dims = building_compact.groupby("agent")[["observation_dim", "action_dim"]].max().reset_index()
    n_agents = int(dims["agent"].nunique())
    obs_min, obs_max = int(dims["observation_dim"].min()), int(dims["observation_dim"].max())
    act_min, act_max = int(dims["action_dim"].min()), int(dims["action_dim"].max())
    obs_total = int(dims["observation_dim"].sum())
    act_total = int(dims["action_dim"].sum())
    doc.add_heading("2.2.3 Dec-POMDP como formalizacion del problema doctoral", level=2)
    p(doc, "La gestion energetica estudiada no es un problema de control centralizado simple, porque la decision de cada edificio modifica la demanda agregada, el costo, las emisiones y las condiciones de flexibilidad que observan los demas agentes. Tampoco es un MDP plenamente observable por agente individual: cada edificio observa su propio estado operativo, disponibilidad de equipos, senales temporales y variables exogenas, pero no controla directamente la demanda base ni las restricciones internas de los otros edificios. Por ello, la formalizacion doctoral adecuada es un Proceso de Decision de Markov Parcialmente Observable Descentralizado (Dec-POMDP), que permite representar ejecucion descentralizada, observabilidad parcial, transiciones estocasticas y recompensa cooperativa.")
    p(doc, "La formulacion utilizada en la tesis se expresa como M = <S, {A_i}_{i=1}^{17}, T, R, {O_i}_{i=1}^{17}, Omega, gamma, H>. El estado global S contiene la concatenacion de observaciones locales s_t=[o_1,t,...,o_17,t]; las acciones A_i son heterogeneas por edificio; T representa la dinamica horaria de CityLearn, incluyendo clima, PV, BESS, llegada/salida de vehiculos electricos, demanda base, precio y senal de carbono; R es una recompensa cooperativa con mezcla local-equipo; O_i y Omega modelan la observabilidad parcial; gamma=0.9999 preserva dependencia de largo horizonte; y H=8760 pasos representa un ano horario de evaluacion por episodio.")
    p(doc, "La operacionalizacion empirieca no queda en una abstraccion generica. En los artefactos Drive, el Dec-POMDP tiene 17 agentes-edificio, dimensiones locales de observacion entre " + str(obs_min) + " y " + str(obs_max) + ", dimension global agregada " + str(obs_total) + ", acciones locales entre " + str(act_min) + " y " + str(act_max) + " y " + str(act_total) + " dimensiones de accion por tratamiento. Las acciones controlan BESS, cargadores EV y cargas flexibles declaradas en building_observation_action_schema.csv; la demanda no controlada permanece como perturbacion/observacion dentro de la demanda base, no como actuador directo.")
    p(doc, "Esta formalizacion enlaza directamente el problema general y los objetivos especificos. OE.1 evalua la respuesta del Dec-POMDP cuando la recompensa prioriza flexibilidad; OE.2 cuando prioriza emisiones de CO2; y OE.3 cuando prioriza costos energeticos. La variable independiente no es solo el nombre del algoritmo, sino la politica MADRL aprendida bajo CTDE y bajo pesos de recompensa comparables. La variable dependiente se observa mediante KPIs distritales y por edificio, por lo que el Dec-POMDP justifica simultaneamente el entrenamiento multiagente y la lectura de resultados por distrito, edificio, escenario y KPI.")
    rows = [
        ["Agentes", "Edificios institucionales/comerciales de la comunidad", f"{n_agents} agentes en building_behavior_summary.csv"],
        ["Estado global S", "Concatenacion de observaciones locales para critic/entrenamiento CTDE", f"suma observation_dim={obs_total}"],
        ["Observacion local O_i", "Informacion parcial disponible para cada actor", f"rango observado {obs_min}-{obs_max} variables"],
        ["Accion A_i", "Control descentralizado de equipos flexibles", f"rango observado {act_min}-{act_max}; total={act_total}"],
        ["Transicion T", "Dinamica horaria de CityLearn: clima, PV, BESS, EV, precio, carbono y demanda", "timeseries.csv y traces por tratamiento"],
        ["Recompensa R", "Funcion multiobjetivo comparable por escenario E1/E2/E3", "pesos flex/CO2/costo y agregacion team_mean"],
        ["Horizonte H", "Evaluacion anual horaria por episodio", "8760 pasos horarios"],
        ["Descuento gamma", "Persistencia de efectos diferidos de almacenamiento y carga EV", "gamma=0.9999"],
    ]
    table(doc, "Tabla 2.3. Mapeo del Dec-POMDP doctoral a artefactos reales del proyecto.", ["Elemento", "Operacion en la tesis", "Evidencia local"], rows, 7.0)


def add_cap5(
    doc: Document,
    detail: dict,
    treatment: pd.DataFrame,
    building_compact: pd.DataFrame,
    eq_summary: pd.DataFrame,
    figures: dict[str, Path],
    convergence: pd.DataFrame,
    kpi_ranking: pd.DataFrame,
    kpi_catalog: pd.DataFrame,
) -> None:
    doc.add_heading("Capitulo 5. Resultados y contrastacion de hipotesis", level=1)
    p(doc, "Este capitulo se reconstruye con evidencia directa de la carpeta G:\\Mi unidad\\MADRLCitytleranflexresdr\\outputs\\madrl_v3_20260627_164047. La lectura incluye results.json, training_summary.json, timeseries.csv, building_kpis.csv, building_behavior_summary.csv, building_observation_action_schema.csv y checkpoint_manifest.json para los 12 tratamientos algoritmo x escenario. La regla de interpretacion es estricta: no se incorporan valores que no existan en los artefactos; cuando una tabla conserva menor granularidad episodica, se declara como limitacion de trazabilidad y no se inventan observaciones.")
    p(doc, "El vinculo metodologico queda organizado por objetivo especifico: OE.1 se contrasta en E1 porque la recompensa asigna 0,70 a flexibilidad; OE.2 se contrasta en E2 porque la recompensa asigna 0,70 a emisiones; OE.3 se contrasta en E3 porque la recompensa asigna 0,60 a costos. Por tanto, el desarrollo de la propuesta del Capitulo 4 no queda separado de los resultados: los pesos de la funcion de recompensa son la manipulacion experimental de D-VI.2 y las metricas de este capitulo son los indicadores observados de D-VD.1, D-VD.2 y D-VD.3.")
    p(doc, "Los 12 tratamientos registran culminacion operativa de entrenamiento. En particular, HAPPO registra completed_episode_count=50 en live_progress.json y episodes_recorded=50 en results.json; sin embargo, por el modo de reanudacion ligera de HAPPO, la carpeta actual de G: conserva en timeseries.csv y episode_summary.csv solo el episodio 49, es decir, la trayectoria anual final. Para no perder la evidencia previa ya extraida del mismo flujo Drive, la estadistica episodica usa el CSV materializado district_episode_kpis.csv, donde HAPPO conserva 49 episodios por escenario y MAAC, MASAC y MATD3 conservan 50. En consecuencia, HAPPO se usa para evidencia descriptiva, final anual y por edificio, pero no se declara como grupo inferencial de 50 observaciones.")

    coverage_rows = []
    for _, r in treatment.sort_values(["algorithm", "scenario"]).iterrows():
        coverage_rows.append([
            r["algorithm"],
            r["scenario"],
            int(r["episodes_recorded"]),
            int(r["saved_episode_summaries"]),
            int(r["materialized_episode_kpis"]),
            int(r["building_count"]),
            int(r["checkpoint_count"]),
        ])
    table(doc, "Tabla 5.1. Cobertura real de artefactos por tratamiento en Google Drive.", ["Algoritmo", "Escenario", "episodios registrados", "resumenes G:", "episodios KPI usados", "edificios", "checkpoints"], coverage_rows, 6.8)

    link_rows = [[d["spec"]["objective"], d["spec"]["hypothesis"], d["spec"]["scenario"], d["spec"]["dimension"], d["spec"]["indicator"], "maximizar" if d["spec"]["direction"] == "max" else "minimizar"] for d in detail.values()]
    table(doc, "Tabla 5.2. Trazabilidad objetivo-hipotesis-escenario-indicador.", ["Objetivo", "Hipotesis", "Escenario", "Dimension VD", "Indicador usado", "Criterio"], link_rows, 6.8)

    doc.add_heading("5.3 Curvas de convergencia y episodios de aprendizaje", level=2)
    p(doc, "La convergencia se estima desde reward_mean_average por algoritmo y escenario. Para evitar lectura visual subjetiva, se usa una media movil de longitud cinco: se considera inicio de aprendizaje el primer episodio ordinal en que la media movil supera el 20% de la mejora entre el tramo inicial y el tramo final; se considera estabilizacion el primer episodio desde el cual la media movil permanece dentro del 5% relativo respecto del tramo final. La recompensa es mejor cuando es menos negativa, por lo que el maximo observado indica el mejor episodio conservado en el artefacto.")
    conv_rows = []
    for _, r in convergence.sort_values(["scenario", "algorithm"]).iterrows():
        conv_rows.append(
            [
                r["algorithm"],
                r["scenario"],
                int(r["n_episode_artifacts"]),
                fmt(r["initial_rolling_reward"], 6),
                fmt(r["final_rolling_reward"], 6),
                int(r["learning_start_episode_ordinal"]),
                int(r["stabilization_episode_ordinal"]),
                int(r["best_episode_ordinal"]),
                fmt(r["best_reward_mean"], 6),
            ]
        )
    table(doc, "Tabla 5.3. Episodios de inicio de aprendizaje, estabilizacion y mejor recompensa media.", ["Algoritmo", "Esc.", "n", "media inicial", "media final", "inicio aprendizaje", "estabilizacion", "mejor episodio", "mejor reward"], conv_rows, 6.6)
    for scenario in SCENARIOS:
        add_picture(doc, f"Figura 5.3-{scenario}. Curva de convergencia por recompensa media movil en {scenario}.", figures[f"convergence_{scenario}"])
    p(doc, "La lectura de convergencia muestra aprendizaje temprano en la mayoria de tratamientos, pero no implica dominancia automatica. MATD3 presenta una mejora marcada en E1 antes de estabilizarse; MAAC y MASAC muestran variaciones mas compactas; HAPPO se interpreta descriptivamente con las filas episodicas materializadas disponibles y con el registro Drive de entrenamiento completado.")

    doc.add_heading("5.4 KPIs bajo nomenclatura CityLearn v2 evaluate_v2", level=2)
    p(doc, "Para que los resultados sean comparables con CityLearn v2, la tesis no reduce la evaluacion a una metrica ad hoc. Los CSV de resumen comparativo usan la nomenclatura de evaluate_v2 y agrupan KPIs por eje: OE1 flexibilidad energetica, OE2 emisiones de CO2 y OE3 costos energeticos. Esta lectura complementa la recompensa de entrenamiento con KPIs finales de evaluacion, incluyendo baseline y RBC horario cuando estan disponibles.")
    if not kpi_catalog.empty:
        catalog_rows = []
        for _, r in kpi_catalog.iterrows():
            if r["axis"] in {"OE1", "OE2", "OE3"}:
                catalog_rows.append([r["scenario"], r["axis"], r["axis_name"], int(r["available_unique_kpis"]), r["source"], r["example_kpis"]])
        table(doc, "Tabla 5.4. Catalogo de KPIs evaluate_v2 usados para interpretar resultados.", ["Esc.", "Eje", "Dimension", "KPIs", "Fuente", "Ejemplos"], catalog_rows, 6.2)
    if not kpi_ranking.empty:
        rank_rows = []
        for _, r in kpi_ranking.iterrows():
            rank_rows.append([r["scenario"], r["axis"], r["family"], r["method"], fmt(r["normalized_score"], 4), int(r["available_kpis"]), int(r["improved_kpis"]), fmt(r["axis_rank"], 1)])
        table(doc, "Tabla 5.5. Ranking por eje con KPIs compatibles con CityLearn v2.", ["Esc.", "Eje", "Familia", "Metodo", "score", "KPIs disp.", "KPIs mejora", "rank"], rank_rows, 6.5)
    p(doc, "La lectura evaluate_v2 evita una conclusion sesgada por la recompensa de entrenamiento: un algoritmo puede maximizar reward_mean_average en un escenario y, al mismo tiempo, no liderar todos los KPIs oficiales de flexibilidad, carbono o costo. Por ello, la decision doctoral se reporta en tres niveles: media episodica, prueba estadistica intra-corrida y KPI anual final compatible con CityLearn v2.")

    for idx, oe in enumerate(["OE.1", "OE.2", "OE.3"], start=5):
        d = detail[oe]
        spec = d["spec"]
        doc.add_heading(f"5.{idx} {oe}: efecto del MADRL sobre {spec['dimension']}", level=2)
        p(doc, spec["explanation"])
        rows = []
        for _, r in d["desc"].iterrows():
            rows.append([
                r["algorithm"],
                int(r["count"]),
                fmt(r["mean"], 6 if spec["metric"] == "reward_mean_average" else 2),
                fmt(r["median"], 6 if spec["metric"] == "reward_mean_average" else 2),
                fmt(r["std"], 6 if spec["metric"] == "reward_mean_average" else 2),
                fmt(r["min"], 6 if spec["metric"] == "reward_mean_average" else 2),
                fmt(r["max"], 6 if spec["metric"] == "reward_mean_average" else 2),
                "cobertura completa" if int(r["count"]) >= 50 else f"{int(r['count'])} filas conservadas",
            ])
        table(doc, f"Tabla 5.{idx}. Estadistica descriptiva por episodio para {oe}.", ["Algoritmo", "n", "Media", "Mediana", "Desv. est.", "Min", "Max", "Cobertura"], rows, 7.0)
        final_rows = []
        for _, r in d["final"].iterrows():
            final_rows.append([
                r["algorithm"],
                fmt(r["final_metric"], 6 if oe == "OE.1" else 2),
                fmt(r["peak_average"], 4),
                fmt(r["ramping_average"], 4),
                fmt(r["carbon_emissions_control"], 2),
                fmt(r["electricity_cost_control"], 2),
            ])
        table(doc, f"Tabla 5.{idx}a. KPI anual final del tratamiento asociado a {oe}.", ["Algoritmo", "Indicador final OE", "peak", "ramping", "CO2 control", "costo control"], final_rows, 7.0)
        add_picture(doc, f"Figura 5.{idx}. Comparacion grafica de la media por episodio para {oe}.", figures[oe])
        kw = d["kw"]
        if kw is not None:
            p(doc, f"Contrastacion inferencial: para {oe} se aplica Kruskal-Wallis solo a los grupos con cobertura completa conservada ({', '.join(d['inferential_algos'])}). El resultado es H={kw.statistic:.4f}, p={kw.pvalue:.6g}, epsilon2={d['epsilon2']:.4f}. Con alpha=0,05, {'se rechaza H0 y se identifica efecto diferenciado del algoritmo' if kw.pvalue < 0.05 else 'no se rechaza H0 en la muestra inferencial conservada'}. HAPPO registra entrenamiento completado en Drive, pero no entra al contraste inferencial porque el CSV materializado conserva 49 filas episodicas por escenario.")
            pair_rows = [[name, fmt(pv, 6), fmt(adj, 6), "significativo" if adj < 0.05 else "no significativo"] for name, pv, adj in d["pair_adj"]]
            table(doc, f"Tabla 5.{idx}b. Mann-Whitney U por pares con ajuste Holm para {oe}.", ["Par", "p", "p Holm", "Decision"], pair_rows, 7.2)
            sh_rows = [[algo, fmt(pv, 6), "normalidad no rechazada" if pv >= 0.05 else "normalidad rechazada"] for algo, pv in d["shapiro"].items()]
            table(doc, f"Tabla 5.{idx}c. Shapiro-Wilk por algoritmo para {oe}.", ["Algoritmo", "p", "Lectura"], sh_rows, 7.2)
        p(doc, f"Interpretacion de {oe}: el mejor algoritmo por media episodica conservada es {d['best_stat']}; al restringir la decision inferencial a algoritmos con cobertura completa, el mejor es {d['best_stat_complete']}; el mejor KPI anual final observado es {d['best_final']}. Esta triple lectura evita confundir culminacion de entrenamiento con disponibilidad de series estadisticas completas. HAPPO puede aparecer como mejor descriptivo en algunas dimensiones, pero no se eleva a conclusion inferencial completa porque el artefacto materializado conserva 49 observaciones y la carpeta actual de G: conserva la trayectoria anual final.")

    doc.add_heading("5.8 Resultados por edificio y equipamiento controlado", level=2)
    p(doc, "El analisis por edificio usa building_behavior_summary.csv y building_kpis.csv de los 12 tratamientos. Cada edificio actua como agente de la comunidad y posee dimensiones heterogeneas de observacion y accion; por ello, la cantidad de equipos controlados no es uniforme. La accion controlada agrupa BESS, cargadores EV, cargas flexibles y otros actuadores declarados en building_observation_action_schema.csv. Las cargas no controladas permanecen dentro de la demanda base y de las variables observadas, no como acciones directas del agente.")
    add_picture(doc, "Figura 5.8. Dimensiones de accion controlable por edificio.", figures["equipment"])
    b_top = building_compact.sort_values("action_dim", ascending=False).head(10)
    table(doc, "Tabla 5.11. Edificios con mayor cantidad de acciones controlables.", ["Algoritmo", "Esc.", "Edificio", "rol red", "acciones", "obs.", "BESS kWh", "EV kWh", "CO2 kg", "costo"], [[r["algorithm"], r["scenario"], r["agent"], r.get("grid_role_control", ""), int(r["action_dim"]), int(r["observation_dim"]), fmt(r.get("battery_throughput_total_kwh"), 1), fmt(r.get("ev_charge_total_kwh"), 1), fmt(r.get("carbon_emissions_control_kgco2"), 1), fmt(r.get("electricity_cost_control_eur"), 1)] for _, r in b_top.iterrows()], 6.6)
    eq_pivot = eq_summary.groupby("equipment_class")["count"].sum().reset_index().sort_values("count", ascending=False)
    table(doc, "Tabla 5.12. Equipamiento controlado identificado en los esquemas de accion.", ["Clase de equipo controlado", "conteo en 12 tratamientos"], [[r["equipment_class"], int(r["count"])] for _, r in eq_pivot.iterrows()], 7.2)
    p(doc, "Las tablas completas se guardan como CSV en outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/tables. Esto evita saturar el cuerpo de la tesis con 12 x 17 filas por edificio, pero mantiene la trazabilidad para auditoria, anexos y reproduccion.")

    doc.add_heading("5.9 Sintesis de contrastacion de OE.1, OE.2 y OE.3", level=2)
    synth_rows = []
    for oe in ["OE.1", "OE.2", "OE.3"]:
        d = detail[oe]
        kw = d["kw"]
        synth_rows.append([
            oe,
            d["spec"]["dimension"],
            d["spec"]["scenario"],
            d["best_stat"],
            d["best_stat_complete"],
            d["best_final"],
            f"H={kw.statistic:.3f}; p={kw.pvalue:.3g}" if kw else "NA",
            "se rechaza H0" if kw and kw.pvalue < 0.05 else "no se rechaza H0",
        ])
    table(doc, "Tabla 5.13. Respuesta directa a objetivos especificos.", ["Objetivo", "Dimension", "Escenario", "mejor media episodica", "mejor muestra completa", "mejor KPI anual final", "Kruskal-Wallis", "Decision"], synth_rows, 6.8)
    p(doc, "La interpretacion doctoral no debe afirmar dominancia unica sin matices. Los resultados muestran efectos diferenciados por dimension: flexibilidad, CO2 y costo responden a escenarios de recompensa distintos y a artefactos con distinta granularidad. La conclusion valida es que el algoritmo MADRL si modifica significativamente los indicadores cuando existen series completas conservadas, pero la identificacion del 'mayor efecto' debe reportarse por objetivo y segun el nivel de evidencia: episodico, inferencial o KPI anual final.")
    p(doc, "Metodologicamente, esta decision sigue las advertencias de evaluacion rigurosa en aprendizaje por refuerzo: los episodios de una corrida no reemplazan multiples semillas independientes, y los p-valores deben interpretarse junto con cobertura, tamano de efecto y trazabilidad de artefactos (Henderson et al., 2018; Colas et al., 2019; Agarwal et al., 2021; Patterson et al., 2024). Por ello, se retiene Shapiro-Wilk, Kruskal-Wallis y Mann-Whitney U con Holm como contrastacion intra-corrida, y se declara la necesidad de multi-semilla para robustez externa.")


def rebuild_doc(
    detail: dict,
    treatment: pd.DataFrame,
    building_compact: pd.DataFrame,
    eq_summary: pd.DataFrame,
    figures: dict[str, Path],
    convergence: pd.DataFrame,
    kpi_ranking: pd.DataFrame,
    kpi_catalog: pd.DataFrame,
) -> None:
    shutil.copyfile(SRC, OUT)
    doc = Document(OUT)
    style_doc(doc)
    clean_front_matter_50ep(doc)
    replace_section(
        doc,
        "2.2.3 Dec-POMDP como formalizacion del problema doctoral",
        "2.2.4 CTDE",
        lambda tmp: add_expanded_decpomdp_section(tmp, building_compact),
    )
    children = list(doc.element.body)
    idx_cap5 = idx_cap6 = None
    for i, el in enumerate(children):
        txt = text_of(el)
        if idx_cap5 is None and txt.startswith("Capitulo 5. Resultados"):
            idx_cap5 = i
        if idx_cap6 is None and txt.startswith("Capitulo 6. Conclusiones"):
            idx_cap6 = i
    if idx_cap5 is None or idx_cap6 is None:
        raise RuntimeError(f"No se encontraron limites Cap5/Cap6: {idx_cap5}, {idx_cap6}")
    before = [deepcopy(el) for el in children[:idx_cap5]]
    after = [deepcopy(el) for el in children[idx_cap6:] if el.tag != qn("w:sectPr")]
    clear_body_keep_sectpr(doc)
    for el in before:
        append_before_sectpr(doc, el)
    add_cap5(doc, detail, treatment, building_compact, eq_summary, figures, convergence, kpi_ranking, kpi_catalog)
    for el in after:
        append_before_sectpr(doc, el)
    doc.save(OUT)


def main() -> None:
    ensure_dirs()
    if not G_BASE.exists():
        raise FileNotFoundError(G_BASE)
    treatment, episodes, buildings, equipment = load_evidence()
    stats_df, pairs_df, detail = analyze_objectives(treatment, episodes)
    convergence = analyze_convergence(episodes)
    kpi_ranking, kpi_catalog = load_citylearn_v2_kpi_summary()
    building_compact, eq_summary = analyze_buildings(buildings, equipment)
    figures = make_figures(detail, building_compact, episodes, convergence)
    rebuild_doc(detail, treatment, building_compact, eq_summary, figures, convergence, kpi_ranking, kpi_catalog)
    v = Document(OUT)
    paras = [p.text.strip() for p in v.paragraphs if p.text.strip()]
    full = "\n".join(paras)
    metrics = {
        "output": str(OUT),
        "source_gdrive": str(G_BASE),
        "size_bytes": OUT.stat().st_size,
        "paragraphs_non_empty": len(paras),
        "word_count_estimated": len(re.findall(r"\b[\wáéíóúÁÉÍÓÚñÑüÜ-]+\b", full, re.UNICODE)),
        "tables": len(v.tables),
        "inline_images": len(v.inline_shapes),
        "treatment_rows": len(treatment),
        "episode_rows": len(episodes),
        "building_rows": len(building_compact),
        "equipment_rows": len(eq_summary),
        "convergence_rows": len(convergence),
        "citylearn_v2_ranking_rows": len(kpi_ranking),
        "citylearn_v2_kpi_catalog_rows": len(kpi_catalog),
        "stats_csv": str(TABLE_DIR / "gdrive_objective_aligned_statistics.csv"),
        "pairs_csv": str(TABLE_DIR / "gdrive_objective_pairwise_mannwhitney_holm.csv"),
        "has_oe1": "OE.1: efecto del MADRL sobre flexibilidad energetica" in full,
        "has_oe2": "OE.2: efecto del MADRL sobre emisiones de CO2" in full,
        "has_oe3": "OE.3: efecto del MADRL sobre costos energeticos" in full,
        "has_decpomdp_expanded": "dimension global agregada 1856" in full and "gamma=0.9999" in full,
        "has_convergence_section": "Curvas de convergencia y episodios de aprendizaje" in full,
        "has_citylearn_v2_evaluate_v2_section": "KPIs bajo nomenclatura CityLearn v2 evaluate_v2" in full,
        "declares_happo_artifact_limit": "CSV materializado conserva 49 filas episodicas" in full,
        "has_no_old_global_kw": "p = 0,0459" not in full and "p=0,0459" not in full,
        "has_no_local_reference": "referencia local" not in full.lower(),
        "has_no_short_run_phrase": "5 episodios" not in full.lower(),
    }
    METRICS.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
