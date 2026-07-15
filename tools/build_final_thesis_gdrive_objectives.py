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
        sub = sub.sort_values("episode").reset_index(drop=True).copy()
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


def load_final_episode_timeseries(treatment: pd.DataFrame) -> pd.DataFrame:
    out_path = TABLE_DIR / "gdrive_final_episode_timeseries_compact.csv"
    frames = []
    cols = [
        "algorithm",
        "scenario",
        "episode",
        "episode_step",
        "time_step",
        "district_net_electricity_consumption",
        "district_net_electricity_consumption_without_storage",
        "district_net_electricity_consumption_cost",
        "district_net_electricity_consumption_emission",
        "electricity_price_mean",
        "carbon_intensity_mean",
        "reward_mean",
    ]
    for _, r in treatment.iterrows():
        algo = r["algorithm"]
        scenario = r["scenario"]
        final_episode = int(r["final_episode_in_artifacts"]) if not pd.isna(r["final_episode_in_artifacts"]) else 49
        path = G_BASE / algo / scenario / "data" / "timeseries.csv"
        if not path.exists():
            continue
        parts = []
        for chunk in pd.read_csv(path, usecols=lambda c: c in cols, chunksize=100_000):
            if "episode" not in chunk.columns:
                continue
            sub = chunk[pd.to_numeric(chunk["episode"], errors="coerce") == final_episode].copy()
            if not sub.empty:
                parts.append(sub)
        if parts:
            df = pd.concat(parts, ignore_index=True)
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    ts = pd.concat(frames, ignore_index=True)
    ts.to_csv(out_path, index=False, encoding="utf-8")
    return ts


def load_trace_samples() -> pd.DataFrame:
    out_path = TABLE_DIR / "gdrive_trace_samples_all.csv"
    frames = []
    for algo in ALGOS:
        for scenario in SCENARIOS:
            path = G_BASE / algo / scenario / "data" / "trace.csv"
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path)
            except pd.errors.EmptyDataError:
                continue
            if df.empty:
                continue
            df["algorithm"] = algo
            df["scenario"] = scenario
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    traces = pd.concat(frames, ignore_index=True)
    traces.to_csv(out_path, index=False, encoding="utf-8")
    return traces


def load_checkpoint_summary() -> pd.DataFrame:
    rows = []
    for algo in ALGOS:
        for scenario in SCENARIOS:
            path = G_BASE / algo / scenario / "data" / "checkpoint_manifest.json"
            if not path.exists():
                continue
            data = read_json(path)
            for ckpt in data.get("checkpoints", []):
                rel = ckpt.get("relative_path", "")
                match = re.search(r"episode_(\d+)", rel)
                rows.append(
                    {
                        "algorithm": algo,
                        "scenario": scenario,
                        "checkpoint_count": data.get("checkpoint_count"),
                        "checkpoint_episode": int(match.group(1)) if match else math.nan,
                        "bytes": ckpt.get("bytes", math.nan),
                        "relative_path": rel,
                    }
                )
    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(TABLE_DIR / "gdrive_checkpoint_manifest_compact.csv", index=False, encoding="utf-8")
    return df


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


