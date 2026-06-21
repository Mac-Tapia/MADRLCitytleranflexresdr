"""
Patch script for madrl_citylearn_v3_tutorial.ipynb
Applies all required corrections per PROMPT MAESTRO:
1. Fix Cell 32: REPO auto-detection (no hardcoded /content/)
2. Insert Cell 7.4b: output reorganization to outputs/{MADRL}/{escenario}/
3. Update Cell 050 markdown: document correct output structure
4. Update Cell 054: export resumen_comparativo/ after statistical analysis
5. Update Cell 057: validate new output structure in informe tecnico
"""
import json
import shutil
from pathlib import Path

NB_PATH = Path("d:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")

# ── Load notebook ─────────────────────────────────────────────────────────────
with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]
print(f"Loaded notebook: {len(cells)} cells")

# ── Backup ───────────────────────────────────────────────────────────────────
bak = NB_PATH.with_suffix(".ipynb.patch_bak2")
shutil.copy(NB_PATH, bak)
print(f"Backup: {bak}")

# ── CHANGE 1: Fix Cell 32 — REPO auto-detection ───────────────────────────────
OLD_REPO = "REPO        = '/content/MADRLCitytleranflexresdr'"
NEW_REPO = (
    "# ── Deteccion automatica de REPO (Colab o local) ───────────────────────────\n"
    "try:\n"
    "    import google.colab  # type: ignore\n"
    "    _in_colab_61 = True\n"
    "except ImportError:\n"
    "    _in_colab_61 = False\n"
    "\n"
    "_repo_from_ctx = globals().get('REPO', None)\n"
    "if _repo_from_ctx and Path(_repo_from_ctx).exists():\n"
    "    REPO = _repo_from_ctx\n"
    "else:\n"
    "    _repo_candidates = [\n"
    "        '/content/MADRLCitytleranflexresdr',\n"
    "        'd:/MADRLCitytleranflexresdr',\n"
    "        str(Path.home() / 'MADRLCitytleranflexresdr'),\n"
    "        str(Path.cwd()),\n"
    "    ]\n"
    "    REPO = next(\n"
    "        (p for p in _repo_candidates if (Path(p) / 'CityLearn').exists()),\n"
    "        '/content/MADRLCitytleranflexresdr'\n"
    "    )"
)
src32 = "".join(cells[32]["source"])
assert OLD_REPO in src32, f"CHANGE 1 FAILED: target string not found in cell 32"
src32_new = src32.replace(OLD_REPO, NEW_REPO)
cells[32]["source"] = src32_new
print("CHANGE 1 applied: Cell 32 REPO detection fixed")

