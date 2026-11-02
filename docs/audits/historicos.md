# Diagnóstico de fallas y retiro de resultados históricos

Fecha de inspección: 2026-11-01, America/Lima. Estado: inventario y diagnóstico para implementación; ningún archivo histórico fue eliminado por redactar este documento.

Este anexo acompaña el plan `docs/plans/entrenamiento.md`. La instrucción posterior del usuario autoriza incluir la limpieza y eliminación de resultados anteriores en el trabajo del agente implementador. Sustituye la instrucción anterior de conservarlos intactos. No autoriza borrar fuentes primarias, Word, código, dependencias, archivos de otros proyectos ni datos nuevos.

Los históricos se pueden leer exclusivamente para inventariar su retiro, documentar incidentes y verificar consumidores. No pueden alimentar entrenamiento, HPO, normalización, baselines, selección, estadística ni aceptación de la campaña nueva. Este anexo es registro de diagnóstico/retiro, no evidencia experimental nueva.

## 1. Ubicación verificada y lista cerrada de eliminación local

Base absoluta de todas las rutas relativas siguientes: `D:/MADRLCitytleranflexresdr/`. Los recuentos son una fotografía de esta inspección; el implementador debe repetirlos y verificar hashes antes de borrar. No decidir eliminación por tamaño, extensión o nombre solamente.

| ID | Ruta relativa exacta autorizada para retirar | Contenido identificado | Archivos presentes | Bytes presentes | Rutas registradas en Git |
|---|---|---|---:|---:|---:|
| R-01 | `outputs/_drive_madrl/` | Espejos locales de Drive, KPI, resultados, CSV, figuras y subcarpetas de análisis históricos | 329 | 1011307009 | 317 |
| R-02 | `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` | Checkpoints nativos y salidas de entrenamiento v4 anterior | 201 | 3737382095 | 6 |
| R-03 | `outputs/madrl_v3_20260627_164047/` | Espejo/resúmenes/figuras de la campaña anterior | 6 | 502198 | 6 |
| R-04 | `outputs/modular_smoke/` | Modelos y salidas de smokes nativos anteriores | 60 | 323040855 | 2 |
| R-05 | `outputs/thesis_objective_evidence/` | Tablas y evidencias derivadas de entrenamientos anteriores | 4 | 253392 | 4 |
| R-06 | `outputs/dataset_cache/` | Cache derivada de CSV del dataset anterior: `.meta.json` y `.pkl`, no archivo meteorológico primario | 2 | 270391563 | 0 |
| R-07 | `outputs/orchestration-tests.xml` | Reporte de pruebas anterior; no acredita la nueva campaña | 1 | 20577 | 0 |

Total inspeccionado en R-01..R-07: 603 archivos presentes y 5342897689 bytes. No garantiza espacio recuperable: pueden intervenir almacenamiento por enlaces, compresión o estado del volumen. Los conteos Git indican rutas del índice, no que los bytes de archivos ignorados tengan respaldo. El agente no debe afirmar recuperabilidad completa sin verificarla.

R-01 contiene, entre otras rutas verificadas:

- `outputs/_drive_madrl/full_data/`: resultados por HAPPO/MASAC/MATD3/MAAC y E1/E2/E3, trazas y análisis.
- `outputs/_drive_madrl/outputs/madrl_v3_20260627_164047/`: otra copia parcial de la campaña, con el registro HAPPO E1 `completed_with_salvage`.
- `outputs/_drive_madrl/kpis/`, `outputs/_drive_madrl/kpi_recalc_20260728/` y `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/`.
- Archivos de sondeo como `download_probe_trace.csv` y `masac_probe_building_kpis.csv`.

Eliminar R-01 completo elimina esos descendientes una sola vez; no enumerarlos como trabajos de borrado independientes. Eliminar archivos `.pt/.pkl` en cualquier otro lugar por su extensión queda prohibido.

R-06 se identificó como cache derivada mediante `citylearn_csv_37b8999ee1d00c241cc8.meta.json` y su par `.pkl`. No deserializar ese pickle para inventariarlo. Si una revisión posterior encuentra fuentes primarias añadidas dentro del directorio, separar ese hallazgo y bloquear ese destino hasta resolver su clasificación; no ampliar automáticamente esta autorización a su contenido nuevo.

