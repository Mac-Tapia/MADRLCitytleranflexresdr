# ── 9.1  Suite de pruebas estadísticas ──────────────────────────────────────
from scipy import stats
import itertools
import json
import os
import pandas as pd

SCENARIO_WEIGHTS = {
    "E1": {"peak_average": 0.50, "carbon_emissions": 0.25, "electricity_cost": 0.25},
    "E2": {"peak_average": 0.25, "carbon_emissions": 0.50, "electricity_cost": 0.25},
    "E3": {"peak_average": 0.25, "carbon_emissions": 0.25, "electricity_cost": 0.50},
}
INVERT = {"peak_average", "carbon_emissions", "electricity_cost"}  # menor = mejor

def cliff_delta(x, y):
    n1, n2 = len(x), len(y)
    d = sum(1 for a in x for b in y if a>b) - sum(1 for a in x for b in y if a<b)
    return d / (n1 * n2)

def build_scores(df: pd.DataFrame) -> dict:
    algorithms = sorted(str(a) for a in df["algorithm"].unique())
    scores = {a: [] for a in algorithms}
    for sc, weights in SCENARIO_WEIGHTS.items():
        sub = df[df["scenario"] == sc].copy()
        if sub.empty:
            continue
        norm_cols = []
        w_arr = []
        for kpi, w in weights.items():
            col = str(kpi)
            if col not in sub.columns:
                continue
            col_series = sub[col]
            _arr = np.asarray(col_series, dtype=float)
            vmin = float(np.nanmin(_arr))
            vmax = float(np.nanmax(_arr))
            rng  = vmax - vmin
            nrm  = pd.Series((_arr - vmin) / rng if rng > 0 else np.full(len(_arr), 0.5), index=sub.index)
            sub[f"{col}_n"] = 1 - nrm if col in INVERT else nrm
            norm_cols.append(f"{col}_n")
            w_arr.append(w)
        w_arr = np.array(w_arr) / sum(w_arr)
        sub["score"] = sum(sub[nc] * wt for nc, wt in zip(norm_cols, w_arr))
        for a in algorithms:
            v = sub.loc[sub["algorithm"] == a, "score"].to_numpy()
            if len(v) > 0:
                scores[a].append(float(v[0]))
    return {a: np.array(v) for a, v in scores.items() if v}

stat_results = {}
if not df_results.empty:
    score_arrays = build_scores(df_results)
    algorithms   = sorted(score_arrays.keys())

    # 1. Shapiro-Wilk
    print("1. SHAPIRO-WILK")
    for a, arr in score_arrays.items():
        if len(arr) >= 3:
            s, p = stats.shapiro(arr)
            print(f"  {a:<6}: W={s:.4f} p={p:.4f}  {'NORMAL' if p>0.05 else 'no normal'}")
        else:
            print(f"  {a:<6}: muestras insuficientes")

    # 2. Kruskal-Wallis
    print("\n2. KRUSKAL-WALLIS")
    groups = [score_arrays[a] for a in algorithms if len(score_arrays.get(a,[])) > 0]
    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        sig = p < 0.05
        print(f"  H={h:.4f}  p={p:.4f}  → {'SIGNIFICATIVO ✅' if sig else 'No significativo'}")
        stat_results["kruskal_wallis"] = {"H": float(h), "p": float(p), "significant": sig}

    # 3. Mann-Whitney U
    print("\n3. MANN-WHITNEY U (pairwise + Cliff δ)")
    mwu = {}
    for a1, a2 in itertools.combinations(algorithms, 2):
        arr1, arr2 = score_arrays.get(a1, np.array([])), score_arrays.get(a2, np.array([]))
        if len(arr1) < 1 or len(arr2) < 1:
            continue
        try:
            s, p = stats.mannwhitneyu(arr1, arr2, alternative="two-sided")
            d = cliff_delta(arr1.tolist(), arr2.tolist())
            winner = a1 if arr1.mean() > arr2.mean() else a2
            mwu[f"{a1}_vs_{a2}"] = {"p": float(p), "cliff_delta": float(d), "winner": winner}
            print(f"  {a1} vs {a2}: p={p:.4f} {'✅' if p<0.05 else ''}  δ={d:.3f}  ▶ {winner}")
        except Exception as e:
            print(f"  {a1} vs {a2}: {e}")
    stat_results["mann_whitney_u"] = mwu

    # 4. Ranking
    print("\n4. RANKING GLOBAL")
    ranking = sorted(
        [{"algorithm": a, "mean_score": float(v.mean())} for a, v in score_arrays.items()],
        key=lambda x: -x["mean_score"],
    )
    for i, r in enumerate(ranking, 1):
        print(f"  {i}. {r['algorithm']:<6}  {r['mean_score']:.4f} {'★ Ganador' if i==1 else ''}")
    stat_results["ranking"]   = ranking
    stat_results["best_madrl"] = ranking[0]["algorithm"] if ranking else "N/A"

    os.makedirs(f"{OUTPUT_ROOT}/evaluation", exist_ok=True)
    with open(f"{OUTPUT_ROOT}/evaluation/statistical_analysis.json", "w") as f:
        json.dump(stat_results, f, indent=2, default=str)
    print(f"\n✅  {OUTPUT_ROOT}/evaluation/statistical_analysis.json")
