# Renombramiento de carpetas y archivos — Implementation Plan

> **For agentic workers:** implementar N1–N7 secuencialmente mediante `superpowers:executing-plans`. No renombrar mientras otro proceso/agente escriba en las rutas. No delegar por defecto ni efectuar cambios masivos fuera del mapa verificado.

**Goal:** Sustituir nombres extensos, fechas/identificadores largos y sufijos de versiones por nombres simples que describan el contenido, conservando identidad, contenido, consumidores y reproducibilidad.

**Architecture:** Un registro `governance/naming.yaml` define nombres y excepciones; un mapa explícito old_path → new_path controla la migración. El layout desacopla identidad científica completa de la etiqueta corta de carpeta. Primero se consolida el contenido duplicado; después se renombra la única fuente canónica.

**Tech Stack:** Python 3.9/PyTorch y herramientas existentes; PowerShell para mover en Windows; pytest para contratos; sin cambios de stack ni dependencias.

**Spec actual:** `docs/design/entrenamiento.md`, §§12–14. **Plan principal actual:** `docs/plans/entrenamiento.md`, tarea T14.

La instrucción posterior del propietario autoriza ejecutar este plan. Las tablas
son la propuesta original; el mapa exacto y el estado real se consultan en
`data/maintenance/names/map.json` y `acceptance.json`. Las herramientas y decisiones
de implementación se describen en `docs/audits/nombres.md`.

## Global Constraints

- Única raíz autorizada `D:/MADRLCitytleranflexresdr`. No renombrar la raíz del repositorio ni cambiar su remoto.
- Antes de cada edición u operación Git: `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1`. Si falla, detener la operación.
- No mover/editar `CityLearn/`, `external/`, `.git/`, el entorno `.venv39-citylearn-v3`, carpetas de skills ni identidades de herramientas obligatorias. No modificar contratos de terceros para obtener un nombre corto.
- Mantener `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`, `Dockerfile`, `pyproject.toml`, `requirements.txt`, `uv.lock`, `.gitmodules`, nombres exigidos por GitHub y clientes. Son convenciones técnicas, no candidatos por estilo.
- No mover rutas de campañas congeladas/activas ni archivos abiertos. Aplicar nombres nuevos antes de congelar hashes para entrenamiento. Si ya hay una campaña ejecutándose, informar el bloqueo por ruta y diferir su migración sin matar procesos ni reescribir manifiestos.
- Históricos R-01..R-07 ya retirados o por retirar: registrar `already_removed`/`retire_by_T0`, no renombrarlos para conservarlos o recrearlos.
- La redacción original fue solo un plan. Su ejecución posterior está autorizada; no se hace commit ni push.
- Un renombramiento no autoriza alterar texto aprobado, resultados, semillas, pesos o hiperparámetros. La revisión de Word se limita a mover archivos cerrados y comprobar integridad, sin fusionar ni editar su contenido en esta tarea.
- No dejar copias `_old`, `_new`, `_final`, `_v2` o enlaces de carpetas como sustituto de actualizar consumidores. Un facade imprescindible de una dependencia protegida requiere excepción específica y no contiene lógica duplicada.

## Review Focus

1. Dos nombres abreviados pueden colisionar en Windows o perder una función: mapear por rol, detectar conflictos y consolidar primero (N2/N3).
2. Cambiar nombres puede romper imports, configs, notebooks, scripts y referencias dinámicas: inventariarlos y probarlos, no solo buscar texto (N4/N6).
3. Acortar fechas/hashes puede mezclar experimentos: conservar identidad completa en metadata y resolver rutas por manifiesto (N5).
4. El árbol cambió desde auditorías previas: repetir inspección y bloquear rutas con escritor/consumidor activo, sin resucitar históricos (N1/N6).
5. Un archivo movido puede invalidar hashes compuestos por ruta: verificar bytes, recalcular identidad antes del freeze y no falsificar un hash anterior (N5/N6).

## Convención de nombres

