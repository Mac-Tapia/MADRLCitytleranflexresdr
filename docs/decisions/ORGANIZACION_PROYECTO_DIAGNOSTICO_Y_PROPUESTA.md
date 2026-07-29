# Diagnóstico y propuesta de organización del proyecto

> **Nota 2026-07-29:** propuesta histórica (jun-2026). `tools/reports/` ya no existe; equivalentes actuales en `tools/dataset/` y `tools/training/` (ver `AUDITORIA_TOOLS_2026-07-29.md`).

Fecha: 2026-06-13
Alcance: `D:\MADRLCitytleranflexresdr` (repo principal `uc3m` + submódulo `CityLearn` + dependencias en `external/`)

Este documento responde a tres preguntas: qué es el proyecto y cómo está armado hoy, qué problemas de organización tiene, y cómo reestructurarlo para que sea mantenible, escalable, entendible y alineado con buenas prácticas — sin romper el flujo operativo ni los entrenamientos en curso descritos en `docs/workflow_manifest.json`.

No se ha movido ningún archivo. Esto es diagnóstico + propuesta para decidir y ejecutar por fases.

---

## 0. Estado de ejecución (actualizado 2026-06-13)

La propuesta fue ejecutada en esta misma fecha, con la corrida oficial `outputs/citylearn_v3_madrl_full_20260613_010234` activa (`status=running`) durante todo el proceso. Resultado por fase:

- **Fase 0** — completada (verificación de contexto previa).
- **Fase 1** — completada: `build/`, `dist/`, `__pycache__/`, `.pytest_cache/`, `uc3m.egg-info/` quedaron marcados para borrado pero **no pudieron eliminarse** por una restricción de permisos del montaje cross-OS ("Operation not permitted"); requieren borrado manual desde Windows. `diagnostico_dataset.py`/`ver_metricas_madrl.py` → `tools/reports/`. `tools/skills/*` → `agent-skills/` (el directorio `tools/skills/` quedó vacío, no se pudo `rmdir` por la misma razón).
- **Fase 2** — completada: `docs/` reorganizado en `architecture/`, `audits/`, `decisions/`, `thesis/`, `contributions/`; `docs/00_INDEX.md` creado; referencias actualizadas en `README.md`, `ESTRATEGIA_3PILARES_MADRL.md`, `tools/ops/verify_workflow_integrity.py` y `docs/workflow_manifest.json`. Los 4 `PLAN_TESIS_*.docx` quedaron documentados en `00_INDEX.md` como pendientes de consolidación (no se fusionaron, por ser binarios).
- **Fase 3** — completada: se creó `outputs/runs/` (vacío, para corridas futuras) y `outputs/_archive/` con las corridas obsoletas/fallidas/stale. La corrida activa se dejó **en `outputs/` raíz** (no en `runs/`) para no perturbar sus file handles abiertos mientras `status=running`; `docs/workflow_manifest.json` documenta esta decisión en `archive_layout_note`. `outputs/dataset_cache/` (962 MB) → `data/cache/`, añadido a `.gitignore`.
- **Fase 4** — **diferida**: no se reorganizó `scripts/` físicamente por el riesgo de romper los `.ps1` que la corrida activa pudiera invocar (todos resuelven `$ProjectRoot` vía `..` desde `$PSScriptRoot`). Se documentó el plan completo de migración en `scripts/README.md`.
- **Fase 5** — completada: `tests/citylearn_v3/` creado con `conftest.py` + `test_schema_smoke.py` (4 tests, todos pasan).
- **Fase 6** — **diferida**: no se subdividió `tools/` por riesgo de romper referencias cruzadas y llamadas `subprocess` con rutas hardcodeadas desde el orquestador. Plan documentado en `tools/README.md`.
- **Fase 7** — completada como **scaffolding local** (sin crear forks reales en GitHub, por decisión del usuario): plantillas `CHANGES.md` + `bibliografia.bib` creadas para los 9 submódulos en `docs/contributions/`, y sección `modified_submodules` añadida a `docs/workflow_manifest.json`.
- **Fase 8** — completada como **scaffolding local** (sin desplegar a AWS, por decisión del usuario): `deploy/` con `inference/` (FastAPI + ONNX + modo stub), `plant-adapter/` (replay + esqueleto Modbus), `dashboard/` (Streamlit), `docker-compose.yml`/`docker-compose.aws.yml`, `aws/iac/` (Terraform esqueleto, no aplicado) + `aws/README_DEPLOY_AWS.md`, y `edge/README_DESPLIEGUE_FISICO.md`.

**Verificación final:** `pytest tests/citylearn_v3/` → 4/4 OK. La corrida `outputs/citylearn_v3_madrl_full_20260613_010234` permanece `status=running` sin alteraciones. `docs/workflow_manifest.json` es JSON válido (verificado vía editor; el mount bash de esta sesión muestra una versión cacheada/obsoleta del archivo — limitación del entorno, no del contenido real).

**Desviaciones respecto a "ejecutar todo"**: Fases 4 y 6 se diferieron (solo `README.md` con plan), priorizando no interrumpir el entrenamiento activo sobre la ejecución literal completa.

---

## 1. Qué es el proyecto (lectura del estado actual)

Es un proyecto de tesis de MADRL (Multi-Agent Deep RL) para gestión energética de una comunidad de 17 edificios reales de Iquitos, construido sobre tres capas:

1. **`CityLearn/`** — fork propio (submódulo git, rama `citylearn-v3-madrl`) de CityLearn v2, con una capa adicional `citylearn/v3/` (Dec-POMDP, config, backends, objetivos) y `scripts/` con los entrenadores oficiales (HAPPO/MASAC/MATD3/MAAC), launchers PowerShell, monitores y generadores de evidencia para la tesis.
2. **`uc3m/`** — paquete Python propio ("Universal CityLearn v3 Modified"), instalable (`pyproject.toml`, `pip install -e .`), con módulos `env`, `reward`, `kpis`, `algorithms`, `geography`, `configs`, y un entrypoint `uc3m/train.py`. Tiene tests en `tests/uc3m/`.
3. **`external/`** — 9 submódulos de repos de terceros (HARL, MAAC, MARLlib, MATD3implementation, MicroGrids, evcc, prosumpy, etc.) usados como backends/referencias.

Alrededor de esto hay: `tools/` (28 scripts de construcción/auditoría del dataset Iquitos + 2 sub-skills de agente en `tools/skills/`), `docs/` (31 archivos: informes de auditoría, planes de tesis en `.docx`, diagramas, manifest canónico `workflow_manifest.json`), `outputs/` (artefactos de entrenamiento, 1.2 GB), `.cache/` (datos meteorológicos, 756 KB) y varios scripts sueltos en la raíz (`.bat`, `.ps1`, `.py`).

El flujo oficial ya está documentado de forma excelente en `docs/workflow_manifest.json` y `docs/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md`: dataset → gate de calidad → entrenamiento (12 jobs = 4 algoritmos × 3 escenarios) → comparación vs CityLearn v2 → evidencia estadística para la tesis. `AGENTS.md` define límites estrictos de proyecto (no tocar `D:\madrl_lima`, verificar contexto antes de cualquier edición/git, no editar `CityLearn/`/`external/` sin permiso explícito).

**Conclusión:** el *diseño conceptual* (UC3M, Meta-Dec-POMDP, ejes de recompensa, manifest canónico) está muy maduro y bien documentado. El problema no es de diseño científico, sino de **higiene de repositorio y organización de artefactos**, que ya empieza a generar fricción (el propio `AUDITORIA_TECNICA` y `workflow_manifest.json` tienen que explicar reglas para "qué carpeta de outputs es la vigente" y "qué documentos quedaron obsoletos").

---

## 2. Diagnóstico

### 2.1 Fortalezas (a preservar)

- Separación conceptual clara entre framework reutilizable (`uc3m/`), simulador (`CityLearn/`) y dependencias externas (`external/`), con `uc3m` empaquetado correctamente (`pyproject.toml`, extras `train`/`dataset`/`dev`, tests con pytest+coverage).
- `docs/workflow_manifest.json` es un manifest canónico machine-readable: ya es la pieza correcta para "single source of truth" del pipeline. Es el mejor activo organizativo que tiene el proyecto.
- `AGENTS.md` define límites de proyecto y un script de verificación de contexto (`scripts/verify_project_context.ps1`) — buena práctica poco común, hay que conservarla y reforzarla.
- Submódulos git usados correctamente para dependencias externas (`.gitmodules` con 9 entradas) en lugar de copiar código de terceros.
- `tests/uc3m/` cubre los módulos centrales del framework (bact, hphi, kpis, reward axes, algorithm factory, env).

### 2.2 Problemas identificados

**A. Entorno virtual dentro del repo de trabajo**
El proyecto mantiene un único entorno local canónico: `.venv39-citylearn-v3/` con Python 3.9 para CityLearn v3, Ray 1.8 y PyTorch CUDA. El entorno genérico `.venv/` fue eliminado porque usaba Python 3.14, no tenía `pip` funcional y no cargaba el stack CityLearn. `scripts/verify_project_context.ps1` falla si aparece cualquier `.venv*` distinto del entorno canónico, para evitar volver a duplicar ambientes.

**B. Artefactos de build/empaquetado obsoletos commiteados junto al código**
`build/lib/uc3m/...` y `dist/uc3m-1.0.0-py3-none-any.whl` son productos de `setup.py build`/`pip wheel`. No deberían vivir en el repo de trabajo; son regenerables y quedan desactualizados respecto a `uc3m/` real (riesgo de confusión: "¿edito `uc3m/train.py` o `build/lib/uc3m/train.py`?").

**C. `outputs/` mezcla datos cacheados, resultados de auditoría, runs vigentes y runs obsoletos**
1.2 GB en `outputs/`, de los cuales `outputs/dataset_cache/` (962 MB) es caché de datos de entrada, no un "resultado". Coexisten `citylearn_v3_madrl_full_*`, `citylearn_v3_madrl_oficial_v6/v7`, `bottleneck_*`, `concurrency_policy_dryrun`, etc. El propio manifest tiene que declarar una `obsolete_reference_policy` con rutas a *no usar* — síntoma claro de que faltan reglas de retención/limpieza automatizadas y de que "resultados de tesis", "runs de depuración" y "caché de dataset" están al mismo nivel.