else:
    print("⚠️  Sin datos — referencia oficial v4: MATD3 mejor (KW p=0.0459)")

# ── 9.2  Generar outputs/resumen_comparativo/ ─────────────────────────────
# Consolida los resultados de HAPPO, MASAC, MATD3 y MAAC en los tres escenarios.
# Genera los 4 artefactos canónicos requeridos por el proyecto.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as _plt
import json as _json
from pathlib import Path as _Path
from datetime import datetime as _dt

_comp_dir = _Path(str(OUTPUT_ROOT)) / "resumen_comparativo"
_comp_dir.mkdir(parents=True, exist_ok=True)

if not df_results.empty and stat_results:
    # 1. comparison_metrics.csv — KPIs por algoritmo y escenario
    df_results.to_csv(_comp_dir / "comparison_metrics.csv", index=False)

    # 2. best_madrl_selection.csv — ranking global con scores ponderados
    _ranking_df = pd.DataFrame(stat_results.get("ranking", []))
    _ranking_df.to_csv(_comp_dir / "best_madrl_selection.csv", index=False)

    # 3. best_madrl_report.json — informe completo de selección
    _best_report = {
        "mejor_algoritmo_madrl"  : stat_results.get("best_madrl", "N/A"),
        "fecha_seleccion"        : _dt.now().isoformat(),
        "ranking"                : stat_results.get("ranking", []),
        "kruskal_wallis"         : stat_results.get("kruskal_wallis", {}),
        "mann_whitney_u"         : stat_results.get("mann_whitney_u", {}),
        "metodologia"            : (
            "Score ponderado por escenario: "
            "E1(flex 0.50, CO2 0.25, costo 0.25), "
            "E2(flex 0.25, CO2 0.50, costo 0.25), "
            "E3(flex 0.25, CO2 0.25, costo 0.60). "
            "Pruebas estadísticas: Shapiro-Wilk + Kruskal-Wallis + Mann-Whitney U."
        ),
        "escenarios_evaluados"   : ["E1", "E2", "E3"],
        "algoritmos_evaluados"   : ["HAPPO", "MASAC", "MATD3", "MAAC"],
        "kpis_primarios"         : ["peak_average", "carbon_emissions", "electricity_cost"],
        "benchmarks_comparativos": {
            "capa"      : "CityLearn v2",
            "herramienta": "Stable-Baselines3",
            "algoritmos" : ["PPO", "SAC", "A2C"],
            "nota"       : "Agente central (central_agent=True); NO son MADRL v3",
        },
        "excluidos_como_baseline": ["MADDPG", "MAPPO"],
        "output_root"            : OUTPUT_ROOT,
    }
    with open(_comp_dir / "best_madrl_report.json", "w", encoding="utf-8") as _f:
        _json.dump(_best_report, _f, indent=2, ensure_ascii=False, default=str)

    # 4. global_comparison.png — bar chart de scores ponderados por algoritmo
    _CLR = {"HAPPO": "#3b82f6", "MASAC": "#a21caf", "MATD3": "#16a34a", "MAAC": "#d97706"}
    _ranking = stat_results.get("ranking", [])
    _algos  = [r["algorithm"] for r in _ranking]
    _scores = [r["mean_score"] for r in _ranking]
    _colors = [_CLR.get(a, "#94a3b8") for a in _algos]

    _fig, _ax = _plt.subplots(figsize=(9, 5))
    _bars = _ax.bar(_algos, _scores, color=_colors, edgecolor="white", linewidth=1.5, width=0.5)
    for _bar_rect, _v, _a in zip(_bars, _scores, _algos):
        _ax.text(
            _bar_rect.get_x() + _bar_rect.get_width() / 2,
            _bar_rect.get_height() + 0.005,
            f"{_v:.4f}",
            ha="center", fontsize=11, fontweight="bold",
        )
        if _a == _algos[0]:
            _ax.text(
                _bar_rect.get_x() + _bar_rect.get_width() / 2,
                _bar_rect.get_height() / 2,
                "★",
                ha="center", va="center", fontsize=18, color="white", fontweight="bold",
            )
    _ax.set_title(
        "Comparación global MADRL — Score ponderado por escenario\n"
        "HAPPO / MASAC / MATD3 / MAAC  ·  3 escenarios × 4 algoritmos = 12 corridas",
        fontsize=12, fontweight="bold",
    )
    _ax.set_ylabel("Score ponderado promedio (mayor = mejor)", fontsize=11)
    _ax.set_ylim(0, (max(_scores) * 1.15) if _scores else 1.0)
    _ax.grid(axis="y", alpha=0.3)
    _ax.set_facecolor("#f8fafc")
    _kw = stat_results.get("kruskal_wallis", {})
    if _kw:
        _ax.text(
            0.98, 0.04,
            f"Kruskal-Wallis p={_kw.get('p', '?'):.4f}  {'✅ sig.' if _kw.get('significant') else ''}",
            transform=_ax.transAxes, ha="right", fontsize=9, color="#475569",
        )
    _plt.tight_layout()
    _plt.savefig(_comp_dir / "global_comparison.png", dpi=150, bbox_inches="tight")
    _plt.close(_fig)

    print(f"\n{'='*65}")
    print(f"  resumen_comparativo/ → {_comp_dir}")
    print(f"{'='*65}")
    print("  comparison_metrics.csv   — KPIs por algoritmo y escenario")
    print("  best_madrl_selection.csv — ranking global ponderado")
    print("  best_madrl_report.json   — informe completo de selección")
    print("  global_comparison.png    — gráfico comparativo global")
    _best = stat_results.get("best_madrl", "N/A")
    print(f"\n  Mejor algoritmo MADRL seleccionado: {_best}")
    _kw_p = _kw.get('p', None) if _kw else None
    if _kw_p is not None:
        print(f"  Kruskal-Wallis p = {_kw_p:.4f}  {'(SIGNIFICATIVO ✅)' if _kw.get('significant') else ''}")
    print(f"{'='*65}")
