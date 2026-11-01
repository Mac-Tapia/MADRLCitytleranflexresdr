# ── 7.1  Preflight A100 + dry-run oficial ─────────────────────────────────────
# 0. Verificar existencia de launcher y schema
_launcher_path = Path(LAUNCHER)
_schema_path   = Path(SCHEMA_PATH)
if not _launcher_path.exists():
    raise FileNotFoundError(
        f'Launcher no encontrado: {LAUNCHER}\n'
        f'  → Vuelve a ejecutar la celda de clonado (1.2) para restaurar el submodulo CityLearn.'
    )
if not _schema_path.exists():
    raise FileNotFoundError(
        f'Schema no encontrado: {SCHEMA_PATH}\n'
        f'  → Genera el dataset Iquitos primero (celdas 3.x).'
    )

# 0b. Verificar protocolo two_phase_happo_masac_v3 (bloquea layout antiguo 9+3)
verify_two_phase_protocol()
_parallel_ok = _ensure_launcher_parallel()
if _parallel_ok:
    print(f'Launcher : {LAUNCHER}  [two_phase_happo_masac ✓]')
    print(f'Monitor  : {MONITOR}  [two_phase ✓]')
else:
    raise RuntimeError(
        'Launcher/monitor sin two_phase_happo_masac. Ejecuta celda 1.2 y vuelve a 7.0/7.1.'
    )
print(f'Schema   : {SCHEMA_PATH}')

# 1. Dry-run oficial: valida CUDA/A100, imports, rutas y 12 comandos planificados
dry_run_cmd = launcher_base_args() + ['--dry-run', '--skip-completed']
run_cmd(dry_run_cmd)
monitor_once()

# 2. Leer y validar status.json (desde colab_protocol_guard.py sincronizado en 1.2)
import importlib.util

_guard_path = Path(REPO) / 'CityLearn/scripts/colab_protocol_guard.py'
_spec = importlib.util.spec_from_file_location('_colab_protocol_guard', _guard_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f'No se pudo cargar colab_protocol_guard desde {_guard_path}')
_pg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pg)

status_path = Path(OUTPUT_ROOT) / 'official_full_status.json'
with open(status_path) as f:
    status = json.load(f)
_pg.validate_dry_run_status(status)
_strategy = (status.get('parallelization') or {}).get('strategy', '')

# 3. Verificar que cada output_dir es unico y esta dentro de OUTPUT_ROOT
expected_root = Path(str(OUTPUT_ROOT)).resolve()
seen_outputs = set()
for job in status['jobs']:
    job_output = Path(job['output_dir'])
    if not job_output.is_absolute():
        job_output = Path(REPO) / job_output
    job_output = job_output.resolve()
    rel = job_output.relative_to(expected_root)
    parts = rel.parts
    assert len(parts) == 2, f'Layout inesperado: {job_output}'
    _algos_lower = {a.lower() for a in ALGORITHMS}
    assert parts[0].lower() in _algos_lower, f'Algoritmo inesperado en output_dir: {parts[0]}'
    assert parts[1].upper() in set(SCENARIOS), f'Scenario inesperado: {parts[1]}'
    seen_outputs.add(str(job_output))
assert len(seen_outputs) == 12, f'Output dirs duplicados o incompletos: {len(seen_outputs)}'

print('Dry-run validado: 12 jobs, 2 fases (6 paralelos/fase), sin stagger, outputs aislados en OUTPUT_ROOT.')
print(f'  strategy: {_strategy}')

# Marca el dry-run como validado: 7.2 omitira su dry-run interno si la config no cambia.
if 'mark_dry_run_validated' in globals():
    mark_dry_run_validated()

# 4. Preview skip/resume con HAPPO_ROLLOUT_THREADS ya fijado (misma fuente que 2.1b).
import importlib
_c71 = importlib.import_module('citylearn_v3_training_common')
_c71.notebook_jobs_resume_preview(
    Path(str(OUTPUT_ROOT)),
    target_episodes=int(globals().get('N_EPISODES', globals().get('EPISODES', 50))),
    episode_time_steps=int(globals().get('EPISODE_STEPS', 8760)),
    happo_rollout_threads=int(globals().get('HAPPO_ROLLOUT_THREADS', 0)) or None,
    label='7.1',
    show_footer_hint=False,
    require_canonical_plan=not bool(globals().get('_created_new_run')),
)