**D. `docs/` mezcla documentación viva, informes históricos/auditorías puntuales y entregables binarios de tesis**
31 archivos en un solo directorio plano: el manifest canónico (`workflow_manifest.json`), guías de arquitectura vigentes, ~10 informes de auditoría con fecha/versión específica (`INFORME_AUDITORIA_*`, `INFORME_VALIDACION_*`), 4 `.docx` de planes de tesis (versiones V1/V3/V4/evidencia real — historial de versiones de un mismo documento usando el nombre de archivo como control de versiones), diagramas `.png`/`.pdf`, y un `.xlsx` de resultados. No hay manera de distinguir a simple vista "qué documento es la referencia vigente" sin leer `AUDITORIA_TECNICA` o el manifest.

**E. Scripts de orquestación dispersos en 4 ubicaciones distintas**
Hay `.ps1`/`.bat` de entrenamiento/monitoreo en: raíz del repo (`monitor_citylearn_training_visible.bat`, `relanzar_entrenamiento_madrl.bat`, `run_citylearn_training_live_visible.bat`), `scripts/` (6 `.ps1`), `CityLearn/scripts/` (13 `.py` + 6 `.ps1`), y `tools/` (28 `.py`). Algunos nombres son casi duplicados entre raíz y `scripts/` (`monitor_citylearn_training_visible.bat` vs `scripts/monitor_citylearn_training_visible.ps1`), lo que obliga al manifest a documentar explícitamente cuál es "legacy wrapper" vs "primary".

**F. Scripts Python sueltos en la raíz**
`diagnostico_dataset.py` y `ver_metricas_madrl.py` (más su `.pyc` cacheado en `__pycache__/` de la raíz) no pertenecen conceptualmente a la raíz del repo: son herramientas de análisis que deberían vivir junto a `tools/`.

**G. Carpetas de plataforma/herramientas mezcladas en la raíz**
`.vscode/`, `.claude/`, `.sixth/`, `.pytest_cache/`, `__pycache__/` conviven con el código fuente en el nivel superior. La mayoría son artefactos de herramientas (cacheables/ignorables) pero su presencia visual en la raíz compite con las carpetas que sí importan (`uc3m/`, `CityLearn/`, `tools/`, `docs/`, `tests/`).

**H. `tools/` mezcla scripts de pipeline con "skills" de agente**
`tools/skills/` contiene dos skills completas de agente (con `references/`, `scripts/`, `agents/`) dentro de la carpeta de herramientas de dataset. Son cosas de naturaleza distinta (herramientas de pipeline de datos vs. configuración de asistente IA) y mezclarlas dificulta saber qué es parte del pipeline reproducible de la tesis y qué es tooling auxiliar.

**I. Naming inconsistente y muy verboso**
Conviven convenciones `snake_case` en inglés (`train.py`, `wrappers.py`), nombres descriptivos largos en español/mayúsculas para docs (`INFORME_AUDITORIA_DIMENSIONAMIENTO_DER_IQUITOS.md`), scripts con sufijos repetidos (`_citylearn_v3_`, `_madrl_`, `_iquitos_` aparecen en casi todos los nombres de `CityLearn/scripts/`), y carpetas de salida con sufijos ad-hoc (`_oficial_v6`, `_oficial_v7`, `_full_<timestamp>`). Funciona, pero el costo cognitivo de leer/teclear esos nombres es alto y propenso a errores de copy-paste entre rutas casi idénticas.

**J. Doble framework de configuración**
`uc3m/configs/*.yaml` (config propia del framework) y los parámetros del workflow (escenarios, episodios, GPU profile) viven embebidos en `docs/workflow_manifest.json` y en flags de los `.ps1`. No hay un único lugar "config" que ambos consuman; el manifest documenta valores que también existen como YAML/argumentos CLI, con riesgo de que se desincronicen.

**K. Tests solo cubren `uc3m/`, no la capa `CityLearn/citylearn/v3/` ni `tools/`**
`pyproject.toml` fija `coverage source = ["uc3m"]` y excluye `tools/*` y `external/*`. La capa `CityLearn/citylearn/v3/` (config, environment, backends, objectives, marllib_env) — que es donde vive buena parte de la lógica Dec-POMDP/CTDE — no tiene tests visibles ni cobertura configurada, igual que los 28 scripts de `tools/` que construyen el dataset (alto riesgo: son los que generan los datos de entrada de toda la tesis).

### 2.3 Riesgos si no se actúa

- Cada nueva corrida de entrenamiento añade una carpeta más a `outputs/` y otro párrafo más de "reglas de qué ignorar" al manifest — la deuda crece con cada experimento.
- Un colaborador nuevo (o tú en 6 meses) tarda en entender qué documento de `docs/` es la fuente de verdad sin leer primero `AUDITORIA_TECNICA_SKILL_*` completo.
- El riesgo de editar accidentalmente `build/lib/uc3m/` en vez de `uc3m/` (o viceversa) y no notarlo.
- La capa `CityLearn/citylearn/v3/`, sin tests, es la más expuesta a regresiones silenciosas porque alimenta directamente los 12 jobs de entrenamiento oficiales.

---

## 3. Propuesta de organización

Principio guía: **separar por naturaleza del artefacto** (código fuente vs. configuración vs. datos/caché vs. resultados vs. documentación vs. herramientas de entorno), manteniendo intactos los submódulos git (`CityLearn/`, `external/*`) y el contrato del manifest (rutas que el workflow ya espera, para no romper nada operativo).

### 3.1 Árbol propuesto (vista de alto nivel)

