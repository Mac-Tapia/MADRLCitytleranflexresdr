# ── 7.0  Helpers de ejecucion y monitor ─────────────────────────────────────────
# IMPORTANTE: tras git pull, re-ejecuta celdas 1.2 → 6.1 → 7.0 → 7.1 antes de 7.2.
import subprocess
import sys
import os
import json
import re
from pathlib import Path


def run_cmd(cmd, *, cwd=REPO, check=True):
    print('\n' + '=' * 80)
    print(' '.join(str(c) for c in cmd))
    print('=' * 80)
    sys.stdout.flush()
    proc = subprocess.run(cmd, cwd=cwd, text=True, stderr=subprocess.PIPE)
    if proc.stderr:
        print(proc.stderr, end='', file=sys.stderr, flush=True)
    if check and proc.returncode != 0:
        stderr_snippet = (proc.stderr or '').strip()[-1500:]
        msg = f'Comando fallo con exit={proc.returncode}'
        if stderr_snippet:
            msg += f'\n--- stderr (ultimas 1500 chars) ---\n{stderr_snippet}'
        raise RuntimeError(msg)
    return proc.returncode


def _launcher_flags():
    """Devuelve el conjunto de flags --foo registrados en el launcher."""
    try:
        src = Path(LAUNCHER).read_text(encoding='utf-8')
        return set(re.findall(r'add_argument\(["\'](-{1,2}[\w-]+)["\']', src))
    except Exception:
        return set()


def _launcher_has_two_phase():
    """True si el launcher implementa two_phase_happo_masac (no el layout antiguo 9+3)."""
    try:
        src = Path(LAUNCHER).read_text(encoding='utf-8')
        return (
            'run_two_phase_happo_masac_jobs' in src
            and 'TWO_PHASE_P1_HM' in src
            and ('two_phase_happo_masac' in src)
        )
    except Exception:
        return False


def _monitor_has_two_phase():
    try:
        src = Path(MONITOR).read_text(encoding='utf-8')
        return 'two_phase_happo_masac' in src and 'TWO_PHASE_P1' in src and 'TWO_PHASE_P2' in src
    except Exception:
        return False


def verify_two_phase_protocol():
    """Verifica que launcher/monitor implementan two_phase_happo_masac_v3 (6+6, sin stagger)."""
    launcher_path = Path(LAUNCHER)
    monitor_path = Path(MONITOR)
    if not launcher_path.exists() or not monitor_path.exists():
        raise RuntimeError(
            f'Scripts no encontrados: launcher={launcher_path} monitor={monitor_path}. '
            'Ejecuta celda 1.2 (hard reset) y vuelve a 7.0.'
        )
    launcher_src = launcher_path.read_text(encoding='utf-8')
    monitor_src = monitor_path.read_text(encoding='utf-8')
    required = [
        'run_two_phase_happo_masac_jobs',
        'TWO_PHASE_P1_HM',
        'LAUNCHER_PROTOCOL_ID',
        'two_phase_happo_masac_v3',
    ]
    forbidden = [
        'TWO_PHASE_LIGHT',
        'run_two_phase_jobs',
        'algo_sequential',
        'FASE 1: HAPPO + MATD3',
    ]
    missing = [s for s in required if s not in launcher_src]
    legacy = [s for s in forbidden if s in launcher_src]
    if missing or legacy:
        msg = ['Protocolo two_phase_happo_masac_v3 NO verificado en launcher.']
        if missing:
            msg.append(f'  Faltan: {missing}')
        if legacy:
            msg.append(f'  Layout antiguo detectado: {legacy}')
        msg.append('  Ejecuta celda 1.2 (checkout -B CityLearn) y re-ejecuta 6.1 -> 7.0 -> 7.1.')
        raise RuntimeError('\n'.join(msg))
    if 'MONITOR_PROTOCOL_ID' not in monitor_src or 'two_phase_happo_masac_v3' not in monitor_src:
        raise RuntimeError(
            'Monitor sin MONITOR_PROTOCOL_ID two_phase_happo_masac_v3. '
            'Ejecuta celda 1.2 (checkout -B CityLearn).'
        )
    print(f'[protocol] launcher={launcher_src.splitlines()[0][:40]}... OK')
    print('[protocol] verify_two_phase_protocol PASSED')
    if Path(PROTOCOL_GUARD).is_file():
        subprocess.check_call(
            [str(PYTHON), str(PROTOCOL_GUARD), 'verify-repo', '--repo', str(REPO)],
            cwd=str(REPO),
        )
    return True


_LAUNCHER_SCRIPTS = (
    'scripts/colab_a100_official_launcher.py',
    'scripts/colab_a100_live_monitor.py',
)