## 2. Elementos excluidos de la eliminación

- `CityLearn/`, `external/` y sus datasets/código: no se editan ni se borran por este retiro. El dataset horario anterior bajo `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` queda excluido como entrada de la campaña nueva, pero su eliminación dentro de la dependencia no está autorizada por AGENTS.md.
- `CityLearn/data/buildingcsv/`, facturas e inventario originales verificados. No borrar datos de origen para limpiar resultados.
- `.git/`, Git LFS objects, ramas, commits y worktrees: no reescribir historial ni usar `git clean`, `git reset --hard` o purga de LFS.
- `data/audits/`: auditorías de gobierno, licencias, seguridad, SBOM y manifiestos. Los reportes de entrenamiento allí pueden marcarse `superseded`, pero no se borran todos como si fueran checkpoints.
- `data/dataset_audit/` y `tools/dataset/dataset_docs/`: conservar auditorías y fuentes de trazabilidad, marcadas como no válidas para la campaña nueva cuando proceda. No heredar `ready` desde ellas.
- `docs/*.docx`, fuentes de tesis, figuras integradas y documentos aprobados. No borrar Word ni reescribir conclusiones en este encargo.
- `outputs/README.md`, configuraciones, scripts y generadores: actualizar sus referencias, no eliminarlos por referirse a archivos retirados.
- `data/campaigns/`, `outputs/campaigns/`, artefactos de mantenimiento nuevos y cualquier trabajo concurrente: nunca pertenecen a R-01..R-07.
- Copias remotas en Drive, rutas sincronizadas fuera del repositorio u otros proyectos: fuera de alcance. Esta lista solo autoriza retiro local dentro de la raíz verificada.

Punteros `outputs/latest_colab_output_root.txt` y `outputs/latest_visible_training_output_root.txt`: no estaban presentes en esta inspección. Si aparecen, retirar únicamente el archivo puntero cuando su contenido resuelto apunte a R-01..R-06; no seguirlo y borrar su destino arbitrariamente. Si apunta a trabajo nuevo, preservarlo y reportar el conflicto.

## 3. Procedimiento que debe implementar el agente

Entregables nuevos: `tools/ops/historical_inventory.py`, `scripts/maintenance/retire_historical_outputs.ps1`, `tests/fresh_training/test_historical_retirement.py`. Directorio de evidencia mínima: `data/maintenance/historicos/`.

1. Ejecutar la verificación de contexto y capturar el estado de cambios sin incluir contenido secreto. Inventariar R-01..R-07 por archivo: ruta absoluta/resuelta y relativa, bytes, SHA-256, fechas, condición Git, enlaces y consumidores identificados.
2. Conservar solo la explicación mínima de incidentes, sus rutas/hashes y el manifiesto de eliminación. No hacer una copia de checkpoints/CSV históricos dentro de la campaña nueva. No afirmar que ese manifiesto permite recuperar bytes borrados. Si el usuario pide respaldo, resolverlo como un entregable explícito; este plan no crea otra copia de los resultados por defecto.
3. Generar `retirement_plan.json`: lista exacta de objetivos, hashes, razones, exclusiones y consumidores. La autorización para ejecutar esa lista procede de la petición del usuario; no pedir una aprobación genérica adicional de lo ya autorizado. Un objetivo fuera de lista o con datos concurrentes/primarios ambiguos se bloquea individualmente y se informa.
4. Identificar accesos dinámicos, notebooks, scripts, pruebas, pointers y procesos que estén usando estas raíces. No matar procesos ajenos ni borrar datos abiertos de un entrenamiento activo. Registrar cualquier bloqueo con PID/consumidor, sin exponer argumentos sensibles.
5. Desacoplar lectores activos antes de borrar: `docs/workflow_manifest.json`, `README.md`, `outputs/README.md`, scripts y tests de §4. Los caminos productivos deben recibir la nueva identidad explícita o fallar con `retired_historical_input`; no volver a descargar/recrear los resultados borrados para hacer pasar pruebas. Las menciones de diagnóstico o historia pueden conservarse rotuladas.
6. Probar el procedimiento en árboles temporales desechables, incluyendo un enlace hacia fuera, archivo protegido, cambio de hash después del inventario, solapamiento de padre/hijo y un destino nuevo concurrente. El comportamiento esperado es rechazar lo no permitido antes de tocarlo.
7. Justo antes de cada borrado, repetir contexto y validar que la ruta absoluta resuelta está dentro del `outputs/` de esta raíz y pertenece exactamente a la lista. Rechazar reparse points/enlaces en el objetivo y ancestros/descendientes; comprobar que no cambió el inventario ni hay consumidores activos. No usar glob de borrado ni borrar `outputs/` entero.
8. Ejecutar eliminación mediante cmdlets nativos PowerShell con `Remove-Item -LiteralPath` y `-Recurse` únicamente para directorios aprobados. Mantener una sola shell para mutaciones; no pasar rutas construidas a `cmd /c`. El modo predeterminado del script es `Inventory`; únicamente `-Phase Execute -Manifest <ruta>` ejecuta la lista exacta validada. No ocultar fallos con `SilentlyContinue`.
9. Guardar `retirement_result.json` con destino, estado deleted/already_absent/blocked/failed, exit code y hora. Repetir la búsqueda y probar que los siete destinos quedaron ausentes, que las exclusiones siguen presentes y que la nueva campaña no los vuelve a crear. Cambios Git de borrado pueden quedar para revisión; no stage global/commit/push automático.

