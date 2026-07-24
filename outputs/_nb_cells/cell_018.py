# ── 1.2  Clonar repositorio completo + todos los submódulos ─────────────────
# Repo padre: scripts/, tools/, uc3m/, docs/, outputs/, deploy/
# Submódulos fijados (pinned commits en .gitmodules):
#   CityLearn        → Mac-Tapia/CityLearn (Colab rama viva: codex/iquitos-distillation-madrl-docs; .gitmodules pin: citylearn-v3-madrl)
#   external/HARL    → github.com/Mac-Tapia/HARL
#   external/MAAC    → github.com/Mac-Tapia/MAAC (rama viva codex/integrar-limpieza-diagnosticos: fix cuda/cpu Adam)
#   external/MARL    → github.com/Mac-Tapia/MARL
#   external/MARLlib → github.com/Mac-Tapia/MARLlib
#   external/MATD3implementation → github.com/Mac-Tapia/MATD3implementation
#   external/MicroGrids  → github.com/Mac-Tapia/MicroGrids
#   external/evcc        → github.com/evcc-io/evcc
#   external/prosumpy    → github.com/Mac-Tapia/prosumpy
# CityLearn se lleva a su rama viva (sale del detached HEAD del clone).
import os
import subprocess
from pathlib import Path

REPO_URL         = 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git'
REPO_BRANCH      = 'codex/fix-madrl-traceability-docs'  # rama de trabajo Colab
REPO             = '/content/MADRLCitytleranflexresdr'

CITYLEARN_URL    = 'https://github.com/Mac-Tapia/CityLearn.git'
CITYLEARN_BRANCH = 'codex/iquitos-distillation-madrl-docs'  # two_phase_happo_masac
CITYLEARN_DIR    = f'{REPO}/CityLearn'

# external/MAAC vive en su propia rama viva (fix cuda/cpu del optimizador Adam al
# reanudar desde checkpoint). Igual que CityLearn, se saca del commit fijado por el
# padre y se lleva a la punta de su rama para garantizar el parche en Colab.
MAAC_URL         = 'https://github.com/Mac-Tapia/MAAC.git'
MAAC_BRANCH      = 'codex/integrar-limpieza-diagnosticos'
MAAC_DIR         = f'{REPO}/external/MAAC'


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
    print(f'Repo existente — HARD SYNC a origin/{REPO_BRANCH} ...')
    git_check(['fetch', 'origin', REPO_BRANCH], cwd=REPO)
    git_check(['reset', '--hard', f'origin/{REPO_BRANCH}'], cwd=REPO)
    git_check(['clean', '-fd'], cwd=REPO)
    # Actualizar submódulos fijados (todo excepto CityLearn que se trata aparte)
    git_check(['submodule', 'sync', '--recursive'], cwd=REPO)
    git_check([
        'submodule', 'update', '--init', '--recursive',
        '--force',
    ], cwd=REPO)
    parent_head = git_out(['rev-parse', '--short', 'HEAD'], cwd=REPO)
    print(f'[OK] Rama {REPO_BRANCH} @ {parent_head} (hard reset)')

# ── C: Hacer que CityLearn viva en su rama propia (no detached HEAD) ─────────
# Después de --recurse-submodules CityLearn queda en el commit fijado por el
# padre (detached HEAD). Lo llevamos a la punta de codex/iquitos-distillation-madrl-docs
# para que el notebook, badge Open in Colab y scripts esten actualizados.
print()
print(f'Activando CityLearn en rama viva: {CITYLEARN_BRANCH} ...')

# Asegurar que el remote mac-tapia apunte al fork correcto
existing_remotes = git_out(['remote'], cwd=CITYLEARN_DIR).splitlines()
if 'mac-tapia' not in existing_remotes:
    git_check(['remote', 'add', 'mac-tapia', CITYLEARN_URL], cwd=CITYLEARN_DIR)
else:
    git_check(['remote', 'set-url', 'mac-tapia', CITYLEARN_URL], cwd=CITYLEARN_DIR)

# Fetch la rama y checkout (rama viva, no detached HEAD)
git_check(['fetch', 'mac-tapia', CITYLEARN_BRANCH], cwd=CITYLEARN_DIR)
git_check(['checkout', '-B', CITYLEARN_BRANCH, f'mac-tapia/{CITYLEARN_BRANCH}'], cwd=CITYLEARN_DIR)
git_check(['clean', '-fd'], cwd=CITYLEARN_DIR)

