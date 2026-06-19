"""Insert launch guide markdown cell into notebook."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
nb_path = REPO_ROOT / 'CityLearn' / 'examples' / 'madrl_citylearn_v3_tutorial.ipynb'
nb = json.load(open(nb_path, encoding='utf-8'))

guide_source = """\
## Guia Rapida de Lanzamiento en Colab A100

> **Tiempo estimado:** ~30 h para 75 episodios completos (12 corridas).
> **Prerequisito:** Runtime tipo A100 activado antes de ejecutar celda 1.1.

---

### Paso 1 — Seleccionar runtime A100

En Colab: **Entorno de ejecucion > Cambiar tipo de entorno de ejecucion**
Acelerador de hardware: **A100 GPU** (requiere Colab Pro+)

---

### Paso 2 — Ejecutar la configuracion inicial (Seccion 1)

| Celda | Accion |
|-------|--------|
| **1.1** | Verificar GPU — debe mostrar `Tesla A100-SXM4-40GB` |
| **1.2** | Clonar repo + submodulos (`--recurse-submodules --depth 1`) |
| **1.3** | Instalar dependencias (`pip install -e CityLearn/ external/HARL/ ...`) |
| **1.4** | Configurar `sys.path`, CUDA env y smoke imports |
| **1.5** | Montar Google Drive (recomendado para persistencia de checkpoints) |

---

### Paso 3 — Configurar rutas de salida (Seccion 2)

Ejecutar **celda 2.1** — genera `OUTPUT_ROOT` con timestamp.
Si Drive esta montado, los artefactos van a `MyDrive/MADRL_CityLearn_v3/colab_madrl_a100_<timestamp>/`.

---

### Paso 4 — Verificar dataset y entorno (Secciones 3-5)

Opcional pero recomendado en la primera corrida:

- **3.1** Verificar 222 CSV, 17 edificios, 26 304 pasos.
- **4.1** Smoke-test del entorno Dec-POMDP (4 pasos, 17 agentes).
- **5.1** Ver pesos de recompensa por escenario E1/E2/E3.

---

### Paso 5 — Configurar hiperparametros (Seccion 6)

Ejecutar **celda 6.1**. Variables clave:

```python
QUICK_TEST = False   # True = 3 ep (prueba infra), False = 75 ep (real)
EPISODES   = 75      # episodios por corrida
GPU_PROFILE = 'aws'  # perfil memoria CUDA para A100
```

---

### Paso 6 — Lanzar entrenamiento (Seccion 7)

| Celda | Accion | Duracion aprox. |
|-------|--------|-----------------|
| **7.0** | Cargar helpers de ejecucion | < 1 s |
| **7.1** | **Dry-run / Preflight** — valida A100 + 12 jobs | ~ 20 s |
| **7.2** | **Lanzar entrenamiento completo** (75 ep x 12 corridas) | ~ 30 h |
| **7.3** | Monitor manual (puede ejecutarse mientras corre) | en cualquier momento |

> Si Colab se desconecta: vuelve a ejecutar 1.1 → 1.5 → 2.1 → 6.1 → 7.0 → 7.2.
> `--skip-completed` detecta jobs ya terminados y los omite automaticamente.

---

### Paso 7 — Analisis de resultados (Secciones 8-9)

| Celda | Accion |
|-------|--------|
| **8.1** | Cargar `results.json` de 12 corridas → DataFrame de KPIs |
| **8.2** | Curvas de convergencia por algoritmo y escenario |
| **9.1** | Suite estadistica: Kruskal-Wallis, Mann-Whitney U, ranking global |
| **10** | Resumen final de la sesion |

---

### Estructura de artefactos generados

```
OUTPUT_ROOT/
  happo/E1_seed_0/data/results.json        # KPIs finales
  happo/E1_seed_0/data/timeseries.csv      # reward por paso
  happo/E1_seed_0/checkpoints/ep_*.pt      # modelos guardados
  happo/E1_seed_0/figures/*.png            # 13 graficas
  masac/E1_seed_0/...
  matd3/E1_seed_0/...   <- ganador corrida v4
  maac/E1_seed_0/...
  official_full_status.json                # estado global 12 jobs
  live_progress.json                       # ultimo snapshot en tiempo real
```

---

### Reanudacion rapida tras desconexion

```python
# Pegar en celda nueva de Colab; OUTPUT_ROOT debe apuntar al directorio ya creado
OUTPUT_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3/<tu_timestamp>'
# Luego ejecutar en orden: 1.2 -> 1.3 -> 1.4 -> 1.5 -> 6.1 -> 7.0 -> 7.2
```
"""

guide_cell = {
    'cell_type': 'markdown',
    'id': 'launch_guide',
    'metadata': {},
    'source': guide_source.splitlines(keepends=True),
}

cells = nb['cells']

# Check if already inserted
if any(c['id'] == 'launch_guide' for c in cells):
    print('launch_guide already exists — skipping insert')
else:
    title_idx = next(i for i, c in enumerate(cells) if c['id'] == '140637d5')
    cells.insert(title_idx + 1, guide_cell)
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f'Inserted launch_guide at index {title_idx + 1}')

print(f'Total cells: {len(nb["cells"])}')