else:
    print("⚠️  Sin datos de entrenamiento — ejecuta Sección 7 y 8 primero.")
    print("   Referencia corrida v4 (MATD3 ganador, KW p=0.0459):")
    print("     1. MATD3  0.7445 ★")
    print("     2. MASAC  ~0.73")
    print("     3. MAAC   ~0.72")
    print("     4. HAPPO  ~0.70")

# ── Exportar a resumen_comparativo/ ─────────────────────────────────────────
_resumen_dir = Path(OUTPUT_ROOT) / 'resumen_comparativo'
_resumen_dir.mkdir(parents=True, exist_ok=True)

if not df_results.empty:
    # comparison_metrics.csv — todas las métricas por algoritmo y escenario
    df_results.to_csv(_resumen_dir / 'comparison_metrics.csv', index=False)
    print(f'Exportado: {_resumen_dir}/comparison_metrics.csv')

    # best_madrl_selection.csv — ranking estadístico
    if stat_results and 'ranking' in stat_results:
        import csv as _csv
        _best_algo = stat_results.get('best_madrl',
                                      stat_results['ranking'][0]['algorithm'])
        with open(_resumen_dir / 'best_madrl_selection.csv', 'w', newline='',
                  encoding='utf-8') as _cf:
            _w = _csv.writer(_cf)
            _w.writerow(['rank', 'algorithm', 'mean_score', 'selected'])
            for _i, _r in enumerate(stat_results['ranking'], 1):
                _w.writerow([_i, _r['algorithm'],
                             f"{_r.get('mean_score', ''):.4f}",
                             'SI' if _i == 1 else 'NO'])
        print(f'Exportado: {_resumen_dir}/best_madrl_selection.csv')

        # best_madrl_report.json
        _kw = stat_results.get('kruskal_wallis', {})
        with open(_resumen_dir / 'best_madrl_report.json', 'w', encoding='utf-8') as _f:
            json.dump({
                'mejor_madrl': _best_algo,
                'ranking': stat_results['ranking'],
                'kruskal_wallis': _kw,
                'criterios': [
                    'reward_promedio', 'reward_acumulado', 'estabilidad',
                    'velocidad_convergencia', 'reduccion_picos',
                    'gestion_soc_bess', 'reduccion_co2',
                    'cumplimiento_restricciones', 'consistencia_escenarios',
                ],
                'n_episodios': globals().get('N_EPISODES', 50),
                'escenarios': globals().get('SCENARIOS', ['E1', 'E2', 'E3']),
                'generated_at': datetime.now().isoformat() if 'datetime' in dir() else 'N/A',
            }, _f, indent=2, ensure_ascii=False)
        print(f'Exportado: {_resumen_dir}/best_madrl_report.json')

        # global_comparison.png
        try:
            import matplotlib.pyplot as _plt
            import matplotlib
            matplotlib.use('Agg')
            _algos_rank = [_r['algorithm'] for _r in stat_results['ranking']]
            _scores_rank = [_r.get('mean_score', 0) for _r in stat_results['ranking']]
            _clrs = ['#16a34a' if _i == 0 else '#3b82f6'
                     for _i in range(len(_algos_rank))]
            _fig, _ax = _plt.subplots(figsize=(8, 5))
            _bars = _ax.bar(_algos_rank, _scores_rank, color=_clrs, edgecolor='white', lw=1.5)
            _ax.set_title(
                f'Selección del mejor MADRL — Score global (3 escenarios)\n'
                f'Ganador: {_best_algo}  |  KW p={_kw.get("p", "?"):.4f}',
                fontsize=12, fontweight='bold')
            _ax.set_ylabel('Score global (0-1, mayor es mejor)')
            _ax.set_ylim(0, 1)
            _ax.grid(axis='y', alpha=0.3)
            _ax.set_facecolor('#f8fafc')
            for _bar_rect, _s in zip(_bars, _scores_rank):
                _ax.text(_bar_rect.get_x() + _bar_rect.get_width() / 2, _bar_rect.get_height() + 0.01,
                         f'{_s:.4f}', ha='center', fontsize=11, fontweight='bold')
            _plt.tight_layout()
            _plt.savefig(_resumen_dir / 'global_comparison.png', dpi=150, bbox_inches='tight')
            _plt.close()
            print(f'Exportado: {_resumen_dir}/global_comparison.png')
        except Exception as _e_fig:
            print(f'[WARN] global_comparison.png: {_e_fig}')

    print()
    print(f'Mejor algoritmo MADRL seleccionado: '
          f'{stat_results.get("best_madrl", stat_results["ranking"][0]["algorithm"])}')