La limpieza se completa antes del primer microentrenamiento nuevo de T5. Primero T0-A inventaría/diagnostica, T1 implementa aislamiento y T0-B realiza el retiro validado; después T2..T11. Ningún agente elimina archivos por el mero hecho de leer este anexo: debe ejecutar la fase de implementación autorizada con los controles anteriores.

## 4. Consumidores conocidos que deben desacoplarse

Inspección de código, no lista exhaustiva de consumidores:

| Ruta | Dependencia histórica identificada | Cambio requerido |
|---|---|---|
| `docs/workflow_manifest.json` | `canonical_50ep_drive`, mirror, cache, stats y reportes anteriores | Marcar retiro; quitarlo como manifiesto activo; el nuevo flujo usa campaign manifest explícito |
| `README.md`, `outputs/README.md` | Ganador/resultados antiguos y punteros de corrida | Retirar afirmaciones de vigencia; enlazar estado nuevo sin inventar resultados |
| `uc3m/multicriteria/pipeline.py`, `uc3m/train.py` | Descubrimiento/análisis y entrada de entrenamiento paralela | Exigir campaign manifest nuevo en el perfil nuevo; comprobar consumidores dinámicos; `uc3m/validate.py` no existe y no se considera consumidor confirmado |
| `tools/eval/aggregate_colab_drive_kpis.py`, `tools/eval/run_colab_drive_statistical_analysis.py`, `tools/eval/kpi_rankings.py` | Punteros y raíces de análisis anteriores | Fuera del DAG nuevo; modo archivístico explícito o error por datos retirados |
| `tools/colab/generate_colab_notebook.py`, `tools/colab/harden_colab_notebook_launch.py` y patchers de notebook | Punteros `latest` y precarga de salidas | El notebook nuevo exige identidad nueva y no usa esos defaults |
| `tools/drive/`, `scripts/fetch_and_generate_drive_figures.ps1`, `scripts/close_multicriteria.py` | Descarga/regeneración de históricos | No ejecutarlos en preparación/gates; no borrar copias remotas |
| `tests/uc3m/test_madrl_multicriteria.py::test_pipeline_real_only_drive_50ep_no_illustrative` | Corpus Drive anterior; hace skip si falta | Sacar del perfil nuevo y crear equivalente con campaña nueva; ausencia histórica no cuenta como PASS |
| `tools/training/test_job_resume_state.py::test_validate_canonical_skip_plan_from_drive_kpis` | Acceso directo a `outputs/_drive_madrl/kpis`, retorno silencioso si no existe | Perfil archivístico rotulado o caso nuevo autocontenido; nunca aprobación silenciosa |
| `tools/ops/audit_modular_training.py` | Default `outputs/modular_smoke` | Para aceptación nueva exigir raíz de campaña explícita y no leer smoke retirado |
| `tools/thesis/update_word_quantitative_50episodes.py` y generadores de figuras de Drive | Análisis y figuras de la campaña anterior | No integrarlos como generadores activos de la campaña nueva; mantener Word protegidos |