def _ensure_launcher_parallel():
    """Garantiza launcher + monitor con two_phase_happo_masac (6+6, sin stagger).

    No degrada a argparse parcial ni al layout antiguo (Fase1 HAPPO+MATD3+MAAC x9).
    Orden: mac-tapia fetch → submodule update --remote → submodule init.
    """
    if _launcher_has_two_phase() and _monitor_has_two_phase():
        return True

    print('\n[launcher] Scripts desactualizados — se requiere two_phase_happo_masac.')
    if Path(LAUNCHER).exists():
        src = Path(LAUNCHER).read_text(encoding='utf-8')
        if 'TWO_PHASE_LIGHT' in src or 'run_two_phase_jobs' in src:
            print('[launcher] Detectado layout ANTIGUO (9+3 con stagger). Actualizando...')

    cl_dir = str(Path(LAUNCHER).parent.parent)
    _CL_BRANCH = globals().get('CITYLEARN_BRANCH', 'codex/iquitos-distillation-madrl-docs')
    _remotes = ('mac-tapia', 'origin')

    for remote in _remotes:
        r_fetch = subprocess.run(
            ['git', 'fetch', remote, _CL_BRANCH],
            cwd=cl_dir, capture_output=True, text=True, timeout=90
        )
        if r_fetch.returncode != 0:
            continue
        r_co = subprocess.run(
            ['git', 'checkout', f'{remote}/{_CL_BRANCH}', '--', *_LAUNCHER_SCRIPTS],
            cwd=cl_dir, capture_output=True, text=True, timeout=30
        )
        if r_co.returncode == 0 and _launcher_has_two_phase() and _monitor_has_two_phase():
            print(f'[launcher] Actualizado via {remote}/{_CL_BRANCH} — two_phase OK.')
            return True

    for cmd in (
        ['git', 'submodule', 'update', '--init', '--remote', 'CityLearn'],
        ['git', 'submodule', 'update', '--init', 'CityLearn'],
    ):
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and _launcher_has_two_phase() and _monitor_has_two_phase():
            print('[launcher] CityLearn sincronizado — two_phase OK.')
            return True

    print('[launcher] *** FALLO: no se pudo obtener two_phase_happo_masac. ***')
    print('[launcher] Reinicia runtime, ejecuta celda 1.2 y vuelve a 7.0/7.1.')
    return False