| Elemento | Regla del proyecto |
|---|---|
| Carpetas propias | `lower_snake_case`, una a tres palabras; objetivo <=24 caracteres por componente |
| Archivos propios | Nombre por contenido/acción, `lower_snake_case`; objetivo <=40 caracteres incluyendo extensión |
| Idioma | Código/config/carpetas técnicas siguen inglés; documentos en español pueden usar un nombre español simple y consistente |
| Caracteres | ASCII, sin espacios, tildes ni caracteres reservados de Windows; no nombres CON/PRN/AUX/NUL/COM1..9/LPT1..9 |
| Números | Se permiten IDs cortos con significado: `e1`, `seed_1001`, `try_01`, `cap2`, `001`. No cadenas de seis o más dígitos, fechas ISO o hashes en rutas controladas por el proyecto |
| Fechas y versiones | `created_at`, `protocol_version`, `source_commit`, hashes y fecha del informe dentro del manifiesto/documento, sin concatenarlos al filename |
| Identidad | Un nombre por rol; no eliminar palabras necesarias para diferenciar evaluación, entrenamiento, seguridad o informe |
| Colisiones | Rechazar destino ocupado, equivalencia case-insensitive y Unicode normalizado; nunca sobrescribir con Force |
| Excepciones | Archivos del backend, nombres de clientes o formatos externos obligatorios: registrar motivo, consumidor y alcance; sin excepción genérica para toda una carpeta propia |

Los límites de longitud y la prohibición de fechas en nombres son decisiones de este proyecto por solicitud del usuario, no límites impuestos por PEP 8 o GitHub.

## Estado observado y prioridad

En la inspección de esta sesión se identificaron 71 candidatos por fecha, secuencia larga o basename >46 caracteres, fuera de dependencias, entorno, Git, caches y skills. El auditor de N1 usa la regla final de 40/24, por lo que su lista puede ser mayor. También se observó actividad nueva en `data/maintenance/historicos/` y `outputs/colab_delivery/`; no se presume que estas rutas estén disponibles para mover.

Las carpetas históricas largas citadas en el anexo de retiro no estaban presentes en la inspección actual de `outputs/`. No asumir que están pendientes de renombrar; comprobar su estado. La carpeta técnica `.superpowers/sdd/entrenamiento/` es estado de herramienta, no evidencia científica ni destino de un movimiento durante su uso.

Prioridad: documentos de control y carpetas de mantenimiento; configuraciones/rutas propuestas aún no creadas; código propio retenido por T12; fuentes de figuras/reportes; datasets/resultados nuevos antes de congelación. No hacer un `rename` recursivo global por expresión regular.

## Mapa inicial de carpetas

| Origen actual o propuesto antes de esta instrucción | Destino simple | Condición |
|---|---|---|
| `docs/plans/` | `docs/plans/` | Mover documentos canónicos retenidos, actualizar todos los lectores y links; no copiar ambas ramas |
| `docs/design/` | `docs/design/` | Conservar raíz `specs/` para contratos SPEC; diseño narrativo queda en docs/design |
| `docs/chapters/` | `docs/chapters/` | Solo con generadores, imports/rutas y links actualizados |
| `data/maintenance/historicos/` | `data/maintenance/historicos/` | Esperar cierre de escritor; preservar registro de fecha, hashes y rutas originales dentro de los manifiestos |
| `data/maintenance/repository_layout_20261101/` (propuesto) | `data/maintenance/layout/` | Si no existe todavía, crearlo directamente con nombre simple |
| `data/maintenance/github_readiness_20261101/` (propuesto) | `data/maintenance/github/` | Mismo criterio; la fecha vive en el reporte |
| Campaña propuesta `data/campaigns/<campaign_id_largo>/` | `data/campaigns/iquitos/` | Alias corto `iquitos`; identidad completa en campaign manifest; no reutilizar carpeta ocupada |
| Campaña propuesta `outputs/campaigns/<campaign_id_largo>/` | `outputs/campaigns/iquitos/` | Antes del freeze y de entrenar; lector recibe manifiesto explícito |
| `outputs/colab_delivery/` (actual) | Mantener | Nombre corto y funcional; revisar actividad/consumidores, no es histórico por defecto |
| `CityLearn/`, `external/`, `tools/skills/`, `.superpowers/sdd/` | Mantener | Dependencias/estado técnico protegidos; no aplicar movimientos masivos |

Si `iquitos` está ocupado, fallar. Proponer otro alias corto con significado (`iquitos_ev`, `iquitos_base`) y registrarlo antes de crear el experimento; no anexar un timestamp/hash automáticamente ni sobrescribir una campaña anterior.