def make_figures(
    detail: dict,
    treatment: pd.DataFrame,
    buildings: pd.DataFrame,
    eq_summary: pd.DataFrame,
    episodes: pd.DataFrame,
    convergence: pd.DataFrame,
    kpi_ranking: pd.DataFrame,
    final_ts: pd.DataFrame,
    traces: pd.DataFrame,
    checkpoints: pd.DataFrame,
) -> dict[str, Path]:
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

    # Distribucion episodica por objetivo: permite ver dispersion, mediana y atipicos.
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    for ax, oe in zip(axes, ["OE.1", "OE.2", "OE.3"]):
        spec = detail[oe]["spec"]
        metric = spec["metric"]
        sub = episodes[episodes["scenario"] == spec["scenario"]].copy()
        data = [sub[sub["algorithm"] == algo][metric].dropna().values for algo in ALGOS]
        ax.boxplot(data, labels=ALGOS, showmeans=True)
        ax.set_title(f"{oe} - {spec['dimension']}")
        ax.set_ylabel(metric)
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    out = FIG_DIR / "episode_objective_distributions_boxplot.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    paths["episode_boxplots"] = out

    fig, ax = plt.subplots(figsize=(7, 4))
    oes = ["OE.1", "OE.2", "OE.3"]
    vals = [detail[oe]["epsilon2"] for oe in oes]
    ax.bar(oes, vals, color=["#2F6B52", "#406A9F", "#C77D2A"])
    for i, oe in enumerate(oes):
        kw = detail[oe]["kw"]
        ax.text(i, vals[i] + 0.005, f"p={kw.pvalue:.3g}", ha="center", fontsize=8)
    ax.axhline(0.01, color="gray", linestyle="--", linewidth=0.8)
    ax.axhline(0.06, color="gray", linestyle=":", linewidth=0.8)
    ax.axhline(0.14, color="gray", linestyle="-.", linewidth=0.8)
    ax.set_title("Tamano de efecto inferencial por objetivo (epsilon2)")
    ax.set_ylabel("epsilon2 Kruskal-Wallis")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out = FIG_DIR / "objective_effect_size_epsilon2.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    paths["effect_size"] = out

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, oe in zip(axes, ["OE.1", "OE.2", "OE.3"]):
        labels = ALGOS
        mat = pd.DataFrame(1.0, index=labels, columns=labels)
        for name, _pv, adj in detail[oe]["pair_adj"]:
            a, b = name.split(" vs ")
            mat.loc[a, b] = adj
            mat.loc[b, a] = adj
        img = ax.imshow(-mat.applymap(lambda x: math.log10(max(float(x), 1e-12))).values, cmap="YlOrRd", vmin=0, vmax=8)
        ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
        ax.set_yticks(range(len(labels)), labels)
        ax.set_title(f"{oe}: -log10(p Holm)")
    fig.colorbar(img, ax=axes.ravel().tolist(), shrink=0.8)
    out = FIG_DIR / "pairwise_holm_pvalue_heatmaps.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    paths["pairwise_heatmaps"] = out

    if not kpi_ranking.empty:
        pivot = kpi_ranking.pivot_table(index="method", columns="scenario", values="normalized_score", aggfunc="mean")
        fig, ax = plt.subplots(figsize=(6.5, 4.2))
        img = ax.imshow(pivot.values, cmap="viridis")
        ax.set_xticks(range(len(pivot.columns)), pivot.columns)
        ax.set_yticks(range(len(pivot.index)), pivot.index)
        ax.set_title("Ranking KPI CityLearn v2 evaluate_v2 (score normalizado)")
        for i in range(pivot.shape[0]):
            for j in range(pivot.shape[1]):
                ax.text(j, i, f"{pivot.iloc[i, j]:.3f}", ha="center", va="center", color="white", fontsize=8)
        fig.colorbar(img, ax=ax, shrink=0.85)
        fig.tight_layout()
        out = FIG_DIR / "citylearn_v2_kpi_ranking_heatmap.png"
        fig.savefig(out, dpi=180)
        plt.close(fig)
        paths["kpi_ranking_heatmap"] = out

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {"HAPPO": "#9AA7B2", "MAAC": "#2F6B52", "MASAC": "#C77D2A", "MATD3": "#406A9F"}
    markers = {"E1": "o", "E2": "s", "E3": "^"}
    for _, r in treatment.iterrows():
        size = 40 + 120 * (float(r.get("pv_self_consumption_ratio", 0) or 0))
        ax.scatter(r["electricity_cost_control"], r["carbon_emissions_control"], s=size, c=colors.get(r["algorithm"], "gray"), marker=markers.get(r["scenario"], "o"), edgecolor="black", linewidth=0.4)
        ax.text(r["electricity_cost_control"], r["carbon_emissions_control"], f"{r['algorithm']}-{r['scenario']}", fontsize=7)
    ax.set_title("Trade-off multiobjetivo: costo vs CO2 vs autoconsumo PV")
    ax.set_xlabel("electricity_cost_control")
    ax.set_ylabel("carbon_emissions_control")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out = FIG_DIR / "multiobjective_tradeoff_cost_co2_pv.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    paths["tradeoff"] = out

    def building_heatmap(value_col: str, key: str, title: str, log_scale: bool = False) -> None:
        if value_col not in buildings.columns:
            return
        pivot = buildings.pivot_table(index="agent", columns="algorithm", values=value_col, aggfunc="mean").reindex(columns=ALGOS)
        values = pivot.astype(float).values
        if log_scale:
            values = pd.DataFrame(values).applymap(lambda x: math.copysign(math.log10(1.0 + abs(float(x))), float(x))).values
        fig, ax = plt.subplots(figsize=(7.2, 6.2))
        img = ax.imshow(values, aspect="auto", cmap="mako" if False else "viridis")
        ax.set_xticks(range(len(pivot.columns)), pivot.columns)
        ax.set_yticks(range(len(pivot.index)), pivot.index)
        ax.set_title(title)
        fig.colorbar(img, ax=ax, shrink=0.75)
        fig.tight_layout()
        out = FIG_DIR / f"{key}.png"
        fig.savefig(out, dpi=180)
        plt.close(fig)
        paths[key] = out

    building_heatmap("ev_departure_success_rate", "building_ev_success_heatmap", "EV departure success rate por edificio y algoritmo")
    building_heatmap("carbon_emissions_control_kgco2", "building_carbon_heatmap", "CO2 control por edificio y algoritmo (log10)", True)
    building_heatmap("electricity_cost_control_eur", "building_cost_heatmap", "Costo control por edificio y algoritmo (log10)", True)

    if not eq_summary.empty:
        pivot = eq_summary.pivot_table(index="agent", columns="equipment_class", values="count", aggfunc="sum", fill_value=0)
        fig, ax = plt.subplots(figsize=(8, 6))
        img = ax.imshow(pivot.values, aspect="auto", cmap="Blues")
        ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=35, ha="right")
        ax.set_yticks(range(len(pivot.index)), pivot.index)
        ax.set_title("Equipamiento controlado por edificio y clase")
        fig.colorbar(img, ax=ax, shrink=0.75)
        fig.tight_layout()
        out = FIG_DIR / "controlled_equipment_class_heatmap.png"
        fig.savefig(out, dpi=180)
        plt.close(fig)
        paths["equipment_class_heatmap"] = out

    if not final_ts.empty:
        for scenario in SCENARIOS:
            sub = final_ts[final_ts["scenario"] == scenario].copy()
            if sub.empty:
                continue
            sub["hour"] = pd.to_numeric(sub.get("episode_step", sub.get("time_step")), errors="coerce")
            fig, axes = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
            for algo in ALGOS:
                alg = sub[sub["algorithm"] == algo].sort_values("hour")
                if alg.empty:
                    continue
                roll = alg["district_net_electricity_consumption"].rolling(24, min_periods=1).mean()
                axes[0].plot(alg["hour"], roll, label=algo, linewidth=1.2)
                axes[1].plot(alg["hour"], alg["district_net_electricity_consumption_cost"].rolling(24, min_periods=1).mean(), linewidth=1.0)
                axes[2].plot(alg["hour"], alg["district_net_electricity_consumption_emission"].rolling(24, min_periods=1).mean(), linewidth=1.0)
            axes[0].set_title(f"Serie temporal distrital final - {scenario} (media movil 24h)")
            axes[0].set_ylabel("energia neta")
            axes[1].set_ylabel("costo")
            axes[2].set_ylabel("CO2")
            axes[2].set_xlabel("hora del episodio final")
            axes[0].legend(ncol=4, fontsize=8)
            for ax in axes:
                ax.grid(alpha=0.25)
            fig.tight_layout()
            out = FIG_DIR / f"final_episode_district_timeseries_{scenario.lower()}.png"
            fig.savefig(out, dpi=180)
            plt.close(fig)
            paths[f"final_timeseries_{scenario}"] = out

    if not traces.empty:
        agg = traces.groupby(["algorithm", "scenario"])[["action_l2", "action_mean", "ev_charge_kwh", "ev_v2g_export_kwh", "electrical_storage_soc"]].mean(numeric_only=True).reset_index()
        fig, axes = plt.subplots(1, 3, figsize=(13, 4))
        for ax, col, title in zip(axes, ["action_l2", "ev_charge_kwh", "electrical_storage_soc"], ["Intensidad de accion", "Carga EV media", "SOC BESS medio"]):
            pivot = agg.pivot(index="algorithm", columns="scenario", values=col).reindex(index=ALGOS, columns=SCENARIOS)
            img = ax.imshow(pivot.values, cmap="plasma")
            ax.set_xticks(range(len(SCENARIOS)), SCENARIOS)
            ax.set_yticks(range(len(ALGOS)), ALGOS)
            ax.set_title(title)
            for i in range(pivot.shape[0]):
                for j in range(pivot.shape[1]):
                    ax.text(j, i, f"{pivot.iloc[i,j]:.2f}", ha="center", va="center", color="white", fontsize=8)
        fig.colorbar(img, ax=axes.ravel().tolist(), shrink=0.75)
        out = FIG_DIR / "trace_policy_action_heatmaps.png"
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        paths["trace_policy_heatmaps"] = out

    if not checkpoints.empty:
        counts = checkpoints.groupby(["algorithm", "scenario"])["checkpoint_episode"].count().reset_index(name="count")
        fig, ax = plt.subplots(figsize=(7, 4))
        x = range(len(counts))
        ax.bar([f"{r.algorithm}-{r.scenario}" for r in counts.itertuples()], counts["count"], color="#406A9F")
        ax.set_title("Cobertura de checkpoints por tratamiento")
        ax.set_ylabel("checkpoints en manifest")
        ax.tick_params(axis="x", rotation=70)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        out = FIG_DIR / "checkpoint_coverage_by_treatment.png"
        fig.savefig(out, dpi=180)
        plt.close(fig)
        paths["checkpoint_coverage"] = out
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


def insert_section_before(document: Document, target_prefix: str, writer) -> None:
    body = document.element.body
    children = list(body)
    target = None
    for i, el in enumerate(children):
        if text_of(el).startswith(target_prefix):
            target = i
            break
    if target is None:
        raise RuntimeError(f"No se encontro punto de insercion: {target_prefix}")
    tmp = Document()
    clear_body_keep_sectpr(tmp)
    writer(tmp)
    new_children = [deepcopy(el) for el in tmp.element.body if el.tag != qn("w:sectPr")]
    for offset, el in enumerate(new_children):
        body.insert(target + offset, el)


def insert_section_before_any(document: Document, target_prefixes: list[str], writer) -> None:
    last_error = None
    for prefix in target_prefixes:
        try:
            insert_section_before(document, prefix, writer)
            return
        except RuntimeError as exc:
            last_error = exc
    raise RuntimeError(f"No se encontro punto de insercion entre: {target_prefixes}") from last_error


def normalize_chapter2_numbering(doc: Document) -> None:
    replacements = {
        "2.1.1 Aprendizaje por refuerzo y MADRL": "2.2.1 Aprendizaje por refuerzo y MADRL",
        "2.1.2 Formalizacion matematica Dec-POMDP": "2.2.2 Formalizacion matematica Dec-POMDP",
        "2.1.3 CityLearn y simulacion multiobjetivo": "2.2.4 CityLearn y simulacion multiobjetivo",
        "2.2.1 Variable independiente (VI)": "2.3.1 Variable independiente (VI)",
        "2.2.2 Variable dependiente (VD)": "2.3.2 Variable dependiente (VD)",
        "2.3.1 Flexibilidad energetica": "2.4.1 Flexibilidad energetica",
        "2.3.2 Emisiones de carbono y control consciente de intensidad de carbono": "2.4.2 Emisiones de carbono y control consciente de intensidad de carbono",
        "2.3.3 Costos energeticos, precios dinamicos y respuesta economica": "2.4.3 Costos energeticos, precios dinamicos y respuesta economica",
        "2.3.4 Algoritmos MADRL evaluados": "2.4.4 Algoritmos MADRL evaluados",
        "2.3.5 Aportes fisicos al motor como base teorica de CityLearn v3 propuesto": "2.4.5 Aportes fisicos al motor como base teorica de CityLearn v3 propuesto",
        "2.4.1 Antecedentes internacionales": "2.5.1 Antecedentes internacionales",
        "2.4.2 Antecedentes nacionales y peruanos": "2.5.2 Antecedentes nacionales y peruanos",
        "2.4.3 Sintesis critica de antecedentes y brecha cientifica": "2.5.3 Sintesis critica de antecedentes y brecha cientifica",
        "2.5.1 Definicion de terminos y delimitaciones conceptuales": "2.6.1 Definicion de terminos y delimitaciones conceptuales",
        "2.5.2 Posicion teorica de la tesis": "2.6.2 Posicion teorica de la tesis",
        "2.6 Sintesis critica y triangulacion del marco teorico": "2.7 Sintesis critica y triangulacion del marco teorico",
    }
    for para in doc.paragraphs:
        text = para.text.strip()
        if text in replacements:
            set_paragraph_text(para, replacements[text])


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