def launcher_base_args():
    # Todos los hiperparametros A100-SXM4-80GB explicitamente para maxima visibilidad.
    _flags = _launcher_flags()

    def _opt(flag, *values):
        return [flag, *values] if flag in _flags else []

    base = [
        PYTHON, '-B', LAUNCHER,
        '--scenario', 'ALL',
        '--seed', str(SEED),
        '--episode-time-steps', str(EPISODE_STEPS),
        '--episodes', str(EPISODES),
        '--schema-path', SCHEMA_PATH,
        '--output-root', OUTPUT_ROOT,
        '--torch-threads', str(TORCH_THREADS),
        '--live-progress-interval', str(LIVE_PROGRESS_INT),
        '--live-heartbeat-seconds', str(LIVE_HEARTBEAT_SEC),
        '--artifact-profile', ARTIFACT_PROFILE,
        '--trace-record-interval', str(TRACE_INTERVAL),
        '--trace-detail', TRACE_DETAIL,
        '--gpu-profile', GPU_PROFILE,
        '--cuda-memory-fraction', str(CUDA_MEMORY_FRACTION),
        '--require-a100',
        '--smoke-imports',
        '--oom-retry',
        # El panel del notebook (celda 7.2) ya renderiza el dashboard global con
        # componentes/kpis; --no-live-monitor evita duplicar la salida del launcher.
        '--no-live-monitor',
        # ── HAPPO ─────────────────────────────────────────────────────────────
        '--happo-hidden-size', '512',
        '--happo-n-rollout-threads', str(HAPPO_ROLLOUT_THREADS),
        # num_mini_batch=0 -> auto: mas rollouts usan RAM; minibatch GPU ~constante (VRAM).
        '--happo-num-mini-batch', '0',
        '--happo-gpu-rollout-ref', str(HAPPO_GPU_ROLLOUT_REF),
        # ppo_epoch/critic_epoch 5->10: mas pasadas GPU/update (aprovecha GPU ociosa on-policy)
        '--happo-ppo-epoch', '10',
        '--happo-critic-epoch', '10',
        # ── MASAC (6-parallel: replay CPU, critic_batch=1 ep QMIX) ────────────
        '--masac-critic-batch-size', str(SIX_JOB_MASAC_BATCH),
        '--masac-buffer-size', str(SIX_JOB_MASAC_BUF),
        '--masac-max-replay-buffer-gib', str(SIX_JOB_MASAC_GIB),
        '--masac-rnn-hidden-dim', '64',
        '--masac-qmix-hidden-dim', '32',
        '--masac-hyper-hidden-dim', '64',
        '--masac-preload-batch-device', 'auto',  # replay RAM (CPU) + batch en GPU (fallback CPU si OOM)
        '--masac-actor-sample-times', '1',
        '--masac-critic-train-steps', '1',
        # ── MATD3 (6-parallel fase 2: buffers RAM conservadores) ────────────────
        '--matd3-batch-size', str(SIX_JOB_MATD3_BATCH),
        '--matd3-buffer-size', str(SIX_JOB_MATD3_BUF),
        '--matd3-hidden-size', str(SIX_JOB_MATD3_HIDDEN),
        '--matd3-train-interval', '100',  # v4 estable (ganadora 3/3)
        # ── MAAC (6-parallel fase 2: buffers RAM conservadores) ────────────────
        '--maac-batch-size', str(SIX_JOB_MAAC_BATCH),
        '--maac-buffer-length', str(SIX_JOB_MAAC_BUF),
        '--maac-hidden-size', str(SIX_JOB_MAAC_HIDDEN),
        '--maac-steps-per-update', '50',
        '--maac-num-updates', str(SIX_JOB_MAAC_UPDATES),
    ]
    base += [
        '--execution-mode', 'two_phase_happo_masac',
        '--two-phase-torch-threads', str(TORCH_THREADS),
        # Auto-escala a las vCPU del runtime (sin sobre-suscribir): H100 ~26 vCPU
        # (primario) -> Fase1 torch=2/rollout=4; A100 12 vCPU -> torch=1/rollout=2.
        '--two-phase-p1-torch-threads', str(TWO_PHASE_P1_TORCH),
        '--two-phase-p2-torch-threads', str(TWO_PHASE_P2_TORCH),
        '--six-job-cuda-fraction', str(SIX_JOB_CUDA_FRAC),
        '--six-job-masac-cuda-fraction', str(SIX_JOB_MASAC_CUDA_FRAC),
        '--six-job-masac-buffer-size', str(SIX_JOB_MASAC_BUF),
        '--six-job-masac-max-replay-gib', str(SIX_JOB_MASAC_GIB),
        '--six-job-masac-critic-batch-size', str(SIX_JOB_MASAC_BATCH),
    ]
    if int(globals().get('MAX_CONCURRENT_JOBS', 0) or 0) > 0:
        base += ['--max-concurrent-jobs', str(int(MAX_CONCURRENT_JOBS))]
    return base


def monitor_once():
    """Snapshot unico del monitor (fuente: citylearn_v3_training_common)."""
    try:
        import importlib
        _cm = importlib.import_module('citylearn_v3_training_common')
        if hasattr(_cm, 'refresh_colab_live_monitor_once'):
            rc = _cm.refresh_colab_live_monitor_once(
                Path(REPO), Path(OUTPUT_ROOT),
                python_executable=PYTHON, log_tail=18,
            )
            return rc
    except Exception:
        pass
    return run_cmd([PYTHON, '-B', MONITOR, '--output-root', OUTPUT_ROOT, '--once', '--log-tail', '18'], check=False)


def resolve_output_root_or_latest():
    """OUTPUT_ROOT desde el scope, o puntero resuelto a ruta absoluta.

    Fuente unica del fallback que antes estaba copiado en 7.2/7.3/7.5.
    """
    _repo = Path(globals().get('REPO', '.'))
    _gdrive = globals().get('GDRIVE_ROOT')
    _gdrive_path = Path(_gdrive) if _gdrive else None
    _scripts = _repo / 'CityLearn' / 'scripts'
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
    import importlib
    _common = importlib.import_module('citylearn_v3_training_common')
    return _common.resolve_notebook_output_root(
        _repo,
        output_root=globals().get('OUTPUT_ROOT', ''),
        gdrive_root=_gdrive_path,
    )


def _launch_signature():
    """Firma de la config de lanzamiento; invalida el dry-run si algo cambia."""
    return (
        str(globals().get('OUTPUT_ROOT', '')),
        int(globals().get('EPISODES', 0) or 0),
        int(globals().get('HAPPO_ROLLOUT_THREADS', 0) or 0),
        int(globals().get('MAX_CONCURRENT_JOBS', 0) or 0),
    )


def mark_dry_run_validated():
    """Lo llama 7.1 tras un dry-run exitoso para que 7.2 no lo repita."""
    globals()['_DRY_RUN_VALIDATED'] = _launch_signature()


def dry_run_already_validated():
    """True si 7.1 ya valido el dry-run para esta misma config (OUTPUT_ROOT/episodios/hilos)."""
    return globals().get('_DRY_RUN_VALIDATED') == _launch_signature()