## Mapa de carpetas SPEC conservando sus identificadores

Solo cambia el slug; los IDs SPEC/FR y su trazabilidad permanecen. Actualizar `tests/contract/test_spec_kit_consistency.py::EXPECTED_SPECS`, índices, enlaces, generadores y contratos; no reducir el número de requisitos para aprobar.

| Origen bajo `specs/` | Destino bajo `specs/` |
|---|---|
| `000-foundation` | `000-foundation` (mantener) |
| `001-provenance` | `001-provenance` |
| `002-objectives` | `002-objectives` |
| `003-orchestration` | `003-orchestration` |
| `004-manifests` | `004-manifests` |
| `005-evaluation` | `005-evaluation` |
| `006-evidence` | `006-evidence` |
| `007-agents` | `007-agents` |
| `008-artifacts` | `008-artifacts` |
| `009-jury` | `009-jury` |
| `010-panel` | `010-panel` |
| `011-pipeline` | `011-pipeline` |
| `012-hygiene` | `012-hygiene` |

## Mapa inicial de archivos de control y documentación

Prefijos relativos de la tabla son actuales; los destinos de docs/plans y docs/design se crean con el movimiento coordinado de su carpeta. Este plan nuevo se mueve junto a los demás a `docs/plans/renombrar_rutas.md`.

| Origen | Destino |
|---|---|
| `docs/plans/entrenamiento.md` | `docs/plans/entrenamiento.md` |
| `docs/plans/encargo.md` | `docs/plans/encargo.md` |
| `docs/design/entrenamiento.md` | `docs/design/entrenamiento.md` |
| `docs/audits/historicos.md` | `docs/audits/historicos.md` |
| `docs/plans/fundacion.md` | `docs/plans/fundacion.md` |
| `docs/plans/jurado.md` | `docs/plans/jurado.md` |
| `docs/plans/modernizacion.md` | `docs/plans/modernizacion.md` |
| `docs/plans/objetivos.md` | `docs/plans/objetivos.md` |
| `docs/plans/orquestacion.md` | `docs/plans/orquestacion.md` |
| `docs/plans/correcciones.md` | `docs/plans/correcciones.md` |
| `docs/plans/agentes.md` | `docs/plans/agentes.md` |
| `docs/design/modernizacion.md` | `docs/design/modernizacion.md` |
| `docs/audits/jurado.md` | `docs/audits/jurado.md` |
| `docs/audits/der.md` | `docs/audits/der.md` |
| `docs/audits/vehiculos.md` | `docs/audits/vehiculos.md` |
| `docs/audits/edificios.md` | `docs/audits/edificios.md` |
| `docs/audits/recompensas.md` | `docs/audits/recompensas.md` |
| `docs/architecture/flujo.md` | `docs/architecture/flujo.md` |
| `docs/architecture/entrenamiento.md` | `docs/architecture/entrenamiento.md` |
| Su export PDF, si se conserva por rol distinto | `docs/architecture/entrenamiento.pdf` |
| `docs/architecture/coordinacion.md` | `docs/architecture/coordinacion.md` |
| Su export PDF, si se conserva | `docs/architecture/coordinacion.pdf` |
| `docs/architecture/plano.png` | `docs/architecture/plano.png` (solo la canónica de T12) |
| `docs/architecture/_refs/citylearn_v2_environment.jpg` | Mantener, nombre funcional y sin timestamp |

Los planes antiguos se renombrarán solo si T12 demuestra que conservan un rol/capacidad propia. Si son versiones redundantes del plan activo, integrar contenido válido y retirarlos según T12 en vez de mantener ocho planes activos con distintos nombres.

### Word y reportes asociados: propuesta sin cambio de contenido

| Origen | Destino propuesto | Condición |
|---|---|---|
| `docs/tesis.docx` | `docs/tesis.docx` | Documento cerrado, identidad documental preservada, todos los consumidores actualizados |
| `docs/informe.docx` | `docs/informe.docx` | Mismo criterio; no insertar resultados nuevos ni editar texto aprobado |
| `docs/auditoria_tesis.docx` | `docs/auditoria_tesis.docx` | Solo si T12 demuestra rol distinto; si es versión del mismo informe, consolidar primero, no crear otra canónica |
| `docs/audits/informe.json` | `docs/audits/informe.json` | Preservar qué archivo/hash/fecha auditó originalmente, sin relabelarlo como auditoría del documento nuevo |

