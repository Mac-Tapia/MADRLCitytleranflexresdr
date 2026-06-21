"""Patch notebook cells 7.0 and 7.1 with robust stderr capture and pre-validation."""
import json, sys

nb_path = 'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb'
nb = json.load(open(nb_path, encoding='utf-8'))

# ── new source for cell 7.0 (id=2adf11df) ────────────────────────────────────
new_src_70 = [
    "# ── 7.0  Helpers de ejecucion y monitor ─────────────────────────────────────────\n",
    "import subprocess, sys, os, json\n",
    "from pathlib import Path\n",
    "\n",
    "\n",
    "def run_cmd(cmd, *, cwd=REPO, check=True):\n",
    "    print('\\n' + '=' * 80)\n",
    "    print(' '.join(str(c) for c in cmd))\n",
    "    print('=' * 80)\n",
    "    sys.stdout.flush()\n",
    "    proc = subprocess.run(cmd, cwd=cwd, text=True, stderr=subprocess.PIPE)\n",
    "    # Mostrar stderr (errores argparse, trazas, advertencias) para que sea visible\n",
    "    if proc.stderr:\n",
    "        print(proc.stderr, end='', file=sys.stderr, flush=True)\n",
    "    if check and proc.returncode != 0:\n",
    "        stderr_snippet = (proc.stderr or '').strip()[-1500:]\n",
    "        msg = f'Comando fallo con exit={proc.returncode}'\n",
    "        if stderr_snippet:\n",
    "            msg += f'\\n--- stderr (ultimas 1500 chars) ---\\n{stderr_snippet}'\n",
    "        raise RuntimeError(msg)\n",
    "    return proc.returncode\n",
    "\n",
    "\n",
    "def launcher_base_args():\n",
    "    # Todos los hiperparámetros son explícitos aquí para máxima visibilidad y control.\n",
    "    # A100-SXM4-80GB: 73.6 GiB VRAM usable, 167 GiB RAM, 3 escenarios en paralelo.\n",
    "    return [\n",
    "        PYTHON, '-B', LAUNCHER,\n",
    "        '--scenario', 'ALL',\n",
    "        '--seed', str(SEED),\n",
    "        '--episode-time-steps', str(EPISODE_STEPS),\n",
    "        '--episodes', str(EPISODES),\n",
    "        '--schema-path', SCHEMA_PATH,\n",
    "        '--output-root', OUTPUT_ROOT,\n",
    "        '--torch-threads', str(TORCH_THREADS),        # 4 hilos CPU por proceso (12 cores / 3 paralelos)\n",
    "        '--parallel-scenarios', '3',                  # E1/E2/E3 concurrentes por algoritmo\n",
    "        '--live-progress-interval', str(LIVE_PROGRESS_INT),\n",
    "        '--live-heartbeat-seconds', str(LIVE_HEARTBEAT_SEC),\n",
    "        '--artifact-profile', ARTIFACT_PROFILE,\n",
    "        '--trace-record-interval', str(TRACE_INTERVAL),\n",
    "        '--trace-detail', TRACE_DETAIL,\n",
    "        '--gpu-profile', GPU_PROFILE,\n",
    "        '--cuda-memory-fraction', str(CUDA_MEMORY_FRACTION),\n",
    "        '--require-a100',\n",
    "        '--smoke-imports',\n",
    "        '--oom-retry',\n",
    "        '--live-monitor',\n",
    "        '--monitor-interval', '30',\n",
    "        # ── HAPPO — on-policy HARL ────────────────────────────────────────────\n",
    "        # VRAM: 3 instancias x ~2 GiB = 6 GiB (sin buffer en GPU)\n",
    "        '--happo-hidden-size', '1024',                # [1024,1024]: 4x params vs 512\n",
    "        # ── MASAC — off-policy RNN+QMIX (buffer en CPU) ─────────────────────────\n",
    "        # VRAM: 3 x ~1 GiB modelo = 3 GiB; RAM: 3 x 40 GiB buffer = 120 GiB\n",
    "        '--masac-critic-batch-size', '1024',          # batch grande: rellena Tensor Cores A100\n",
    "        '--masac-buffer-size', '40',                  # 40 episodios = 350400 pasos por instancia\n",
    "        '--masac-max-replay-buffer-gib', '40.0',      # 40/73.6 GiB = 54% VRAM (si fuera GPU; esta en CPU)\n",
    "        '--masac-rnn-hidden-dim', '1024',             # GRU actor: 2x capacidad recurrente\n",
    "        '--masac-qmix-hidden-dim', '512',             # QMIX monotonic: 2x capacidad mezcla\n",
    "        '--masac-hyper-hidden-dim', '1024',           # hiper-red: 2x para generar pesos QMIX\n",
    "        '--masac-preload-batch-device', 'cpu',        # buffer en RAM (no VRAM) → permite 3 paralelos\n",
    "        '--masac-actor-sample-times', '10',           # 2x actualizaciones actor por paso critico\n",
    "        '--masac-critic-train-steps', '2',            # 2 pasos critico por paso entorno (A100 rapido)\n",
    "        # ── MATD3 — off-policy Twin Delayed DDPG ────────────────────────────────\n",
    "        # VRAM: 3 x ~1.5 GiB = 4.5 GiB; RAM buffer: 3 x ~14 GiB = 42 GiB\n",
    "        '--matd3-batch-size', '1024',                 # Tensor Cores A100 optimo a batch>=512\n",
    "        '--matd3-buffer-size', '2000000',             # 228 episodios diversidad; ~14 GiB RAM por instancia\n",
    "        '--matd3-hidden-size', '1024',                # actor+critic: 4x params vs 512\n",
    "        '--matd3-train-interval', '100',              # actualizar critico/actor cada 100 pasos entorno\n",
    "        # ── MAAC — off-policy SAC + Attention Critic ────────────────────────────────\n",
    "        # VRAM: 3 x ~1.5 GiB = 4.5 GiB; RAM buffer: 3 x ~7 GiB = 21 GiB\n",
    "        '--maac-batch-size', '1024',                  # Tensor Cores A100\n",
    "        '--maac-buffer-length', '1000000',            # 2x vs 500K; ~7 GiB RAM por instancia\n",
    "        '--maac-hidden-size', '1024',                 # 4x params vs 512\n",
    "        '--maac-steps-per-update', '100',             # pasos entorno antes de actualizar\n",
    "        '--maac-num-updates', '16',                   # 2x gradientes por actualizacion (A100 GPU rapida)\n",
    "    ]\n",
    "\n",
    "\n",
    "def monitor_once():\n",
    "    return run_cmd([PYTHON, '-B', MONITOR, '--output-root', OUTPUT_ROOT, '--once', '--log-tail', '18'], check=False)\n",
]