```text
MADRLCitytleranflexresdr/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore  (ampliado, ver 3.4)
│
├── uc3m/                         # paquete framework (sin cambios de fondo)
│   ├── env/ reward/ kpis/ algorithms/ geography/
│   ├── configs/                  # YAML por algoritmo + base + escenarios
│   └── train.py
│
├── CityLearn/                     # submódulo (fork propio) — editable como aporte de tesis
├── external/                      # 9 submódulos (forks propios) — editables como aporte,
│                                   #   ver 3.5 para el flujo fork + justificación bibliográfica
│
├── tools/                         # SOLO pipeline de dataset/auditoría (28 scripts)
│   ├── dataset/                   # generate_*, distill_*, calibrate_*, fix_*
│   ├── audit/                     # audit_*, evaluate_*, verify_*, check_*
│   ├── reports/                   # dataset_report.py, deep_dataset_analysis.py,
│   │                               #   diagnostico_dataset.py, ver_metricas_madrl.py
│   └── dataset_docs/              # (igual que hoy)
│
├── agent-skills/                  # ex tools/skills/* — movido fuera del pipeline
│   ├── iquitos-citylearn-dataset/
│   └── madrl-citylearn-thesis-integrated/   (+ literature-review)
│
├── scripts/                       # orquestación operativa (PowerShell/launchers)
│   ├── verify_project_context.ps1
│   ├── training/                  # launch/run/relanzar/resume + .bat de raíz
│   ├── monitoring/                # monitor_*.ps1/.bat
│   └── setup/                     # activate_citylearn_v3.ps1, env setup
│
├── tests/
│   ├── uc3m/                      # como hoy
│   └── citylearn_v3/              # NUEVO — tests de CityLearn/citylearn/v3/
│
├── data/
│   └── cache/                     # ex .cache/ (weather parquet, etc.)
│
├── outputs/                       # SOLO resultados de entrenamiento/comparación
│   ├── runs/                      # citylearn_v3_madrl_full_<timestamp>/, oficial_v*/
│   ├── dataset_audit/             # (igual que hoy)
│   ├── thesis/  thesis_objective_evidence/  plan_tesis/
│   ├── validation/
│   └── _archive/                  # runs obsoletos según obsolete_reference_policy
│       └── (mover aquí oficial_v4, v5, official_full_cuda_v2, relaunch_20260602...)
│
├── docs/
│   ├── workflow_manifest.json     # se mantiene en la raíz de docs (referenciado por path)
│   ├── 00_INDEX.md                 # NUEVO — mapa de qué leer primero
│   ├── architecture/               # ARQUITECTURA_*, PLANO_*, COOPERACION_*, FLUJO_*
│   ├── audits/                     # INFORME_AUDITORIA_*, INFORME_VALIDACION_*, AUDITORIA_TECNICA_*
│   ├── decisions/                  # JUSTIFICACION_*
│   ├── thesis/                     # PLAN_TESIS_*.docx (con sufijo de versión/fecha consistente),
│   │                                #   APORTES_CIENTIFICOS_*, INFORME_TESIS_*, Resultados_*.xlsx
│   └── contributions/              # NUEVO — ver 3.5: 1 carpeta por submódulo modificado
│       ├── CityLearn/              #   CHANGES.md + bibliografia.bib (tesis/maestrias/articulos <5 anios)
│       ├── HARL/
│       ├── MAAC/
│       ├── MATD3implementation/
│       └── <otros submódulos modificados>/
│
└── build/, dist/, .venv*/, __pycache__, .pytest_cache  →  eliminados o solo locales (ver 3.4)
```

### 3.2 Por qué esta estructura

- **`uc3m/`, `CityLearn/`, `external/` no cambian de lugar ni de contrato**: cero riesgo para el código que ya importa `from uc3m...` o que CityLearn referencia como submódulo. Solo se reorganiza *alrededor*.
- **`tools/` queda 100% dedicado al pipeline reproducible del dataset** (generación, calibración, auditoría, reportes), separado de `agent-skills/`, que es tooling de asistente IA y no parte del pipeline científico. Esto responde directamente a "entendible": alguien que audita la tesis solo necesita mirar `tools/`.
- **`scripts/` se convierte en el único punto de entrada operativo** (training/monitoring/setup), absorbiendo los `.bat`/`.py` sueltos de la raíz y evitando la duplicación raíz vs `scripts/` vs `CityLearn/scripts/` (los de `CityLearn/scripts/` quedan donde están porque es submódulo, pero `docs/00_INDEX.md` y el manifest dejan claro cuál es el wrapper "primary" y cuál el de `CityLearn/`).
- **`outputs/runs/` + `outputs/_archive/`** convierte la `obsolete_reference_policy` actual (una lista de excepciones en el manifest) en una regla estructural: lo vigente vive en `runs/`, lo histórico se mueve a `_archive/` apenas se declara obsoleto. `dataset_cache/` sale de `outputs/` porque es un insumo, no un resultado — pasa a `data/cache/` junto con `.cache/` (weather).
- **`docs/` con subcarpetas temáticas + `00_INDEX.md`**: separa "qué es el sistema" (architecture), "qué se validó y cuándo" (audits, con nomenclatura `YYYYMMDD_` para version-control real), "por qué se decidió así" (decisions) y "entregables de tesis" (thesis). El manifest (`workflow_manifest.json`) sigue siendo la fuente machine-readable; `00_INDEX.md` es la puerta de entrada humana que apunta a él primero.
- **`tests/citylearn_v3/`**: cierra el hueco de cobertura más crítico (capa Dec-POMDP/CTDE que alimenta los 12 jobs oficiales), sin tocar el submódulo CityLearn — los tests viven en el repo principal e importan `CityLearn.citylearn.v3...` igual que hoy hace `tests/uc3m`.

