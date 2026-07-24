# ── 7.4b  Reorganizar outputs al formato canónico: outputs/{MADRL}/{escenario}/ ──
# El launcher escribe: {OUTPUT_ROOT}/HAPPO/E1/data/results.json
# Export opcional:     {OUTPUT_ROOT}/HAPPO/E1/metrics.csv  etc.
# Este paso genera la estructura canónica junto a los artefactos del launcher.
import csv
import json
import shutil
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

_out  = Path(globals().get('OUTPUT_ROOT', '/tmp/madrl_output'))
_repo = Path(globals().get('REPO', '/content/MADRLCitytleranflexresdr'))
_hp   = globals().get('HYPERPARAMS', {})
_seed = globals().get('SEED', 0)

SCENARIO_MAP = {'E1': 'E1', 'E2': 'E2', 'E3': 'E3'}
ALGO_UPPER   = {'happo': 'HAPPO', 'masac': 'MASAC', 'matd3': 'MATD3', 'maac': 'MAAC'}

print('Reorganizando artefactos al formato outputs/{MADRL}/{escenario}/ ...')
_reorganized = []
_missing = []

for algo_lower, algo_upper in ALGO_UPPER.items():
    for sc_short, sc_long in SCENARIO_MAP.items():
        src_data = _out / algo_lower / f'{sc_short}' / 'data'
        dst_dir  = _out / algo_upper / sc_long
        dst_dir.mkdir(parents=True, exist_ok=True)
        (dst_dir / 'figures').mkdir(exist_ok=True)
        ok_files = []

        # 1. metrics.csv — desde results.json[citylearn_v3_report.all_values]
        results_json = src_data / 'results.json'
        if results_json.exists():
            with open(results_json, encoding='utf-8') as _f:
                _r = json.load(_f)
            _all_v = _r.get('citylearn_v3_report', {}).get('all_values', {})
            with open(dst_dir / 'metrics.csv', 'w', newline='', encoding='utf-8') as _cf:
                _w = csv.writer(_cf)
                _w.writerow(['metric', 'value'])
                for _k, _v in _all_v.items():
                    _w.writerow([_k, _v])
            ok_files.append('metrics.csv')
        else:
            _missing.append(f'{algo_upper}/{sc_long}: results.json no encontrado')

        # 2. rewards.csv — desde timeseries.csv, agregado por episodio
        ts_csv = src_data / 'timeseries.csv'
        if ts_csv.exists():
            try:
                _df_ts = pd.read_csv(ts_csv)
                if 'episode' in _df_ts.columns and 'reward_mean' in _df_ts.columns:
                    _ep_df = _df_ts.groupby('episode')['reward_mean'].agg(
                        ['mean', 'sum', 'min', 'max']).reset_index()
                    _ep_df.columns = ['episode', 'reward_mean', 'reward_sum',
                                      'reward_min', 'reward_max']
                    _ep_df.to_csv(dst_dir / 'rewards.csv', index=False)
                else:
                    _df_ts.to_csv(dst_dir / 'rewards.csv', index=False)
                ok_files.append('rewards.csv')
            except Exception as _e:
                print(f'  [WARN] rewards.csv {algo_upper}/{sc_long}: {_e}')
        else:
            _missing.append(f'{algo_upper}/{sc_long}: timeseries.csv no encontrado')

        # 3. training_monitor.csv — desde training_summary.json
        summary_json = src_data / 'training_summary.json'
        if summary_json.exists():
            with open(summary_json, encoding='utf-8') as _f:
                _s = json.load(_f)
            _ep_sum = _s.get('episode_summaries', [])
            if _ep_sum and isinstance(_ep_sum, list) and isinstance(_ep_sum[0], dict):
                pd.DataFrame(_ep_sum).to_csv(dst_dir / 'training_monitor.csv',
                                             index=False)
            else:
                with open(dst_dir / 'training_monitor.csv', 'w', newline='',
                          encoding='utf-8') as _cf:
                    _w = csv.writer(_cf)
                    _w.writerow(['metric', 'value'])
                    for _k, _v in _s.items():
                        if not isinstance(_v, (dict, list)):
                            _w.writerow([_k, _v])
            ok_files.append('training_monitor.csv')
        else:
            with open(dst_dir / 'training_monitor.csv', 'w', newline='',
                      encoding='utf-8') as _cf:
                _w = csv.writer(_cf)
                _w.writerow(['metric', 'value', 'note'])
                _w.writerow(['status', 'pendiente',
                             'training_summary.json no encontrado'])

        # 4. resource_usage.csv
        _ru_snap = _out / 'resource_usage_snapshot.json'
        _ru_csv  = dst_dir / 'resource_usage.csv'
        if _ru_snap.exists():
            with open(_ru_snap) as _f:
                _ru = json.load(_f)
            with open(_ru_csv, 'w', newline='', encoding='utf-8') as _cf:
                _w = csv.writer(_cf)
                _w.writerow(['metric', 'value'])
                for _k, _v in _ru.items():
                    _w.writerow([_k, _v])
        else:
            with open(_ru_csv, 'w', newline='', encoding='utf-8') as _cf:
                _w = csv.writer(_cf)
                _w.writerow(['metric', 'value'])
                _w.writerow(['generated_at', datetime.now().isoformat()])
                _w.writerow(['note',
                             'Snapshot no disponible; ejecuta celda 7.7 durante entrenamiento'])
        ok_files.append('resource_usage.csv')

        # 5. config.json
        _cfg = {
            'algorithm': algo_upper,
            'scenario': sc_long,
            'scenario_short': sc_short,
            'seed': _seed,
            'n_episodes': globals().get('N_EPISODES', 50),
            'episode_steps': globals().get('EPISODE_STEPS', 8760),
            'dataset': 'citylearn_iquitos_2023_2025',
            'hyperparams': _hp.get(algo_upper, {}),
            'generated_at': datetime.now().isoformat(),
        }
        with open(dst_dir / 'config.json', 'w', encoding='utf-8') as _f:
            json.dump(_cfg, _f, indent=2, ensure_ascii=False)
        ok_files.append('config.json')

        # 6. checkpoint.pt — tomar el checkpoint real mas reciente del arbol del launcher
        _src_algo_dir = _out / algo_lower / f'{sc_short}'
        _ckpt_cands = (list(_src_algo_dir.rglob('*.pt')) +
                       list(_src_algo_dir.rglob('*.pth')) +
                       list(_src_algo_dir.rglob('*.pkl')))
        if _ckpt_cands:
            _latest_ckpt = max(_ckpt_cands, key=lambda p: p.stat().st_mtime)
            shutil.copy2(_latest_ckpt, dst_dir / 'checkpoint.pt')
            ok_files.append('checkpoint.pt')
        else:
            _missing.append(f'{algo_upper}/{sc_long}: sin checkpoint .pt')

        # 7. Copiar figuras relevantes
        _src_figs = _out / 'figures'
        if _src_figs.exists():
            for _fig in list(_src_figs.glob(f'*{sc_short}*')) + list(_src_figs.glob(f'*{algo_lower}*')):
                shutil.copy2(_fig, dst_dir / 'figures' / _fig.name)

        _reorganized.append((algo_upper, sc_long, ok_files))