Actualizar `tools/thesis/thesis_word_canons.py`, docs/índices, manifiestos y generadores en el mismo lote. El movimiento por sí solo conserva SHA-256 del DOCX. Si el documento contiene enlaces externos dependientes del filename, inventariarlos; cualquier reparación interna requiere el flujo documental autorizado y verificación de texto aprobado/render, sin fingir que fue un movimiento byte a byte.

### Reportes de parches con fecha

No proponer un solo nombre `report.json` para todos: distinguir capítulo y asunto. Ejemplos verificables para el mapa expandido N2:

| Origen en `docs/` | Destino en `docs/audits/word/` |
|---|---|
| `cap2_control.json` | `cap2_control.json` |
| `cap2_decpomdp.json` | `cap2_decpomdp.json` |
| `cap2_modelo.json` | `cap2_modelo.json` |
| `cap3_diseno.json` | `cap3_diseno.json` |
| `cap4_implementacion.json` | `cap4_implementacion.json` |
| `cap5_kpis.json` | `cap5_kpis.json` |
| `cap5_rankings.json` | `cap5_rankings.json` |
| `figuras.json` | `figuras.json` |
| `comparacion.json` | `comparacion.json` |

Otros reportes se agregan uno por uno después de leer su rol. Si existen varias auditorías distintas del mismo asunto, mantener registros por revisión corta `r01/r02` y fecha/hash dentro de cada JSON; no sobrescribir la evidencia. Ese historial de auditoría no se convierte en datos de entrenamiento.

## Código y configuración retenidos

Renombrar solo herramientas que T12 retenga como canónicas. Si el análisis histórico fue retirado, marcarlo `retired`, no crear un reemplazo que vuelva a usar resultados eliminados.

| Origen | Destino propuesto |
|---|---|
| `tools/eval/hypothesis.py` | `tools/eval/hypothesis.py` |
| `tools/eval/building_analysis.py` | `tools/eval/building_analysis.py` |
| `tools/eval/kpi_rankings.py` | `tools/eval/kpi_rankings.py` |
| `tools/eval/performance_figures.py` | `tools/eval/performance_figures.py` |
| `tools/figures/building_control.py` | `tools/figures/building_control.py` |
| `tools/thesis/patch_anchors.py` | `tools/thesis/patch_anchors.py` |
| `tools/thesis/patch_cap2_control.py` | `tools/thesis/patch_cap2_control.py` |
| `tools/thesis/patch_cap5_rankings.py` | `tools/thesis/patch_cap5_rankings.py` |
| `configs/experiments/iquitos.yaml` (propuesto) | `configs/experiments/iquitos.yaml` |
| `configs/algorithms/native.yaml` (propuesto) | `configs/algorithms/native.yaml` |
| `configs/evaluation/kpis.yaml` (propuesto) | `configs/evaluation/kpis.yaml` |

Los nombres nuevos de configuración se usan desde su creación si los archivos antiguos no existen. La versión de protocolo y condición fresh quedan en el contenido/configuración y en sus controles, no dependen del filename.

## Árbol simple para la campaña nueva

```text
docs/
  plans/entrenamiento.md
  plans/encargo.md
  plans/renombrar_rutas.md
  design/entrenamiento.md
  audits/historicos.md
  chapters/
data/
  maintenance/historicos/
  maintenance/layout/
  maintenance/github/
  maintenance/names/
  campaigns/iquitos/
    campaign.json
    raw/
    dataset/
    splits/train/
    splits/validation/
    splits/test/
outputs/
  campaigns/iquitos/
    campaign.json
    confirm/happo/e1/seed_1001/try_01/
      data/
      checkpoints/
      figures/
    hpo/happo/e1/config_01/seed_901/try_01/
    sensitivity/happo/e1/weight_01/seed_1001/try_01/
    evaluation/validation/
    evaluation/test/
    reports/
```

