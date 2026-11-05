# Inventario exhaustivo: lectura mecánica completa, revisión de contenido todavía no

**Todavía no cumplí del todo tu pedido.** Cada archivo se leyó por máquina hasta el final, pero yo solo he revisado por dentro una pequeña parte.

| Nivel de cobertura | Alcance | Estado |
|---|---|---|
| Lectura mecánica hasta el final (hash, tamaño, líneas) | 14.734 archivos, 7,2 GiB, submódulos incluidos | ✅ 100 %, 0 ilegibles |
| Análisis estructural (duplicados, referencias, huérfanos, sintaxis) | Código y documentos propios versionados y sin versionar; los duplicados abarcan también lo ignorado | ✅ Completo |
| Revisión de contenido, línea por línea | 773 archivos propios de código y documentación, 140.917 líneas | ⚠️ Unos 30 archivos, cerca del 4 % |
| Revisión de contenido de submódulos | Unas 431.000 líneas | ❌ Solo rutas puntuales |

Quedan fuera solo `.git` y el entorno virtual (contados, sin hash) y 20 enlaces locales que no seguí. No borré ni moví nada; lo único nuevo es una nota de memoria con tu criterio de cobertura.

## 🔴 Lo más urgente: sesión de navegador dentro del proyecto

En `tools/skills/notebooklm-mcp/data/` hay un **perfil completo de navegador**, con `Login Data`, `state.json` y `auth_info.json`. **No abrí esos archivos.**

- **Lo tranquilizador:** está ignorado por Git, no aparece en el historial, no va en `colab_modular_overlay.zip` y el `Dockerfile` raíz solo copia carpetas concretas que no lo incluyen.
- **El riesgo:** cualquier copia o zip manual de la carpeta se lleva una sesión de Google, y el repositorio es público.

Recomiendo moverlo fuera del proyecto. Esa decisión es tuya, porque cerraría la sesión de esa herramienta.

## Hallazgos por categoría

### Fallas
- **Pruebas:** 1088 de 1093 aprobadas y 5 fallidas, según la corrida de la otra sesión. Excluye 4 microentrenamientos reales.

| Prueba que falla | Causa |
|---|---|
| `test_declared_dependencies_cover_runtime_imports` | Imports sin dependencia declarada |
| `test_real_repository_indexes_have_no_active_broken_reference` | 4 referencias rotas en índices activos |
| `test_root_contains_only_project_files` | El `.docx` de tesis está en la raíz |
| `test_inventory_lists_every_file_still_referencing_the_retired_campaign` | `historical_inventory.py` sigue nombrando la campaña retirada |
| `test_consolidate_execute_only_on_matching_plan_in_temp_copy` | Sale con código 1 y sin mensajes; sin diagnosticar |

- **Lint:** `ruff` da 3 errores en el ámbito de CI, y CI lo trataría como fallo.
- **`bandit`:** 1 aviso alto (MD5 en una herramienta obsoleta) y 6 medios (4 `torch.load`, 2 `urlopen`).
- **Pruebas sin aserción visible:** `test_reset_pareto_clears` y `test_set_baseline` son candidatas a revisar. Otras dos solo compilan celdas, lo cual es válido.
- **Lo ya informado:** siguen abiertos los P0 de la puerta de aceptación, Drive y CI.

### Faltantes
- **Referencias rotas:** 170 en documentos, repartidas sobre todo en `docs/plans/` y `README.md`. Muchas son rutas históricas o de ejecución, no defectos; el conjunto activo confirmado por prueba son 4.
- **Planes sin estado real:** los 11 de `docs/plans/` suman **519 tareas abiertas y 0 cerradas**, aunque gran parte del código existe, así que esas casillas no informan el avance. Las specs tienen otras 34 abiertas.
- **Dependencia sin gobierno:** `external/off-policy` (117 archivos, tiene `LICENSE`) está copiado dentro del repositorio. `uc3m` lo usa, pero no está en `.gitmodules` ni en `[tool.uc3m.local-dependencies]`.
- **Herramienta prometida que no existe:** `tools/training/export_winning_model_onnx.py`.
- **LFS:** `STATUS.md` dice que está configurado, pero hay 0 archivos en LFS.
- **Corrección a mi informe anterior:** dije que `docs/failures/` no existía, pero no lo verifiqué bien. Lo seguro es que no hay notas de fallos versionadas.

### Vacíos
- **Carpetas vacías:** 51. La mayoría está en `.superpowers/` y en el perfil de navegador; 4 son `CityLearn/pytest-cache-files-*`.
- **Marcadores sin terminar:** 53 `NotImplementedError` (sin clasificar, pueden estar en código de terceros), 14 `placeholder`, 9 `pending_owner` y 2 `TODO`.
- **Contratos sin usar:** `SimulatorPort` no tiene consumidores y `REGISTER_MAP` de Modbus está vacío.

### Cuellos de botella
- **Guarda de contexto:** tardó **43 s** en mi medición, y `AGENTS.md` la exige antes de cada edición u operación Git. **El escaneo que incluye el perfil de navegador tarda 15 s y sin él cerca de 0 s** (una sola medición, posible efecto de caché). El resto no está explicado.
- **Suite de pruebas:** 60 minutos. `test_names` y `test_historical_retirement` suman 1108 s, el 31 %; según la auditoría previa, el segundo invoca esa guarda antes de cada borrado.
- **Hash en memoria:** `directory_digest` carga cada archivo entero en RAM, y hay checkpoints de 144 a 259 MiB.
- **Tamaño de `.git`:** 5,6 GiB. Los blobs de 101 MiB no están en la historia de HEAD, pero sí blobs de 31 MiB de resultados v4 retirados.
- **Ya informados:** los requisitos de memoria de MASAC y la reserva de recursos por fase (H03, H04).