def add_cap1_validation(doc: Document) -> None:
    doc.add_heading("1.7 Validacion estructural y triangulacion del planteamiento", level=2)
    p(doc, "El Capitulo 1 cumple la estructura minima exigida para una tesis aplicada: formula el problema de investigacion, declara objetivos, hipotesis, justificacion, alcances y limitaciones. La coherencia interna se sostiene porque el problema no se define como una deficiencia algoritmica aislada, sino como una tension entre gestion descentralizada, flexibilidad energetica, emisiones de CO2 y costos en una comunidad electrica aislada. Este encuadre es consistente con la literatura de CityLearn, que plantea la necesidad de entornos reproducibles para comparar controladores de respuesta a la demanda, con CityLearn v2, que amplia la evaluacion hacia comunidades grid-interactive, resilientes y carbon-aware, y con EVLearn, que subraya que la integracion de vehiculos electricos requiere simulacion especifica de flexibilidad de carga y descarga (Vazquez-Canteli et al., 2020; Nweye et al., 2024; Fonseca et al., 2024).")
    p(doc, "La pregunta general y las preguntas especificas quedan operacionalizadas en tres dimensiones dependientes. PE.1 se vincula con flexibilidad energetica, PE.2 con emisiones de CO2 y PE.3 con costos energeticos. Esta separacion evita que el desempeno del algoritmo se reduzca a una recompensa unica sin interpretabilidad; por el contrario, permite contrastar la variable independiente MADRL contra indicadores observables por distrito, edificio y escenario. La triangulacion entre CityLearn, MARL energetico y evaluacion estadistica de RL justifica que el estudio reporte resultados descriptivos e inferenciales, y que declare como limitacion la ausencia de multiples semillas independientes en lugar de sobregeneralizar una unica corrida experimental (Henderson et al., 2018; Agarwal et al., 2021; Nweye et al., 2024).")
    table(
        doc,
        "Tabla 1.7. Validacion del Capitulo 1 frente a la estructura minima.",
        ["Elemento requerido", "Estado", "Refuerzo incorporado"],
        [
            ["Problema de investigacion", "Cumple", "Se alinea con flexibilidad, carbono y costo en comunidad aislada."],
            ["Objetivos", "Cumple", "OG y OE.1-OE.3 mantienen correspondencia con PE.1-PE.3."],
            ["Hipotesis", "Cumple", "Se conservan por tratarse de diseno experimental comparativo."],
            ["Justificacion", "Cumple", "Se refuerza con reproducibilidad CityLearn y necesidad de evaluacion estadistica."],
            ["Alcances y limitaciones", "Cumple", "Se explicita la lectura intra-corrida y la no extrapolacion multi-semilla."],
        ],
        7.0,
    )


def add_cap2_validation(doc: Document) -> None:
    doc.add_heading("2.6 Sintesis critica y triangulacion del marco teorico", level=2)
    p(doc, "El marco teorico contiene estado del arte, bases teoricas, trabajos relacionados, definicion de variables y posicion teorica. La triangulacion central se organiza en tres capas. Primero, CityLearn aporta el marco de evaluacion reproducible para comunidades de edificios y demanda flexible; CityLearn v2 agrega objetivos de flexibilidad, resiliencia, ocupacion y carbono; EVLearn extiende el mismo ecosistema a vehiculos electricos y estrategias V1G/V2G (Vazquez-Canteli et al., 2020; Nweye et al., 2024; Fonseca et al., 2024). Segundo, la teoria MADRL fundamenta la ejecucion descentralizada con entrenamiento centralizado: MAAC introduce criticos con atencion para seleccionar interacciones relevantes entre agentes, HAPPO extiende optimizacion de region de confianza a agentes heterogeneos, SAC/MASAC aporta exploracion por maxima entropia y TD3/MATD3 controla sesgo de sobreestimacion con criticos dobles y actualizaciones retrasadas (Iqbal & Sha, 2019; Kuba et al., 2021; Haarnoja et al., 2018; Fujimoto et al., 2018). Tercero, la literatura de evaluacion de RL advierte que una comparacion algoritmica debe acompanar los promedios con dispersion, pruebas estadisticas y trazabilidad experimental (Henderson et al., 2018; Agarwal et al., 2021).")
    p(doc, "La principal mejora incorporada al Capitulo 2 consiste en separar el soporte teorico de cada decision metodologica. El Dec-POMDP no se presenta como formalismo decorativo, sino como condicion necesaria para representar 17 agentes con observacion parcial, acciones heterogeneas, recompensa cooperativa y horizonte anual. La funcion de recompensa multiobjetivo se sustenta en la literatura de control de comunidades energeticas, pero se interpreta dentro de CityLearn v2 para evitar que flexibilidad, emisiones y costos sean confundidos como una unica variable latente. Esta posicion teorica permite que el Capitulo 5 lea resultados por escenario y no solo por algoritmo.")
    table(
        doc,
        "Tabla 2.6. Triangulacion teorica por eje de la tesis.",
        ["Eje", "Fuentes trianguladas", "Uso en la tesis"],
        [
            ["Entorno y KPIs", "CityLearn v1/v2; CityLearn Challenge; EVLearn", "Justifica benchmark, KPIs evaluate_v2 y control de EV/BESS."],
            ["MADRL", "MAAC; HAPPO; SAC; TD3", "Justifica comparacion de familias actor-critic multiagente."],
            ["Evaluacion rigurosa", "Henderson et al.; Agarwal et al.", "Justifica pruebas no parametricas y cautela ante una sola corrida."],
            ["Variables", "Flexibilidad, CO2 y costo en comunidades grid-interactive", "Sostiene D-VD.1, D-VD.2 y D-VD.3."],
        ],
        6.8,
    )


def add_cap3_validation(doc: Document) -> None:
    doc.add_heading("3.7 Validez metodologica, trazabilidad y control de sesgos", level=2)
    p(doc, "El Capitulo 3 cumple con el tipo de investigacion, diseno metodologico, datos utilizados, variables, tecnicas, herramientas y procedimiento experimental. La tesis corresponde a una investigacion aplicada, cuantitativa y explicativa bajo simulacion computacional, porque manipula la variable independiente MADRL mediante cuatro algoritmos y tres escenarios de recompensa, y observa sus efectos sobre indicadores cuantitativos de flexibilidad, emisiones y costos. Esta estrategia es compatible con la estandarizacion buscada por CityLearn para comparar controladores en comunidades energeticas, pero requiere trazabilidad estricta de artefactos para evitar sesgos de seleccion o interpretacion (Vazquez-Canteli et al., 2020; Nweye et al., 2024).")
    p(doc, "La validez interna se protege mediante un diseno factorial 4x3, mismo dataset, mismos escenarios E1-E3 y mismas reglas de extraccion de KPIs. La validez estadistica se aborda con estadistica descriptiva, Shapiro-Wilk, Kruskal-Wallis y Mann-Whitney con ajuste Holm, debido a que las distribuciones episodicas no deben asumirse normales por defecto. La validez externa se declara limitada: Henderson et al. (2018) y Agarwal et al. (2021) advierten que las conclusiones de RL con pocas corridas pueden variar si no se reporta incertidumbre, por lo que la tesis interpreta los resultados como evidencia intra-corrida y recomienda una extension multi-semilla.")
    table(
        doc,
        "Tabla 3.7. Control metodologico de validez y trazabilidad.",
        ["Riesgo", "Control aplicado", "Evidencia"],
        [
            ["Comparacion no equivalente", "Mismo dataset, mismos escenarios y misma funcion de evaluacion", "12 tratamientos algoritmo x escenario."],
            ["Normalidad no garantizada", "Pruebas no parametricas y Shapiro-Wilk", "CSV estadisticos generados desde episodios Drive."],
            ["Sobregeneralizacion", "Declaracion de inferencia intra-corrida", "Limitacion multi-semilla en Capitulo 6."],
            ["Datos inventados", "Uso exclusivo de results, timeseries, traces, checkpoints y CSV materializados", "Validacion de cobertura en Capitulo 5."],
        ],
        6.8,
    )