`seed_1001` contiene la semilla real, no un número decorativo. HAPPO/MASAC/MATD3/MAAC, E1/E2/E3, candidatos e intentos se mantienen inequívocos. Si una interfaz nativa exige una hoja `E1_s1001` o filenames de checkpoint específicos, conservar esa hoja interna en `native/` mediante una excepción concreta y registrar el mapeo; no modificar la dependencia ni copiar dos juegos de checkpoints.

El `campaign_id` completo, fingerprint, fuente/fecha, semilla, algoritmo y schema hash permanecen en `campaign.json` y en cada manifiesto de tratamiento. `iquitos` es un alias de almacenamiento, no reemplaza esos identificadores. El runner ya no debe usar automáticamente el run_id largo como nombre de carpeta: el layout resuelve tratamiento→ruta corta desde el manifiesto y rechaza que un alias pertenezca a otro fingerprint.

## N1. Inventario vigente y mapa de consumidores

**Files:** crear `tools/ops/audit_names.py`, `tests/fresh_training/test_names.py`; registros en `data/maintenance/names/`.

**Interfaces:** `inventory_names(root: Path, policy_path: Path) -> NamingInventory`; tipo con paths/rol/estado, bytes/hash, enlaces, consumidor, protección y actividad. No cargar pickle ni leer datos históricos como muestras nuevas.

- [ ] Escribir pruebas `test_inventory_excludes_dependencies_and_runtime_state`, `test_long_date_and_hash_names_are_candidates`, `test_active_writer_blocks_rename` y ejecutar con Python canónico para observar RED.
- [ ] Implementar inventario actual y lectura de consumidores/imports/config/rutas dinámicas. No seguir junctions ni inferir obsolescencia por nombre. Añadir archivos nuevos de otros agentes solo como observados, no como objetivos ya autorizados para mover durante su trabajo.
- [ ] Ejecutar pruebas y guardar `inventory.json`, alcance/exclusiones y `blocked_paths`. Recalcular estado de las tablas de este documento: exists/planned/already_removed/retired/blocked.

## N2. Política y mapa uno a uno sin colisiones

**Files:** crear `governance/naming.yaml`; extender `tools/ops/audit_names.py` y `tests/fresh_training/test_names.py`.

**Interfaces:** `build_rename_map(inventory: NamingInventory, proposals) -> RenameMap`; cada entrada tiene old_path, new_path, role, state, source_hash, consumer_actions, parent_move y reason. El mapa expandido contiene rutas exactas; no patrones de ejecución.

- [ ] Pruebas `test_reserved_windows_names_rejected`, `test_casefold_collision_rejected`, `test_two_versions_cannot_overwrite_one_destination`, `test_parent_child_moves_have_single_owner`, `test_unique_role_preserved`; confirmar RED.
- [ ] Aplicar límites 24/40, ASCII/lower_snake_case y excepciones específicas. Expandir cada propuesta y resolver duplicados T12 antes de fijar destino. Dos movimientos al mismo target fallan; no usar `--force`.
- [ ] Verificar PASS y producir `map.json`. Mantener las identidades SPEC/FR y fechas dentro de metadata. No cambiar nombres obligatorios de herramientas ni una raíz protegida.

## N3. Documentos, planes e índices

**Files:** documentos del mapa retenidos por T12; `docs/00_INDEX.md`, README, `docs/workflow_manifest.json`, referencias de AGENTS/harness y `tools/thesis/thesis_word_canons.py` cuando corresponda. Los nombres concretos son los pares old/new del mapa aprobado por contratos, no una lista adicional de copias.

**Interfaces:** `plan_reference_updates(rename_map: RenameMap) -> ReferenceUpdatePlan` en `tools/ops/audit_names.py`; registros con archivo consumidor, tipo de referencia, valor anterior/nuevo y necesidad de revisión documental.

- [ ] Pruebas `test_plan_links_resolve_after_move`, `test_spec_ids_preserved`, `test_word_bytes_unchanged_on_move`, `test_unique_document_content_not_dropped`; confirmar RED usando temporales nuevos.
- [ ] Preparar cambios de referencias antes de mover. Los cuatro documentos de control tienen roles diferentes; no fusionarlos por tener la misma fecha. Los planes realmente redundantes se consolidan T12 primero.
- [ ] Verificar cobertura y referencias para destinos cortos. Word abierto/con enlaces internos que exijan editar: dejar ese ítem bloqueado con causa precisa; no alterar texto por una tarea de filenames.

