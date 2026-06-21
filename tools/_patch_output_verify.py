"""Patch notebook: cell 1.5 (Drive free space), cell 43 (7.4 audit), cell 56 (a100_tuning)."""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path(
    r'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb'
)
nb = json.loads(NB_PATH.read_bytes().decode('utf-8-sig'))


def set_cell_source(ci, src):
    lines = src.split('\n')
    nb['cells'][ci]['source'] = (
        [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. CELL 22 (1.5 Drive): MIN_DRIVE_FREE_GIB 15 → 30
# ─────────────────────────────────────────────────────────────────────────────
src22 = ''.join(nb['cells'][22]['source'])
old22 = 'MIN_DRIVE_FREE_GIB = 15.0  # artefactos ~10-12 GiB para 12 corridas completas'
new22 = 'MIN_DRIVE_FREE_GIB = 30.0  # A100-80GB HAPPO hidden=512: checkpoints + timeseries persistentes'
if old22 in src22:
    src22 = src22.replace(old22, new22, 1)
    set_cell_source(22, src22)
    print('Cell 22: MIN_DRIVE_FREE_GIB 15→30 OK')
else:
    print('Cell 22: NOTFOUND')

# ─────────────────────────────────────────────────────────────────────────────
# 2. CELL 43 (7.4): reescribir como auditoría estructural completa
# ─────────────────────────────────────────────────────────────────────────────
NEW_CELL43 = r"""# ── 7.4  Auditoría de artefactos — estructura y archivos por job ────────────
# Verifica que cada uno de los 12 jobs (4 algos x 3 escenarios) tiene:
#   data/results.json · data/timeseries.csv · data/trace.csv
#   checkpoints/*.pt  · data/artifact_audit.json
# Muestra tamaño, episodios registrados y si el job esta completo.
import json, os
from pathlib import Path

ALGOS = ['happo', 'masac', 'matd3', 'maac']
SCENS = ['E1', 'E2', 'E3']
REQUIRED = {
    'data/results.json'       : 'results',
    'data/timeseries.csv'     : 'timeseries',
    'data/trace.csv'          : 'trace',
    'data/checkpoint_manifest.json': 'ckpt_manifest',
    'data/artifact_audit.json': 'audit',
}
OPTIONAL = {
    'data/training_summary.json'       : 'train_summary',
    'data/building_behavior_summary.csv': 'bldg_summary',
    'data/building_kpis.csv'           : 'bldg_kpis',
}

out = Path(OUTPUT_ROOT)
SEP  = '=' * 76
THIN = '-' * 76

def _sz(p):
    try:
        b = p.stat().st_size
        if b < 1024:
            return f'{b}B'
        if b < 1048576:
            return f'{b/1024:.1f}KB'
        return f'{b/1048576:.1f}MB'
    except Exception:
        return '?'

def _n_rows(p):
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            return sum(1 for _ in f) - 1  # minus header
    except Exception:
        return -1

def _ep_from_ts(data_dir):
    ts = data_dir / 'timeseries.csv'
    if not ts.exists():
        return None
    try:
        with open(ts, encoding='utf-8') as f:
            rows = sum(1 for _ in f) - 1
        return rows  # 1 row per episode
    except Exception:
        return None

# ── Estado global del manifest ───────────────────────────────────────────────
status_path = out / 'official_full_status.json'
all_jobs = []
global_status = '?'
if status_path.exists():
    st = json.loads(status_path.read_text())
    all_jobs = st.get('jobs', [])
    global_status = st.get('status', '?')

def _job_status(algo, scen):
    for j in all_jobs:
        if j.get('name','').lower() == algo and j.get('scenario','').upper() == scen:
            if j.get('skipped'):
                return 'SKIP'
            if j.get('exit_code') == 0:
                return 'OK  '
            if j.get('completed_at') is None:
                return 'RUN '
            return 'FAIL'
    return '----'

# ── Checkpoints ──────────────────────────────────────────────────────────────
def _ckpt_info(job_dir):
    ckpt_dir = job_dir / 'checkpoints'
    exts = {'.pt', '.pth', '.pkl', '.ckpt', '.zip'}
    files = [p for p in ckpt_dir.rglob('*') if p.is_file() and p.suffix.lower() in exts] if ckpt_dir.exists() else []
    if not files:
        # fallback: buscar en el dir raiz del job
        files = [p for p in job_dir.glob('*') if p.is_file() and p.suffix.lower() in exts]
    if not files:
        return 'sin checkpoints'
    total_mb = sum(p.stat().st_size for p in files) / 1048576
    return f'{len(files)} archivo(s)  {total_mb:.1f} MB'

# ── Imprimir cabecera ─────────────────────────────────────────────────────────
print(SEP)
print(f'  AUDITORÍA DE ARTEFACTOS — MADRL CityLearn v3 · A100-SXM4-80GB')
print(f'  Run: {out.name}')
print(f'  Ruta: {OUTPUT_ROOT}')
print(f'  Estado global: {global_status}')
print(SEP)

# ── Espacio en disco ─────────────────────────────────────────────────────────
try:
    import shutil
    usage = shutil.disk_usage(str(out) if out.exists() else '/content/drive/MyDrive')
    free_gib = usage.free / (1024**3)
    used_run = sum(f.stat().st_size for f in out.rglob('*') if f.is_file()) / (1024**3) if out.exists() else 0
    print(f'  Drive libre: {free_gib:.1f} GiB  |  Uso esta corrida: {used_run:.2f} GiB')
except Exception:
    pass
print()

# ── Por algoritmo y escenario ─────────────────────────────────────────────────
missing_critical = []
total_jobs = 0
ok_jobs = 0

for algo in ALGOS:
    print(f'  ┌── {algo.upper()} ─────────────────────────────────────────────────────')
    for scen in SCENS:
        total_jobs += 1
        job_dir  = out / algo / f'{scen}_seed_0'
        data_dir = job_dir / 'data'
        jst = _job_status(algo, scen)

        print(f'  │  {algo.upper()}/{scen}  [{jst}]  {job_dir.relative_to(out) if job_dir.exists() else "(sin carpeta)"}')

        if not job_dir.exists():
            print(f'  │    ⚠ Carpeta no existe aún (job pendiente o no iniciado)')
            missing_critical.append(f'{algo.upper()}/{scen}: carpeta {job_dir.name} inexistente')
            print('  │')
            continue

        # Archivos requeridos
        all_ok = True
        for rel, label in REQUIRED.items():
            p = job_dir / rel
            if p.exists():
                sz = _sz(p)
                extra = ''
                if rel == 'data/timeseries.csv':
                    ep = _n_rows(p)
                    extra = f'  ({ep} episodios)' if ep >= 0 else ''
                elif rel == 'data/results.json':
                    try:
                        rd = json.loads(p.read_text())
                        algo_key = rd.get('algorithm', '')
                        kw_p = rd.get('kruskal_wallis', {}).get('p_value', None)
                        extra = f'  [algo={algo_key}]' + (f'  KW_p={kw_p:.4f}' if kw_p else '')
                    except Exception:
                        pass
                print(f'  │    ✓ {label:<16} {sz:>8}{extra}')
            else:
                print(f'  │    ✗ {label:<16} FALTA')
                all_ok = False
                if jst == 'OK  ':
                    missing_critical.append(f'{algo.upper()}/{scen}: {rel} falta (job=OK)')

        # Archivos opcionales
        for rel, label in OPTIONAL.items():
            p = job_dir / rel
            if p.exists():
                print(f'  │    · {label:<16} {_sz(p):>8}')

        # Checkpoints
        ckpt_info = _ckpt_info(job_dir)
        ckpt_icon = '✓' if 'archivo' in ckpt_info else '⚠'
        print(f'  │    {ckpt_icon} checkpoints     {ckpt_info}')

        # Figuras
        figs = list((job_dir / 'figures').glob('*.png')) if (job_dir / 'figures').exists() else []
        if figs:
            fig_mb = sum(f.stat().st_size for f in figs) / 1048576
            print(f'  │    · figuras          {len(figs)} PNG  {fig_mb:.1f} MB')

        # live_progress (si activo)
        lp = job_dir / 'live_progress.json'
        if lp.exists():
            try:
                lpd = json.loads(lp.read_text())
                ep  = lpd.get('episode', '?')
                st  = lpd.get('global_step', '?')
                fps = lpd.get('fps', '?')
                print(f'  │    ► live_progress    ep={ep}  step={st}  fps={fps}')
            except Exception:
                print(f'  │    ► live_progress    (ilegible)')

        if all_ok and jst == 'OK  ':
            ok_jobs += 1

        print('  │')
    print('  └' + '─' * 70)
    print()

# ── Resumen final ─────────────────────────────────────────────────────────────
print(SEP)
print(f'  RESUMEN: {ok_jobs}/{total_jobs} jobs con artefactos completos')
if missing_critical:
    print(f'  PROBLEMAS ({len(missing_critical)}):')
    for m in missing_critical:
        print(f'    ✗ {m}')
else:
    if ok_jobs == total_jobs:
        print('  ✓ Todos los jobs completados y artefactos verificados.')
    else:
        print(f'  ℹ {total_jobs - ok_jobs} jobs pendientes/en progreso.')
print(SEP)

# Mostrar estructura esperada
print()
print('  ESTRUCTURA ESPERADA POR JOB:')
print('  {OUTPUT_ROOT}/{algo}/{scenario}_seed_0/')
print('    data/results.json         ← KPIs finales, ganancia vs baseline')
print('    data/timeseries.csv       ← retorno y métricas por episodio (50 filas)')
print('    data/trace.csv            ← observ./acciones muestreadas (cada 24 pasos)')
print('    data/checkpoint_manifest.json')
print('    data/artifact_audit.json')
print('    checkpoints/              ← modelos .pt (actor/critic por agente)')
print('    figures/*.png             ← 13 gráficas de convergencia y KPIs')
print(SEP)
"""

set_cell_source(43, NEW_CELL43)
print('Cell 43: 7.4 audit reescrita OK')

# ─────────────────────────────────────────────────────────────────────────────
# 3. CELL 56 (10): actualizar a100_tuning dict
# ─────────────────────────────────────────────────────────────────────────────
src56 = ''.join(nb['cells'][56]['source'])

OLD_TUNING = """    "a100_tuning": {
        "happo_hidden":         512,
        "masac_buffer_size":    40,
        "masac_critic_batch":   512,
        "masac_max_buf_gib":    40,
        "matd3_batch_size":     1024,
        "matd3_buffer_size":    1000000,
        "maac_batch_size":      1024,
        "maac_buffer_length":   500000,
    },"""

NEW_TUNING = """    "a100_tuning": {
        "happo_hidden_size"    : 512,
        "masac_buffer_episodes": 40,
        "masac_critic_batch"   : 1024,
        "masac_rnn_hidden_dim" : 1024,
        "masac_qmix_hidden"    : 512,
        "masac_hyper_hidden"   : 1024,
        "masac_actor_samples"  : 10,
        "masac_critic_steps"   : 2,
        "masac_max_buf_gib"    : 40,
        "matd3_batch_size"     : 1024,
        "matd3_buffer_size"    : 2000000,
        "matd3_hidden_size"    : 1024,
        "maac_batch_size"      : 1024,
        "maac_buffer_length"   : 1000000,
        "maac_hidden_size"     : 1024,
        "maac_num_updates"     : 16,
        "maac_attention_heads" : 8,
        "torch_threads"        : 4,
        "parallel_scenarios"   : 3,
    },"""

if OLD_TUNING in src56:
    src56 = src56.replace(OLD_TUNING, NEW_TUNING, 1)
    set_cell_source(56, src56)
    print('Cell 56: a100_tuning dict actualizado OK')
else:
    print('Cell 56: NOTFOUND — buscando manualmente')
    idx = src56.find('"a100_tuning"')
    print(f'  a100_tuning encontrado en pos {idx}')
    print(repr(src56[idx:idx+400]))

# ── Guardar
import ast
for ci, label in [(22, '1.5 Drive'), (43, '7.4 audit'), (56, '10 summary')]:
    src = ''.join(nb['cells'][ci]['source'])
    try:
        ast.parse(src)
        print(f'Cell {ci} ({label}): sintaxis OK')
    except SyntaxError as e:
        print(f'Cell {ci} ({label}): SYNTAX ERROR {e}')

NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('\nGuardado.')