### 3.3 Convenciones a adoptar (naming y versionado)

- **Código** (`uc3m/`, `tools/`, `scripts/`): `snake_case` en inglés, ya consistente — mantener.
- **Carpetas de runs** (`outputs/runs/`): mantener el patrón ya bueno `citylearn_v3_madrl_full_<yyyyMMdd_HHmmss>` (está en el manifest); eliminar progresivamente los sufijos ambiguos `_oficial_vN`.
- **Documentos de auditoría** (`docs/audits/`): prefijo de fecha `YYYYMMDD_INFORME_...md` para que el orden de archivos refleje cronología sin abrir cada uno.
- **Planes de tesis** (`docs/thesis/`): un solo archivo "vigente" (p.ej. `PLAN_TESIS_MADRL_VIGENTE.docx`) + versiones anteriores movidas a `docs/thesis/_historico/` con su sufijo de versión actual (V1, V3, V4) — hoy las 4 versiones compiten visualmente por ser "la buena".
- **`README.md` raíz**: añadir al inicio una sección "Mapa del repo" de 10-15 líneas que enlace a `docs/00_INDEX.md`, `docs/workflow_manifest.json` y a esta estructura, para que la "buena documentación interna" (que ya existe) sea lo primero que se vea.

### 3.4 Limpieza de higiene de repo (independiente de la reestructuración)

Estos cambios reducen ruido sin reorganizar nada conceptual:

1. **`build/` y `dist/`**: añadir a `.gitignore` (si no lo están) y borrar del working tree — son regenerables con `pip install -e .` / `python -m build`.
2. **`__pycache__/`, `.pytest_cache/`** en la raíz: confirmar que están en `.gitignore` y borrarlos del working tree periódicamente.
3. **Entorno Python**: mantener solo `.venv39-citylearn-v3/` como entorno canónico del proyecto. No recrear `.venv/` ni otros `.venv*`; el verificador de contexto bloquea entornos duplicados en la raíz.
4. **`.sixth/`, `.claude/`**: si están vacíos o son cachés de herramientas, añadir a `.gitignore`.
5. **`.markdownlint.json`**: ya existe — buena señal de que hay intención de lint en docs; se podría extender con un hook de pre-commit que también valide que cada nuevo run en `outputs/runs/` tenga su entrada correspondiente actualizada en `latest_visible_training_output_root.txt`.

### 3.5 Modificación de submódulos (CityLearn + los 9 de `external/`, incl. los 4 backends MADRL) como aportes de investigación

Punto aclarado por el usuario: la regla "no editar `CityLearn/`/`external/` sin permiso explícito" de `AGENTS.md` **no significa que esos módulos sean intocables** — significa que cualquier modificación debe hacerse de forma controlada, porque son la base sobre la que se construyen los aportes de la tesis. Todos los submódulos, incluidos los backends HAPPO (HARL), MASAC, MATD3 (MATD3implementation) y MAAC, son objeto legítimo de modificación cuando la modificación es un aporte/mejora de la investigación.

Flujo propuesto para que esto sea trazable y defendible en la tesis:

1. **Fork propio de cada submódulo a modificar.** Igual que ya se hizo con `CityLearn` → `Mac-Tapia/CityLearn` (rama `citylearn-v3-madrl`), cada uno de los 9 repos de `external/` que se modifique debe forkearse a una cuenta/organización propia, y el `.gitmodules` debe repuntar a ese fork (con una rama propia, p.ej. `madrl-iquitos-mods`). Esto preserva el upstream original como referencia y aísla los cambios propios.
2. **Cada modificación se documenta en `docs/contributions/<modulo>/CHANGES.md`** con: (a) qué se cambió y por qué, (b) qué limitación del algoritmo/módulo original motivó el cambio, (c) referencias bibliográficas que lo sustentan.
3. **Referencias bibliográficas**: tesis doctorales y de maestría, y artículos científicos de los últimos 5 años (2021-2026), priorizando los más recientes/actualizados. Cada `CHANGES.md` lleva su propio `bibliografia.bib` (BibTeX) para integrarse directamente con el gestor de referencias de la tesis (Mendeley, ya usado según `docs/`).
4. **Trazabilidad código↔referencia**: en el código modificado, un comentario corto apunta a la entrada del `CHANGES.md`/`.bib` (p.ej. `# Modificación UC3M: ver docs/contributions/HARL/CHANGES.md#critico-centralizado`), de forma que el diff contra upstream sea auditable sin tener que adivinar la motivación.
5. **`docs/workflow_manifest.json`** gana una sección opcional `modified_submodules` que liste fork, rama y commit de referencia de cada submódulo modificado — para que quede registrado qué versión exacta del aporte se usó en cada corrida de entrenamiento (relevante para reproducibilidad de resultados de tesis).

Esto no cambia nada del árbol de carpetas de la sección 3.1 más allá de añadir `docs/contributions/`; es un proceso, no una reestructuración.

---

## 4. Plan de migración por fases (sin romper el entrenamiento activo)