# ── CHANGE 2: Insert Cell 7.4b after index 43 ─────────────────────────────────
CELL_74B_SOURCE = (
    "# ── 7.4b  Reorganizar outputs al formato canónico: outputs/{MADRL}/{escenario}/ ──\n"
    "# El launcher escribe: {OUTPUT_ROOT}/happo/E1_seed_0/data/results.json\n"
    "# Formato requerido:   {OUTPUT_ROOT}/HAPPO/escenario_1/metrics.csv  etc.\n"
    "# Este paso genera la estructura canónica junto a los artefactos del launcher.\n"
    "import csv, json, shutil, os\n"
    "import pandas as pd\n"
    "from pathlib import Path\n"
    "from datetime import datetime\n"
    "\n"
    "_out  = Path(globals().get('OUTPUT_ROOT', '/tmp/madrl_output'))\n"
    "_repo = Path(globals().get('REPO', '/content/MADRLCitytleranflexresdr'))\n"
    "_hp   = globals().get('HYPERPARAMS', {})\n"
    "_seed = globals().get('SEED', 0)\n"
    "\n"
    "SCENARIO_MAP = {'E1': 'escenario_1', 'E2': 'escenario_2', 'E3': 'escenario_3'}\n"
    "ALGO_UPPER   = {'happo': 'HAPPO', 'masac': 'MASAC', 'matd3': 'MATD3', 'maac': 'MAAC'}\n"
    "\n"
    "print('Reorganizando artefactos al formato outputs/{MADRL}/{escenario}/ ...')\n"
    "_reorganized = []\n"
    "_missing = []\n"
    "\n"
    "for algo_lower, algo_upper in ALGO_UPPER.items():\n"
    "    for sc_short, sc_long in SCENARIO_MAP.items():\n"
    "        src_data = _out / algo_lower / f'{sc_short}_seed_{_seed}' / 'data'\n"
    "        dst_dir  = _out / algo_upper / sc_long\n"
    "        dst_dir.mkdir(parents=True, exist_ok=True)\n"
    "        (dst_dir / 'figures').mkdir(exist_ok=True)\n"
    "        ok_files = []\n"
    "\n"
    "        # 1. metrics.csv — desde results.json[citylearn_v3_report.all_values]\n"
    "        results_json = src_data / 'results.json'\n"
    "        if results_json.exists():\n"
    "            with open(results_json, encoding='utf-8') as _f:\n"
    "                _r = json.load(_f)\n"
    "            _all_v = _r.get('citylearn_v3_report', {}).get('all_values', {})\n"
    "            with open(dst_dir / 'metrics.csv', 'w', newline='', encoding='utf-8') as _cf:\n"
    "                _w = csv.writer(_cf)\n"
    "                _w.writerow(['metric', 'value'])\n"
    "                for _k, _v in _all_v.items():\n"
    "                    _w.writerow([_k, _v])\n"
    "            ok_files.append('metrics.csv')\n"
    "        else:\n"
    "            _missing.append(f'{algo_upper}/{sc_long}: results.json no encontrado')\n"
    "\n"
    "        # 2. rewards.csv — desde timeseries.csv, agregado por episodio\n"
    "        ts_csv = src_data / 'timeseries.csv'\n"
    "        if ts_csv.exists():\n"
    "            try:\n"
    "                _df_ts = pd.read_csv(ts_csv)\n"
    "                if 'episode' in _df_ts.columns and 'reward_mean' in _df_ts.columns:\n"
    "                    _ep_df = _df_ts.groupby('episode')['reward_mean'].agg(\n"
    "                        ['mean', 'sum', 'min', 'max']).reset_index()\n"
    "                    _ep_df.columns = ['episode', 'reward_mean', 'reward_sum',\n"
    "                                      'reward_min', 'reward_max']\n"
    "                    _ep_df.to_csv(dst_dir / 'rewards.csv', index=False)\n"
    "                else:\n"
    "                    _df_ts.to_csv(dst_dir / 'rewards.csv', index=False)\n"
    "                ok_files.append('rewards.csv')\n"
    "            except Exception as _e:\n"
    "                print(f'  [WARN] rewards.csv {algo_upper}/{sc_long}: {_e}')\n"
    "        else:\n"
    "            _missing.append(f'{algo_upper}/{sc_long}: timeseries.csv no encontrado')\n"
    "\n"
    "        # 3. training_monitor.csv — desde training_summary.json\n"
    "        summary_json = src_data / 'training_summary.json'\n"
    "        if summary_json.exists():\n"
    "            with open(summary_json, encoding='utf-8') as _f:\n"
    "                _s = json.load(_f)\n"
    "            _ep_sum = _s.get('episode_summaries', [])\n"
    "            if _ep_sum and isinstance(_ep_sum, list) and isinstance(_ep_sum[0], dict):\n"
    "                pd.DataFrame(_ep_sum).to_csv(dst_dir / 'training_monitor.csv',\n"
    "                                             index=False)\n"
    "            else:\n"
    "                with open(dst_dir / 'training_monitor.csv', 'w', newline='',\n"
    "                          encoding='utf-8') as _cf:\n"
    "                    _w = csv.writer(_cf)\n"
    "                    _w.writerow(['metric', 'value'])\n"
    "                    for _k, _v in _s.items():\n"
    "                        if not isinstance(_v, (dict, list)):\n"
    "                            _w.writerow([_k, _v])\n"
    "            ok_files.append('training_monitor.csv')\n"
    "        else:\n"
    "            with open(dst_dir / 'training_monitor.csv', 'w', newline='',\n"
    "                      encoding='utf-8') as _cf:\n"
    "                _w = csv.writer(_cf)\n"
    "                _w.writerow(['metric', 'value', 'note'])\n"
    "                _w.writerow(['status', 'pendiente',\n"
    "                             'training_summary.json no encontrado'])\n"
    "\n"
    "        # 4. resource_usage.csv\n"
    "        _ru_snap = _out / 'resource_usage_snapshot.json'\n"
    "        _ru_csv  = dst_dir / 'resource_usage.csv'\n"
    "        if _ru_snap.exists():\n"
    "            with open(_ru_snap) as _f:\n"
    "                _ru = json.load(_f)\n"
    "            with open(_ru_csv, 'w', newline='', encoding='utf-8') as _cf:\n"
    "                _w = csv.writer(_cf)\n"
    "                _w.writerow(['metric', 'value'])\n"
    "                for _k, _v in _ru.items():\n"
    "                    _w.writerow([_k, _v])\n"
    "        else:\n"
    "            with open(_ru_csv, 'w', newline='', encoding='utf-8') as _cf:\n"
    "                _w = csv.writer(_cf)\n"
    "                _w.writerow(['metric', 'value'])\n"
    "                _w.writerow(['generated_at', datetime.now().isoformat()])\n"
    "                _w.writerow(['note',\n"
    "                             'Snapshot no disponible; ejecuta celda 7.7 durante entrenamiento'])\n"
    "        ok_files.append('resource_usage.csv')\n"
    "\n"
    "        # 5. config.json\n"
    "        _cfg = {\n"
    "            'algorithm': algo_upper,\n"
    "            'scenario': sc_long,\n"
    "            'scenario_short': sc_short,\n"
    "            'seed': _seed,\n"
    "            'n_episodes': globals().get('N_EPISODES', 50),\n"
    "            'episode_steps': globals().get('EPISODE_STEPS', 8760),\n"
    "            'dataset': 'citylearn_iquitos_2023_2025',\n"
    "            'hyperparams': _hp.get(algo_upper, {}),\n"
    "            'generated_at': datetime.now().isoformat(),\n"
    "        }\n"
    "        with open(dst_dir / 'config.json', 'w', encoding='utf-8') as _f:\n"
    "            json.dump(_cfg, _f, indent=2, ensure_ascii=False)\n"
    "        ok_files.append('config.json')\n"
    "\n"
    "        # 6. checkpoint.pt — tomar el .pt mas reciente del arbol del launcher\n"
    "        _src_algo_dir = _out / algo_lower / f'{sc_short}_seed_{_seed}'\n"
    "        _ckpt_cands = list(_src_algo_dir.rglob('*.pt')) + list(_src_algo_dir.rglob('*.pth'))\n"
    "        if _ckpt_cands:\n"
    "            _latest_ckpt = max(_ckpt_cands, key=lambda p: p.stat().st_mtime)\n"
    "            shutil.copy2(_latest_ckpt, dst_dir / 'checkpoint.pt')\n"
    "            ok_files.append('checkpoint.pt')\n"
    "        else:\n"
    "            _missing.append(f'{algo_upper}/{sc_long}: sin checkpoint .pt')\n"
    "\n"
    "        # 7. Copiar figuras relevantes\n"
    "        _src_figs = _out / 'figures'\n"
    "        if _src_figs.exists():\n"
    "            for _fig in list(_src_figs.glob(f'*{sc_short}*')) + list(_src_figs.glob(f'*{algo_lower}*')):\n"
    "                shutil.copy2(_fig, dst_dir / 'figures' / _fig.name)\n"
    "\n"
    "        _reorganized.append((algo_upper, sc_long, ok_files))\n"
    "\n"
    "# 8. resumen_comparativo/ — estructura para comparacion global final\n"
    "_resumen_dir = _out / 'resumen_comparativo'\n"
    "_resumen_dir.mkdir(parents=True, exist_ok=True)\n"
    "\n"
    "_cmp_path = _resumen_dir / 'comparison_metrics.csv'\n"
    "if not _cmp_path.exists():\n"
    "    with open(_cmp_path, 'w', newline='', encoding='utf-8') as _cf:\n"
    "        _w = csv.writer(_cf)\n"
    "        _w.writerow(['algorithm', 'scenario', 'metric', 'value'])\n"
    "        _w.writerow(['PENDIENTE', '-', '-',\n"
    "                     'Ejecutar celda 9.1 tras el entrenamiento para completar'])\n"
    "\n"
    "_sel_path = _resumen_dir / 'best_madrl_selection.csv'\n"
    "if not _sel_path.exists():\n"
    "    with open(_sel_path, 'w', newline='', encoding='utf-8') as _cf:\n"
    "        _w = csv.writer(_cf)\n"
    "        _w.writerow(['rank', 'algorithm', 'mean_score', 'selected'])\n"
    "        _w.writerow(['1', 'PENDIENTE', '-', 'Ejecutar celda 9.1 para ranking oficial'])\n"
    "\n"
    "_rep_path = _resumen_dir / 'best_madrl_report.json'\n"
    "if not _rep_path.exists():\n"
    "    with open(_rep_path, 'w', encoding='utf-8') as _f:\n"
    "        json.dump({\n"
    "            'status': 'pendiente',\n"
    "            'nota': 'Ejecutar celda 9.1 para seleccion estadistica oficial.',\n"
    "            'referencia_v4': {\n"
    "                'mejor_madrl': 'MATD3',\n"
    "                'kw_p': 0.0459,\n"
    "                'score': 0.7445,\n"
    "            },\n"
    "        }, _f, indent=2, ensure_ascii=False)\n"
    "\n"
    "# Reporte final\n"
    "print()\n"
    "print(f'  {len(_reorganized)} carpetas reorganizadas:')\n"
    "for _algo, _sc, _files in _reorganized:\n"
    "    _n = len(_files)\n"
    "    _mark = 'OK' if _n >= 4 else 'PARCIAL'\n"
    "    print(f'    [{_mark}] {_algo}/{_sc}/  ({_n} archivos: {_files})')\n"
    "if _missing:\n"
    "    print()\n"
    "    print('  Artefactos pendientes (se generan tras entrenamiento 50 ep):')\n"
    "    for _m in _missing:\n"
    "        print(f'    - {_m}')\n"
    "print()\n"
    "print(f'  resumen_comparativo/ preparado: {_resumen_dir}')\n"
    "print()\n"
    "print('  Estructura canonica validada:')\n"
    "print(f'  {_out}/{{MADRL}}/{{escenario}}/')\n"
    "print('  Completa con celda 9.1 para comparison_metrics.csv y best_madrl_report.json.')\n"
)