No eliminar scripts completos solo por un match de texto. Revisar llamadas, wrappers, configuración, variables y notebook generado. Las pruebas nuevas deben detectar que el proceso no abre una ruta retirada durante preparación/ejecución.

La instrucción posterior sobre árbol y duplicados añade T12 y §12 del diseño: permite consolidar/eliminar clones demostrados de código/configuración/activos del padre después de actualizar consumidores y conservar cobertura. Es un flujo distinto al retiro R-01..R-07: no ampliar esa lista de resultados por un match de nombre. Word con contenido único y dependencias siguen protegidos. Los hashes D-01/D-02 acreditan imágenes idénticas; no acreditan duplicación de los otros documentos o módulos.

## 5. HAPPO: qué falló y qué todavía no está demostrado

**Incidente comprobado H-01:**

- Archivo: `outputs/_drive_madrl/outputs/madrl_v3_20260627_164047/HAPPO/E1/data/results.json`.
- Campos literales: `algorithm=HAPPO`, `backend=external/HARL`, `status=completed_with_salvage`, `salvage_reason=NameError: name 'VecEnvWrapper' is not defined`.
- SHA-256 del archivo inspeccionado: `5574ac8b5b19e8995935f7ea2863290911b355f70035f3636479aee995cfb9fc`.
- El registro acredita una excepción de nombre al resolver una interfaz de vectorización/wrapping. No acredita por sí solo OOM, gradientes NaN, falta de convergencia ni un defecto teórico de HAPPO.
- No se encontró un traceback completo en los archivos de texto locales inspeccionados que permita fijar si la excepción se originó dentro de actualización, evaluación, `unwrapped`, reporte o escritura final. No atribuir una fase precisa sin nueva evidencia.

**Cobertura y reanudación comprobadas H-02:**

- `outputs/_drive_madrl/full_data/HAPPO/E1..E3/data/results.json` declara `episodes=50`/`episodes_recorded=50`, mientras su `hyperparameters.job_resume` registra `completed_episodes=49`, `remaining_episodes=1`, `target_episodes=50`.
- `training_summary.json` de esos tratamientos registra `episodes=1`: puede describir el tramo reanudado, no demuestra por sí solo que hubiera un único episodio total. La combinación requiere separar total materializado, tramo reanudado y elegibilidad de KPI; no sumar etiquetas como prueba.
- La matriz del jurado `docs/audits/jurado.md`, J-04, identifica falta de KPI-gains finales homogéneos e inconsistencia 49/50 frente a curva reconstruida. Esa es una limitación de evidencia, no una demostración de que el algoritmo no aprendió.
- Hashes de referencia E1: results `56e09a32e4edbd1ae2f5ae02a566628257d82fbb07b5d711fadf2e945acee759`; summary `1066e13ac6bf01b56547f940c2866121db7718e0fbf13f8e54fbd73793b17007`.

**Estado del código actual H-03:**

- `external/HARL/harl/envs/env_wrappers.py` ya contiene una clase de compatibilidad `VecEnvWrapper` y `ShareVecEnv.unwrapped` retorna `self`. Por tanto, no se afirma que el NameError histórico siga presente hoy ni se prescribe agregar el mismo workaround otra vez.
- `CityLearn/scripts/train_citylearn_v3_happo.py` captura excepciones de `runner.run()`, salva artefactos y registra `run_completed_with_salvage`/`run_error`; también puede generar resultados mínimos tras fallo de escritura. Este comportamiento protege evidencia, pero obliga a una puerta del padre que no promocione salvage a ejecución científica completa.
- El correctivo requerido es una regresión con HAPPO nativo actual que cubra entorno vectorizado, `unwrapped`, aprendizaje, evaluación/reporte, guardado, recarga y cierre. El ciclo debe conservar traceback/stage/exit code y fallar si cualquier fase falla. Crear una clase vacía o verificar solo importación no cumple esa regresión.

No usar checkpoints de H-01/H-02 para probar la corrección. Todo modelo de la regresión nace nuevo. El padre debe fallar con `blocked_dependency_interface` si no puede satisfacer el contrato sin modificar una dependencia; no editar HARL/CityLearn sin autorización explícita de esa modificación.

## 6. Matriz de fallas y correcciones obligatorias