El manifest indica entrenamientos en curso/recientes (`citylearn_v3_madrl_full_2026061*`) y reglas estrictas de contexto (`AGENTS.md`). Por eso la migración se hace en fases de bajo riesgo primero, dejando para el final lo que tocan rutas referenciadas por scripts activos.

**Fase 0 — Pre-requisito (siempre):**
Ejecutar `scripts/verify_project_context.ps1` antes de cualquier cambio, y hacerlo en una rama nueva, no en la rama con el entrenamiento corriendo.

**Fase 1 — Higiene sin impacto funcional (riesgo casi nulo):**
- Eliminar/ignorar `build/`, `dist/`, `__pycache__/` de la raíz.
- Mover `diagnostico_dataset.py` y `ver_metricas_madrl.py` a `tools/reports/`.
- Mover `tools/skills/` → `agent-skills/` (actualizar referencias internas si las hay; estas skills no son invocadas por el pipeline de entrenamiento).

**Fase 2 — Documentación (riesgo nulo, alto valor):**
- Crear `docs/00_INDEX.md`.
- Reorganizar `docs/*` en subcarpetas `architecture/`, `audits/`, `decisions/`, `thesis/` — **manteniendo `workflow_manifest.json` en `docs/` raíz** (verificar primero todas las referencias a rutas `docs/...` en `.md`/`.ps1`/`.py` y actualizarlas en el mismo commit).
- Consolidar los 4 `PLAN_TESIS_*.docx` en vigente + histórico.

**Fase 3 — `outputs/` (coordinar con el estado del entrenamiento):**
- Esperar a que la corrida activa (`outputs/latest_visible_training_output_root.txt`) termine o esté en un punto seguro.
- Crear `outputs/runs/` y mover ahí los `citylearn_v3_madrl_*` y `*_oficial_v*`.
- Mover los obsoletos listados en `obsolete_reference_policy` a `outputs/_archive/`.
- Mover `outputs/dataset_cache/` → `data/cache/` (962 MB; actualizar cualquier ruta hardcodeada en `tools/dataset/orchestrate_citylearn_dataset.py` y similares).
- Actualizar `outputs/latest_visible_training_output_root.txt` y `docs/workflow_manifest.json` con las nuevas rutas (`outputs/runs/...`).

**Fase 4 — `scripts/` y raíz (requiere actualizar launchers):**
- Mover los `.bat` de raíz a `scripts/training/` y `scripts/monitoring/`.
- Reagrupar `scripts/*.ps1` en `training/`, `monitoring/`, `setup/`.
- Actualizar rutas dentro de cada `.ps1`/`.bat` y en `docs/workflow_manifest.json`.
- Probar con un `dry-run`/smoke (`run_citylearn_v3_env_smoke.py`) antes de lanzar un entrenamiento completo.

**Fase 5 — Cobertura de tests (incremental, no bloqueante):**
- Crear `tests/citylearn_v3/` con tests para `CityLearn/citylearn/v3/{config,environment,objectives,backends}.py`.
- Ampliar `pyproject.toml` (`tool.coverage.run.source`) si se decide medir cobertura también de esa capa.

**Fase 6 — `tools/` interno (opcional, cosmético):**
- Subdividir los 28 scripts en `dataset/`, `audit/`, `reports/` según el árbol propuesto. Como son invocados por ruta completa desde el manifest y los `.ps1`, esto requiere actualizar cada referencia — hacerlo solo si el equipo valora la organización interna más que el costo de actualizar ~10-15 referencias.

**Fase 7 — Forks de submódulos para aportes MADRL (independiente, según 3.5):**
- Por cada submódulo a modificar (CityLearn ya está forkeado; definir cuáles de HARL/MAAC/MATD3implementation/MARLlib/MARL/MicroGrids/evcc/prosumpy aplican), crear el fork propio y repuntar `.gitmodules` a esa URL/rama.
- Crear `docs/contributions/<modulo>/CHANGES.md` + `bibliografia.bib` ANTES o en paralelo a cada cambio de código (no después), para mantener trazabilidad cambio↔referencia desde el inicio.
- Añadir la sección `modified_submodules` a `docs/workflow_manifest.json` con fork/rama/commit de cada submódulo modificado.
- Esta fase es independiente de las 1-6 y puede avanzar en paralelo, módulo por módulo, a medida que la investigación produzca cada aporte.

---

## 5. Resumen de impacto

| Fase | Riesgo | Beneficio | Bloqueado por |
|---|---|---|---|
| 1. Higiene raíz | Muy bajo | Repo más limpio para navegar/buscar | — |
| 2. Reorganizar `docs/` | Bajo | Resuelve el problema #D, mejora onboarding | Actualizar referencias de rutas |
| 3. Reorganizar `outputs/` | Medio | Resuelve #C, hace estructural la política de obsolescencia | Estado del entrenamiento activo |
| 4. Reorganizar `scripts/` y raíz | Medio | Resuelve #E/#F | Probar launchers tras mover |
| 5. Tests `citylearn_v3` | Bajo (aditivo) | Resuelve #K, cubre la capa más crítica | — |
| 6. Subdividir `tools/` | Bajo pero tedioso | Resuelve #H/parte de #I | Muchas referencias a actualizar |
| 7. Forks de submódulos MADRL + `docs/contributions/` | Bajo (aditivo, por módulo) | Habilita y documenta los aportes científicos de la tesis | Avance de la investigación (por módulo) |