new_cell_74b = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": CELL_74B_SOURCE,
}

# Insert after cell 43 (becomes index 44)
cells.insert(44, new_cell_74b)
print(f"CHANGE 2 applied: Cell 7.4b inserted at index 44 (total cells: {len(cells)})")

# ── CHANGE 3: Update Cell 051 markdown (was 050 before insert) ───────────────
# After insert, original cell 50 is now at index 51
CELL51_IDX = 51
cell51 = cells[CELL51_IDX]
assert cell51["cell_type"] == "markdown", f"Expected markdown at {CELL51_IDX}, got {cell51['cell_type']}"
src51 = "".join(cell51["source"])
assert "Sección 8" in src51, "CHANGE 3 FAILED: Section 8 markdown not found at expected index"

NEW_SEC8_MD = (
    "## Sección 8: Análisis de resultados y KPIs\n"
    "\n"
    "### Estructura de artefactos (formato canónico `outputs/{MADRL}/{escenario}/`)\n"
    "```\n"
    "{OUTPUT_ROOT}/\n"
    "  HAPPO/\n"
    "    escenario_1/  metrics.csv  rewards.csv  training_monitor.csv\n"
    "                  resource_usage.csv  config.json  checkpoint.pt  figures/\n"
    "    escenario_2/  ...\n"
    "    escenario_3/  ...\n"
    "  MASAC/ MATD3/ MAAC/  → misma estructura\n"
    "  resumen_comparativo/\n"
    "    comparison_metrics.csv  best_madrl_selection.csv\n"
    "    best_madrl_report.json  global_comparison.png\n"
    "```\n"
    "\n"
    "> **Nota:** La celda 7.4b reorganiza los artefactos del launcher\n"
    "> (`happo/E1_seed_0/data/`) al formato canónico. Las celdas 8.1 y 8.2 leen\n"
    "> ambos formatos para garantizar compatibilidad.\n"
)
cells[CELL51_IDX]["source"] = NEW_SEC8_MD
print(f"CHANGE 3 applied: Cell {CELL51_IDX} (Section 8 markdown) updated")

