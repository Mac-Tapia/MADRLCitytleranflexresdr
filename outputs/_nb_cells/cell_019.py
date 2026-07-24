# ── 1.2b  Validar repo Colab: padre + CityLearn en rama viva ───────────────
import glob
import os
import subprocess

PROJECT_NAME = 'MADRLCitytleranflexresdr'
REPO_URL     = globals().get('REPO_URL', 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git')
REPO_BRANCH  = globals().get('REPO_BRANCH', 'codex/fix-madrl-traceability-docs')

# ── Detección automática de REPO (Colab o local; independiente de celda 1.2) ─
import importlib.util
_in_colab_12b = importlib.util.find_spec('google.colab') is not None

_repo_from_ctx = globals().get('REPO', None)
if _repo_from_ctx and Path(_repo_from_ctx).exists() and (Path(_repo_from_ctx) / 'CityLearn').exists():
    REPO = _repo_from_ctx
elif _in_colab_12b:
    REPO = '/content/MADRLCitytleranflexresdr'
    if not Path(REPO).exists():
        raise RuntimeError(
            f'{REPO} no existe. Ejecuta celda 1.2 (clone + hard sync) antes de 1.2b.'
        )
else:
    _start = Path.cwd()
    _candidates = [
        _start,
        _start.parent,
        _start.parent.parent,
        Path('d:/MADRLCitytleranflexresdr'),
        Path.home() / 'MADRLCitytleranflexresdr',
    ]
    REPO = next(
        (
            str(p)
            for p in _candidates
            if (p / 'CityLearn').exists() and (p / '.git').exists()
        ),
        None,
    )
    if REPO is None:
        raise RuntimeError(
            'No se encontró el repo MADRLCitytleranflexresdr. '
            'Ejecuta celda 1.2 en Colab o abre el notebook desde la raíz del proyecto.'
        )

DATASET_DIR        = f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025'
SCHEMA_FOR_CONTEXT = f'{DATASET_DIR}/schema.json'
CITYLEARN_URL      = globals().get('CITYLEARN_URL', 'https://github.com/Mac-Tapia/CityLearn.git')
CITYLEARN_BRANCH   = globals().get('CITYLEARN_BRANCH', 'codex/iquitos-distillation-madrl-docs')
MAAC_URL           = globals().get('MAAC_URL', 'https://github.com/Mac-Tapia/MAAC.git')
MAAC_BRANCH        = globals().get('MAAC_BRANCH', 'codex/integrar-limpieza-diagnosticos')


def sh(args, cwd=REPO) -> str:
    return subprocess.check_output([str(a) for a in args], cwd=cwd, text=True).strip()


# 1. Repo padre en la rama correcta
repo_root = sh(['git', 'rev-parse', '--show-toplevel'])
branch    = sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
head      = sh(['git', 'rev-parse', 'HEAD'])
origin    = sh(['git', 'config', '--get', 'remote.origin.url'])

assert Path(repo_root).resolve() == Path(REPO).resolve(), f'Repo root: {repo_root}'
assert branch == REPO_BRANCH, (
    f'Rama incorrecta: {branch!r} != {REPO_BRANCH!r}. '
    f'Ejecuta la celda 1.2 para sincronizar.'
)
assert origin == REPO_URL, f'Origin: {origin!r} != {REPO_URL!r}'
print(f'[OK] Repo padre: {branch} @ {head[:12]}')

# 2. CityLearn en su rama viva (NO detached HEAD, NO commit fijado antiguo)
cl_dir    = f'{REPO}/CityLearn'
cl_branch = sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=cl_dir)
cl_commit = sh(['git', 'rev-parse', 'HEAD'], cwd=cl_dir)

if cl_branch == 'HEAD':
    print('[FIX] CityLearn en detached HEAD — activando rama viva ...')
    _remotes = sh(['git', 'remote'], cwd=cl_dir).splitlines()
    if 'mac-tapia' not in _remotes:
        subprocess.check_call(
            ['git', 'remote', 'add', 'mac-tapia', CITYLEARN_URL], cwd=cl_dir
        )
    subprocess.check_call(
        ['git', 'fetch', 'mac-tapia', CITYLEARN_BRANCH], cwd=cl_dir
    )
    subprocess.check_call(
        ['git', 'checkout', '-B', CITYLEARN_BRANCH, f'mac-tapia/{CITYLEARN_BRANCH}'],
        cwd=cl_dir,
    )
    cl_branch = sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=cl_dir)
    cl_commit = sh(['git', 'rev-parse', 'HEAD'], cwd=cl_dir)
    print(f'[OK] CityLearn reparado: {cl_branch} @ {cl_commit[:12]}')

assert cl_branch == CITYLEARN_BRANCH, (
    f'CityLearn en rama incorrecta: {cl_branch!r} != {CITYLEARN_BRANCH!r}. '
    f'Ejecuta la celda 1.2 para activar la rama viva.'
)
print(f'[OK] CityLearn: {cl_branch} @ {cl_commit[:12]}  ← rama viva')

# 2b. external/MAAC en su rama viva (parche cuda/cpu del optimizador Adam)
maac_dir    = f'{REPO}/external/MAAC'
maac_branch = sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=maac_dir)
maac_commit = sh(['git', 'rev-parse', 'HEAD'], cwd=maac_dir)
if maac_branch != MAAC_BRANCH:
    print(f'[FIX] external/MAAC en {maac_branch!r} — activando rama viva ...')
    _mremotes = sh(['git', 'remote'], cwd=maac_dir).splitlines()
    if 'mac-tapia' not in _mremotes:
        subprocess.check_call(['git', 'remote', 'add', 'mac-tapia', MAAC_URL], cwd=maac_dir)
    subprocess.check_call(['git', 'fetch', 'mac-tapia', MAAC_BRANCH], cwd=maac_dir)
    subprocess.check_call(
        ['git', 'checkout', '-B', MAAC_BRANCH, f'mac-tapia/{MAAC_BRANCH}'], cwd=maac_dir,
    )
    maac_branch = sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=maac_dir)
    maac_commit = sh(['git', 'rev-parse', 'HEAD'], cwd=maac_dir)