Recomendación de orden de ejecución: **1 → 2 → 5 → 3 → 4 → 6**, en paralelo con **7** (que avanza por su propio ritmo según qué backend se esté modificando), priorizando lo que no depende del estado del entrenamiento y lo que más reduce el riesgo de regresiones silenciosas (tests) antes de tocar rutas que los launchers usan.

---

## 6. Fase 8 — Despliegue (Docker + AWS): demo de operatividad y camino a producción física

Una vez seleccionado el mejor MADRL (vía HPHI/Score_OG y las 4 pruebas estadísticas ya definidas en el flujo), esta fase empaqueta esa política entrenada como un **servicio de control** que se pueda demostrar corriendo "en vivo" (local con Docker, y en AWS como demo accesible), y que tenga una ruta clara hacia un **EMS real** (Energy Management System) conectado a hardware físico (BESS, cargadores EV, medidores). Es una fase nueva, no reemplaza nada de las fases 1-7; se activa al final del ciclo de entrenamiento/selección.

### 6.1 Objetivo y alcance de la demo

- **Entrada**: checkpoint del algoritmo ganador (`outputs/runs/.../data/checkpoint_manifest.json` + pesos) + `uc3m/configs/algorithms/<ganador>.yaml` + `UC3MEnv` (observaciones BACTTensor 29D).
- **Salida**: un contenedor Docker que expone un servicio de inferencia (la política entrenada ejecutando en modo "execution-only", coherente con CTDE descentralizado) que recibe observaciones por edificio y devuelve acciones de control (BESS, EV charging, setpoints), más un dashboard que visualiza KPIs en tiempo real (igual que los del manifest: `core_kpis`, `OE1/OE2/OE3_*_kpis`).
- **Dos entornos de demo**:
  1. **Local (Docker Compose)** — réplica completa en el laptop/PC para validar el pipeline de inferencia + dashboard + "simulador de planta" (que reemplaza temporalmente a CityLearn con un generador de observaciones sintéticas/replay del dataset Iquitos, simulando sensores reales).
  2. **AWS (demo accesible)** — la misma imagen Docker corriendo en la nube, accesible vía URL, para mostrar a un comité/jurado sin depender del laptop.
- **Camino a producción física**: el mismo contenedor de inferencia, sin cambios de lógica, se reubica en un dispositivo edge (industrial PC / Jetson) en sitio, cambiando solo el adaptador de I/O (de "simulador/replay" a "Modbus/OPC-UA hacia el EMS/BMS real de cada edificio").

### 6.2 Arquitectura de la demo