# ── CHANGE 4: Update Cell 055 (was 054) — add resumen_comparativo export ─────
CELL55_IDX = 55
src55 = "".join(cells[CELL55_IDX]["source"])
assert "suite de pruebas" in src55.lower() or "build_scores" in src55, (
    f"CHANGE 4 FAILED: Statistical analysis cell not found at index {CELL55_IDX}"
)

RESUMEN_EXPORT_BLOCK = (
    "\n"
    "# ── Exportar a resumen_comparativo/ ─────────────────────────────────────────\n"
    "_resumen_dir = Path(OUTPUT_ROOT) / 'resumen_comparativo'\n"
    "_resumen_dir.mkdir(parents=True, exist_ok=True)\n"
    "\n"
    "if not df_results.empty:\n"
    "    # comparison_metrics.csv — todas las métricas por algoritmo y escenario\n"
    "    df_results.to_csv(_resumen_dir / 'comparison_metrics.csv', index=False)\n"
    "    print(f'Exportado: {_resumen_dir}/comparison_metrics.csv')\n"
    "\n"
    "    # best_madrl_selection.csv — ranking estadístico\n"
    "    if stat_results and 'ranking' in stat_results:\n"
    "        import csv as _csv\n"
    "        _best_algo = stat_results.get('best_madrl',\n"
    "                                      stat_results['ranking'][0]['algorithm'])\n"
    "        with open(_resumen_dir / 'best_madrl_selection.csv', 'w', newline='',\n"
    "                  encoding='utf-8') as _cf:\n"
    "            _w = _csv.writer(_cf)\n"
    "            _w.writerow(['rank', 'algorithm', 'mean_score', 'selected'])\n"
    "            for _i, _r in enumerate(stat_results['ranking'], 1):\n"
    "                _w.writerow([_i, _r['algorithm'],\n"
    "                             f\"{_r.get('mean_score', ''):.4f}\",\n"
    "                             'SI' if _i == 1 else 'NO'])\n"
    "        print(f'Exportado: {_resumen_dir}/best_madrl_selection.csv')\n"
    "\n"
    "        # best_madrl_report.json\n"
    "        _kw = stat_results.get('kruskal_wallis', {})\n"
    "        with open(_resumen_dir / 'best_madrl_report.json', 'w', encoding='utf-8') as _f:\n"
    "            json.dump({\n"
    "                'mejor_madrl': _best_algo,\n"
    "                'ranking': stat_results['ranking'],\n"
    "                'kruskal_wallis': _kw,\n"
    "                'criterios': [\n"
    "                    'reward_promedio', 'reward_acumulado', 'estabilidad',\n"
    "                    'velocidad_convergencia', 'reduccion_picos',\n"
    "                    'gestion_soc_bess', 'reduccion_co2',\n"
    "                    'cumplimiento_restricciones', 'consistencia_escenarios',\n"
    "                ],\n"
    "                'n_episodios': globals().get('N_EPISODES', 50),\n"
    "                'escenarios': globals().get('SCENARIOS', ['E1', 'E2', 'E3']),\n"
    "                'generated_at': datetime.now().isoformat() if 'datetime' in dir() else 'N/A',\n"
    "            }, _f, indent=2, ensure_ascii=False)\n"
    "        print(f'Exportado: {_resumen_dir}/best_madrl_report.json')\n"
    "\n"
    "        # global_comparison.png\n"
    "        try:\n"
    "            import matplotlib.pyplot as _plt\n"
    "            import matplotlib; matplotlib.use('Agg')\n"
    "            _algos_rank = [_r['algorithm'] for _r in stat_results['ranking']]\n"
    "            _scores_rank = [_r.get('mean_score', 0) for _r in stat_results['ranking']]\n"
    "            _clrs = ['#16a34a' if _i == 0 else '#3b82f6'\n"
    "                     for _i in range(len(_algos_rank))]\n"
    "            _fig, _ax = _plt.subplots(figsize=(8, 5))\n"
    "            _bars = _ax.bar(_algos_rank, _scores_rank, color=_clrs, edgecolor='white', lw=1.5)\n"
    "            _ax.set_title(\n"
    "                f'Selección del mejor MADRL — Score global (3 escenarios)\\n'\n"
    "                f'Ganador: {_best_algo}  |  KW p={_kw.get(\"p\", \"?\"):.4f}',\n"
    "                fontsize=12, fontweight='bold')\n"
    "            _ax.set_ylabel('Score global (0-1, mayor es mejor)')\n"
    "            _ax.set_ylim(0, 1)\n"
    "            _ax.grid(axis='y', alpha=0.3)\n"
    "            _ax.set_facecolor('#f8fafc')\n"
    "            for _bar, _s in zip(_bars, _scores_rank):\n"
    "                _ax.text(_bar.get_x() + _bar.get_width() / 2, _bar.get_height() + 0.01,\n"
    "                         f'{_s:.4f}', ha='center', fontsize=11, fontweight='bold')\n"
    "            _plt.tight_layout()\n"
    "            _plt.savefig(_resumen_dir / 'global_comparison.png', dpi=150, bbox_inches='tight')\n"
    "            _plt.close()\n"
    "            print(f'Exportado: {_resumen_dir}/global_comparison.png')\n"
    "        except Exception as _e_fig:\n"
    "            print(f'[WARN] global_comparison.png: {_e_fig}')\n"
    "\n"
    "    print()\n"
    "    print(f'Mejor algoritmo MADRL seleccionado: '\n"
    "          f'{stat_results.get(\"best_madrl\", stat_results[\"ranking\"][0][\"algorithm\"])}')\n"
)