def add_cap3_methodology(doc: Document) -> None:
    doc.add_heading("Capitulo 3. Metodologia", level=1)
    p(doc, "El presente estudio adopta una metodologia cuantitativa, aplicada y explicativa-comparativa, sustentada en simulacion computacional controlada. Esta decision responde a la naturaleza del problema doctoral: evaluar en que medida distintos algoritmos MADRL modifican indicadores cuantificables de flexibilidad energetica, emisiones de CO2 y costos energeticos en una comunidad electrica modelada bajo CityLearn. De acuerdo con Hernandez-Sampieri y Mendoza (2018), la ruta cuantitativa se caracteriza por la medicion de variables, el uso de procedimientos sistematicos y la contrastacion de hipotesis; Creswell y Creswell (2023) enfatizan que los disenos cuantitativos permiten examinar relaciones entre variables mediante mediciones numericas y analisis estadistico. En esta tesis, la variable independiente se manipula computacionalmente mediante el algoritmo MADRL y el escenario de recompensa, mientras que la variable dependiente se observa mediante KPIs oficiales y resultados episodicos.")

    doc.add_heading("3.1 Enfoque, tipo, nivel y diseno de investigacion", level=2)
    p(doc, "La investigacion es aplicada porque desarrolla y evalua una solucion computacional para gestion energetica multiagente en una comunidad del SEAI Iquitos. Es cuantitativa porque los resultados se expresan en metricas numericas: recompensa, costo, emisiones, pico, rampa, factor de carga, energia de almacenamiento, exito EV y KPIs evaluate_v2. Es explicativa-comparativa porque no se limita a describir los algoritmos; contrasta si la variacion de la variable independiente produce efectos diferenciados sobre las dimensiones D-VD.1, D-VD.2 y D-VD.3. Esta clasificacion es coherente con los criterios de alcance y diseno propuestos por Hernandez-Sampieri y Mendoza (2018), con la logica de diseno cuantitativo de Creswell y Creswell (2023), y con la tradicion de diseno experimental orientado a factores, tratamientos y respuestas descrita por Montgomery (2019).")
    p(doc, "El diseno no se considera no experimental en sentido estricto, porque si existe manipulacion controlada de factores dentro del entorno de simulacion: algoritmo MADRL y escenario de recompensa. Tampoco corresponde a un experimento de campo con sujetos humanos, sino a un experimento computacional in silico. Por ello, se define como diseno experimental-computacional factorial 4x3, con control de dataset, entorno, recompensa, horizonte temporal, agentes y protocolo de evaluacion. La inferencia es intra-corrida y se interpreta con cautela, porque Shadish, Cook y Campbell (2002) advierten que la validez interna, estadistica, de constructo y externa deben declararse de forma diferenciada; en este caso, la validez externa queda limitada por la ausencia de multiples semillas independientes.")
    table(
        doc,
        "Tabla 3.1. Clasificacion metodologica de la investigacion.",
        ["Criterio", "Decision metodologica", "Sustento"],
        [
            ["Enfoque", "Cuantitativo", "Medicion numerica de KPIs y contrastacion estadistica."],
            ["Tipo", "Aplicada", "Desarrollo y evaluacion de una propuesta MADRL para gestion energetica."],
            ["Nivel", "Explicativo-comparativo", "Evalua efecto de algoritmos y escenarios sobre dimensiones VD."],
            ["Diseno", "Experimental-computacional factorial 4x3", "Manipulacion controlada de algoritmo y escenario en simulacion."],
            ["Temporalidad", "Longitudinal por episodios y horizonte anual horario", "Cada episodio recorre una trayectoria anual de 8760 pasos."],
            ["Inferencia", "Intra-corrida con limitacion multi-semilla", "No se generaliza mas alla de los artefactos auditados."],
        ],
        6.8,
    )

    doc.add_heading("3.2 Diseno experimental-computacional factorial 4x3", level=2)
    p(doc, "El diseno factorial se compone de dos factores principales. El primer factor es el algoritmo MADRL, con cuatro niveles: HAPPO, MAAC, MASAC y MATD3. El segundo factor es el escenario de recompensa, con tres niveles: E1 orientado a flexibilidad, E2 orientado a emisiones de CO2 y E3 orientado a costos energeticos. La combinacion genera 12 tratamientos algoritmo x escenario. Montgomery (2019) sostiene que los disenos factoriales permiten estudiar efectos de factores bajo condiciones controladas; en esta tesis, el control se materializa en el mismo dataset, el mismo entorno CityLearn, la misma comunidad de 17 edificios, el mismo horizonte de evaluacion y la misma familia de KPIs.")
    p(doc, "La unidad experimental principal es el tratamiento algoritmo-escenario. La unidad de observacion episodica es el episodio conservado en los artefactos de Drive, y la unidad de observacion espacial es el edificio-agente. Esta doble lectura permite responder los objetivos en tres escalas: distrito, edificio y politica multiagente. Para la inferencia estadistica se usan los episodios materializados: MAAC, MASAC y MATD3 conservan cobertura completa en los tres escenarios; HAPPO registra entrenamiento completado, pero conserva 49 filas episodicas por escenario en el CSV materializado, por lo que se reporta como evidencia descriptiva y no como grupo inferencial completo.")
    table(
        doc,
        "Tabla 3.2. Matriz factorial 4x3 de tratamientos experimentales.",
        ["Factor", "Niveles", "Funcion metodologica"],
        [
            ["Algoritmo MADRL", "HAPPO, MAAC, MASAC, MATD3", "Variable independiente principal; compara familias actor-critic multiagente."],
            ["Escenario de recompensa", "E1, E2, E3", "Manipulacion de prioridad multiobjetivo: flexibilidad, CO2 y costo."],
            ["Tratamientos", "12 combinaciones", "Base de comparacion para resultados por objetivo especifico."],
            ["Horizonte", "50 episodios registrados por tratamiento", "Evidencia de entrenamiento Drive; se declara cobertura materializada por algoritmo."],
        ],
        6.8,
    )

    doc.add_heading("3.3 Datos utilizados y fuente empirica", level=2)
    p(doc, "Los datos utilizados corresponden al dataset citylearn_iquitos_2023_2025 y a la corrida canonica Drive madrl_v3_20260627_164047. La tesis no incorpora datos simulados manualmente fuera del pipeline; usa artefactos generados por scripts del proyecto y resultados auditables: results.json, training_summary.json, timeseries.csv, trace.csv, building_kpis.csv, building_behavior_summary.csv, building_observation_action_schema.csv y checkpoint_manifest.json. La fuente empirica combina meteorologia, demanda, PV, BESS, EV, precios, intensidad de carbono y KPIs CityLearn. Esta trazabilidad responde a la exigencia metodologica de reproducibilidad y control de medicion que Hernandez-Sampieri y Mendoza (2018) y Creswell y Creswell (2023) asocian con la ruta cuantitativa.")
    p(doc, "El dataset representa 17 edificios de una comunidad energetica de Iquitos, con equipos controlables heterogeneos y variables de observacion locales. La representacion por edificio permite modelar el problema como Dec-POMDP y evaluar la ejecucion descentralizada de politicas MADRL. Para evitar alucinacion o sobreinterpretacion, los resultados del Capitulo 5 se derivan exclusivamente de los archivos existentes y de tablas materializadas en outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis.")
    table(
        doc,
        "Tabla 3.3. Fuentes de datos y artefactos de analisis.",
        ["Artefacto", "Contenido", "Uso metodologico"],
        [
            ["timeseries.csv", "Serie temporal distrital por episodio", "Energia, costo, CO2, recompensa y senales horarias."],
            ["trace.csv", "Trazas por agente", "Acciones, SOC, EV, PV, importacion/exportacion y recompensa individual."],
            ["building_kpis.csv / building_behavior_summary.csv", "KPIs por edificio", "Analisis espacial por agente y equipamiento."],
            ["checkpoint_manifest.json", "Registro de checkpoints", "Trazabilidad de entrenamiento y cobertura por tratamiento."],
            ["district_episode_kpis.csv", "KPIs episodicos materializados", "Base de estadistica descriptiva e inferencial."],
        ],
        6.7,
    )

    doc.add_heading("3.4 Variables, dimensiones e indicadores", level=2)
    p(doc, "La variable independiente (VI) es el algoritmo MADRL implementado bajo un esquema CTDE y condicionado por escenario de recompensa. Sus dimensiones operacionales son: D-VI.1 tipo de algoritmo, D-VI.2 ponderacion multiobjetivo del escenario y D-VI.3 controles experimentales. La variable dependiente (VD) es el desempeno energetico coordinado de la comunidad, desagregado en tres dimensiones: D-VD.1 flexibilidad energetica, D-VD.2 emisiones de CO2 y D-VD.3 costos energeticos. Esta definicion mantiene correspondencia vertical con PE.1, PE.2, PE.3, OE.1, OE.2 y OE.3.")
    p(doc, "La operacionalizacion sigue la logica de medicion cuantitativa: cada dimension debe tener indicadores observables, fuente de datos y criterio de interpretacion. En D-VD.1 se consideran recompensa en E1 y KPIs de flexibilidad como peak, ramping, load factor, autoconsumo PV y uso de almacenamiento. En D-VD.2 se consideran emisiones distritales, carbon_emissions_control, carbon_emissions_delta y consumo ponderado por intensidad de carbono. En D-VD.3 se consideran district_cost, electricity_cost_control, electricity_cost_delta y senales de precio. Esta estructura evita confundir recompensa de entrenamiento con resultado final de evaluacion.")
    table(
        doc,
        "Tabla 3.4. Operacionalizacion metodologica de variables.",
        ["Variable", "Dimension", "Indicadores principales", "Fuente"],
        [
            ["VI", "D-VI.1 Algoritmo", "HAPPO, MAAC, MASAC, MATD3", "Configuracion de tratamiento."],
            ["VI", "D-VI.2 Escenario", "E1, E2, E3; pesos flex/CO2/costo", "reward_axis_weights y protocolo experimental."],
            ["VD", "D-VD.1 Flexibilidad", "reward_mean E1, peak, ramping, load factor, BESS/PV", "episodes, results, evaluate_v2."],
            ["VD", "D-VD.2 CO2", "district_emission, carbon_emissions_control/delta", "timeseries, results, building KPIs."],
            ["VD", "D-VD.3 Costos", "district_cost, electricity_cost_control/delta", "timeseries, results, building KPIs."],
        ],
        6.6,
    )

    doc.add_heading("3.5 Tecnicas, herramientas e instrumentos", level=2)
    p(doc, "Las tecnicas utilizadas son simulacion computacional, entrenamiento MADRL, evaluacion por KPIs, estadistica descriptiva, contrastacion no parametrica y visualizacion analitica. Las herramientas principales son Python, PyTorch, CityLearn v2, la extension CityLearn v3 propuesta, backends HAPPO/MAAC/MASAC/MATD3, scripts de orquestacion del proyecto y artefactos Drive. En terminos metodologicos, el instrumento de medicion no es un cuestionario ni una entrevista, sino el entorno computacional validado y sus archivos de salida.")
    p(doc, "La decision de usar estadistica no parametrica se debe a que las recompensas y KPIs episodicos de RL pueden presentar no normalidad, dependencia temporal, asimetria o valores atipicos. Por ello se aplica Shapiro-Wilk para normalidad, Kruskal-Wallis para diferencias globales entre algoritmos con cobertura completa y Mann-Whitney U con ajuste Holm para comparaciones por pares. Esta eleccion es coherente con la recomendacion metodologica de no asumir supuestos estadisticos no verificados y con las advertencias de evaluacion robusta en aprendizaje por refuerzo reportadas por Henderson et al. (2018) y Agarwal et al. (2021).")
    table(
        doc,
        "Tabla 3.5. Tecnicas, herramientas e instrumentos.",
        ["Componente", "Aplicacion en la tesis", "Resultado esperado"],
        [
            ["Simulacion CityLearn", "Recrear comunidad energetica multiagente", "Series, KPIs y trazas auditables."],
            ["MADRL", "Entrenar politicas bajo CTDE", "Politicas por algoritmo y escenario."],
            ["evaluate_v2 / KPIs", "Evaluar flexibilidad, CO2 y costo", "Ranking comparable con baseline."],
            ["Estadistica no parametrica", "Contrastar diferencias entre algoritmos", "p-valores, epsilon2 y decisiones HE."],
            ["Visualizacion", "Interpretar convergencia, trade-offs, edificios y acciones", "Figuras del Capitulo 5."],
        ],
        6.8,
    )

    doc.add_heading("3.6 Procedimiento experimental", level=2)
    p(doc, "El procedimiento experimental se estructura en siete fases reproducibles. Primero, se verifica el contexto del repositorio y la disponibilidad de artefactos. Segundo, se valida el dataset citylearn_iquitos_2023_2025 y el esquema de edificios/equipos. Tercero, se ejecutan o recuperan las 12 corridas algoritmo x escenario desde Drive. Cuarto, se consolidan episodios, timeseries, traces, building KPIs y checkpoints. Quinto, se calculan KPIs distritales, por edificio y por objetivo. Sexto, se aplican pruebas estadisticas y rankings evaluate_v2. Septimo, se generan tablas, figuras y redaccion interpretativa en el documento final.")
    p(doc, "Cada fase se documenta mediante archivos de salida. La decision de no completar manualmente valores ausentes es parte del control metodologico: si un artefacto no conserva una granularidad determinada, se declara como limitacion y no se sintetiza. Esta regla es consistente con la validez de medicion y la transparencia experimental recomendadas por Shadish et al. (2002) y Montgomery (2019).")
    table(
        doc,
        "Tabla 3.6. Procedimiento experimental reproducible.",
        ["Fase", "Actividad", "Evidencia"],
        [
            ["1", "Verificacion de contexto y rutas", "scripts/verify_project_context.ps1."],
            ["2", "Validacion de dataset y esquema CityLearn", "schema, building files y auditorias."],
            ["3", "Entrenamiento/recuperacion de 12 tratamientos", "Drive madrl_v3_20260627_164047."],
            ["4", "Consolidacion de resultados", "timeseries, traces, checkpoints y KPIs."],
            ["5", "Analisis descriptivo e inferencial", "CSV de estadisticas y comparaciones Holm."],
            ["6", "Visualizacion doctoral", "Figuras por convergencia, KPIs, edificios y trade-offs."],
            ["7", "Integracion en Word", "Documento final reproducible desde el generador."],
        ],
        6.8,
    )

    doc.add_heading("3.7 Validez metodologica, trazabilidad y control de sesgos", level=2)
    p(doc, "La validez interna se fortalece por el control del entorno: todos los algoritmos se evaluan sobre el mismo dataset, la misma comunidad, los mismos escenarios y los mismos criterios de extraccion de KPIs. La validez de constructo se protege mediante la correspondencia entre preguntas, objetivos, variables e indicadores. La validez estadistica se aborda con pruebas no parametricas y tamanos de efecto, evitando asumir normalidad sin evidencia. La validez externa se declara limitada porque la corrida canonica no sustituye una campana multi-semilla; por tanto, las conclusiones se formulan como evidencia doctoral intra-corrida y no como generalizacion universal.")
    p(doc, "El control de sesgos se apoya en cinco reglas: no mezclar resultados de otros proyectos, no usar artefactos ajenos a Drive/local autorizado, no inventar datos faltantes, distinguir evidencia descriptiva de evidencia inferencial y reportar limitaciones de cobertura. Este criterio es central para una tesis doctoral basada en RL, donde diferencias aparentemente favorables pueden depender de semillas, hiperparametros, entorno y criterio de evaluacion.")
    table(
        doc,
        "Tabla 3.7. Control metodologico de validez y trazabilidad.",
        ["Dimension de validez", "Riesgo", "Control aplicado"],
        [
            ["Interna", "Comparacion desigual entre algoritmos", "Mismo dataset, mismo entorno y escenarios controlados."],
            ["Constructo", "Indicadores no alineados con objetivos", "PE/OE/VD/KPI vinculados por tabla de operacionalizacion."],
            ["Estadistica", "Normalidad o significancia asumida", "Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney-Holm y epsilon2."],
            ["Externa", "Generalizacion indebida", "Declaracion de inferencia intra-corrida y recomendacion multi-semilla."],
            ["Trazabilidad", "Datos inventados o mezclados", "Uso exclusivo de artefactos Drive y CSV materializados."],
        ],
        6.8,
    )


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

    doc.add_heading("5.1 Cobertura de artefactos experimentales", level=2)
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
    if "checkpoint_coverage" in figures:
        add_picture(doc, "Figura 5.1. Cobertura de checkpoints por tratamiento.", figures["checkpoint_coverage"])

    doc.add_heading("5.2 Trazabilidad entre objetivos, hipotesis e indicadores", level=2)
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
        if "kpi_ranking_heatmap" in figures:
            add_picture(doc, "Figura 5.4. Mapa de calor del ranking KPI CityLearn v2 evaluate_v2.", figures["kpi_ranking_heatmap"])
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
        ts_key = f"final_timeseries_{spec['scenario']}"
        if ts_key in figures:
            add_picture(doc, f"Figura 5.{idx}a. Serie temporal distrital del episodio final para {spec['scenario']}.", figures[ts_key])
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
    for key, caption in [
        ("building_ev_success_heatmap", "Figura 5.8a. Exito de salida EV por edificio y algoritmo."),
        ("building_carbon_heatmap", "Figura 5.8b. CO2 control por edificio y algoritmo."),
        ("building_cost_heatmap", "Figura 5.8c. Costo control por edificio y algoritmo."),
        ("equipment_class_heatmap", "Figura 5.8d. Equipamiento controlado por edificio y clase."),
        ("trace_policy_heatmaps", "Figura 5.8e. Politicas y acciones medias desde trace.csv."),
    ]:
        if key in figures:
            add_picture(doc, caption, figures[key])
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
    for key, caption in [
        ("episode_boxplots", "Figura 5.9a. Distribucion episodica por objetivo y algoritmo."),
        ("effect_size", "Figura 5.9b. Tamano de efecto inferencial por objetivo."),
        ("pairwise_heatmaps", "Figura 5.9c. Matriz de p-valores Holm por objetivo."),
    ]:
        if key in figures:
            add_picture(doc, caption, figures[key])
    p(doc, "La interpretacion doctoral no debe afirmar dominancia unica sin matices. Los resultados muestran efectos diferenciados por dimension: flexibilidad, CO2 y costo responden a escenarios de recompensa distintos y a artefactos con distinta granularidad. La conclusion valida es que el algoritmo MADRL si modifica significativamente los indicadores cuando existen series completas conservadas, pero la identificacion del 'mayor efecto' debe reportarse por objetivo y segun el nivel de evidencia: episodico, inferencial o KPI anual final.")
    p(doc, "Metodologicamente, esta decision sigue las advertencias de evaluacion rigurosa en aprendizaje por refuerzo: los episodios de una corrida no reemplazan multiples semillas independientes, y los p-valores deben interpretarse junto con cobertura, tamano de efecto y trazabilidad de artefactos (Henderson et al., 2018; Colas et al., 2019; Agarwal et al., 2021; Patterson et al., 2024). Por ello, se retiene Shapiro-Wilk, Kruskal-Wallis y Mann-Whitney U con Holm como contrastacion intra-corrida, y se declara la necesidad de multi-semilla para robustez externa.")
    add_cap5_triangulated_discussion(doc, detail, kpi_ranking, figures)


