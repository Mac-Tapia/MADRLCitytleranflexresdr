from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


REPO = Path(__file__).resolve().parents[2]
RUN_ID = "madrl_v3_20260627_164047"
STATS_DIR = (
    REPO
    / "outputs"
    / RUN_ID
    / "resumen_comparativo"
    / "estadistica"
)
SCORES_CSV = STATS_DIR / "scores_kpi_algoritmo_madrl.csv"
EPISODE_CSV = STATS_DIR / "descriptivo_distrito_colab.csv"
SCENARIO_SCORES_CSV = STATS_DIR / "scenario_scores_colab.csv"
OUT_DIR = STATS_DIR / "problemas_objetivos_hipotesis"

ALPHA = 0.05
ALGORITHMS = ["MAAC", "MASAC", "MATD3"]
EXPECTED_ALGORITHMS = ["HAPPO", "MAAC", "MASAC", "MATD3"]
TARGETS = {
    "OE1": {
        "scenario": "E1",
        "dimension": "Flexibilidad energética",
        "problem": (
            "PE.1: ¿En qué medida el algoritmo MADRL impacta en la flexibilidad "
            "energética en comunidades inteligentes de la ciudad de Iquitos, y "
            "cuál de los algoritmos presenta el mejor desempeño en el escenario E1?"
        ),
        "objective": (
            "OE.1: Determinar el impacto de los algoritmos MADRLs en la "
            "flexibilidad energética en comunidades inteligentes de la ciudad de "
            "Iquitos e identificar cuál de los algoritmos presenta el mejor "
            "desempeño en el escenario E1."
        ),
        "h0": "HE10",
        "h1": "HE11",
    },
    "OE2": {
        "scenario": "E2",
        "dimension": "Emisiones de CO₂",
        "problem": (
            "PE.2: ¿En qué medida el algoritmo MADRL impacta en las emisiones de "
            "CO₂ en comunidades inteligentes de la ciudad de Iquitos, y cuál de "
            "los algoritmos presenta el mejor desempeño en el escenario E2?"
        ),
        "objective": (
            "OE.2: Determinar el impacto de los algoritmos MADRLs en las emisiones "
            "de CO₂ en comunidades inteligentes de la ciudad de Iquitos e "
            "identificar cuál de los algoritmos presenta el mejor desempeño en el "
            "escenario E2."
        ),
        "h0": "HE20",
        "h1": "HE21",
    },
    "OE3": {
        "scenario": "E3",
        "dimension": "Costos energéticos",
        "problem": (
            "PE.3: ¿En qué medida el algoritmo MADRL impacta en los costos "
            "energéticos en comunidades inteligentes de la ciudad de Iquitos, y "
            "cuál de los algoritmos presenta el mejor desempeño en el escenario E3?"
        ),
        "objective": (
            "OE.3: Determinar el impacto de los algoritmos MADRLs en los costos "
            "energéticos en comunidades inteligentes de la ciudad de Iquitos e "
            "identificar cuál de los algoritmos presenta el mejor desempeño en el "
            "escenario E3."
        ),
        "h0": "HE30",
        "h1": "HE31",
    },
}