### Obsoletos
- **Declarados y sin retirar:** 27 herramientas clasificadas como obsoletas en `evaluation_tools_inventory.json` siguen presentes, y otras 16 esperan tu decisión.
- **Scripts que nadie nombra:** 48, de ellos 21 en `tools/thesis/`. Pueden ser de uso manual, así que no significa que sobren. `patch_cap6_conclusiones_desc_inf_docx.py` y `patch_resumen_align_kpi_gains_docx.py` tienen contenido único: **no borrarlos**.
- **Con señales de ser antiguos, por confirmar:**
  - `configs/experiments/full_campaign_4x3x3.yaml`
  - `scripts/quality/run_orchestration_gates.ps1`
  - `docs/workflow_manifest.json` (lo citan 16 archivos)
  - el tutorial que aún nombra el perfil v5
  - el `Dockerfile`, que apunta a `deploy/aws/training`, ya retirado

### Duplicados
- **Exactos:** 1090 grupos y 2,3 GiB redundantes; 905 grupos son solo datos. **No hay que deduplicar por hash**, porque la auditoría previa advierte que las generaciones de dataset tienen identidades distintas.
- **Código copiado:**
  - `build/lib/uc3m` es idéntico a `uc3m` (0 diferencias).
  - `docs/audits/deep_20261101/inspection_cut/` contiene 17 archivos versionados, entre ellos copias de `uc3m`.
- **Mismo nombre, distinto archivo, confunde al buscar:**
  - `entrenamiento.md` ×3
  - `colab.md`, `modernizacion.md`, `encargo.md` y `test_model_selection.py` ×2 cada uno
- **No son duplicados reales:** según la auditoría previa, los pares entre `scripts/` y `tools/` son fachadas válidas.

### Desorganizados
- **Pruebas fuera de `tests/`:** 4 archivos que `pytest` no recoge por defecto, incluido `tools/training/test_job_resume_state.py` con 1575 líneas y `deploy/inference/test_app.py`.
- **`docs/` sin orden:** 15 archivos sueltos en la raíz, que mezclan análisis, Word, PDF y manifiestos.
- **Scripts desordenados:** `scripts/` tiene 10 sueltos, con funciones que se solapan con `tools/`.
- **Funciones gigantes:** `build` tiene 1096 líneas y `run_checks` 445.
- **Paquetes de auditoría en el historial:** `docs/audits/` ocupa 12 MiB, con logs y copias de código.

### Sueltos
| Elemento | Tamaño | Nota |
|---|---|---|
| `.superpowers/sdd/` | 2,9 GiB | **3 pruebas dependen de él**, no borrar sin resolverlo antes |
| `data/maintenance/` | 1,4 GiB | Ignorado; sin revisar qué conserva |
| `outputs/dataset_cache/` | 360 MiB | Regenerable |
| `.git/objects/*/tmp_obj_*` | 33 MiB | Restos de operaciones interrumpidas |
| `build/`, `uc3m.egg-info/`, `.ruff_cache/` | Pequeño | Derivados, regenerables |
| `external/MAAC/.git_commit_msg.tmp` | Mínimo | Ensucia el submódulo |
| `CityLearn/pytest-cache-files-*`, `CityLearn/render_logs/` | Vacíos | Restos dentro del submódulo |
| `docs/audits/architecture_thesis_20261101/` | 5,5 MiB | Trabajo de otra sesión, sin confirmar |

## Decisión pendiente

**¿Autorizas una revisión con varios agentes para leer los 773 archivos propios hasta el final?** Solo así puedo cumplir lo que pediste con una cobertura verificable.

- **Cómo sería:** hasta 10 agentes de solo lectura, cada uno con una parte del registro. Cada archivo queda marcado como revisado y un paso final comprueba que no falte ninguno.
- **Costo aproximado:** unos 2 millones de tokens de lectura, una estimación a partir de las líneas contadas.
- **Submódulos:** aparte. Recomiendo incluir solo `CityLearn` y los backends propios (HARL, MAAC, MARL, MATD3), que suman unas 161.000 líneas. Dejaría fuera `evcc`, `MARLlib`, `MicroGrids` y `prosumpy`, porque la ruta canónica no pasa por ellos o no lo he confirmado; lo verificaría antes de lanzar.
- **Si prefieres gastar menos:** empiezo por `uc3m/`, `configs/`, `scripts/`, `deploy/` y `governance/`, unas 22.000 líneas, y lo hago yo sin agentes.

Para lanzarla basta con que respondas «usa un workflow». Avísame también si `pip-audit` entra: sigue sin ejecutarse, porque enviaría la lista de paquetes a un servicio externo.

El registro por archivo y el inventario completo están en:
- `C:\Users\LENOVO~1\AppData\Local\Temp\claude\d--MADRLCitytleranflexresdr\865ad199-53fa-4aa9-acc3-c3dfb37f0edd\scratchpad\ledger.csv`
- `C:\Users\LENOVO~1\AppData\Local\Temp\claude\d--MADRLCitytleranflexresdr\865ad199-53fa-4aa9-acc3-c3dfb37f0edd\scratchpad\inventory.json`
