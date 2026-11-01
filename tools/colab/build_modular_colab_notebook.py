"""Build a Colab companion without overwriting the original tutorial notebook."""
from __future__ import annotations

import json
import hashlib
import zipfile
from pathlib import Path

from uc3m.application.training.context import repository_revision
from uc3m.application.training.preflight import _source_paths, dataset_digest, source_snapshot


ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb'
DESTINATION = ROOT/'examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb'


def cell(kind, source):
    result = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True),
              'id': 'modular-' + hashlib.sha256(source.encode('utf-8')).hexdigest()[:12]}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result


def build_notebook(original, expected_dataset_hash):
    setup = next(''.join(item['source']) for item in original['cells']
                 if item['cell_type'] == 'code' and '# 1.3 Instalar dependencias' in ''.join(item['source']))
    cells = [cell('markdown', '''# MADRL · Entrenamiento modular en Google Colab

Complemento del tutorial original: reutiliza su instalación Python 3.9 y el
constructor original de argumentos HAPPO/MASAC/MATD3/MAAC. No sustituye ni
sobrescribe sus 77 celdas. E1–E3, 50 episodios de 8760 pasos por defecto.

No exige Colab Pro: detecta recursos reales y reduce concurrencia. A100/H100
pueden usar las dos fases de hasta seis procesos cuando CPU/RAM/VRAM lo permiten.
La disponibilidad de GPU y duración de sesión depende de Colab.

**Importante:** los cambios locales aún no publicados NO aparecen al clonar
GitHub. Subir el paquete `colab_modular_overlay.zip` entregado junto a este
notebook; contiene código y dataset actuales, sin entornos ni credenciales.
No ejecutar los lanzadores originales y este simultáneamente sobre la misma salida.
'''), cell('code', '''# 1. Subir paquete local y reconstruir el checkout exacto
from google.colab import files
from pathlib import Path, PurePosixPath
import io, json, subprocess, zipfile, os

uploaded = files.upload()
payload = uploaded.get('colab_modular_overlay.zip')
if payload is None:
    raise RuntimeError('Sube colab_modular_overlay.zip generado en tu proyecto local')
with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
    BUNDLE_MANIFEST = json.loads(bundle.read('colab_bundle_manifest.json'))
    PROJECT_ROOT = Path('/content/MADRLCitytleranflexresdr')
    if not PROJECT_ROOT.exists():
        subprocess.run(['git', 'clone', '--recursive',
            'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git', str(PROJECT_ROOT)], check=True)
        subprocess.run(['git', 'checkout', BUNDLE_MANIFEST['commit']], cwd=PROJECT_ROOT, check=True)
        subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], cwd=PROJECT_ROOT, check=True)
    origin = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=PROJECT_ROOT, text=True).strip()
    if origin != 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git':
        raise RuntimeError('Origen equivocado; no se aplica el paquete')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, text=True).strip()
    if head != BUNDLE_MANIFEST['commit']:
        raise RuntimeError('El checkout existente es de otra revisión. Usa un runtime limpio, no se sobrescribe.')
    for entry in bundle.infolist():
        name = PurePosixPath(entry.filename)
        if name.is_absolute() or '..' in name.parts:
            raise RuntimeError('Ruta insegura dentro del paquete')
        target = (PROJECT_ROOT/entry.filename).resolve()
        target.relative_to(PROJECT_ROOT)
        if not entry.is_dir():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.read(entry))
os.chdir(PROJECT_ROOT)
print('Código y dataset preparados; instalar dependencias en la celda siguiente.')
'''), cell('markdown', '## 2. Instalación original del proyecto\nSe reutiliza literalmente la celda Python 3.9 del tutorial original.\n'),
        cell('code', setup), cell('code', '''# 3. Destino persistente y comprobación del paquete
from google.colab import drive
drive.mount('/content/drive')
import json, subprocess
from pathlib import Path

PYTHON = PROJECT_ROOT/'.venv39-citylearn-v3/bin/python'
if not PYTHON.is_file():
    raise RuntimeError('No existe el Python 3.9 del proyecto; revisar la instalación original')
OUTPUT_ROOT = Path('/content/drive/MyDrive/MADRL_modular_training')
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
code = """from pathlib import Path
from uc3m.application.training.preflight import dataset_digest
from uc3m.application.training.lock import run_lock
import json
root=Path('/content/MADRLCitytleranflexresdr')
manifest=json.loads((root/'colab_bundle_manifest.json').read_text())
schema=root/'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
assert dataset_digest(schema)==manifest['dataset_sha256'], 'Dataset diferente al paquete local'
with run_lock(Path('/content/drive/MyDrive/MADRL_modular_training/.preflight.lock')):
    print('Dataset y bloqueo de persistencia verificados')
"""
subprocess.run([str(PYTHON), '-c', code], cwd=PROJECT_ROOT, check=True)
'''), cell('markdown', '''## 4. Preparar campaña: no inicia entrenamiento

Revisar el presupuesto detectado y `colab_campaign.json`. La misma combinación
de datos, código, argumentos y semilla tiene identidad estable. Cambiar buffers,
redes o recursos efectivos crea otro tratamiento; no mezclar sus estadísticas.
'''), cell('code', '''N_EPISODES = 50
EPISODE_STEPS = 8760
SEEDS = [0]  # Para la campaña multisemilla, declarar aquí las semillas previstas.
BASE_COMMAND = [str(PYTHON), '-m', 'uc3m.application.training.colab',
    '--output-root', str(OUTPUT_ROOT), '--episodes', str(N_EPISODES),
    '--episode-time-steps', str(EPISODE_STEPS), '--seeds', *map(str, SEEDS)]
subprocess.run(BASE_COMMAND, cwd=PROJECT_ROOT, check=True)
print((OUTPUT_ROOT/'colab_campaign.json').read_text()[:6000])
'''), cell('markdown', '''## 5. Lanzamiento explícito y reanudación

Se conserva el orden original: HAPPO+MASAC, después MATD3+MAAC. La concurrencia
se limita según recursos medidos. No hay desconexión automática ni compra de
unidades. `RUN_TRAINING=False` evita iniciar una campaña por ejecutar todo.
'''), cell('code', '''RUN_TRAINING = False
if RUN_TRAINING:
    subprocess.run(BASE_COMMAND + ['--execute', '--resume'], cwd=PROJECT_ROOT, check=True)
else:
    print('Campaña preparada. Activa RUN_TRAINING solo después de revisar el plan.')
'''), cell('code', '''# 6. Monitor embebido: no expone puertos públicos ni túneles
import pandas as pd
code = "from pathlib import Path; import json; from uc3m.application.training.monitor import list_runs; print(json.dumps(list_runs(Path(" + repr(str(OUTPUT_ROOT)) + "))))"
result = subprocess.check_output([str(PYTHON), '-c', code], cwd=PROJECT_ROOT, text=True)
display(pd.DataFrame(json.loads(result)))
'''), cell('markdown', '''## Alcance de validación

Preparado y probado estructuralmente en local. No se ha ejecutado una sesión
real de Colab desde esta entrega. Un smoke no sustituye campaña completa,
reanudación del optimizador/RNG/replay ni selección científica del ganador.

Sustento: Charbonnier (2023), tesis doctoral, https://doi.org/10.5287/ora-ovzyxredj;
Costea (2026), tesis de maestría, https://webthesis.biblio.polito.it/40396/;
Pineau et al. (2021), JMLR, https://www.jmlr.org/papers/v22/20-303.html .
Recursos Colab: https://research.google.com/colaboratory/faq.html .
''')]
    return {'nbformat': 4, 'nbformat_minor': 5,
            'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                         'colab': {'name': DESTINATION.name}, 'accelerator': 'GPU',
                         'expected_dataset_sha256': expected_dataset_hash}, 'cells': cells}


def main():
    commit, submodules = repository_revision(ROOT)
    schema = ROOT/'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
    digest = dataset_digest(schema)
    notebook = build_notebook(json.loads(ORIGINAL.read_text(encoding='utf-8')), digest)
    DESTINATION.write_text(json.dumps(notebook, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
    bundle_path = ROOT/'outputs/colab_delivery/colab_modular_overlay.zip'
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'commit': commit, 'submodules': submodules,
                'dataset_sha256': digest, 'source_sha256': source_snapshot(ROOT)}
    paths = set(_source_paths(ROOT))
    paths.update(path for path in schema.parent.rglob('*') if path.is_file() and path.suffix in {'.csv', '.json'})
    paths.update(path for path in (ROOT/'pyproject.toml', ROOT/'requirements.txt') if path.is_file())
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('colab_bundle_manifest.json', json.dumps(manifest, indent=2))
        for path in sorted(paths):
            bundle.write(path, path.relative_to(ROOT).as_posix())
    print(json.dumps({'notebook': str(DESTINATION), 'bundle': str(bundle_path),
                      'bundle_bytes': bundle_path.stat().st_size}))


if __name__ == '__main__':
    main()