## N4. Imports, scripts, configuración y contratos

**Files:** herramientas retenidas en el mapa, scripts/notebooks/CI/tests consumidores; `tests/contract/test_spec_kit_consistency.py`; loaders de configuración y CLI.

**Interfaces:** usar ReferenceUpdatePlan; no crear otro parser/algoritmo para acompañar el nombre nuevo.

- [ ] Pruebas `test_import_and_cli_contract_survive_rename`, `test_config_reference_points_to_single_file`, `test_notebook_uses_canonical_cli`, `test_spec_folder_contract_keeps_all_requirements`; observar RED.
- [ ] Cambiar imports/rutas de consumidores propios de forma estructurada y mantener comportamiento/flags. Solo eliminar un shim si todos sus lectores son modificables y ya migraron. No hacer replace global de textos/hashes/resultados o imports de dependencias protegidas.
- [ ] Verificar nuevos imports/CLI y que no hay dos configuraciones activas. Si el origen es planned, crear directamente el destino corto cuando se implemente su tarea original.

## N5. Layout corto sin perder identidad científica

**Files:** `uc3m/application/training/layout.py`, `runner.py`, `preflight.py`, `uc3m/domain/experiments.py` solo donde consume path, el registro de layout de T12, tests nuevos de identidad/rutas.

**Interfaces:** `campaign_path(spec, naming_registry) -> Path`; `treatment_path(campaign_manifest, phase: str, algorithm: str, scenario: str, seed: int, attempt: int, candidate: str | None = None) -> Path`, definidos en `layout.py`. Python 3.9: usar Optional[str] en la implementación, no activar sintaxis/runtime nuevo por este pseudotipo de contrato.

- [ ] Pruebas `test_short_path_retains_real_seed_and_scenario`, `test_same_alias_other_fingerprint_rejected`, `test_two_treatments_never_share_output`, `test_renaming_cannot_mutate_frozen_run`, `test_path_based_digest_is_recomputed_before_freeze`; confirmar RED.
- [ ] Conservar run_id/fingerprints completos como campos, no filenames. Tabla de lookup obligatoria por campaña/tratamiento; no adivinar una identidad analizando nombres ni truncar hashes para desambiguar rutas.
- [ ] Verificar que un movimiento simple preserva bytes, pero que hashes compuestos por nombres/rutas pueden cambiar. Recalcularlos y refijar manifests antes de cualquier entrenamiento; no editar una identidad histórica/congelada para hacerla coincidir ni heredar aceptación previa.

## N6. Movimiento transaccional y validación

**Files:** crear `scripts/maintenance/rename_paths.ps1`; ampliar tests nuevos en temporales. El script procesa `map.json`, no expresiones de shell.

**Interfaces:** `-Phase Plan|Execute|Verify -Manifest <ruta>`, default Plan. Evidencia `results.json` con pending/moved/blocked/failed y checks de contenido/consumidores.

- [ ] Pruebas `test_external_target_rejected`, `test_source_changed_since_inventory_blocks_move`, `test_occupied_target_not_overwritten`, `test_case_only_rename_uses_checked_temporary_path`, `test_no_silent_partial_success`; confirmar RED.
- [ ] Antes de mover cada lote, verificar contexto, rutas absolutas resueltas dentro del workspace, ausencia de enlaces y escritor activo, hashes y destino libre. PowerShell nativo `Move-Item -LiteralPath` en una sola shell; no pasar listas a cmd ni formar comandos concatenados. El nombre temporal de cambios solo de mayúsculas también se valida y no puede existir previamente.
- [ ] Ejecutar primero sobre árbol temporal y verificar PASS; después lotes reales sin autoresumir tras un fallo. Restaurar solo el lote propio desde el mapa si es seguro, sin tocar cambios de otros agentes. Registrar fallos, no declarar todo movido si una ruta quedó bloqueada.
- [ ] Validar hashes de objetos movidos, imports, CLI, enlaces, schema paths, CI y T12/T13. No deserializar checkpoints antiguos para probar el rename.

## N7. Cierre del plan y entrega al agente

**Files:** índices/registros/T12/T13 y nuevos `data/maintenance/names/{inventory,map,results,aliases,acceptance}.json`. `aliases.json` es registro de procedencia, no otro árbol de archivos ni bypass de aislamiento.

