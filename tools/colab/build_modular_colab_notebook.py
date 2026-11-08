"""Build the modular Colab notebook (docs/plans/cuaderno_colab.md) and its overlay bundle.

The notebook is a thin client: code cells are marked ``# [Cn] <title>`` (C1..C11) and
call tools/colab/colab_session.py (stdlib, kernel side), the campaign CLI and
``python -m uc3m.application.pipeline`` (project Python 3.9). This module is the only
source of the .ipynb; never edit it by hand.

    python tools/colab/build_modular_colab_notebook.py [--output ZIP] [--notebook IPYNB] [--config YAML]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import zipfile
from pathlib import Path

from uc3m.application.training.context import repository_revision
from uc3m.application.training.preflight import (_FRESH_FOLDERS, _FRESH_ROOT_FILES, _FRESH_SUFFIXES,
                                                 fresh_source_paths, source_snapshot)

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb'
DESTINATION = ROOT/'examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb'
BUNDLE = ROOT/'outputs/colab_delivery/colab_modular_overlay.zip'
CAMPAIGN_CONFIG = ROOT/'configs/experiments/iquitos.yaml'
SESSION_MODULE = ROOT/'tools/colab/colab_session.py'
# Measured peak RSS of one frozen evaluation (validation_2024, full year, CPU, RBC policy):
# see EVAL_RAM_MEASUREMENT; a trained policy adds its parameters (largest: MATD3, ~0.3 GiB).
EVAL_RAM_GIB = 1.45
EVAL_RAM_MEASUREMENT = ('2026-11-01 local Windows CPU: run_frozen_episode(validation_2024, RbcPolicy, '
                        'scenario E1, seed 1001), 8783 steps in 2744 s; peak working set 1.21 GiB '
                        '(psutil RSS sampled every 0.5 s: 1.04 GiB) + 0.24 GiB parameters of the largest '
                        'policy (MATD3, 17 x h=256, ~64.5 M float32, computed)')
# The copied tutorial setup cell refers to tutorial cells that do not exist here.
SETUP_REFERENCE_FIXES = {
    'vuelve a ejecutar desde la celda 1.2b.': 'vuelve a ejecutar desde la celda C1 de este cuaderno.',
    'Ejecuta primero la celda 1.2.': 'Ejecuta primero la celda C1 de este cuaderno.',
    'Celda 1.3 OK': 'C2 OK',
    # Annotation only: the helpers never combine check with captured output (they print the log tail).
    'def run(cmd, *, cwd=None, env=None, check=True):': 'def run(cmd, *, cwd=None, env=None, check: bool = True):',
    'def run_shell(script, *, cwd=None, env=None, check=True):':
        'def run_shell(script, *, cwd=None, env=None, check: bool = True):',
}
# Unpinned requirements of the setup cell; versions come from uv.lock (Python 3.9 entry)
# when the package is locked, otherwise from the local project environment, never typed.
PINNED_FROM_LOCK_OR_ENV = ('requests', 'tqdm', 'psutil', 'platformdirs', 'tensorboardX', 'setproctitle',
                           'simplejson', 'absl-py', 'dm-tree', 'importlib-metadata')
# Not installed in .venv39-citylearn-v3 nor in uv.lock (the off-policy backend logs with
# tensorboardX): removed instead of left unpinned.
DROPPED_UNPINNED = ('tensorboard',)


def locked_versions(lock_path: Path = ROOT/'uv.lock') -> dict:
    """name -> version of uv.lock, preferring the entry resolved for Python < 3.10."""
    versions = {}
    for block in Path(lock_path).read_text(encoding='utf-8').split('[[package]]'):
        name = re.search(r'^name = "([^"]+)"', block, re.M)
        version = re.search(r'^version = "([^"]+)"', block, re.M)
        if not (name and version):
            continue
        key = name.group(1).lower()
        if key not in versions or "python_full_version < '3.10'" in block:
            versions[key] = version.group(1)
    return versions


def local_version(distribution: str) -> str:
    import importlib.metadata
    return importlib.metadata.version(distribution).split('+')[0]


def local_uv_version() -> str:
    import subprocess as sp
    return re.search(r'uv (\d+\.\d+\.\d+)', sp.check_output(['uv', '--version'], text=True)).group(1)


def pin_setup(setup: str) -> str:
    """Pin torch, the base dependencies and the uv installer (uv.lock first, then the local env)."""
    locked = locked_versions()
    for name in PINNED_FROM_LOCK_OR_ENV:
        version = locked.get(name.lower()) or local_version(name)
        setup = re.sub(r"'" + re.escape(name) + r"(?:[<>=][^']*)?'", f"'{name}=={version}'", setup, count=1)
    for name in DROPPED_UNPINNED:
        setup = setup.replace(f"    '{name}',\n", '', 1)
    pins = {"TORCH_PACKAGES = ('torch', 'torchvision')":
            f"TORCH_PACKAGES = ('torch=={local_version('torch')}', 'torchvision=={local_version('torchvision')}')",
            "    'pyyaml',\n": f"    'pyyaml=={locked.get('pyyaml') or local_version('PyYAML')}',\n",
            'https://astral.sh/uv/install.sh': f'https://astral.sh/uv/{local_uv_version()}/install.sh'}
    for stale, pinned in pins.items():
        if stale not in setup:
            raise ValueError(f'setup cell changed, cannot pin: {stale!r}')
        setup = setup.replace(stale, pinned)
    return setup


def campaign_identity(root: Path) -> dict:
    """alias, campaign_id, dataset_root and splits of the campaign config (single source)."""
    import yaml
    payload = yaml.safe_load((Path(root)/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
    return {'alias': str(payload['storage_alias']), 'campaign_id': str(payload['campaign_id']),
            'dataset_root': str(payload['dataset_root']), 'splits': list(payload['splits'])}


def campaign_from_config(config_path: Path):
    """(storage_alias, dataset_root) of a campaign config file."""
    import yaml
    payload = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
    return str(payload['storage_alias']), str(payload['dataset_root'])


STDLIB_MODULES = {'importlib', 'json', 'os', 'pathlib', 'platform', 're', 'shutil', 'subprocess', 'sys'}


def self_contained(source):
    """Prepend stdlib imports a copied cell uses but relied on earlier cells for."""
    tree = ast.parse(source)
    imported = {alias.asname or alias.name.split('.')[0] for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    imported |= {node.module.split('.')[0] for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom) and node.module}
    used = {node.value.id for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)}
    missing = sorted((used & STDLIB_MODULES) - imported)
    return ''.join(f'import {name}\n' for name in missing) + source


def cell(kind, source):
    result = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True),
              'id': 'modular-' + hashlib.sha256(source.encode('utf-8')).hexdigest()[:12]}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result


INTRO = '''# MADRL · Entrenamiento modular en Google Colab

Cliente de la CLI de la campaña nueva (`python -m uc3m.application.training.cli`): no
contiene otra lógica de entrenamiento. Reutiliza la instalación Python 3.9 del tutorial
original sin sobrescribir sus celdas. Cada celda de código empieza con `# [Cn]` (C1–C11).

Cada backend entrena con su capacidad nativa, sin recortes silenciosos. Antes de entrenar,
la entrada nativa mide RAM y VRAM y rechaza (`insufficient_resources:<algoritmo>:<ram|vram>`)
si no alcanzan los requisitos de `configs/algorithms/native.yaml` (episodios de 8760 pasos):
__REQUIREMENTS__.

**MASAC con los valores del autor (lote del crítico de 32 episodios) es el que fija la GPU:**
necesita __MASAC_VRAM__ GiB de VRAM con `rnn_hidden_dim` __MASAC_RNN__, su único candidato (D-M3-8). Una A100/H100
de 80 GB expone unas 74,5 GiB, así que cabe con poco margen. Un rechazo
`insufficient_resources:MASAC:vram` deja incompleta la campaña: es un fallo que se revisa, no un
resultado aceptable. Los requisitos son estimaciones. C6 guarda el pico de VRAM de cada etapa, y el piloto
no llega al lote de 32 episodios, de modo que su pico no es el máximo de la campaña.
Usar Colab Pro con RAM alta; la disponibilidad de GPU y la duración de la sesión dependen
de Colab.

**Importante:** los cambios locales aún no publicados NO aparecen al clonar GitHub. Subir
el paquete `colab_modular_overlay.zip` generado junto a este cuaderno; contiene código y
dataset actuales con su hash por archivo, sin entornos ni credenciales.
'''

C1 = '''# [C1] Paquete y checkout exacto
from google.colab import files
from pathlib import Path
import importlib.util, io, json, os, subprocess, zipfile

ORIGIN = 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git'
PROJECT_ROOT = Path('/content/MADRLCitytleranflexresdr')
uploaded = files.upload()
payload = uploaded.get('colab_modular_overlay.zip')
if payload is None:
    raise RuntimeError('Sube colab_modular_overlay.zip generado en tu proyecto local')
bundle = zipfile.ZipFile(io.BytesIO(payload))
BUNDLE_MANIFEST = json.loads(bundle.read('colab_bundle_manifest.json'))
import sys
spec = importlib.util.spec_from_loader('colab_session', loader=None)
cs = importlib.util.module_from_spec(spec)
sys.modules['colab_session'] = cs                   # dataclasses need the module registered
exec(compile(bundle.read('colab_session.py').decode('utf-8'), 'colab_session.py', 'exec'), cs.__dict__)
if not PROJECT_ROOT.exists():
    subprocess.run(['git', 'clone', '--recursive', ORIGIN, str(PROJECT_ROOT)], check=True)
    subprocess.run(['git', 'checkout', BUNDLE_MANIFEST['commit']], cwd=PROJECT_ROOT, check=True)
    subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], cwd=PROJECT_ROOT, check=True)
applied = cs.apply_overlay(bundle, PROJECT_ROOT)
reasons = cs.verify_checkout(PROJECT_ROOT, BUNDLE_MANIFEST, origin=ORIGIN)
if reasons:
    raise RuntimeError(f'El checkout no coincide con el paquete local: {reasons[:20]}')
os.chdir(PROJECT_ROOT)
print('Paquete aplicado:', applied['written'], 'archivos; retirados del clon:', applied['removed'])
print('Checkout verificado contra el paquete (commit, submódulos, hash por archivo).')
'''

C3 = '''# [C3] Campaña, dataset y Drive por identidad
from google.colab import drive
drive.mount('/content/drive')
import json, yaml
from pathlib import Path

PYTHON = cs.project_python(PROJECT_ROOT, PROJECT_PYTHON)     # el Python 3.9 preparado en C2
CONFIG = 'configs/experiments/iquitos.yaml'
CAMPAIGN = yaml.safe_load((PROJECT_ROOT/CONFIG).read_text())
ALIAS, CAMPAIGN_ID = CAMPAIGN['storage_alias'], CAMPAIGN['campaign_id']
if (ALIAS, CAMPAIGN_ID) != (BUNDLE_MANIFEST['alias'], BUNDLE_MANIFEST['campaign_id']):
    raise RuntimeError('El paquete es de otra campaña que la configuración')
CAMPAIGN_ROOT = PROJECT_ROOT/CAMPAIGN['dataset_root']
ARTIFACTS = PROJECT_ROOT/'outputs/campaigns'/ALIAS
MANIFEST = ARTIFACTS/'campaign_manifest.json'
acceptance = json.loads((CAMPAIGN_ROOT/'dataset_acceptance.json').read_text())
if not acceptance['dataset_verified'] or acceptance['dataset_hash'] != BUNDLE_MANIFEST['dataset_hash']:
    raise RuntimeError('Dataset de la campaña no verificado o distinto al paquete local')
split_manifest = {s['split_id']: s for s in json.loads((CAMPAIGN_ROOT/'split_manifest.json').read_text())['splits']}
for split_id in CAMPAIGN['splits']:
    if split_id not in split_manifest or not (CAMPAIGN_ROOT/'splits'/split_manifest[split_id]['schema_path']).is_file():
        raise RuntimeError(f'Falta el split congelado {split_id}')
snapshot = cs.run_cli([str(PYTHON), '-c', 'import json; from pathlib import Path; '
                       'from uc3m.application.training.preflight import source_snapshot; '
                       "print(json.dumps({'source_sha256': source_snapshot(Path('.'), scope='fresh')}))"],
                      cwd=PROJECT_ROOT, on_line=lambda line: None)
if snapshot.report['source_sha256'] != BUNDLE_MANIFEST['source_sha256']:
    raise RuntimeError('Las fuentes calculadas con el Python del proyecto difieren del paquete')
DRIVE_ROOT = cs.drive_root(Path('/content/drive/MyDrive/MADRL_campaigns'), ALIAS, CAMPAIGN_ID)
DRIVE_ROOT.mkdir(parents=True, exist_ok=True)
CLI = [str(PYTHON), '-m', 'uc3m.application.training.cli', '--config', CONFIG]
SYNC = [str(PYTHON), '-m', 'uc3m.application.training.drive_sync', '--artifacts', str(ARTIFACTS),
        '--drive', str(DRIVE_ROOT)]
print('Campaña', CAMPAIGN_ID, '| dataset', acceptance['dataset_hash'][:12], '| Drive', DRIVE_ROOT)
'''

C4_MD = '''## Restaurar desde Drive los intentos ya terminados

Antes de preparar o lanzar se restauran a `outputs/campaigns/<alias>/` el registro
`treatments.json`, los manifiestos y los intentos terminados que verifican su hash y
`treatment_trust_reasons`, para que la etapa reutilice lo verificado. Un intento
interrumpido es fallido y nunca llegó a Drive (no tenía `completion.json`): su
tratamiento se repite desde cero, sin reanudar. Si hay conflictos o copias rechazadas,
la celda se detiene antes de preparar.
'''

C4 = '''# [C4] Restaurar intentos verificados desde Drive
restored = cs.run_cli(SYNC + ['--restore', '--campaign-id', CAMPAIGN_ID], cwd=PROJECT_ROOT).report
print('Restaurados completos:', len(restored['restored_complete']), '| fallidos:', len(restored['restored_failed']))
if restored['conflicts'] or restored['rejected']:
    raise RuntimeError(f"Drive y la copia local no coinciden: conflictos {restored['conflicts']}, "
                       f"rechazados {restored['rejected']}")
'''

C5_MD = '''## Preparar la campaña: no entrena

`prepare` construye el DAG (piloto, HPO, confirmación y sensibilidad) con su presupuesto
de pasos y mide RAM y VRAM para mostrar el plan de esa máquina; no entrena. Un rechazo muestra
el JSON con su razón.
'''

C5 = '''# [C5] Preparar campaña (no entrena)
prepared = cs.run_cli(CLI + ['--stage', 'prepare'], cwd=PROJECT_ROOT).report
print('Estado:', prepared['status'])
print('Presupuesto:', json.dumps(prepared['budget'], indent=1))
STAGE = 'pilot'  # 'pilot', 'hpo', 'confirm' o 'sensitivity': se muestra su plan aquí y C6 lanza esta misma
for line in cs.phase_plan_lines(prepared, STAGE):        # tal como lo informa prepare, sin lógica propia
    print(line)
'''

C6_MD = '''## Ejecutar una etapa autorizada

Cada intento empieza en el episodio 0 y nunca se reanuda. Mientras corre, cada intento
se copia a Drive en cuanto escribe su `completion.json`, con hash verificado y sin tocar
el intento en curso; al terminar o si la etapa se interrumpe se hace una última copia.
Un intento interrumpido no tiene `completion.json`: no se copia y, al relanzar tras C4,
su tratamiento se repite desde cero en un intento nuevo; los tratamientos con intento
verificado se reutilizan. Cada etapa necesita la decisión escrita del propietario: es `STAGE`
de C5 y solo se lanza con `EXECUTE_STAGE = True` y la referencia a esa decisión en `OWNER_DECISION`, que
queda en `stages/owner_authorizations.jsonl`. Tras lanzar, vuelve a poner `EXECUTE_STAGE = False`. No se edita `configs/experiments/iquitos.yaml`: es
una entrada de la identidad de la campaña. Si una copia a Drive falla, el entrenamiento sigue y la
celda lo avisa. Códigos de la CLI: 0 completa, 1 incompleta, 2 no autorizada o insumos cambiados.
'''

C6 = '''# [C6] Ejecutar etapa autorizada con sincronización
EXECUTE_STAGE = False  # True para lanzar la etapa STAGE elegida y revisada en C5
OWNER_DECISION = ''    # dónde y cuándo autorizó el propietario esta etapa, por ejemplo 'traspaso_sesiones.md 2026-12-01 pilot'
RUN_STAGE = None       # se deriva de STAGE; no escribir aquí otra etapa
if EXECUTE_STAGE:
    RUN_STAGE = STAGE
if RUN_STAGE and RUN_STAGE != STAGE:
    raise RuntimeError(f'RUN_STAGE={RUN_STAGE!r} distinto de la etapa revisada en C5 (STAGE={STAGE!r})')
if RUN_STAGE and not OWNER_DECISION.strip():
    raise RuntimeError('Escribe en OWNER_DECISION la decisión del propietario que autoriza esta etapa')
if RUN_STAGE:
    gpu_peak = ARTIFACTS/'stages'/f'{RUN_STAGE}_gpu_memory.json'
    stage = cs.run_stage_with_sync(CLI + ['--stage', RUN_STAGE, '--execute', '--owner-authorized', OWNER_DECISION], SYNC + ['--sync'],
                                   cwd=PROJECT_ROOT, interval_seconds=60, allowed=(0, 1, 2), gpu_peak_path=gpu_peak)
    report = stage.report or {}
    print('returncode', stage.returncode, '| estado', report.get('status'))
    print('Pico de VRAM:', gpu_peak.read_text() if gpu_peak.is_file() else 'sin lectura de nvidia-smi')
    if stage.sync_problems:
        print('ATENCIÓN: hubo', len(stage.sync_problems), 'copias a Drive fallidas; la última:', stage.sync_problems[-1])
    result_path = ARTIFACTS/'stages'/f'{RUN_STAGE}_result.json'
    stage_result = json.loads(result_path.read_text()) if result_path.is_file() else None
    for line in cs.stage_result_lines(report, stage_result):          # tal como lo informa run_stage
        print(line)
    if report.get('status') == 'insufficient_resources':
        stopped = cs.stopped_phase_label(report)                       # report['stopped_at_phase'] por algoritmos
        reasons = [r for phase in report.get('phase_plan') or [] for r in phase.get('reasons') or []]
        raise RuntimeError(f'Etapa detenida en la fase {stopped} por recursos insuficientes '
                           f'(0 trabajadores): {reasons}. La etapa queda incompleta: revisar GPU y RAM de esta sesión.')
    if stage.returncode == 2:
        raise RuntimeError(f"Etapa NO ejecutada (código 2): {report.get('status')} {report.get('reason', '')}")
    if stage.returncode == 1:
        raise RuntimeError('Etapa incompleta (código 1): hay tratamientos sin intento verificado; NO es un éxito')
    if stage.final_sync_failed:
        raise RuntimeError('La etapa terminó, pero la última copia a Drive falló: vuelve a copiar antes de cerrar la sesión')
    print('Etapa completa:', report['status'])
else:
    print(f'Sin entrenamiento: revisa el plan de {STAGE} en C5 y pon EXECUTE_STAGE = True si el propietario autorizó esta etapa.')
'''

C7_MD = '''## Después del entrenamiento

Las celdas C7–C11 llaman a `python -m uc3m.application.pipeline` con el Python del
proyecto. La última línea es JSON; código 0 = completo o incompleto (informado), 2 =
rechazado con su razón. Nada se sobrescribe: un resultado existente se informa.
'''

C7 = '''# [C7] Estado por tratamiento
status = cs.run_cli([str(PYTHON), '-m', 'uc3m.application.pipeline', 'status', '--manifest', str(MANIFEST)], cwd=PROJECT_ROOT,
                    on_line=lambda line: None).report
for row in status.get('treatments', status if isinstance(status, list) else []):
    print(row.get('stage'), row.get('treatment_id'), 'aceptado' if row.get('accepted') else 'NO aceptado',
          row.get('reasons'))
'''

C8_MD = '''## Congelar la configuración de HPO

Va después de C9 porque el congelado exige los intentos de `hpo` evaluados en `validation_2024`.
Orden de la campaña: `hpo` en C6, C9 con `EVAL_STAGE = 'hpo'`, C8, y luego `confirm` y
`sensitivity` en C6, con C9 sobre cada una.
'''

C8 = '''# [C8] Congelar configuración HPO (validación)
RUN_FREEZE = False
if RUN_FREEZE:
    frozen = cs.run_cli([str(PYTHON), '-m', 'uc3m.application.pipeline', 'freeze', '--manifest', str(MANIFEST), '--config', CONFIG,
                                    '--project-root', str(PROJECT_ROOT)], cwd=PROJECT_ROOT).report
    print(json.dumps(frozen, indent=1)[:4000])
    cs.run_cli(SYNC + ['--sync'], cwd=PROJECT_ROOT, on_line=lambda line: None)
'''

C9_MD = '''## Evaluación congelada

Evalúa con la política congelada cada intento aceptado de la etapa, por defecto en
`validation_2024`. `test_2025` solo se evalúa con un `test_unlock.json` válido. Los
procesos en paralelo son `max(1, cpu_count - 1)`, acotados por la RAM disponible y la
RAM medida de una evaluación (un año de CityLearn con una política, en CPU). Cada evaluación aparece
completa o no aparece, y se copia a Drive mientras la celda corre, de modo que un corte conserva lo terminado.
'''

C9 = '''# [C9] Evaluación congelada
import os, psutil
RUN_EVALUATION = False
EVAL_STAGE, EVAL_SPLIT = 'hpo', 'validation_2024'   # 'hpo' antes de C8; luego 'confirm' y 'sensitivity'
EVAL_RAM_GIB = __EVAL_RAM_GIB__   # medido: __EVAL_RAM_MEASUREMENT__
available = psutil.virtual_memory().available/2**30
workers = max(1, min((os.cpu_count() or 2) - 1, int(available // EVAL_RAM_GIB)))
if RUN_EVALUATION:
    run = cs.run_stage_with_sync([str(PYTHON), '-m', 'uc3m.application.pipeline', 'evaluate', '--manifest', str(MANIFEST), '--stage', EVAL_STAGE,
                                  '--split', EVAL_SPLIT, '--workers', str(workers),
                                  '--project-root', str(PROJECT_ROOT)], SYNC + ['--sync'], cwd=PROJECT_ROOT,
                                 interval_seconds=300, allowed=(0, 2))
    evaluated = run.report or {}
    print('Evaluados:', len(evaluated.get('evaluated', [])), '| existentes:', len(evaluated.get('existing', [])),
          '| fallidos:', evaluated.get('failed'), '| código', run.returncode)
    if run.final_sync_failed:
        raise RuntimeError('La última copia a Drive falló: vuelve a copiar antes de cerrar la sesión')
    if run.returncode != 0:
        raise RuntimeError(f'Evaluación incompleta o rechazada: relanza esta celda; lo evaluado se conserva. {evaluated}')
else:
    print('Sin evaluación; workers previstos:', workers)
'''

C10_MD = '''## Análisis, selección y prueba

Orden en `confirm`: C9 con `validation_2024`, C10 con esa misma partición y selección, y solo después C9 y C10
con `test_2025`. La selección nunca se hace mirando la prueba. Un análisis incompleto se rechaza sin publicarse:
se corrige lo que falta y se relanza. En `sensitivity` se analiza cada variante con `ANALYSIS_CANDIDATE`
(`p055`, `p065`), sobre `validation_2024`.
'''

C10 = '''# [C10] Tabla por semilla y análisis
RUN_ANALYSIS = False
RUN_SELECTION = False
ANALYSIS_CANDIDATE = None   # solo en sensitivity: 'p055' o 'p065'
if RUN_ANALYSIS:
    candidate = ['--candidate', ANALYSIS_CANDIDATE] if ANALYSIS_CANDIDATE else []
    analysis = cs.run_cli([str(PYTHON), '-m', 'uc3m.application.pipeline', 'analyze', '--manifest', str(MANIFEST), '--stage', EVAL_STAGE,
                                      '--split', EVAL_SPLIT] + candidate, cwd=PROJECT_ROOT).report
    print(json.dumps(analysis, indent=1)[:4000])
    if not ANALYSIS_CANDIDATE:
        statistics = cs.run_cli([str(PYTHON), 'tools/eval/build_campaign_statistical_report.py', '--manifest', str(MANIFEST), '--stage', EVAL_STAGE,
                                 '--split', EVAL_SPLIT], cwd=PROJECT_ROOT).report
        print(json.dumps(statistics, indent=1)[:4000])
if RUN_SELECTION:
    selection = cs.run_cli([str(PYTHON), '-m', 'uc3m.application.pipeline', 'select', '--manifest', str(MANIFEST), '--stage', EVAL_STAGE,
                                      '--split', EVAL_SPLIT], cwd=PROJECT_ROOT).report
    print(json.dumps(selection, indent=1)[:4000])
if RUN_ANALYSIS or RUN_SELECTION:
    cs.run_cli(SYNC + ['--sync'], cwd=PROJECT_ROOT, on_line=lambda line: None)
'''

C11 = '''# [C11] Entrega reproducible
RUN_DELIVERY = False
if RUN_DELIVERY:
    delivery = cs.run_cli([str(PYTHON), '-m', 'uc3m.application.pipeline', 'deliver', '--manifest', str(MANIFEST), '--stage', EVAL_STAGE,
                                      '--split', EVAL_SPLIT, '--destination', str(DRIVE_ROOT.parent/'delivery')],
                          cwd=PROJECT_ROOT).report
    print(json.dumps(delivery, indent=1)[:4000])
'''

SOURCES = '''## Alcance de validación y fuentes

El cuaderno es cliente de `uc3m.application.training.cli` y de `uc3m.application.pipeline`.
El dataset, los splits y el normalizador vienen congelados en el paquete y se verifican
por hash. Un piloto no sustituye la campaña confirmatoria ni la selección científica.

Sustento: Charbonnier (2023), tesis doctoral, University of Oxford,
https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5;
Costea (2026), tesis de maestría, https://webthesis.biblio.polito.it/40396/;
Pineau et al. (2021), JMLR, https://www.jmlr.org/papers/v22/20-303.html .
Recursos Colab: https://research.google.com/colaboratory/faq.html .
'''


def setup_cell(original) -> str:
    setup = self_contained(next(''.join(item['source']) for item in original['cells']
                                if item['cell_type'] == 'code'
                                and '# 1.3 Instalar dependencias' in ''.join(item['source'])))
    for stale, fixed in SETUP_REFERENCE_FIXES.items():
        setup = setup.replace(stale, fixed)
    return '# [C2] Instalación Python 3.9 fijada\n' + pin_setup(setup)


def runtime_requirements_text(root: Path = ROOT):
    """Intro requirements read from configs/algorithms/native.yaml, never typed: (phrase, MASAC vram, MASAC rnn)."""
    import yaml
    rows = yaml.safe_load((Path(root)/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))['algorithms']
    parts = []
    for name, row in rows.items():
        needed = row['runtime_requirements']
        vram = needed.get('min_vram_gib', max((needed.get('min_vram_gib_by_rnn_hidden_dim') or {0: 0}).values()))
        parts.append(f"{name} {needed['min_ram_gib']} GiB RAM / {vram} GiB VRAM")
    by_rnn = rows['MASAC']['runtime_requirements']['min_vram_gib_by_rnn_hidden_dim']
    rnn = max(by_rnn)
    return '; '.join(parts), by_rnn[rnn], rnn


def intro(root: Path = ROOT) -> str:
    phrase, vram, rnn = runtime_requirements_text(root)
    return (INTRO.replace('__REQUIREMENTS__', phrase).replace('__MASAC_VRAM__', str(vram))
            .replace('__MASAC_RNN__', str(rnn)))


def build_notebook(original, expected_dataset_hash):
    measured = EVAL_RAM_MEASUREMENT or 'pendiente de medición'
    c9 = C9.replace('__EVAL_RAM_GIB__', repr(EVAL_RAM_GIB or 4.0)).replace('__EVAL_RAM_MEASUREMENT__', measured)
    cells = [cell('markdown', intro()), cell('code', C1),
             cell('markdown', '## Instalación original del proyecto\nSe reutiliza la celda Python 3.9 del tutorial, '
                              'con dependencias fijadas a `uv.lock` y al entorno local.\n'),
             cell('code', setup_cell(original)), cell('code', C3), cell('markdown', C4_MD), cell('code', C4),
             cell('markdown', C5_MD), cell('code', C5), cell('markdown', C6_MD), cell('code', C6),
             cell('markdown', C7_MD), cell('code', C7), cell('markdown', C9_MD), cell('code', c9),
             cell('markdown', C8_MD), cell('code', C8), cell('markdown', C10_MD), cell('code', C10), cell('code', C11),
             cell('markdown', SOURCES)]
    return {'nbformat': 4, 'nbformat_minor': 5,
            'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                         'colab': {'name': DESTINATION.name}, 'accelerator': 'GPU',
                         'expected_dataset_sha256': expected_dataset_hash}, 'cells': cells}


def bundle_paths(root: Path, dataset_root: str):
    """Code, configs and the frozen campaign (dataset, splits, normalizer, manifests); no raw or outputs."""
    campaign = Path(root)/dataset_root
    paths = set(fresh_source_paths(root))
    for path in campaign.rglob('*'):
        relative = path.relative_to(campaign).parts
        if path.is_file() and relative and relative[0] not in {'raw', 'audit'}:
            paths.add(path)
    return sorted(paths)


def source_scope():
    """What colab_session.apply_overlay/verify_checkout treat as source (same rule as fresh_source_paths)."""
    return {'prefixes': list(_FRESH_FOLDERS) + list(_FRESH_ROOT_FILES), 'suffixes': sorted(_FRESH_SUFFIXES),
            'json_prefixes': [folder for folder in _FRESH_FOLDERS if folder.endswith('configs')]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, default=BUNDLE)
    parser.add_argument('--notebook', type=Path, default=DESTINATION)
    parser.add_argument('--config', type=Path, default=CAMPAIGN_CONFIG)
    args = parser.parse_args(argv)
    commit, submodules = repository_revision(ROOT)
    identity = campaign_identity(ROOT)
    alias, dataset_root = campaign_from_config(args.config)
    acceptance = json.loads((ROOT/dataset_root/'dataset_acceptance.json').read_text(encoding='utf-8'))
    notebook = build_notebook(json.loads(ORIGINAL.read_text(encoding='utf-8')), acceptance['dataset_hash'])
    args.notebook.parent.mkdir(parents=True, exist_ok=True)
    args.notebook.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    paths = bundle_paths(ROOT, dataset_root)
    files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    scope = source_scope()
    manifest = {'commit': commit, 'submodules': submodules, 'dataset_hash': acceptance['dataset_hash'],
                'source_sha256': source_snapshot(ROOT, scope='fresh'), 'source_scope': scope['prefixes'],
                'source_suffixes': scope['suffixes'], 'source_json_prefixes': scope['json_prefixes'],
                'files': files, 'campaign_id': identity['campaign_id'], 'alias': alias,
                'dataset_root': dataset_root}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('colab_bundle_manifest.json', json.dumps(manifest, indent=2))
        bundle.write(SESSION_MODULE, 'colab_session.py')
        for path in paths:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    print(json.dumps({'notebook': str(args.notebook), 'bundle': str(args.output),
                      'bundle_bytes': args.output.stat().st_size, 'files': len(files)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