```text
┌──────────────────────────────────────────────────────────────────┐
│ deploy/                                                            │
│                                                                     │
│  ┌─────────────────┐   obs (29D BACT)   ┌─────────────────────┐   │
│  │ plant-adapter    │ ─────────────────▶ │ inference-service   │   │
│  │ (simulador/      │                    │ (FastAPI + torch,   │   │
│  │  replay Iquitos  │ ◀───────────────── │  política ganadora) │   │
│  │  o Modbus/OPC-UA)│   acciones         └──────────┬──────────┘   │
│  └─────────────────┘                                │              │
│                                                      │ métricas/KPIs│
│                                              ┌───────▼──────────┐   │
│                                              │ dashboard-service │   │
│                                              │ (Streamlit /      │   │
│                                              │  Grafana)         │   │
│                                              └───────────────────┘   │
│                                                                     │
│  broker MQTT (mosquitto) ── puente a sensores/actuadores reales    │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 Estructura de carpetas propuesta (`deploy/`)

```text
deploy/
├── inference/                  # servicio de inferencia de la política ganadora
│   ├── app.py                  # FastAPI: /predict, /health, /metrics
│   ├── model_loader.py         # carga checkpoint + config del algoritmo ganador
│   ├── requirements.txt        # fastapi, uvicorn, torch(cpu), numpy, pydantic, pyyaml
│   └── Dockerfile
├── plant-adapter/               # fuente de observaciones para la demo
│   ├── replay_adapter.py        # repite el dataset Iquitos como "stream en vivo"
│   ├── modbus_adapter.py        # PARA SITIO: lectura/escritura real (pymodbus / asyncua)
│   ├── requirements.txt         # pandas, pymodbus, asyncua, paho-mqtt
│   └── Dockerfile
├── dashboard/                   # visualización de KPIs/acciones en tiempo real
│   ├── app.py                   # Streamlit (o Grafana provisioning + dashboards/*.json)
│   ├── requirements.txt         # streamlit, plotly, pandas, requests
│   └── Dockerfile
├── docker-compose.yml           # demo local: inference + plant-adapter(replay) + dashboard + mosquitto
├── docker-compose.aws.yml       # variante para EC2/ECS (sin mosquitto local, usa AWS IoT Core)
├── aws/
│   ├── iac/                     # Terraform o AWS CDK (a elección)
│   │   ├── main.tf / app.py     # ECR + ECS Fargate (o EC2) + ALB + CloudWatch + S3
│   │   └── variables.tf
│   └── README_DEPLOY_AWS.md     # pasos: build → push ECR → deploy ECS → URL demo
├── edge/
│   └── README_DESPLIEGUE_FISICO.md  # checklist para llevar deploy/ a hardware en sitio
└── .env.example
```

### 6.4 Herramientas y librerías requeridas

**Empaquetado del modelo**
- `torch` (build CPU, `torch>=2.0` ya está en `pyproject.toml` extra `train`) para inferencia sin GPU en el contenedor de demo.
- `onnx` + `onnxruntime` (opcional, recomendado): exportar la política a ONNX reduce el tamaño de imagen y la dependencia de PyTorch completo en el edge.

**Servicio de inferencia**
- `fastapi`, `uvicorn[standard]`, `pydantic` — API REST `/predict` (recibe BACTTensor + estado, devuelve acciones por edificio).
- `numpy`, `pyyaml` — carga de `uc3m/configs/algorithms/<ganador>.yaml`.

**Adaptador de planta (simulador/sitio)**
- Demo: `pandas` (replay del dataset `citylearn_iquitos_2023_2025`).
- Sitio real: `pymodbus` (Modbus TCP/RTU — estándar en BMS/inversores), `asyncua` (OPC-UA — estándar en EMS industriales), `paho-mqtt` (publicación de telemetría).

**Dashboard / observabilidad**
- `streamlit` + `plotly` (rápido para demo) **o** Grafana + Prometheus (`prometheus-client` en el servicio de inferencia) si se quiere algo más "producción".
- `eclipse-mosquitto` (imagen oficial Docker) como broker MQTT local para simular telemetría de sensores/actuadores.

**Contenedores y orquestación**
- `Docker` + `Docker Compose` (demo local multi-servicio).
- `docker buildx` para imágenes multi-arquitectura (amd64 para AWS, arm64 si el edge es Jetson/Raspberry Pi).

**AWS (demo en la nube)**
- `AWS ECR` — registro de la imagen Docker.
- `AWS ECS Fargate` (recomendado para demo: sin gestionar servidores) o `EC2` (si se necesita GPU para una demo con inferencia más pesada — instancia `g4dn.xlarge`).
- `Application Load Balancer` — URL pública estable para el dashboard/API de demo.
- `S3` — almacenamiento de checkpoints/artefactos (`outputs/runs/.../data/checkpoint_manifest.json` y pesos).
- `CloudWatch Logs/Metrics` — observabilidad de la demo.
- `AWS IoT Core` (solo si se quiere demostrar el "puente a físico" también desde la nube) — recibe telemetría MQTT de un dispositivo edge real.
- IaC: `Terraform` o `AWS CDK` (Python, coherente con el resto del stack) para reproducibilidad del despliegue — evita "click-ops" y permite recrear la demo para la defensa de tesis.
- `AWS CLI` + `boto3` para scripts de build/push/deploy.

**CI/CD (opcional pero recomendado)**
- GitHub Actions: workflow que en cada release del modelo ganador construye la imagen `deploy/inference`, la sube a ECR y actualiza el servicio ECS — cierra el ciclo "entrenamiento → selección → despliegue" de forma reproducible, igual de auditable que el resto del workflow_manifest.

**Despliegue físico (más allá de la demo)**
- Hardware sugerido: industrial PC o NVIDIA Jetson (si se exporta a ONNX/TensorRT) en cada edificio o en un nodo central que orquesta los 17.
- Protocolos: Modbus TCP/RTU y/o OPC-UA hacia BMS de cada edificio (BESS, chillers, cargadores EV Mode 3 — coherente con los 96 equipos físicos ya documentados en el dataset).
- Seguridad: VPN/sitio-a-sitio o AWS IoT Core + certificados X.509 si la telemetría sale del sitio hacia la nube; segmentación de red OT/IT.
- `docs/contributions/` (3.5) debe incluir también la justificación bibliográfica de la arquitectura de despliegue elegida (papers recientes sobre EMS basados en RL desplegados en campo, 2021-2026).

### 6.5 Plan de ejecución de la Fase 8

1. **8.1 Selección y exportación**: tomar el run ganador de `outputs/runs/`, exportar política a `deploy/inference/model/` (pesos + config), opcionalmente a ONNX.
2. **8.2 Servicio de inferencia**: implementar `deploy/inference/app.py` (FastAPI) que reconstruye `UC3MEnv`/`BACTTensor` y llama a la política — probar primero localmente con `uvicorn`, sin Docker.
3. **8.3 Adaptador de planta (demo)**: `replay_adapter.py` que reproduce el dataset Iquitos como stream, publicando a MQTT y/o llamando directo al `inference-service`.
4. **8.4 Dashboard**: Streamlit/Grafana mostrando KPIs core + OE1/OE2/OE3 en tiempo real desde las respuestas del `inference-service`.
5. **8.5 Dockerización local**: `Dockerfile` por servicio + `docker-compose.yml` — validar la demo end-to-end en el laptop.
6. **8.6 Despliegue AWS**: IaC (`deploy/aws/iac/`) para ECR + ECS/EC2 + ALB + S3 + CloudWatch; publicar URL de demo.
7. **8.7 Documentar puente a físico**: `deploy/edge/README_DESPLIEGUE_FISICO.md` con el checklist Modbus/OPC-UA por edificio, sin implementarlo aún (queda como trabajo futuro/siguiente fase de la investigación).

Esta fase es completamente independiente de las fases 1-7: puede iniciarse en cualquier momento una vez exista al menos un checkpoint "ganador" reproducible, y no requiere tocar `CityLearn/`, `external/` ni `uc3m/` salvo para reutilizar `UC3MEnv`/`BACTTensor` como librerías de inferencia.