def add_cap5_triangulated_discussion(doc: Document, detail: dict, kpi_ranking: pd.DataFrame, figures: dict[str, Path]) -> None:
    doc.add_heading("5.10 Discusion triangulada de resultados, baseline y trabajos relacionados", level=2)
    p(doc, "El Capitulo 5 tiene el mayor peso empirico del documento porque integra experimentos realizados, metricas, resultados, comparacion con baseline, tablas, figuras y discusion. La triangulacion de resultados se realiza en tres niveles: recompensa episodica, KPIs evaluate_v2 y contraste estadistico. Esta estrategia evita que una unica grafica de convergencia se interprete como evidencia suficiente, y responde a las recomendaciones de evaluacion rigurosa en RL, donde se exige reportar variabilidad, tamano de efecto y robustez de la comparacion (Henderson et al., 2018; Agarwal et al., 2021).")
    rows = []
    for oe in ["OE.1", "OE.2", "OE.3"]:
        d = detail[oe]
        kw = d["kw"]
        rows.append([oe, d["spec"]["scenario"], d["spec"]["dimension"], d["best_stat"], d["best_stat_complete"], d["best_final"], f"H={kw.statistic:.4f}; p={kw.pvalue:.6g}; epsilon2={d['epsilon2']:.4f}" if kw else "NA", effect_label(d["epsilon2"])])
    table(doc, "Tabla 5.14. Discusion sintetica por objetivo, efecto y algoritmo dominante.", ["Objetivo", "Esc.", "Dimension", "mejor descriptivo", "mejor inferencial", "mejor KPI final", "Prueba", "Tamano"], rows, 6.5)
    if not kpi_ranking.empty:
        best_rows = []
        for scenario in SCENARIOS:
            sub = kpi_ranking[kpi_ranking["scenario"] == scenario].sort_values("axis_rank")
            if not sub.empty:
                r = sub.iloc[0]
                best_rows.append([scenario, r["axis"], r["family"], r["method"], fmt(r["normalized_score"], 4), fmt(r["axis_rank"], 1)])
        table(doc, "Tabla 5.15. Mejor metodo por eje segun ranking CityLearn v2 evaluate_v2.", ["Esc.", "Eje", "Familia", "Metodo", "score normalizado", "rank"], best_rows, 7.0)
    if "tradeoff" in figures:
        add_picture(doc, "Figura 5.10. Trade-off multiobjetivo costo-CO2-autoconsumo PV.", figures["tradeoff"])
    p(doc, "En flexibilidad energetica (PE.1/OE.1), la evidencia es la mas fuerte: MAAC obtiene la mejor media episodica conservada y lidera la muestra inferencial completa, mientras que Kruskal-Wallis rechaza H0 con epsilon2=0,2334, interpretado como efecto alto. Este resultado es compatible con la teoria de MAAC, porque el critico con atencion puede priorizar interacciones relevantes entre edificios cuando la dimension dominante es la coordinacion de flexibilidad; tambien se relaciona con CityLearn v2, donde los KPIs de flexibilidad incluyen pico, ramping, factor de carga y uso de almacenamiento (Iqbal & Sha, 2019; Nweye et al., 2024; Vazquez-Canteli et al., 2020).")
    p(doc, "En emisiones de CO2 (PE.2/OE.2), la evidencia muestra efecto inferencial significativo pero de tamano bajo. HAPPO presenta el mejor promedio descriptivo conservado, pero al restringir la decision a la muestra inferencial completa el mejor algoritmo es MAAC; en KPI anual final aparece MASAC. Esta divergencia no debe ocultarse, porque indica que el comportamiento carbono-dependiente no se reduce a un unico criterio. La literatura sobre SAC/MASAC sugiere que la regularizacion por entropia puede estabilizar exploracion en problemas continuos, mientras que CityLearn v2 y EVLearn muestran que carbono y carga EV dependen de senales temporales y restricciones de disponibilidad que pueden modificar el ranking final (Haarnoja et al., 2018; Fonseca et al., 2024; Nweye et al., 2024).")
    p(doc, "En costos energeticos (PE.3/OE.3), la prueba inferencial no rechaza H0 y el tamano de efecto es muy bajo. Por ello, la tesis no afirma una superioridad estadistica concluyente. Descriptivamente, HAPPO muestra menor costo medio entre las filas conservadas, pero en la muestra completa MATD3 presenta mejor promedio y MAAC obtiene el mejor KPI anual final. Esta lectura matizada es coherente con la literatura de TD3/MATD3, donde los criticos dobles reducen sesgos de estimacion, pero no garantizan dominancia en todos los objetivos multiobjetivo; tambien coincide con las advertencias de reproducibilidad en RL sobre no convertir diferencias numericas en conclusiones robustas sin replicas independientes (Fujimoto et al., 2018; Henderson et al., 2018; Agarwal et al., 2021).")
    p(doc, "La comparacion con baseline y trabajos relacionados se interpreta como evidencia contextual, no como sustituto de la contrastacion principal. Cuando el ranking evaluate_v2 ubica a un baseline o RBC por encima de MADRL en algun eje, el resultado se reporta porque forma parte de la evidencia real y muestra que el aprendizaje multiagente no domina automaticamente a politicas simples en todos los indicadores. Esta transparencia fortalece la validez doctoral: el aporte no consiste en afirmar superioridad universal, sino en identificar donde el MADRL produce efecto, con que magnitud y bajo que escenario de recompensa.")