assert maac_branch == MAAC_BRANCH, (
    f'external/MAAC en rama incorrecta: {maac_branch!r} != {MAAC_BRANCH!r}. '
    f'Ejecuta la celda 1.2 para activar la rama viva.'
)
print(f'[OK] external/MAAC: {maac_branch} @ {maac_commit[:12]}  ← rama viva')

# 3. Submódulos dependencia en estado correcto (sin '-' ni 'U')
submodule_status = sh(['git', 'submodule', 'status', '--recursive'])
bad_submodules = [
    ln for ln in submodule_status.splitlines()
    if ln and ln[0] in {'-', 'U'}    # '+' para CityLearn es esperado y aceptado
]
if bad_submodules:
    raise RuntimeError(
        'Submódulos no inicializados o en conflicto:\n' + '\n'.join(bad_submodules)
    )
print('[OK] Todos los submódulos de dependencia inicializados')

# 4. Rutas críticas del proyecto
required_paths = [
    'CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb',
    'CityLearn/scripts/colab_a100_official_launcher.py',
    'CityLearn/scripts/colab_a100_live_monitor.py',
    'CityLearn/scripts/colab_protocol_guard.py',
    'CityLearn/scripts/colab_verify_critical_patches.py',
    'CityLearn/scripts/train_citylearn_v3_happo.py',
    'CityLearn/scripts/train_citylearn_v3_masac.py',
    'CityLearn/scripts/train_citylearn_v3_matd3.py',
    'CityLearn/scripts/train_citylearn_v3_maac.py',
    'CityLearn/citylearn/v3/environment.py',
    'external/HARL',
    'external/MARL/src',
    'external/off-policy',
    'external/MAAC',
    'uc3m',
    'tools',
]
missing = [p for p in required_paths if not (Path(REPO) / p).exists()]
if missing:
    raise FileNotFoundError('Rutas requeridas no encontradas: ' + ', '.join(missing))
print(f'[OK] {len(required_paths)} rutas críticas presentes')

# 5. Dataset Iquitos 2023-2025
csv_count = len(glob.glob(f'{DATASET_DIR}/*.csv'))
with open(SCHEMA_FOR_CONTEXT) as f:
    schema_context = json.load(f)
assert csv_count == 222, f'Dataset incompleto: {csv_count}/222 CSV'
assert len(schema_context.get('buildings', {})) == 17, 'Schema: se esperan 17 edificios'
assert schema_context.get('simulation_end_time_step') == 26303
print(f'[OK] Dataset: {csv_count} CSV, 17 edificios, 26304 pasos')

# Protocolo y parches ya verificados en celda 1.2 (sections E/F).

# 5c. Badge Open in Colab alineado con CITYLEARN_BRANCH (push en Mac-Tapia/CityLearn)
_nb_file = Path(REPO) / 'CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb'
_badge_needle = (
    f'github/Mac-Tapia/CityLearn/blob/{CITYLEARN_BRANCH}/'
    'examples/madrl_citylearn_v3_tutorial.ipynb'
)
_nb_raw = _nb_file.read_text(encoding='utf-8')
if _badge_needle not in _nb_raw:
    _colab_url = (
        f'https://colab.research.google.com/github/Mac-Tapia/CityLearn/blob/'
        f'{CITYLEARN_BRANCH}/examples/madrl_citylearn_v3_tutorial.ipynb'
    )
    raise RuntimeError(
        'Badge Open in Colab desactualizado en el notebook.\n'
        f'  Debe apuntar a: {_colab_url}\n'
        '  Actualiza la celda markdown del titulo y haz push a CityLearn.'
    )
print(f'[OK] Open in Colab badge -> Mac-Tapia/CityLearn @ {CITYLEARN_BRANCH}')

# 6. Guardar contexto del proyecto para celdas siguientes
COLAB_PROJECT_CONTEXT = {
    'project_name': PROJECT_NAME,
    'repo_url': REPO_URL,
    'repo_branch': branch,
    'repo_commit': head,
    'repo_root': REPO,
    'citylearn_branch': cl_branch,
    'citylearn_commit': cl_commit,
    'citylearn_live': True,           # confirma que CityLearn está en rama viva
    'launcher_protocol': 'two_phase_happo_masac_v3',
    'dataset_dir': DATASET_DIR,
    'dataset_csv_count': csv_count,
    'buildings': len(schema_context.get('buildings', {})),
    'simulation_steps': schema_context.get('simulation_end_time_step') + 1,
}
os.makedirs(f'{REPO}/outputs', exist_ok=True)
with open(f'{REPO}/outputs/colab_project_context.json', 'w') as f:
    json.dump(COLAB_PROJECT_CONTEXT, f, indent=2)

print()
print('═' * 60)
print('  Repo Colab VALIDADO')
print(f'  Repo padre : {branch} @ {head[:12]}')
print(f'  CityLearn  : {cl_branch} @ {cl_commit[:12]}  ← VIVA')
print(f'  Dataset    : {csv_count} CSV · 17 edificios · 26304 pasos')
print('═' * 60)
