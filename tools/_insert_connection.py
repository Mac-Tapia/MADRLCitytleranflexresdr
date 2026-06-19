"""
Insert Paso 0 connection cells into the notebook.
Two cells inserted AFTER launch_guide (index 1):
  - con0header (markdown): guide for connecting VS Code → Colab A100
  - con0verify  (code):    runtime verification cell
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
nb_path = REPO_ROOT / 'CityLearn' / 'examples' / 'madrl_citylearn_v3_tutorial.ipynb'
nb = json.load(open(nb_path, encoding='utf-8'))
cells = nb['cells']

# Guard: don't insert twice
if any(c['id'] == 'con0header' for c in cells):
    print('con0header already present — skip')
else:
    guide_idx = next(i for i, c in enumerate(cells) if c['id'] == 'launch_guide')

    # ── Markdown header cell ──────────────────────────────────────────────────
    md_source = """\
## Paso 0: Conectar VS Code al runtime A100 de Google Colab

> Haz este paso **UNA SOLA VEZ** antes de ejecutar cualquier celda.
> No se necesita ngrok ni tunnels: la extension `google.colab` de VS Code
> maneja la conexion directamente con tu cuenta de Google.

---

### 0.1  Seleccionar el kernel Colab en VS Code

1. Abre este notebook en VS Code
   (`CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb`)
2. Haz clic en **"Select Kernel"** (esquina superior derecha del notebook)
3. En el menu emergente elige **"Google Colab"**
   (aparece gracias a la extension `google.colab` ya instalada)
4. Si pide autenticacion → inicia sesion con **mac.tapia.c@uni.pe**
5. En la lista de runtimes elige **"New runtime (A100)"**
   *(requiere Colab Pro+ activo en esa cuenta)*

> Si no ves "Google Colab" en el selector: abre la paleta de comandos
> (`Ctrl+Shift+P`) y escribe **"Colab: Sign In"**, autentica, luego repite.

---

### 0.2  Verificar la conexion

Ejecuta la celda de codigo siguiente. Debe mostrar:
```
GPU: Tesla A100-SXM4-40GB   RAM: ~83 GB   Tipo: Colab
```
Si muestra otra GPU o error → vuelve al paso 0.1 y verifica el tipo de runtime.

---

### 0.3  Flujo de trabajo diario

```
VS Code (editor local)
       │
       │  google.colab extension
       ▼
Colab A100 runtime (servidor Google)
  /content/MADRLCitytleranflexresdr/   ← repo clonado en celda 1.2
  /content/drive/MyDrive/MADRL_*/      ← checkpoints en Google Drive
```

- El **codigo se ejecuta en el A100** de Google, no en tu maquina local.
- Los **outputs y graficas** aparecen directamente en VS Code.
- Si Colab desconecta: repetir 0.1, luego reanudar desde celda 1.2.
"""

    verify_source = """\
# ── 0.verify  Verificar conexion al runtime A100 ───────────────────────────
import subprocess, os, sys, platform

def check_connection():
    # 1. GPU
    try:
        result = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        gpu_name, gpu_mem = result.split(',')
        gpu_ok = 'A100' in gpu_name
        print(f"{'[OK]' if gpu_ok else '[WARN]'} GPU    : {gpu_name.strip()}  ({int(gpu_mem.strip()):,} MB)")
        if not gpu_ok:
            print("       ⚠  No es A100. Cambia el runtime en Colab → Runtime > Change runtime type → A100")
    except Exception as e:
        print(f"[FAIL] GPU    : nvidia-smi no disponible ({e})")

    # 2. RAM
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if 'MemTotal' in line:
                    mem_gb = int(line.split()[1]) // 1024 // 1024
                    print(f"[OK] RAM    : ~{mem_gb} GB")
                    break
    except Exception:
        pass

    # 3. Python & runtime type
    print(f"[OK] Python : {sys.version.split()[0]}  ({platform.system()} {platform.machine()})")

    # 4. Google Drive availability
    drive_ok = os.path.exists('/content/drive/MyDrive')
    print(f"{'[OK]' if drive_ok else '[--]'} Drive  : {'montado en /content/drive/MyDrive' if drive_ok else 'no montado (ejecuta celda 1.5)'}")

    # 5. Colab environment
    try:
        import google.colab
        print("[OK] Entorno: Google Colab")
    except ImportError:
        print("[INFO] Entorno: NO es Colab (kernel local u otro)")

    # 6. CUDA
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        if cuda_ok:
            print(f"[OK] CUDA   : {torch.version.cuda}  device={torch.cuda.get_device_name(0)}")
        else:
            print("[WARN] CUDA  : torch disponible pero CUDA no detectado")
    except ImportError:
        print("[--] CUDA   : torch no instalado aun (normal antes de celda 1.3)")

check_connection()
"""

    # Insert verify cell first (so it ends up AFTER the markdown when both are inserted)
    verify_cell = {
        'cell_type': 'code',
        'id': 'con0verify',
        'metadata': {},
        'outputs': [],
        'source': verify_source.splitlines(keepends=True),
    }
    md_cell = {
        'cell_type': 'markdown',
        'id': 'con0header',
        'metadata': {},
        'source': md_source.splitlines(keepends=True),
    }

    # Insert markdown first (after launch_guide), then verify after markdown
    cells.insert(guide_idx + 1, md_cell)
    cells.insert(guide_idx + 2, verify_cell)

    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    print(f'Inserted con0header at {guide_idx+1}, con0verify at {guide_idx+2}')

print(f'Total cells: {len(nb["cells"])}')