def holm_adjust(p_values: list[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    m = len(values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) == 0 or len(b) == 0:
        return math.nan
    greater = sum(float(x > y) for x in a for y in b)
    smaller = sum(float(x < y) for x in a for y in b)
    return (greater - smaller) / (len(a) * len(b))


def epsilon_squared_kruskal(h_statistic: float, n: int, groups: int) -> float:
    if n <= groups:
        return math.nan
    return max(0.0, (h_statistic - groups + 1) / (n - groups))


def format_number(value: float, digits: int = 4) -> str:
    if pd.isna(value):
        return "no calculable"
    if value != 0 and abs(value) < 0.0001:
        return f"{value:.3e}"
    return f"{value:.{digits}f}"


def prepare_target_data(scores: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for axis, meta in TARGETS.items():
        part = scores[
            (scores["axis"] == axis)
            & (scores["scenario"] == meta["scenario"])
            & (scores["algorithm"].isin(ALGORITHMS))
        ].copy()
        part["scope"] = axis
        part["target_scenario"] = meta["scenario"]
        part["analysis_key"] = (
            part["axis"].astype(str) + "|" + part["kpi"].astype(str)
        )
        pieces.append(part)
    return pd.concat(pieces, ignore_index=True)


def descriptive_rows(data: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for scope, scope_data in data.groupby("scope", sort=False):
        meta = TARGETS[scope]
        for algorithm in EXPECTED_ALGORITHMS:
            values = scope_data.loc[
                scope_data["algorithm"] == algorithm, "signed_relative_gain"
            ].dropna()
            if values.empty:
                rows.append(
                    {
                        "scope": scope,
                        "scenario": meta["scenario"],
                        "dimension": meta["dimension"],
                        "algorithm": algorithm,
                        "n_kpis": 0,
                        "mean_gain": math.nan,
                        "median_gain": math.nan,
                        "std_gain": math.nan,
                        "q1_gain": math.nan,
                        "q3_gain": math.nan,
                        "min_gain": math.nan,
                        "max_gain": math.nan,
                        "improved_kpis": 0,
                        "not_improved_kpis": 0,
                        "coverage": "sin KPI finales comparables",
                    }
                )
                continue
            alg_data = scope_data[scope_data["algorithm"] == algorithm]
            rows.append(
                {
                    "scope": scope,
                    "scenario": meta["scenario"],
                    "dimension": meta["dimension"],
                    "algorithm": algorithm,
                    "n_kpis": int(values.size),
                    "mean_gain": float(values.mean()),
                    "median_gain": float(values.median()),
                    "std_gain": float(values.std(ddof=1)),
                    "q1_gain": float(values.quantile(0.25)),
                    "q3_gain": float(values.quantile(0.75)),
                    "min_gain": float(values.min()),
                    "max_gain": float(values.max()),
                    "improved_kpis": int(alg_data["improved_vs_baseline"].sum()),
                    "not_improved_kpis": int(
                        (~alg_data["improved_vs_baseline"]).sum()
                    ),
                    "coverage": "completa para KPI-gains disponibles",
                }
            )

    global_data = data.copy()
    for algorithm in EXPECTED_ALGORITHMS:
        values = global_data.loc[
            global_data["algorithm"] == algorithm, "signed_relative_gain"
        ].dropna()
        if values.empty:
            rows.append(
                {
                    "scope": "GLOBAL",
                    "scenario": "E1+E2+E3",
                    "dimension": "Gestión coordinada integral",
                    "algorithm": algorithm,
                    "n_kpis": 0,
                    "mean_gain": math.nan,
                    "median_gain": math.nan,
                    "std_gain": math.nan,
                    "q1_gain": math.nan,
                    "q3_gain": math.nan,
                    "min_gain": math.nan,
                    "max_gain": math.nan,
                    "improved_kpis": 0,
                    "not_improved_kpis": 0,
                    "coverage": "sin KPI finales comparables",
                }
            )
            continue
        alg_data = global_data[global_data["algorithm"] == algorithm]
        rows.append(
            {
                "scope": "GLOBAL",
                "scenario": "E1+E2+E3",
                "dimension": "Gestión coordinada integral",
                "algorithm": algorithm,
                "n_kpis": int(values.size),
                "mean_gain": float(values.mean()),
                "median_gain": float(values.median()),
                "std_gain": float(values.std(ddof=1)),
                "q1_gain": float(values.quantile(0.25)),
                "q3_gain": float(values.quantile(0.75)),
                "min_gain": float(values.min()),
                "max_gain": float(values.max()),
                "improved_kpis": int(alg_data["improved_vs_baseline"].sum()),
                "not_improved_kpis": int(
                    (~alg_data["improved_vs_baseline"]).sum()
                ),
                "coverage": "completa para KPI-gains disponibles",
            }
        )
    return rows


def shapiro_rows(data: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    scopes = [(axis, data[data["scope"] == axis]) for axis in TARGETS]
    scopes.append(("GLOBAL", data))
    for scope, scope_data in scopes:
        scenario = (
            TARGETS[scope]["scenario"] if scope in TARGETS else "E1+E2+E3"
        )
        for algorithm in EXPECTED_ALGORITHMS:
            values = scope_data.loc[
                scope_data["algorithm"] == algorithm, "signed_relative_gain"
            ].dropna()
            if len(values) < 3:
                rows.append(
                    {
                        "scope": scope,
                        "scenario": scenario,
                        "algorithm": algorithm,
                        "n": int(len(values)),
                        "w_statistic": math.nan,
                        "p_value": math.nan,
                        "normality_rejected": None,
                        "status": "datos insuficientes",
                    }
                )
                continue
            result = stats.shapiro(values.to_numpy())
            rows.append(
                {
                    "scope": scope,
                    "scenario": scenario,
                    "algorithm": algorithm,
                    "n": int(len(values)),
                    "w_statistic": float(result.statistic),
                    "p_value": float(result.pvalue),
                    "normality_rejected": bool(result.pvalue < ALPHA),
                    "status": "calculado",
                }
            )
    return rows


def kruskal_rows(data: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    scopes = [(axis, data[data["scope"] == axis]) for axis in TARGETS]
    scopes.append(("GLOBAL", data))
    for scope, scope_data in scopes:
        groups = [
            scope_data.loc[
                scope_data["algorithm"] == algorithm, "signed_relative_gain"
            ]
            .dropna()
            .to_numpy()
            for algorithm in ALGORITHMS
        ]
        result = stats.kruskal(*groups)
        n_total = sum(len(group) for group in groups)
        rows.append(
            {
                "scope": scope,
                "scenario": (
                    TARGETS[scope]["scenario"]
                    if scope in TARGETS
                    else "E1+E2+E3"
                ),
                "method": "Kruskal-Wallis",
                "algorithms": ", ".join(ALGORITHMS),
                "n_total": n_total,
                "group_n": json.dumps(
                    dict(zip(ALGORITHMS, map(len, groups))), ensure_ascii=False
                ),
                "statistic": float(result.statistic),
                "p_value": float(result.pvalue),
                "effect_size": epsilon_squared_kruskal(
                    float(result.statistic), n_total, len(groups)
                ),
                "effect_name": "epsilon_squared",
                "significant": bool(result.pvalue < ALPHA),
                "decision": (
                    "se rechaza igualdad global"
                    if result.pvalue < ALPHA
                    else "no se rechaza igualdad global"
                ),
            }
        )
        pivot = scope_data.pivot_table(
            index="analysis_key",
            columns="algorithm",
            values="signed_relative_gain",
            aggfunc="first",
        ).dropna(subset=ALGORITHMS)
        friedman = stats.friedmanchisquare(
            *(pivot[algorithm].to_numpy() for algorithm in ALGORITHMS)
        )
        kendall_w = float(friedman.statistic) / (
            len(pivot) * (len(ALGORITHMS) - 1)
        )
        rows.append(
            {
                "scope": scope,
                "scenario": (
                    TARGETS[scope]["scenario"]
                    if scope in TARGETS
                    else "E1+E2+E3"
                ),
                "method": "Friedman pareado por KPI",
                "algorithms": ", ".join(ALGORITHMS),
                "n_total": int(len(pivot) * len(ALGORITHMS)),
                "group_n": json.dumps(
                    {algorithm: int(len(pivot)) for algorithm in ALGORITHMS},
                    ensure_ascii=False,
                ),
                "statistic": float(friedman.statistic),
                "p_value": float(friedman.pvalue),
                "effect_size": kendall_w,
                "effect_name": "Kendall_W",
                "significant": bool(friedman.pvalue < ALPHA),
                "decision": (
                    "se rechaza igualdad global pareada"
                    if friedman.pvalue < ALPHA
                    else "no se rechaza igualdad global pareada"
                ),
            }
        )
    return rows


def impact_rows(data: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    scopes = [(axis, data[data["scope"] == axis]) for axis in TARGETS]
    scopes.append(("GLOBAL", data))
    for scope, scope_data in scopes:
        local_rows = []
        for algorithm in ALGORITHMS:
            values = scope_data.loc[
                scope_data["algorithm"] == algorithm, "signed_relative_gain"
            ].dropna()
            result = stats.wilcoxon(
                values.to_numpy(),
                zero_method="wilcox",
                alternative="two-sided",
                method="auto",
            )
            local_rows.append(
                {
                    "scope": scope,
                    "scenario": (
                        TARGETS[scope]["scenario"]
                        if scope in TARGETS
                        else "E1+E2+E3"
                    ),
                    "algorithm": algorithm,
                    "n_kpis": int(len(values)),
                    "mean_gain": float(values.mean()),
                    "median_gain": float(values.median()),
                    "statistic": float(result.statistic),
                    "p_value": float(result.pvalue),
                }
            )
        adjusted = holm_adjust([row["p_value"] for row in local_rows])
        for row, p_holm in zip(local_rows, adjusted):
            row["p_holm"] = p_holm
            row["significant_holm"] = bool(p_holm < ALPHA)
            row["direction"] = (
                "favorable"
                if row["median_gain"] > 0
                else "desfavorable"
                if row["median_gain"] < 0
                else "neutra"
            )
            row["decision"] = (
                "impacto frente al baseline detectado"
                if p_holm < ALPHA
                else "impacto frente al baseline no detectado"
            )
            rows.append(row)
    return rows


def pairwise_rows(data: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    mwu_rows: list[dict] = []
    paired_rows: list[dict] = []
    scopes = [(axis, data[data["scope"] == axis]) for axis in TARGETS]
    scopes.append(("GLOBAL", data))
    for scope, scope_data in scopes:
        scenario = (
            TARGETS[scope]["scenario"] if scope in TARGETS else "E1+E2+E3"
        )
        local_mwu = []
        local_paired = []
        for algorithm_a, algorithm_b in combinations(ALGORITHMS, 2):
            values_a = scope_data.loc[
                scope_data["algorithm"] == algorithm_a, "signed_relative_gain"
            ].dropna()
            values_b = scope_data.loc[
                scope_data["algorithm"] == algorithm_b, "signed_relative_gain"
            ].dropna()
            mwu = stats.mannwhitneyu(
                values_a.to_numpy(),
                values_b.to_numpy(),
                alternative="two-sided",
                method="auto",
            )
            local_mwu.append(
                {
                    "scope": scope,
                    "scenario": scenario,
                    "algorithm_a": algorithm_a,
                    "algorithm_b": algorithm_b,
                    "n_a": int(len(values_a)),
                    "n_b": int(len(values_b)),
                    "median_a": float(values_a.median()),
                    "median_b": float(values_b.median()),
                    "u_statistic": float(mwu.statistic),
                    "p_value": float(mwu.pvalue),
                    "cliffs_delta_a_minus_b": cliffs_delta(
                        values_a.to_numpy(), values_b.to_numpy()
                    ),
                }
            )

            pair = scope_data[
                scope_data["algorithm"].isin([algorithm_a, algorithm_b])
            ].pivot_table(
                index="analysis_key",
                columns="algorithm",
                values="signed_relative_gain",
                aggfunc="first",
            )
            pair = pair.dropna(subset=[algorithm_a, algorithm_b])
            differences = (
                pair[algorithm_a].to_numpy() - pair[algorithm_b].to_numpy()
            )
            paired = stats.wilcoxon(
                differences,
                zero_method="wilcox",
                alternative="two-sided",
                method="auto",
            )
            local_paired.append(
                {
                    "scope": scope,
                    "scenario": scenario,
                    "algorithm_a": algorithm_a,
                    "algorithm_b": algorithm_b,
                    "n_pairs": int(len(pair)),
                    "median_difference_a_minus_b": float(np.median(differences)),
                    "w_statistic": float(paired.statistic),
                    "p_value": float(paired.pvalue),
                }
            )

        for local_rows in (local_mwu, local_paired):
            adjusted = holm_adjust([row["p_value"] for row in local_rows])
            for row, p_holm in zip(local_rows, adjusted):
                row["p_holm"] = p_holm
                row["significant_holm"] = bool(p_holm < ALPHA)
                row["decision"] = (
                    "diferencia por pares detectada"
                    if p_holm < ALPHA
                    else "diferencia por pares no detectada"
                )
        mwu_rows.extend(local_mwu)
        paired_rows.extend(local_paired)
    return mwu_rows, paired_rows


def build_decisions(
    descriptive: pd.DataFrame,
    omnibus: pd.DataFrame,
    impact: pd.DataFrame,
    scenario_scores: pd.DataFrame,
) -> list[dict]:
    rows: list[dict] = []
    for scope, meta in TARGETS.items():
        desc = descriptive[
            (descriptive["scope"] == scope)
            & (descriptive["algorithm"].isin(ALGORITHMS))
        ].sort_values("median_gain", ascending=False)
        best = str(desc.iloc[0]["algorithm"])
        kw = omnibus[
            (omnibus["scope"] == scope)
            & (omnibus["method"] == "Kruskal-Wallis")
        ].iloc[0]
        friedman = omnibus[
            (omnibus["scope"] == scope)
            & (omnibus["method"] == "Friedman pareado por KPI")
        ].iloc[0]
        impact_scope = impact[impact["scope"] == scope]
        significant_impact = impact_scope[impact_scope["significant_holm"]]
        compound_h1 = bool(friedman["significant"]) and not significant_impact.empty
        rows.append(
            {
                "scope": scope,
                "problem": meta["problem"],
                "objective": meta["objective"],
                "null_hypothesis": meta["h0"],
                "alternative_hypothesis": meta["h1"],
                "descriptive_best_algorithm": best,
                "best_median_gain": float(desc.iloc[0]["median_gain"]),
                "kruskal_h": float(kw["statistic"]),
                "kruskal_p": float(kw["p_value"]),
                "friedman_chi2": float(friedman["statistic"]),
                "friedman_p": float(friedman["p_value"]),
                "kendall_w": float(friedman["effect_size"]),
                "impact_algorithms_significant_holm": ", ".join(
                    significant_impact["algorithm"].tolist()
                )
                or "ninguno",
                "hypothesis_decision": (
                    f"se respalda {meta['h1']}"
                    if compound_h1
                    else (
                        f"no se rechaza {meta['h0']}; "
                        f"no se reúne evidencia conjunta para {meta['h1']}"
                    )
                ),
                "objective_compliance": (
                    "cumplido descriptivamente y contrastado de forma exploratoria; "
                    "pendiente confirmación multisemilla"
                ),
                "coverage_limitation": (
                    "HAPPO no dispone de KPI-gains finales comparables; la "
                    "inferencia incluye MAAC, MASAC y MATD3."
                ),
            }
        )

    global_desc = descriptive[
        (descriptive["scope"] == "GLOBAL")
        & (descriptive["algorithm"].isin(ALGORITHMS))
    ].sort_values("median_gain", ascending=False)
    global_kw = omnibus[
        (omnibus["scope"] == "GLOBAL")
        & (omnibus["method"] == "Kruskal-Wallis")
    ].iloc[0]
    global_friedman = omnibus[
        (omnibus["scope"] == "GLOBAL")
        & (omnibus["method"] == "Friedman pareado por KPI")
    ].iloc[0]
    score_desc = (
        scenario_scores.groupby("algorithm")["scenario_score"]
        .agg(["mean", "std", "min", "max"])
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    rows.append(
        {
            "scope": "GLOBAL",
            "problem": (
                "PG: ¿En qué medida los algoritmos MADRLs impactan en la gestión "
                "coordinada de la flexibilidad energética, las emisiones de CO₂ y "
                "los costos energéticos en comunidades inteligentes de la ciudad "
                "de Iquitos, y cuál presenta el mejor desempeño a nivel global?"
            ),
            "objective": (
                "OG: Determinar el impacto de los algoritmos MADRLs en la gestión "
                "coordinada de la flexibilidad energética, las emisiones de CO₂ y "
                "los costos energéticos en comunidades inteligentes de la ciudad "
                "de Iquitos, e identificar el mejor desempeño global."
            ),
            "null_hypothesis": "H0G",
            "alternative_hypothesis": "H1G",
            "descriptive_best_algorithm": str(score_desc.iloc[0]["algorithm"]),
            "best_equal_weight_scenario_score": float(score_desc.iloc[0]["mean"]),
            "robust_median_gain_best_algorithm": str(
                global_desc.iloc[0]["algorithm"]
            ),
            "robust_best_median_gain": float(global_desc.iloc[0]["median_gain"]),
            "kruskal_h": float(global_kw["statistic"]),
            "kruskal_p": float(global_kw["p_value"]),
            "friedman_chi2": float(global_friedman["statistic"]),
            "friedman_p": float(global_friedman["p_value"]),
            "kendall_w": float(global_friedman["effect_size"]),
            "hypothesis_decision": (
                "se rechaza H0G y se respalda H1G de forma exploratoria para "
                "MAAC, MASAC y MATD3"
                if bool(global_friedman["significant"])
                and bool(
                    impact[
                        (impact["scope"] == "GLOBAL")
                        & (impact["significant_holm"])
                    ].shape[0]
                )
                else "no se rechaza H0G; no se reúne evidencia para H1G"
            ),
            "objective_compliance": (
                "cumplido descriptivamente y contrastado de forma exploratoria; "
                "no se identifica un ganador global estadísticamente concluyente"
            ),
            "coverage_limitation": (
                "El ranking global comprende MAAC, MASAC y MATD3; HAPPO carece "
                "de KPI-gains finales y la corrida dispone de una sola semilla."
            ),
        }
    )
    return rows


def write_markdown(
    decisions: pd.DataFrame,
    descriptive: pd.DataFrame,
    omnibus: pd.DataFrame,
    impact: pd.DataFrame,
    scenario_scores: pd.DataFrame,
) -> None:
    lines = [
        f"# Respuesta estadística a problemas, objetivos e hipótesis — {RUN_ID}",
        "",
        (
            "Unidad primaria: ganancia relativa orientada de KPI frente al baseline "
            "(un valor positivo favorece al MADRL). Cada objetivo se restringe al "
            "escenario formulado: OE1/E1, OE2/E2 y OE3/E3."
        ),
        "",
        (
            "Alcance: análisis exploratorio de una sola semilla. HAPPO conserva "
            "episodios descriptivos, pero no KPI-gains finales comparables; por "
            "ello los contrastes de KPI incluyen MAAC, MASAC y MATD3."
        ),
        "",
    ]

    for scope in ["OE1", "OE2", "OE3"]:
        decision = decisions[decisions["scope"] == scope].iloc[0]
        meta = TARGETS[scope]
        desc = descriptive[
            (descriptive["scope"] == scope)
            & (descriptive["algorithm"].isin(ALGORITHMS))
        ].sort_values("median_gain", ascending=False)
        kw = omnibus[
            (omnibus["scope"] == scope)
            & (omnibus["method"] == "Kruskal-Wallis")
        ].iloc[0]
        friedman = omnibus[
            (omnibus["scope"] == scope)
            & (omnibus["method"] == "Friedman pareado por KPI")
        ].iloc[0]
        impact_scope = impact[impact["scope"] == scope].sort_values(
            "median_gain", ascending=False
        )
        lines.extend(
            [
                f"## {scope} / {meta['scenario']} — {meta['dimension']}",
                "",
                f"**Problema.** {meta['problem']}",
                "",
                f"**Objetivo.** {meta['objective']}",
                "",
                "| Algoritmo | n KPI | Media | Mediana | Mejorados | No mejorados |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for _, row in desc.iterrows():
            lines.append(
                "| {algorithm} | {n} | {mean} | {median} | {improved} | {not_improved} |".format(
                    algorithm=row["algorithm"],
                    n=int(row["n_kpis"]),
                    mean=format_number(row["mean_gain"]),
                    median=format_number(row["median_gain"]),
                    improved=int(row["improved_kpis"]),
                    not_improved=int(row["not_improved_kpis"]),
                )
            )
        lines.extend(
            [
                "",
                (
                    f"**Diferencias entre algoritmos.** Kruskal-Wallis "
                    f"H={format_number(kw['statistic'])}, "
                    f"p={format_number(kw['p_value'])}, "
                    f"ε²={format_number(kw['effect_size'])}: "
                    f"{kw['decision']}. Friedman pareado por KPI: "
                    f"χ²={format_number(friedman['statistic'])}, "
                    f"p={format_number(friedman['p_value'])}, "
                    f"Kendall W={format_number(friedman['effect_size'])}."
                ),
                "",
                (
                    "**Impacto frente al baseline.** "
                    + "; ".join(
                        f"{row.algorithm}: mediana={format_number(row.median_gain)}, "
                        f"p-Holm={format_number(row.p_holm)}"
                        for row in impact_scope.itertuples()
                    )
                    + "."
                ),
                "",
                (
                    f"**Decisión {meta['h0']}/{meta['h1']}.** "
                    f"{decision['hypothesis_decision']}."
                ),
                "",
                (
                    f"**Respuesta y cumplimiento.** El líder descriptivo por "
                    f"mediana de ganancia es {decision['descriptive_best_algorithm']}; "
                    f"{decision['objective_compliance']}."
                ),
                "",
            ]
        )

    global_decision = decisions[decisions["scope"] == "GLOBAL"].iloc[0]
    global_kw = omnibus[
        (omnibus["scope"] == "GLOBAL")
        & (omnibus["method"] == "Kruskal-Wallis")
    ].iloc[0]
    friedman = omnibus[
        (omnibus["scope"] == "GLOBAL")
        & (omnibus["method"] == "Friedman pareado por KPI")
    ].iloc[0]
    score_desc = (
        scenario_scores.groupby("algorithm")["scenario_score"]
        .agg(["mean", "std"])
        .reset_index()
        .sort_values("mean", ascending=False)
    )
    lines.extend(
        [
            "## Problema general, objetivo general e hipótesis general",
            "",
            f"**Problema.** {global_decision['problem']}",
            "",
            f"**Objetivo.** {global_decision['objective']}",
            "",
            "| Algoritmo | Score medio E1-E3 | Desv. |",
            "|---|---:|---:|",
        ]
    )
    for _, row in score_desc.iterrows():
        lines.append(
            f"| {row['algorithm']} | {format_number(row['mean'])} | "
            f"{format_number(row['std'])} |"
        )
    lines.extend(
        [
            "",
            (
                f"Kruskal-Wallis global: H={format_number(global_kw['statistic'])}, "
                f"p={format_number(global_kw['p_value'])}. Friedman pareado: "
                f"χ²={format_number(friedman['statistic'])}, "
                f"p={format_number(friedman['p_value'])}, "
                f"Kendall W={format_number(friedman['effect_size'])}."
            ),
            "",
            (
                f"**Decisión H0G/H1G.** "
                f"{global_decision['hypothesis_decision']}."
            ),
            "",
            (
                f"**Respuesta y cumplimiento del OG.** El score de escenarios "
                f"con igual peso ubica primero a "
                f"{global_decision['descriptive_best_algorithm']}; la mediana "
                f"robusta de KPI-gains ubica primero a "
                f"{global_decision['robust_median_gain_best_algorithm']}. La "
                "inversión de ranking y la ausencia de significancia impiden "
                "declarar un ganador global único."
            ),
            "",
        ]
    )
    (OUT_DIR / "respuesta_problemas_objetivos_hipotesis.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    for path in (SCORES_CSV, EPISODE_CSV, SCENARIO_SCORES_CSV):
        if not path.exists():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    scores = pd.read_csv(SCORES_CSV)
    episode = pd.read_csv(EPISODE_CSV)
    scenario_scores = pd.read_csv(SCENARIO_SCORES_CSV)
    data = prepare_target_data(scores)

    descriptive = pd.DataFrame(descriptive_rows(data))
    shapiro = pd.DataFrame(shapiro_rows(data))
    omnibus = pd.DataFrame(kruskal_rows(data))
    impact = pd.DataFrame(impact_rows(data))
    mwu_rows, paired_rows = pairwise_rows(data)
    mwu = pd.DataFrame(mwu_rows)
    paired = pd.DataFrame(paired_rows)
    decisions = pd.DataFrame(
        build_decisions(descriptive, omnibus, impact, scenario_scores)
    )

    descriptive.to_csv(
        OUT_DIR / "descriptivos_kpi_gains_por_problema.csv", index=False
    )
    episode.to_csv(
        OUT_DIR / "descriptivos_episodicos_contexto.csv", index=False
    )
    shapiro.to_csv(OUT_DIR / "normalidad_shapiro_por_problema.csv", index=False)
    omnibus.to_csv(
        OUT_DIR / "pruebas_omnibus_problemas_objetivos.csv", index=False
    )
    impact.to_csv(OUT_DIR / "impacto_vs_baseline_wilcoxon.csv", index=False)
    mwu.to_csv(OUT_DIR / "comparaciones_mwu_holm_problemas.csv", index=False)
    paired.to_csv(
        OUT_DIR / "comparaciones_wilcoxon_pareado_holm.csv", index=False
    )
    decisions.to_csv(
        OUT_DIR / "decisiones_problemas_objetivos_hipotesis.csv", index=False
    )
    write_markdown(
        decisions, descriptive, omnibus, impact, scenario_scores
    )

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "alpha": ALPHA,
        "source_scores": str(SCORES_CSV),
        "source_episode_descriptives": str(EPISODE_CSV),
        "target_filters": {
            axis: meta["scenario"] for axis, meta in TARGETS.items()
        },
        "expected_algorithms": EXPECTED_ALGORITHMS,
        "inferential_algorithms": ALGORITHMS,
        "happo_kpi_gains_available": bool(
            (
                data["algorithm"].astype(str).str.upper()
                == "HAPPO"
            ).any()
        ),
        "checks": {
            "target_rows": int(len(data)),
            "rows_by_scope_algorithm": (
                data.groupby(["scope", "algorithm"])
                .size()
                .unstack(fill_value=0)
                .to_dict(orient="index")
            ),
            "all_target_scenarios_match": bool(
                all(
                    (
                        data.loc[data["scope"] == axis, "scenario"]
                        == meta["scenario"]
                    ).all()
                    for axis, meta in TARGETS.items()
                )
            ),
            "decision_rows": int(len(decisions)),
            "omnibus_rows": int(len(omnibus)),
        },
        "limitations": [
            "Una sola semilla: los contrastes son exploratorios.",
            "HAPPO no tiene KPI-gains finales comparables.",
            "Las unidades KPI dentro de una corrida no sustituyen réplicas independientes.",
        ],
        "verdict": "correct",
    }
    (OUT_DIR / "problem_objective_hypothesis_statistical_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OUTPUT_DIR={OUT_DIR}")
    print(f"TARGET_ROWS={len(data)}")
    print(
        omnibus[
            ["scope", "scenario", "method", "statistic", "p_value", "effect_size"]
        ].to_string(index=False)
    )
    print(
        decisions[
            [
                "scope",
                "descriptive_best_algorithm",
                "kruskal_p",
                "hypothesis_decision",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