def add_cap5_madrl_nature_figures(doc: Document, figures: dict[str, Path]) -> None:
    doc.add_heading("5.11 Figuras complementarias para evaluar la naturaleza MADRL", level=2)
    p(doc, "La curva de convergencia por recompensa media movil es necesaria para verificar aprendizaje, pero no es suficiente para evaluar la naturaleza de cada MADRL. Por ello se incorporan figuras complementarias basadas en episodios, KPIs oficiales, trazas, series temporales finales, edificios, equipamiento y checkpoints. Estas visualizaciones permiten distinguir aprendizaje, efecto estadistico, trade-off multiobjetivo, comportamiento fisico y cobertura de entrenamiento.")
    figure_plan = [
        ("episode_boxplots", "Figura 5.11a. Distribucion episodica por objetivo y algoritmo."),
        ("effect_size", "Figura 5.11b. Tamano de efecto inferencial por objetivo."),
        ("pairwise_heatmaps", "Figura 5.11c. Matriz visual de p-valores Holm por objetivo."),
        ("kpi_ranking_heatmap", "Figura 5.11d. Ranking de KPIs CityLearn v2 evaluate_v2."),
        ("tradeoff", "Figura 5.11e. Trade-off multiobjetivo costo-CO2-autoconsumo PV."),
        ("building_ev_success_heatmap", "Figura 5.11f. Exito de salida EV por edificio y algoritmo."),
        ("building_carbon_heatmap", "Figura 5.11g. CO2 por edificio y algoritmo."),
        ("building_cost_heatmap", "Figura 5.11h. Costo por edificio y algoritmo."),
        ("equipment_class_heatmap", "Figura 5.11i. Equipamiento controlado por edificio y clase."),
        ("final_timeseries_E1", "Figura 5.11j. Serie temporal distrital final en E1."),
        ("final_timeseries_E2", "Figura 5.11k. Serie temporal distrital final en E2."),
        ("final_timeseries_E3", "Figura 5.11l. Serie temporal distrital final en E3."),
        ("trace_policy_heatmaps", "Figura 5.11m. Politicas/acciones desde trace.csv."),
        ("checkpoint_coverage", "Figura 5.11n. Cobertura de checkpoints por tratamiento."),
    ]
    for key, caption in figure_plan:
        if key in figures and Path(figures[key]).exists():
            add_picture(doc, caption, figures[key], width=5.9)
    p(doc, "Estas figuras no reemplazan las pruebas estadisticas; las complementan. La distribucion episodica muestra variabilidad, el tamano de efecto cuantifica magnitud, los p-valores Holm ubican diferencias por pares, el trade-off evidencia tensiones entre costo y CO2, los mapas por edificio muestran heterogeneidad multiagente, las series temporales finales explican el comportamiento fisico y la cobertura de checkpoints documenta trazabilidad de entrenamiento.")