cl_commit = git_out(['rev-parse', '--short', 'HEAD'], cwd=CITYLEARN_DIR)
cl_branch = git_out(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=CITYLEARN_DIR)
if cl_branch == 'HEAD':
    # Fallback: algunos runtimes dejan detached HEAD tras fetch; forzar rama local
    git_check(['checkout', '-B', CITYLEARN_BRANCH], cwd=CITYLEARN_DIR)
    cl_commit = git_out(['rev-parse', '--short', 'HEAD'], cwd=CITYLEARN_DIR)
    cl_branch = git_out(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=CITYLEARN_DIR)
if cl_branch != CITYLEARN_BRANCH:
    raise RuntimeError(
        f'CityLearn sigue en detached HEAD ({cl_branch!r}). '
        f'Esperado {CITYLEARN_BRANCH!r}. Revisa permisos git en {CITYLEARN_DIR}.'
    )
print(f'[OK] CityLearn activo en rama: {cl_branch} @ {cl_commit}')

# ── C2: Hacer que external/MAAC viva en su rama propia (no detached HEAD) ─────
# El backend MAAC necesita el parche _sync_optimizer_state (estado Adam a GPU al
# reanudar). Lo llevamos a la punta de MAAC_BRANCH igual que CityLearn.
print()
print(f'Activando external/MAAC en rama viva: {MAAC_BRANCH} ...')
_maac_remotes = git_out(['remote'], cwd=MAAC_DIR).splitlines()
if 'mac-tapia' not in _maac_remotes:
    git_check(['remote', 'add', 'mac-tapia', MAAC_URL], cwd=MAAC_DIR)
else:
    git_check(['remote', 'set-url', 'mac-tapia', MAAC_URL], cwd=MAAC_DIR)
git_check(['fetch', 'mac-tapia', MAAC_BRANCH], cwd=MAAC_DIR)
git_check(['checkout', '-B', MAAC_BRANCH, f'mac-tapia/{MAAC_BRANCH}'], cwd=MAAC_DIR)
git_check(['clean', '-fd'], cwd=MAAC_DIR)
maac_commit = git_out(['rev-parse', '--short', 'HEAD'], cwd=MAAC_DIR)
maac_branch = git_out(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=MAAC_DIR)
if maac_branch != MAAC_BRANCH:
    raise RuntimeError(
        f'external/MAAC en rama incorrecta: {maac_branch!r} != {MAAC_BRANCH!r}.'
    )
print(f'[OK] external/MAAC activo en rama: {maac_branch} @ {maac_commit}')

# ── D: Verificar submódulos restantes (excluir CityLearn/MAAC que están adelante) ─
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

COLAB_OPEN_URL = (
    f'https://colab.research.google.com/github/Mac-Tapia/CityLearn/blob/'
    f'{CITYLEARN_BRANCH}/examples/madrl_citylearn_v3_tutorial.ipynb'
)
print(f'Open in Colab (GitHub): {COLAB_OPEN_URL}')

# ── E: Bloqueo protocolo en disco (no continuar con scripts legacy) ───────────
import sys as _sys_guard
_guard_py = f'{REPO}/CityLearn/scripts/colab_protocol_guard.py'
if not os.path.isfile(_guard_py):
    raise FileNotFoundError(f'Falta colab_protocol_guard.py: {_guard_py}')
subprocess.check_call([_sys_guard.executable, _guard_py, 'verify-repo', '--repo', REPO])
print('[OK] protocol-guard: launcher/monitor two_phase_happo_masac_v3 en /content')

# ── F: Verificación de parches (script en disco — inmune a notebook/kernel en caché)
# El hard sync de 1.2 actualiza este .py; no depende del texto de la celda en Colab.
_verify_patches_py = f'{REPO}/CityLearn/scripts/colab_verify_critical_patches.py'
if not os.path.isfile(_verify_patches_py):
    raise FileNotFoundError(
        f'Falta {_verify_patches_py}. Re-ejecuta celda 1.2 (hard sync).'
    )
subprocess.check_call([_sys_guard.executable, _verify_patches_py, '--repo', REPO])