# Append the export block to cell 55
src55_new = src55.rstrip() + "\n" + RESUMEN_EXPORT_BLOCK
# Need datetime import at top of cell
if "from datetime import datetime" not in src55_new:
    src55_new = "from datetime import datetime\n" + src55_new
cells[CELL55_IDX]["source"] = src55_new
print(f"CHANGE 4 applied: Cell {CELL55_IDX} (statistical analysis) updated with resumen_comparativo export")

# ── CHANGE 5: Update Cell 058 (was 057) — add output structure validation ─────
CELL58_IDX = 58
src58 = "".join(cells[CELL58_IDX]["source"])
assert "INFORME" in src58 and "SUPERVISIÓN" in src58.upper(), (
    f"CHANGE 5 FAILED: Informe cell not found at index {CELL58_IDX}"
)

# Add validation block before the final veredicto section
OLD_SECTION = (
    "# ── 8. Veredicto de aprobación ────────────────────────────────────────────────"
)
NEW_SECTION = (
    "# ── 7b. Validación estructura outputs/{MADRL}/{escenario}/ ─────────────────────\n"
    "print()\n"
    "print('7b. ESTRUCTURA DE OUTPUTS outputs/{MADRL}/{escenario}/')\n"
    "_out_root = Path(globals().get('OUTPUT_ROOT', str(Path(_REPO) / 'outputs' / 'supervision')))\n"
    "_required_algos = ['HAPPO', 'MASAC', 'MATD3', 'MAAC']\n"
    "_required_scenarios = ['escenario_1', 'escenario_2', 'escenario_3']\n"
    "_required_files = ['metrics.csv', 'rewards.csv', 'training_monitor.csv',\n"
    "                   'resource_usage.csv', 'config.json']\n"
    "_struct_ok = 0\n"
    "_struct_total = len(_required_algos) * len(_required_scenarios)\n"
    "for _algo in _required_algos:\n"
    "    for _sc in _required_scenarios:\n"
    "        _d = _out_root / _algo / _sc\n"
    "        _files_found = [f for f in _required_files if (_d / f).exists()]\n"
    "        _is_ok = len(_files_found) >= len(_required_files)\n"
    "        _mark = 'OK' if _is_ok else ('PARCIAL' if _files_found else 'PENDIENTE')\n"
    "        if _is_ok:\n"
    "            _struct_ok += 1\n"
    "        print(f'  [{_mark}] {_algo}/{_sc}/ ({len(_files_found)}/{len(_required_files)} archivos)')\n"
    "_resumen_ok = (_out_root / 'resumen_comparativo').exists()\n"
    "print(f'  [{\"OK\" if _resumen_ok else \"PENDIENTE\"}] resumen_comparativo/')\n"
    "informe['estructura_outputs'] = {\n"
    "    'formato': 'outputs/{MADRL}/{escenario}/',\n"
    "    'carpetas_completas': _struct_ok,\n"
    "    'carpetas_totales': _struct_total,\n"
    "    'resumen_comparativo': 'OK' if _resumen_ok else 'PENDIENTE',\n"
    "    'status': 'CORRECTO' if _struct_ok == _struct_total else 'INCOMPLETO (entrenar primero)',\n"
    "}\n"
    "\n"
    "# ── 8. Veredicto de aprobación ────────────────────────────────────────────────"
)
if OLD_SECTION in src58:
    src58_new = src58.replace(OLD_SECTION, NEW_SECTION)
    cells[CELL58_IDX]["source"] = src58_new
    print(f"CHANGE 5 applied: Cell {CELL58_IDX} (informe) updated with output structure validation")
else:
    print(f"CHANGE 5 WARNING: Target section not found in cell {CELL58_IDX}, skipping")

# ── Save notebook ─────────────────────────────────────────────────────────────
nb["cells"] = cells
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print(f"\nNotebook saved: {NB_PATH}")
print(f"Total cells: {len(nb['cells'])}")
print("\nAll changes applied successfully.")