def effect_label(epsilon2: float) -> str:
    if pd.isna(epsilon2):
        return "no estimado"
    if epsilon2 >= 0.14:
        return "efecto alto"
    if epsilon2 >= 0.06:
        return "efecto medio"
    if epsilon2 >= 0.01:
        return "efecto bajo"
    return "efecto muy bajo"


def add_cap4_problem_question_response(doc: Document, detail: dict) -> None:
    doc.add_heading("4.9 Respuesta operacional a las preguntas especificas PE.1, PE.2 y PE.3", level=2)
    p(doc, "La propuesta no se limita a describir una arquitectura MADRL; tambien define como se responde cada pregunta especifica mediante la salida empirica de la corrida Drive madrl_v3_20260627_164047. La respuesta se apoya en dos planos: analisis descriptivo de los episodios y KPIs anuales finales, y analisis inferencial intra-corrida con Kruskal-Wallis sobre los algoritmos que conservan cobertura episodica completa. Esta regla evita mezclar una diferencia numerica descriptiva con una afirmacion causal o inferencial no sustentada.")
    question_map = {
        "OE.1": ("PE.1", "¿En que medida el algoritmo MADRL (VI) produce un efecto sobre la dimension de flexibilidad energetica de la comunidad (D-VD.1), y cual algoritmo genera el mayor efecto?"),
        "OE.2": ("PE.2", "¿En que medida el algoritmo MADRL (VI) produce un efecto sobre la dimension de emisiones de CO2 de la comunidad (D-VD.2), y cual algoritmo genera el mayor efecto?"),
        "OE.3": ("PE.3", "¿En que medida el algoritmo MADRL (VI) produce un efecto sobre la dimension de costos energeticos de la comunidad (D-VD.3), y cual algoritmo genera el mayor efecto?"),
    }
    rows = []
    for oe in ["OE.1", "OE.2", "OE.3"]:
        d = detail[oe]
        spec = d["spec"]
        kw = d["kw"]
        epsilon2 = d["epsilon2"]
        decision = "se rechaza H0" if kw and kw.pvalue < 0.05 else "no se rechaza H0"
        measure = f"H={kw.statistic:.4f}; p={kw.pvalue:.6g}; epsilon2={epsilon2:.4f} ({effect_label(epsilon2)})" if kw else "sin prueba inferencial"
        rows.append(
            [
                question_map[oe][0],
                spec["dimension"],
                spec["scenario"],
                spec["metric"],
                measure,
                decision,
                d["best_stat"],
                d["best_stat_complete"],
                d["best_final"],
            ]
        )
    table(
        doc,
        "Tabla 4.10. Respuesta directa a PE.1, PE.2 y PE.3 desde la evidencia descriptiva e inferencial.",
        ["Pregunta", "Dimension", "Esc.", "Indicador", "Medida del efecto", "Decision", "mejor descriptivo", "mejor inferencial", "mejor KPI final"],
        rows,
        6.2,
    )
    for oe in ["OE.1", "OE.2", "OE.3"]:
        d = detail[oe]
        pe, question = question_map[oe]
        spec = d["spec"]
        kw = d["kw"]
        desc = d["desc"].copy()
        values = []
        for _, r in desc.iterrows():
            nd = 6 if spec["metric"] == "reward_mean_average" else 2
            values.append(f"{r['algorithm']}={fmt(r['mean'], nd)} (n={int(r['count'])})")
        if kw and kw.pvalue < 0.05:
            inferential_text = f"El efecto inferencial existe porque Kruskal-Wallis rechaza H0 (H={kw.statistic:.4f}; p={kw.pvalue:.6g}; epsilon2={d['epsilon2']:.4f}, {effect_label(d['epsilon2'])})."
        else:
            inferential_text = f"No se demuestra efecto inferencial suficiente en la muestra conservada porque Kruskal-Wallis no rechaza H0 (H={kw.statistic:.4f}; p={kw.pvalue:.6g}; epsilon2={d['epsilon2']:.4f}, {effect_label(d['epsilon2'])})."
        p(doc, f"{pe}. {question} Respuesta: en {spec['scenario']}, el indicador {spec['metric']} muestra los siguientes promedios episodicos conservados: " + "; ".join(values) + f". {inferential_text} El mayor efecto descriptivo corresponde a {d['best_stat']}; al exigir cobertura inferencial completa, corresponde a {d['best_stat_complete']}; y por KPI anual final corresponde a {d['best_final']}.")
    p(doc, "Por tanto, el Capitulo 4 deja definido el mecanismo de respuesta: PE.1 se responde con flexibilidad en E1, PE.2 con emisiones de CO2 en E2 y PE.3 con costos en E3. El Capitulo 5 desarrolla la contrastacion, figuras, tablas por edificio y ranking CityLearn v2, pero la relacion pregunta-variable-indicador-decision queda fijada aqui para mantener continuidad entre problema, propuesta y resultados.")