- [ ] Pruebas `test_no_unjustified_long_names_in_owned_scope`, `test_all_active_refs_use_canonical_paths`, `test_old_path_kept_only_in_explicit_provenance`, `test_naming_acceptance_requires_no_unresolved_move`; confirmar RED y después PASS.
- [ ] Reinspeccionar el árbol real. Objetivo: cero nombres largos no justificados en el alcance propio; una ruta activa por rol; cero pérdida de contenido; cero referencias activas rotas; identidades/semillas conservadas. Excepciones de nombres obligatorios quedan inventariadas, sin afirmar limpieza universal de dependencias.
- [ ] Marcar `naming_verified=true` solo con evidencia completa; `blocked` conserva la causa y la siguiente acción. Si falta inspección, sigue pending. Adjuntar mapa ejecutado y comandos; sin commit/push automático ni entrenamiento por completar este plan.

## Comandos de trabajo futuros

Los helpers nuevos se implementan antes de ejecutar estos comandos:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/ops/audit_names.py --phase inventory --policy governance/naming.yaml --output data/maintenance/names/inventory.json
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/ops/audit_names.py --phase plan --policy governance/naming.yaml --inventory data/maintenance/names/inventory.json --output data/maintenance/names/map.json
powershell -ExecutionPolicy Bypass -File scripts/maintenance/rename_paths.ps1 -Phase Plan -Manifest data/maintenance/names/map.json
# Execute solo tras verificar el lote sin actividad concurrente y sus consumidores.
powershell -ExecutionPolicy Bypass -File scripts/maintenance/rename_paths.ps1 -Phase Verify -Manifest data/maintenance/names/map.json
```

No confundir Plan/Verify con renombramiento ejecutado. `Execute` mueve exclusivamente la lista exacta validada; un fichero nuevo sin clasificar no se incorpora automáticamente.

## Sustento y límites

- PEP 8 recomienda nombres de módulos cortos y en minúsculas, con underscores cuando mejoran legibilidad: https://peps.python.org/pep-0008/ . No prescribe estos nombres españoles, límites de 24/40 ni eliminar fechas: son preferencias del usuario convertidas en política del proyecto.
- GitHub documenta renombramiento vía CLI/web y seguimiento del cambio: https://docs.github.com/en/repositories/working-with-files/managing-files/renaming-a-file . No renombrar remoto, rama o submódulos por esa guía ni asumir que actualizar enlaces/imports ocurre automáticamente.
- Pineau et al. (2021), JMLR 22(164), *Improving reproducibility in machine learning research*, https://www.jmlr.org/papers/v22/20-303.html , apoya preservar trazabilidad de código/datos/procedimientos. Justifica registrar mapa y hashes; no demuestra que abreviar mejore un KPI energético.
- Costea, C. C. (2026), maestría, Politecnico di Torino, https://webthesis.biblio.polito.it/40396/ ; Charbonnier, F. (2023), doctorado, Oxford, https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5 . Sus fichas institucionales sustentan el alcance CityLearn/MARL y la separación de métricas/evaluación, no la elección exacta del árbol o una mejora de entrenamiento por renombrar. No se etiqueta una tesis como artículo indexado.

Fuentes primarias contrastadas el 2026-11-01. La matriz de artículos científicos, aplicabilidad e indexación editorial verificada del artículo CityLearn está en §10 del diseño principal. Ningún resultado histórico fue usado para seleccionar nombres o validar una nueva política.

## Autorrevisión

- Mapas distinguen existing/planned/retired y no resucitan resultados eliminados.
- N1..N7 cubren cada riesgo de Review Focus con pruebas concretas.
- Mantener IDs científicos/semillas/versiones dentro de manifests, sin ocultarlos ni confundirlos con el alias corto.
- Una renombrada de carpeta se expande a movimientos sin doble propietario; no dos destinos para una única canónica.
- Las rutas actuales de este documento siguen siendo válidas hasta ejecutar el mapa; después se actualizan todos los documentos de control juntos.
- Estado de implementación: consultar `data/maintenance/names/acceptance.json`. La existencia del plan o de helpers no acredita cierre; se exigen ejecución nativa, hashes de consumidores y verificación de nombres/vínculos.