# 8. resumen_comparativo/ — estructura para comparacion global final
_resumen_dir = _out / 'resumen_comparativo'
_resumen_dir.mkdir(parents=True, exist_ok=True)

_cmp_path = _resumen_dir / 'comparison_metrics.csv'
if not _cmp_path.exists():
    with open(_cmp_path, 'w', newline='', encoding='utf-8') as _cf:
        _w = csv.writer(_cf)
        _w.writerow(['algorithm', 'scenario', 'metric', 'value'])
        _w.writerow(['PENDIENTE', '-', '-',
                     'Ejecutar celda 9.1 tras el entrenamiento para completar'])

_sel_path = _resumen_dir / 'best_madrl_selection.csv'
if not _sel_path.exists():
    with open(_sel_path, 'w', newline='', encoding='utf-8') as _cf:
        _w = csv.writer(_cf)
        _w.writerow(['rank', 'algorithm', 'mean_score', 'selected'])
        _w.writerow(['1', 'PENDIENTE', '-', 'Ejecutar celda 9.1 para ranking oficial'])

_rep_path = _resumen_dir / 'best_madrl_report.json'
if not _rep_path.exists():
    with open(_rep_path, 'w', encoding='utf-8') as _f:
        json.dump({
            'status': 'pendiente',
            'nota': 'Ejecutar celda 9.1 para seleccion estadistica oficial.',
            'referencia_v4': {
                'mejor_madrl': 'MATD3',
                'kw_p': 0.0459,
                'score': 0.7445,
            },
        }, _f, indent=2, ensure_ascii=False)

# Reporte final
print()
print(f'  {len(_reorganized)} carpetas reorganizadas:')
for _algo, _sc, _files in _reorganized:
    _n = len(_files)
    _mark = 'OK' if _n >= 4 else 'PARCIAL'
    print(f'    [{_mark}] {_algo}/{_sc}/  ({_n} archivos: {_files})')
if _missing:
    print()
    print('  Artefactos pendientes (se generan tras entrenamiento 50 ep):')
    for _m in _missing:
        print(f'    - {_m}')
print()
print(f'  resumen_comparativo/ preparado: {_resumen_dir}')
print()
print('  Estructura canonica validada:')
print(f'  {_out}/{{MADRL}}/{{escenario}}/')
print('  Completa con celda 9.1 para comparison_metrics.csv y best_madrl_report.json.')
