"""
Fix cells 17 and 18 of the notebook:
- Cell 17: clone from master; after submodule init, checkout CityLearn en su rama viva
- Cell 18: relaxar check CityLearn commit (permitir + que indica rama adelantada)
"""
import json
from pathlib import Path

NB = Path("d:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
with open(NB, "r", encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

# ─────────────────────────────────────────────────────────────────────────────
# CELL 17 — nuevo contenido completo
# ─────────────────────────────────────────────────────────────────────────────
NEW_CELL_17 = """\
# ── 1.2  Clonar repositorio completo y dejar CityLearn en rama viva ─────────
# El repo padre (MADRLCitytleranflexresdr) contiene scripts, tools, uc3m, data
# y los submódulos HARL, off-policy, MAAC, MARL como dependencias fijadas.
# El submódulo CityLearn/ se clona primero desde el pinned commit del padre y
# luego se sube a la punta de su rama propia (citylearn-v3-madrl) para que el
# código esté siempre actualizado y NO en detached HEAD.
import os, subprocess
from pathlib import Path

REPO_URL         = 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git'
REPO_BRANCH      = 'master'                          # rama estable del repo padre
REPO             = '/content/MADRLCitytleranflexresdr'

CITYLEARN_URL    = 'https://github.com/Mac-Tapia/CityLearn.git'
CITYLEARN_BRANCH = 'citylearn-v3-madrl'              # rama viva del submódulo
CITYLEARN_DIR    = f'{REPO}/CityLearn'


def git_check(args, cwd=None):
    cmd = ['git'] + [str(a) for a in args]
    print('+', ' '.join(cmd))
    kw = {'cwd': cwd} if cwd else {}
    subprocess.check_call(cmd, **kw)


def git_out(args, cwd=None) -> str:
    kw = {'cwd': cwd} if cwd else {}
    return subprocess.check_output(
        ['git'] + [str(a) for a in args], text=True, **kw
    ).strip()


# ── A: Clonar repo padre con submódulos (si no existe) ───────────────────────
if not os.path.exists(f'{REPO}/.git'):
    if os.path.exists(REPO):
        raise RuntimeError(
            f'{REPO} existe pero sin .git. Elimina la carpeta y vuelve a ejecutar.'
        )
    print(f'Clonando {REPO_URL} (rama {REPO_BRANCH}) con submódulos ...')
    git_check([
        'clone',
        '--branch', REPO_BRANCH,
        '--depth', '1',
        '--recurse-submodules',
        '--shallow-submodules',
        REPO_URL, REPO,
    ])
    print('[OK] Repo padre clonado con todos los submódulos')

# ── B: Repo padre ya existe — refrescar ──────────────────────────────────────
else:
    current_origin = git_out(['config', '--get', 'remote.origin.url'], cwd=REPO)
    if current_origin != REPO_URL:
        raise RuntimeError(
            f'Repo apunta a {current_origin}; esperado {REPO_URL}. '
            'Elimina /content/MADRLCitytleranflexresdr y vuelve a ejecutar.'
        )
    print(f'Repo existente — actualizando a {REPO_BRANCH} ...')
    git_check(['fetch', '--depth', '1', 'origin', REPO_BRANCH], cwd=REPO)
    git_check(['checkout', '-B', REPO_BRANCH, 'FETCH_HEAD'], cwd=REPO)
    # Actualizar submódulos fijados (todo excepto CityLearn que se trata aparte)
    git_check(['submodule', 'sync', '--recursive'], cwd=REPO)
    git_check([
        'submodule', 'update', '--init', '--recursive',
        '--force', '--depth', '1',
    ], cwd=REPO)
    print(f'[OK] Rama {REPO_BRANCH} actualizada')

# ── C: Hacer que CityLearn viva en su rama propia (no detached HEAD) ─────────
# Después de --recurse-submodules CityLearn queda en el commit fijado por el
# padre (detached HEAD). Lo llevamos a la punta de citylearn-v3-madrl para que
# el notebook y todos los scripts de entrenamiento estén actualizados.
print()
print(f'Activando CityLearn en rama viva: {CITYLEARN_BRANCH} ...')

# Asegurar que el remote mac-tapia apunte al fork correcto
existing_remotes = git_out(['remote'], cwd=CITYLEARN_DIR).splitlines()
if 'mac-tapia' not in existing_remotes:
    git_check(['remote', 'add', 'mac-tapia', CITYLEARN_URL], cwd=CITYLEARN_DIR)
else:
    git_check(['remote', 'set-url', 'mac-tapia', CITYLEARN_URL], cwd=CITYLEARN_DIR)

# Fetch la rama con historial mínimo (--depth 1 para velocidad en Colab)
git_check(['fetch', '--depth', '1', 'mac-tapia', CITYLEARN_BRANCH], cwd=CITYLEARN_DIR)

# Checkout a la punta de la rama (sale del detached HEAD)
git_check(['checkout', '-B', CITYLEARN_BRANCH, f'mac-tapia/{CITYLEARN_BRANCH}'], cwd=CITYLEARN_DIR)

cl_commit = git_out(['rev-parse', '--short', 'HEAD'], cwd=CITYLEARN_DIR)
cl_branch = git_out(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=CITYLEARN_DIR)
print(f'[OK] CityLearn activo en rama: {cl_branch} @ {cl_commit}')

# ── D: Verificar submódulos restantes (excluir CityLearn que ya está adelante) ─
status_lines = git_out(['submodule', 'status', '--recursive'], cwd=REPO).splitlines()
bad = [
    ln for ln in status_lines
    if ln and ln[0] in {'-', 'U'}            # '-' = no inicializado, 'U' = conflicto
    # '+' para CityLearn es ESPERADO (está adelante del commit fijado)
]
if bad:
    print('[ERROR] Submódulos sin inicializar o en conflicto:')
    for ln in bad:
        print(f'  {ln}')
    raise RuntimeError('Repara los submódulos antes de continuar.')

print()
print('═' * 60)
print('  Repositorio listo')
print(f'  Padre    : {REPO_BRANCH} @ {git_out(["rev-parse", "--short", "HEAD"], cwd=REPO)}')
print(f'  CityLearn: {cl_branch} @ {cl_commit}  ← RAMA VIVA')
print('═' * 60)

os.chdir(REPO)
"""

# ─────────────────────────────────────────────────────────────────────────────
# CELL 18 — nuevo contenido completo
# ─────────────────────────────────────────────────────────────────────────────
NEW_CELL_18 = """\
# ── 1.2b  Validar espejo Colab: repo padre + CityLearn en rama viva ─────────
import glob, json, os, subprocess
from pathlib import Path

PROJECT_NAME     = 'MADRLCitytleranflexresdr'
DATASET_DIR      = f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025'
SCHEMA_FOR_CONTEXT = f'{DATASET_DIR}/schema.json'


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

assert cl_branch == CITYLEARN_BRANCH, (
    f'CityLearn en rama incorrecta: {cl_branch!r} != {CITYLEARN_BRANCH!r}. '
    f'Ejecuta la celda 1.2 para activar la rama viva.'
)
print(f'[OK] CityLearn: {cl_branch} @ {cl_commit[:12]}  ← rama viva')

# 3. Submódulos dependencia en estado correcto (sin '-' ni 'U')
submodule_status = sh(['git', 'submodule', 'status', '--recursive'])
bad_submodules = [
    ln for ln in submodule_status.splitlines()
    if ln and ln[0] in {'-', 'U'}    # '+' para CityLearn es esperado y aceptado
]
if bad_submodules:
    raise RuntimeError(
        'Submódulos no inicializados o en conflicto:\\n' + '\\n'.join(bad_submodules)
    )
print('[OK] Todos los submódulos de dependencia inicializados')

# 4. Rutas críticas del proyecto
required_paths = [
    'CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb',
    'CityLearn/scripts/colab_a100_official_launcher.py',
    'CityLearn/scripts/colab_a100_live_monitor.py',
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
print('  Espejo Colab VALIDADO')
print(f'  Repo padre : {branch} @ {head[:12]}')
print(f'  CityLearn  : {cl_branch} @ {cl_commit[:12]}  ← VIVA')
print(f'  Dataset    : {csv_count} CSV · 17 edificios · 26304 pasos')
print('═' * 60)
"""

# ── Apply to notebook ─────────────────────────────────────────────────────────
assert cells[17]["cell_type"] == "code", "Cell 17 is not code"
assert cells[18]["cell_type"] == "code", "Cell 18 is not code"

cells[17]["source"] = NEW_CELL_17
cells[18]["source"] = NEW_CELL_18

nb["cells"] = cells
with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Cells 17 and 18 replaced.")
print(f"Total cells: {len(nb['cells'])}")

# Quick verify
with open(NB, "r", encoding="utf-8") as f:
    nb2 = json.load(f)
assert "citylearn-v3-madrl" in "".join(nb2["cells"][17]["source"])
assert "CITYLEARN_BRANCH" in "".join(nb2["cells"][18]["source"])
assert "mac-tapia" in "".join(nb2["cells"][17]["source"])
assert "rama viva" in "".join(nb2["cells"][17]["source"])
print("Verification PASSED")