| ID | Falla o limitación demostrada | Corrección prevista | Tarea y prueba nueva |
|---|---|---|---|
| H-01 | HAPPO E1 salvado con NameError VecEnvWrapper | Ciclo nativo completo actual; error por fase/traceback; nunca completar por salvage | T5 `test_happo_vector_env_report_reload_close` y T6 `test_salvage_is_not_training_complete` |
| H-02 | Cobertura/tramo reanudado/curva se confunden | Inicio cero; una trayectoria por intento, pasos/episodios reales; sin concatenar históricos | T1/T6 `test_retry_starts_at_zero`, `test_episode_claim_cannot_replace_trajectory` |
| H-03 | Fix de compatibilidad existe, sin prueba nueva de cierre integral | Probar comportamiento real y fijar hash de dependencia; no repetir un parche por suposición | T5 `test_happo_current_wrapper_contract` |
| H-04 | Entrenador UC3M usa acciones aleatorias y puede anunciar fin | Ruta única al aprendiz real o error explícito; actualización y cambio de parámetros | T5 `test_placeholder_training_rejected` |
| H-05 | Extractor promedia alias de delta total y diario | KPI desde trazas; total=control-baseline; contratos de unidad y ventana | T4 `test_total_never_averages_daily_value` |
| H-06 | Evaluador UC3M estima ahorros por porcentajes y resiliencia por SOC | No usarlo como evidencia nueva; baseline ejecutado y métricas observables | T4/T7 `test_no_estimated_savings_as_measured_kpi` |
| H-07 | Columnas de pronóstico replican exactamente futuro observado | Excluirlas del actor principal; transformaciones ajustadas solo en train | T3 `test_no_predicted_fields_in_effective_actor_input` |
| H-08 | Pesos efectivos/configuración y textos no representan un protocolo único | Configuración resuelta con hash, misma tarifa/activos y pesos explícitos por tratamiento | T6 `test_resolved_config_matches_backend` |
| H-09 | Resume modular exige estado que el recolector no clasifica | Resume deshabilitado; reinicio cero; continuidad futura requiere otra aceptación | T6 `test_all_treatments_force_no_resume` |
| H-10 | Agregador multisemilla no extrae las estructuras KPI nativas inspeccionadas | Contrato nuevo de KPI + extracción anidada y cobertura estricta | T9 `test_nested_native_report_extracts_new_kpis` |
| H-11 | Una semilla, KPI correlacionados y selección sin referencia común limitan inferencia | Semillas independientes; endpoints fijados; hipervolumen con referencia común; IC | T8/T9, pruebas de n y referencia común |
| H-12 | Pruebas pueden omitir/retornar ante ausencia de históricos | Retiro de consumidores + aceptación nueva estricta, sin descargar el corpus eliminado | T0/T10 `test_retired_inputs_not_opened`, `test_skips_xfail_xpass_fail_new_acceptance` |

Los valores de rendimiento previos no forman parte de expected de estas pruebas. Los casos de excepción y los casos analíticos se generan de nuevo; la aceptación de interfaces/optimización usa dependencias reales.

## 7. Sustento y límites del diagnóstico

El error registrado es evidencia local; ninguna publicación permite inferir que un NameError causó OOM o que HAPPO es inferior. La separación de demostración, selección y evaluación sigue a Patterson et al. (2024), *Empirical Design in Reinforcement Learning*, JMLR 25(318), https://jmlr.org/papers/v25/23-0183.html . La custodia mínima de código/procedimiento/errores antes del retiro sigue el criterio de reproducibilidad de Pineau et al. (2021), JMLR 22(164), https://www.jmlr.org/papers/v22/20-303.html ; no prescribe conservar indefinidamente todos los artefactos ni autoriza una eliminación específica.

Costea (2026), tesis de maestría de Politecnico di Torino, https://webthesis.biblio.polito.it/40396/ , respalda comparación con baseline/RBC y métricas de edificio/distrito. Charbonnier (2023), tesis doctoral de Oxford, https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5 , fundamenta estudiar coordinación y compromisos energéticos. Ninguna valida pesos exactos, reparación de wrappers o superioridad de esta campaña. Fichas y fuentes primarias contrastadas el 2026-11-01; no se presume indexación de tesis. La matriz bibliográfica y la verificación editorial de indexación del artículo CityLearn están en §10 del diseño nuevo enlazado.