def add_cap6_completion_plan(doc: Document) -> None:
    doc.add_heading("6.5 Criterios de cierre doctoral y control de calidad final", level=2)
    p(doc, "Las conclusiones del estudio se consideran suficientemente sustentadas para responder las preguntas especificas desde la corrida Drive analizada. Dado que el Capitulo 6 ya contiene trabajo pendiente y plan de culminacion, esta seccion define criterios de cierre doctoral: validar numeracion y formato APA del documento completo, ejecutar una extension multi-semilla si se requiere robustez externa, revisar visualmente todas las figuras en Word/PDF y completar una lectura cruzada entre objetivos, hipotesis, resultados y conclusiones. Esta planificacion no agrega datos nuevos; delimita el control de calidad requerido para elevar la trazabilidad formal del manuscrito.")
    table(
        doc,
        "Tabla 6.2. Criterios de cierre y control de calidad final.",
        ["Actividad", "Proposito", "Criterio de cierre"],
        [
            ["Revision APA integral", "Alinear citas, tablas, figuras y referencias", "Todas las citas tienen entrada bibliografica y viceversa."],
            ["Revision multi-semilla opcional", "Mejorar validez externa de la comparacion MADRL", "Replicas documentadas o limitacion explicitada."],
            ["Auditoria de figuras y tablas", "Confirmar legibilidad y correspondencia con CSV/Drive", "Cada figura/tabla apunta a fuente de datos verificable."],
            ["Revision de coherencia vertical", "Asegurar que PE, OE, hipotesis y conclusiones respondan lo mismo", "Matriz problema-objetivo-resultado-conclusion sin vacios."],
        ],
        6.8,
    )


def append_apa_references(doc: Document) -> None:
    doc.add_paragraph()
    cap = doc.add_paragraph()
    run = cap.add_run("Referencias complementarias incorporadas en la revision")
    run.bold = True
    refs = [
        "Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A. C., & Bellemare, M. G. (2021). Deep reinforcement learning at the edge of the statistical precipice. Advances in Neural Information Processing Systems, 34, 29304-29320.",
        "Creswell, J. W., & Creswell, J. D. (2023). Research design: Qualitative, quantitative, and mixed methods approaches (6th ed.). SAGE Publications.",
        "Fonseca, N., Nweye, K., & Nagy, Z. (2024). EVLearn: A mixed-autonomy multi-agent reinforcement learning environment for electric vehicle charging management. arXiv. https://arxiv.org/abs/2403.07612",
        "Fujimoto, S., van Hoof, H., & Meger, D. (2018). Addressing function approximation error in actor-critic methods. Proceedings of the 35th International Conference on Machine Learning, 80, 1587-1596.",
        "Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018). Soft actor-critic: Off-policy maximum entropy deep reinforcement learning with a stochastic actor. Proceedings of the 35th International Conference on Machine Learning, 80, 1861-1870.",
        "Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., & Meger, D. (2018). Deep reinforcement learning that matters. Proceedings of the AAAI Conference on Artificial Intelligence, 32(1).",
        "Hernandez-Sampieri, R., & Mendoza, C. P. (2018). Metodologia de la investigacion: Las rutas cuantitativa, cualitativa y mixta. McGraw-Hill Education.",
        "Iqbal, S., & Sha, F. (2019). Actor-attention-critic for multi-agent reinforcement learning. Proceedings of the 36th International Conference on Machine Learning, 97, 2961-2970.",
        "Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., & Yang, Y. (2021). Trust region policy optimisation in multi-agent reinforcement learning. arXiv. https://arxiv.org/abs/2109.11251",
        "Montgomery, D. C. (2019). Design and analysis of experiments (10th ed.). Wiley.",
        "Nweye, K., Sankur, M. D., Wu, C., & Nagy, Z. (2024). CityLearn v2: Energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities. Journal of Building Performance Simulation, 17(1), 1-20.",
        "Shadish, W. R., Cook, T. D., & Campbell, D. T. (2002). Experimental and quasi-experimental designs for generalized causal inference. Houghton Mifflin.",
        "Vazquez-Canteli, J. R., Dey, S., Henze, G., & Nagy, Z. (2020). CityLearn: Standardizing research in multi-agent reinforcement learning for demand response and urban energy management. arXiv. https://arxiv.org/abs/2012.10504",
    ]
    for ref in refs:
        para = doc.add_paragraph(ref)
        para.paragraph_format.left_indent = Inches(0.3)
        para.paragraph_format.first_line_indent = Inches(-0.3)


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
    body_text = "\n".join(text_of(el) for el in doc.element.body)
    if "2.2.3 Dec-POMDP" in body_text:
        replace_section(
            doc,
            "2.2.3 Dec-POMDP",
            "2.2.4 CTDE",
            lambda tmp: add_expanded_decpomdp_section(tmp, building_compact),
        )
    else:
        insert_section_before_any(doc, ["2.1.3 CityLearn", "2.2.4 CityLearn", "2.3 Variables de la investigacion"], lambda tmp: add_expanded_decpomdp_section(tmp, building_compact))
    insert_section_before(doc, "Capitulo 2.", add_cap1_validation)
    insert_section_before(doc, "Capitulo 3.", add_cap2_validation)
    replace_section(doc, "Capitulo 3. Metodologia", "Capitulo 4.", add_cap3_methodology)
    insert_section_before(doc, "Referencias bibliograficas", add_cap6_completion_plan)
    normalize_chapter2_numbering(doc)
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
    add_cap4_problem_question_response(doc, detail)
    add_cap5(doc, detail, treatment, building_compact, eq_summary, figures, convergence, kpi_ranking, kpi_catalog)
    for el in after:
        append_before_sectpr(doc, el)
    append_apa_references(doc)
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
    final_ts = load_final_episode_timeseries(treatment)
    traces = load_trace_samples()
    checkpoints = load_checkpoint_summary()
    figures = make_figures(detail, treatment, building_compact, eq_summary, episodes, convergence, kpi_ranking, final_ts, traces, checkpoints)
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
        "final_timeseries_rows": len(final_ts),
        "trace_rows": len(traces),
        "checkpoint_rows": len(checkpoints),
        "figure_count_generated": len(figures),
        "stats_csv": str(TABLE_DIR / "gdrive_objective_aligned_statistics.csv"),
        "pairs_csv": str(TABLE_DIR / "gdrive_objective_pairwise_mannwhitney_holm.csv"),
        "has_oe1": "OE.1: efecto del MADRL sobre flexibilidad energetica" in full,
        "has_oe2": "OE.2: efecto del MADRL sobre emisiones de CO2" in full,
        "has_oe3": "OE.3: efecto del MADRL sobre costos energeticos" in full,
        "has_decpomdp_expanded": "dimension global agregada 1856" in full and "gamma=0.9999" in full,
        "has_convergence_section": "Curvas de convergencia y episodios de aprendizaje" in full,
        "has_citylearn_v2_evaluate_v2_section": "KPIs bajo nomenclatura CityLearn v2 evaluate_v2" in full,
        "has_distributed_madrl_figures": "Figura 5.9a. Distribucion episodica" in full and "Figura 5.10. Trade-off multiobjetivo" in full,
        "has_no_aggregate_figure_section": "5.11 Figuras complementarias" not in full,
        "declares_happo_artifact_limit": "CSV materializado conserva 49 filas episodicas" in full,
        "has_no_old_global_kw": "p = 0,0459" not in full and "p=0,0459" not in full,
        "has_no_local_reference": "referencia local" not in full.lower(),
        "has_no_short_run_phrase": "5 episodios" not in full.lower(),
    }
    METRICS.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