# ── new source for cell 7.1 (id=3c0758f9) ────────────────────────────────────
new_src_71 = [
    "# ── 7.1  Preflight A100 + dry-run oficial ─────────────────────────────────────\n",
    "# 0. Verificar existencia de launcher y schema antes de lanzar\n",
    "_launcher_path = Path(LAUNCHER)\n",
    "_schema_path   = Path(SCHEMA_PATH)\n",
    "if not _launcher_path.exists():\n",
    "    raise FileNotFoundError(\n",
    "        f'Launcher no encontrado: {LAUNCHER}\\n'\n",
    "        f'  → Verifica que el submodulo CityLearn esta clonado (celda 1.2).'\n",
    "    )\n",
    "if not _schema_path.exists():\n",
    "    raise FileNotFoundError(\n",
    "        f'Schema no encontrado: {SCHEMA_PATH}\\n'\n",
    "        f'  → Verifica que el dataset Iquitos esta generado (celdas 3.x).'\n",
    "    )\n",
    "print(f'Launcher : {LAUNCHER}')\n",
    "print(f'Schema   : {SCHEMA_PATH}')\n",
    "\n",
    "# 1. Dry-run oficial: valida CUDA/A100, imports, rutas y 12 comandos planificados\n",
    "dry_run_cmd = launcher_base_args() + ['--dry-run', '--skip-completed']\n",
    "run_cmd(dry_run_cmd)\n",
    "monitor_once()\n",
    "\n",
    "# 2. Leer y validar status.json\n",
    "status_path = Path(OUTPUT_ROOT) / 'official_full_status.json'\n",
    "with open(status_path) as f:\n",
    "    status = json.load(f)\n",
    "assert status['status'] == 'dry_run', status['status']\n",
    "assert status['training_config']['a100_ready'] is True\n",
    "assert len(status['jobs']) == 12, len(status['jobs'])\n",
    "\n",
    "# 3. Verificar que cada output_dir es unico y esta dentro de OUTPUT_ROOT\n",
    "expected_root = Path(OUTPUT_ROOT).resolve()\n",
    "seen_outputs = set()\n",
    "for job in status['jobs']:\n",
    "    job_output = Path(job['output_dir'])\n",
    "    if not job_output.is_absolute():\n",
    "        job_output = Path(REPO) / job_output\n",
    "    job_output = job_output.resolve()\n",
    "    rel = job_output.relative_to(expected_root)\n",
    "    parts = rel.parts\n",
    "    assert len(parts) == 2, f'Layout inesperado: {job_output}'\n",
    "    assert parts[0] in ALGORITHMS, f'Algoritmo inesperado en output_dir: {parts[0]}'\n",
    "    assert parts[1] in {f'{sc}_seed_{SEED}' for sc in SCENARIOS}, f'Scenario/seed inesperado: {parts[1]}'\n",
    "    seen_outputs.add(str(job_output))\n",
    "assert len(seen_outputs) == 12, f'Output dirs duplicados o incompletos: {len(seen_outputs)}'\n",
    "\n",
    "print('Dry-run validado: 12 jobs planificados, A100 config lista, outputs aislados en OUTPUT_ROOT.')\n",
]

# Apply changes
changed = 0
for cell in nb['cells']:
    cid = cell.get('id', '')
    if cid == '2adf11df':
        cell['source'] = new_src_70
        cell['outputs'] = []
        cell['execution_count'] = None
        changed += 1
    elif cid == '3c0758f9':
        cell['source'] = new_src_71
        cell['outputs'] = []
        cell['execution_count'] = None
        changed += 1

print(f'Modified {changed} cells', file=sys.stderr)
json.dump(nb, open(nb_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('Saved OK', file=sys.stderr)