def _tutorial_notebook_path():
    repo = Path(globals().get('REPO', '/content/MADRLCitytleranflexresdr'))
    return repo / 'CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb'


POST_TRAINING_MARKERS = (
    '# ── 7.3',
    '# ── 7.4  Auditoría',
    '# ── 7.4b',
    '# ── 7.5',
    '#  7.6',
    '# ── 7.7',
)
SECTION_8_MARKERS = (
    '# ── 8.1 ',
    '# ── 8.1b',
    '# ── 8.2 ',
)
SECTION_9_MARKERS = (
    '# ── 9.1',
    '# ── 9.2',
)


def verify_training_artifacts_complete(output_root=None):
    """True cuando 12/12 jobs tienen KPIs auditados (episodes>=target, citylearn_v3_report)."""
    import importlib.util
    output_root = Path(output_root or resolve_output_root_or_latest())
    repo = Path(globals().get('REPO', '.'))
    common_mod = repo / 'CityLearn/scripts/citylearn_v3_training_common.py'
    spec = importlib.util.spec_from_file_location('_cl_v3_common_verify', common_mod)
    if spec is None or spec.loader is None:
        raise ImportError(f'No se pudo cargar citylearn_v3_training_common desde {common_mod}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    n_ep = int(globals().get('N_EPISODES', globals().get('EPISODES', 50)))
    seed = int(globals().get('SEED', 0))
    report = mod.build_jobs_resume_report(
        output_root,
        target_episodes=n_ep,
        seed=seed,
        happo_rollout_threads=globals().get('HAPPO_ROLLOUT_THREADS'),
    )
    missing = []
    kpi_ok = 0
    for row in report.get('jobs', []):
        algo = str(row['algorithm']).lower()
        scen = str(row['scenario'])
        run_dir = mod.resolve_existing_job_run_dir(output_root, algo, scen, seed)
        if run_dir is None:
            missing.append(f'{algo.upper()}/{scen}: sin carpeta de run')
            continue
        if mod.job_meets_launcher_complete_requirements(run_dir, target_episodes=n_ep, output_root=output_root):
            kpi_ok += 1
            continue
        payload = mod.read_job_results_json(run_dir) or {}
        kpi_ep = mod._kpi_evaluated_episodes_from_results(payload)
        blockers = mod.job_launcher_completion_blockers(run_dir, target_episodes=n_ep, output_root=output_root)
        detail = f'kpi_ep={kpi_ep}/{n_ep}'
        if blockers:
            detail += ' | ' + '; '.join(blockers[:2])
        missing.append(f"{algo.upper()}/{scen}: {detail}")
    return {
        'ok': kpi_ok == 12 and not missing,
        'output_root': str(output_root),
        'jobs_complete': kpi_ok,
        'audit_ok': kpi_ok,
        'missing': missing,
        'report': report,
    }


def print_training_artifacts_verdict(verdict):
    print('\n[verify] Verificacion de artefactos post-entrenamiento')
    print(f"  OUTPUT_ROOT: {verdict['output_root']}")
    print(f"  Jobs con KPIs auditados (50/50): {verdict['jobs_complete']}/12")
    if verdict.get('missing'):
        print(f"  PROBLEMAS ({len(verdict['missing'])}):")
        for item in verdict['missing']:
            print(f'    x {item}')
    elif verdict.get('ok'):
        print('  OK 12/12 jobs completos con artefactos verificados.')
    else:
        print('  Verificacion incompleta — revisa celda 7.4.')


def run_post_training_notebook_cells(
    *,
    include_section_8: bool = True,
    include_section_9: bool = True,
):
    """Ejecuta celdas 7.3→7.7 y secciones 8/9 del tutorial (mismo kernel)."""
    import nbformat
    nb_path = _tutorial_notebook_path()
    if not nb_path.is_file():
        raise FileNotFoundError(f'Notebook no encontrado: {nb_path}')
    nb = nbformat.read(str(nb_path), as_version=4)
    markers: list[str] = list(POST_TRAINING_MARKERS)
    if include_section_8:
        markers.extend(SECTION_8_MARKERS)
    if include_section_9:
        markers.extend(SECTION_9_MARKERS)
    g = globals()
    ran = 0
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue
        src = cell.source or ''
        first = src.split('\n', 1)[0].strip()
        if not any(first.startswith(m) for m in markers):
            continue
        print(f'\n{"=" * 78}\n[post-train] >>> {first}\n{"=" * 78}')
        exec(compile(src, f'<{first}>', 'exec'), g)
        ran += 1
    tail = '9.x' if include_section_9 else ('8.x' if include_section_8 else '7.7')
    print(f'\n[post-train] {ran} celdas ejecutadas (7.3→{tail}).')
    return ran
