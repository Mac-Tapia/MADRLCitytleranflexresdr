# Plan de implementación completa: cierre de SPEC-000 a SPEC-016

> **Para agentes:** sub-skill requerido: `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans`, tarea por tarea. Los pasos usan casillas (`- [ ]`). Antes de editar, leer `C:/Users/Lenovo Legion/.agents/COORDINATION.md`, `C:/Users/Lenovo Legion/.agents/skills/team-agent-orchestration/SKILL.md`, [AGENTS.md](../../AGENTS.md) y [AGENT_HARNESS.md](../architecture/AGENT_HARNESS.md).

**Objetivo:** cerrar todos los specs sin pendientes, módulo por módulo, y dejar el entrenamiento (módulo 8) como única etapa restante, que se ejecuta solo con autorización.

**Arquitectura:** cada módulo se cierra por separado con un ciclo fijo: spec, pruebas en rojo y luego en verde, puerta `-Scope Repository` sobre su commit, CI en verde, registros actualizados y publicación ([hoja de ruta](hoja_ruta_modulos.md)). Los módulos 3b, 5 y 8 son subsistemas grandes: antes de ejecutarlos, cada uno recibe su propio plan TDD detallado, derivado de la sección correspondiente de este documento.

**Stack:** Python 3, pytest, CityLearn v3 (fork `Mac-Tapia/CityLearn`), backends nativos en `external/` (HARL, MARL, MATD3implementation y MAAC), PowerShell para las puertas y Colab A100 80 GB para el módulo 8.

**Specs:** [STATUS](../../specs/STATUS.md), [SPEC-015](../../specs/015-modulo3-algoritmos/spec.md), [SPEC-016](../../specs/016-iquitos-v6/spec.md) y las carpetas `specs/000-…` a `specs/012-…`.

## Restricciones globales

- Antes de editar u operar con Git: `powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1`. Si falla, detenerse.
- No leer ni usar `D:\madrl_lima`.
- No se entrena hasta cerrar todo: `resource_authorization.authorized_stages=[]` se mantiene vacío, porque ese archivo forma parte de la identidad de la campaña. Cada etapa necesita la autorización explícita del propietario y se lanza con `--owner-authorized`.
- `scientific_acceptance=false` e `implementation_ready_for_training=false` hasta que sus puertas lo acrediten.
- Los 4 MADRL conservan la capacidad nativa de sus autores (D-M3-5). Ninguna tarea encoge un búfer, un lote o una red.
- Los ajustes de Colab no cambian salvo para mejorar (D-M3-4).
- Commits con rutas explícitas; nunca `git add -A`. Commit y push solo con autorización del propietario en la sesión, una fase revisada cada vez.
- El submódulo `CityLearn/` se publica en su fork (`git -C CityLearn push origin <rama>`) antes de actualizar su referencia en el repositorio principal.
- Las pruebas que lanzan el simulador se ejecutan solas, sin otro simulador en paralelo: la caché compartida hace fallar el fixture.
- Un solo escritor por archivo. La propiedad vigente está en [traspaso_sesiones.md](traspaso_sesiones.md).
- Nombres neutros: ningún archivo, rama ni identificador lleva `claude`, `codex`, `cursor` ni `copilot` (FR-012.1).
- Todo valor del dataset es realista y trazable. Una constante sin fuente se marca `assumption`, y su confirmación se pide al propietario con una recomendación.

## Foco de revisión

Fallos que el spec implica, que ninguna prueba ejercitaba y que tienen más probabilidad de afectar:

1. **Edificio sin algún equipo** (sin BESS o sin cargadores): ningún agente discreto puede elegir la acción, y las salidas continuas sobrantes se declaran inertes. Pruebas: Tarea 3.1, paso 1, y Tarea 3b.4.
2. **Dataset que cambia con requisitos de memoria viejos**: la puerta falla en lugar de aprobar con las cifras anteriores. Prueba: Tarea 3b.5, paso 2.
3. **Campaña incompleta o con semillas desiguales en la selección**: se rechaza y nunca declara ganador. Prueba: Tarea 4.1.
4. **Mes sin pico previo en el bloque de 18:00 a 23:00** (primera hora del mes): el cargo por potencia empieza en 0 y la suma mensual reproduce la factura sin el cargo fijo. Prueba: Tarea 3b.3.
5. **Restauración con un archivo alterado**: falla cerrada con la ruta del archivo. Prueba: Tarea 6.1 (reutiliza la prueba sintética de SPEC-008 sobre una corrida real del módulo 8).

---

## Módulo 3: cerrar SPEC-015 (siguiente)

### Tarea 3.1: verificar FR-015.7 (máscaras D03) y publicarlo

El código ya está escrito y sin commit (ver traspaso, sesión `-e0`).

**Archivos:**
- Submódulo: `CityLearn/scripts/citylearn_v3_training_common.py`, `CityLearn/scripts/train_citylearn_v3_maac.py` y `CityLearn/scripts/train_citylearn_v3_masac.py`.
- Principal: `configs/algorithms/native.yaml`, `uc3m/adapters/citylearn/policy_inference.py`, `tests/fresh_training/test_frozen_evaluation.py` y `tests/fresh_training/test_action_masks.py`.

**Interfaces producidas:** `discrete_action_rows_by_agent(env) -> list[list[int]]`, `discrete_action_mask_by_agent(env) -> list[list[int]]` y `discrete_action_map() -> dict`. SPEC-016 las reutiliza (FR-016.10).

- [ ] **Paso 1: comprobar que `test_action_masks.py` cubre lo que exige FR-015.7.** Debe afirmar que, en los 17 edificios del dataset activo, el mapa coincide con `action_names`, y que con la máscara aplicada ningún agente de MASAC o MAAC puede elegir una acción sin equipo. Si falta un caso, añadirlo y verlo en rojo con el código comentado.
- [ ] **Paso 2: ejecutar la tanda completa, sola.**
  `python -m pytest tests/fresh_training/test_action_masks.py tests/fresh_training/test_author_capacity.py tests/fresh_training/test_campaign_contract.py tests/fresh_training/test_runtime_requirements.py tests/fresh_training/test_learning_observer.py tests/fresh_training/test_real_learning.py tests/fresh_training/test_frozen_evaluation.py -v`
  Resultado esperado: todo en verde, incluido `test_real_learning.py` para los 4 backends.
- [ ] **Paso 3: con autorización, commit y push del submódulo.**
  `git -C CityLearn add scripts/citylearn_v3_training_common.py scripts/train_citylearn_v3_maac.py scripts/train_citylearn_v3_masac.py`, luego `git -C CityLearn commit -m "feat(v3): native discrete action masks per agent (D03)"` y `git -C CityLearn push origin <rama>`.
- [ ] **Paso 4: commit en el repositorio principal**, con los 4 archivos y `CityLearn` (referencia del submódulo). Mensaje: `feat(algorithms): native action interface with masks (FR-015.7)`.

### Tarea 3.2: puerta del módulo, registros y publicación

**Archivos:** `specs/STATUS.md`, `specs/015-modulo3-algoritmos/spec.md`, `docs/plans/hoja_ruta_modulos.md` y `docs/plans/traspaso_sesiones.md`.

- [ ] **Paso 1:** `powershell -ExecutionPolicy Bypass -File scripts\quality\run_fresh_training_gates.ps1 -Scope Repository`. Resultado esperado: JSON de la puerta aprobado en `data/maintenance/gates/Repository_profile_<stamp>.json`, sin fallos ni pruebas omitidas.
- [ ] **Paso 2: conciliar STATUS.**
  - Añadir las filas de SPEC-015 (`implemented`) y SPEC-016 (`draft`).
  - Quitar de las filas de SPEC-002, 003 y 004 lo que ya cerró el módulo 3: la descomposición de la recompensa en los registros, la cancelación de hijos, la conformidad de `NativeBackend` y `save_training_state` en los 4 lanzadores.
  - Marcar el estado de SPEC-015 como `implemented` y el módulo 3 como «Cerrado» en la hoja de ruta.
- [ ] **Paso 3:** con autorización, commit de los documentos y `git push` de la rama (18 commits previos más los nuevos). Esperar el CI en verde.
- [ ] **Paso 4:** revisar `external/MAAC/.git_commit_msg.tmp`, que no tiene autoría conocida: preguntar al propietario antes de borrarlo. Nunca se edita `external/`.

---

## Módulo 3b: SPEC-016, dataset `iquitos_v6`

Necesita su propio plan TDD detallado antes de ejecutarse: `docs/plans/modulo3b_iquitos_v6.md`. Tareas y su orden, con dependencias reales:

**Reordenado el 2026-11-07 (D-V6-14):** la regresión con punto de cambio no identifica la refrigeración en Iquitos ([auditoría](../audits/cambio_punto_iquitos_20261107/README.md)). La capacidad del aire acondicionado (antes 3b.2) va primero, porque el reparto calibrado la consume.

### Tarea 3b.1: aire acondicionado por norma (FR-016.3)

- **Archivos:**
  - nuevo `configs/dataset/hvac_norms.yaml`: RNE EM.050 y EM.030; NTS 110 y 119 del MINSA para B11 y B12, con artículo citado; origen `cited`, `design_rule` o `assumption` por valor;
  - nuevo `uc3m/application/dataset/hvac_capacity.py`;
  - modificación del dimensionado en `tools/dataset/fix_schema_cooling.py`.
- **Interfaz producida:** `hvac_capacity_kw(inventory: BuildingInventory, norms: dict) -> CapacityEstimate`, con `kw`, `w_per_m2`, `source` y `components`.
- **Pruebas:**
  - la potencia de cada edificio cae en el rango de W/m² de su tipo;
  - deja de depender de la demanda modelada (B11 deja de ser 4,7 W/m² y B04 de ser 175,6 W/m²);
  - cada valor de `hvac_norms.yaml` tiene origen y, si es `cited`, la norma y el artículo.
- **Diseño fijado por D-V6-16 y D-V6-17 (2026-11-07):**
  - `capacity_kw_th = splits × 5,275 + [sistema grande] × (carga_aire_exterior + ganancia_ocupantes)`;
  - `carga_aire_exterior = ρ · Vbz · (h_ext − h_int)`, con `Vbz = Rp·Pz + Ra·Az` y `Pz = Rd/100 · Az` (EM.030, Tabla N° 01);
  - `h_ext`: percentil 99 de la entalpía horaria de NASA POWER 2023; `h_int`: 24 °C y 50 % de HR;
  - potencia eléctrica = térmica ÷ COP del equipo.
- **Correspondencia tipo → fila de la Tabla N° 01** (`Rp` l/s·persona, `Ra` l/s·m², `Rd` personas/100 m²):

  | Tipo | Fila | Rp | Ra | Rd |
  |---|---|---|---|---|
  | Office, Office_Critical | Ambiente de oficinas | 2,5 | 0,3 | 5 |
  | Retail | Supermercados | 3,8 | 0,3 | 8 |
  | Commercial_Mall | Áreas comunes de centros comerciales | 3,8 | 0,3 | 40 |
  | MultiFamily_Hotel | Hoteles, salas de estar | 2,5 | 0,3 | 10 |
  | Education | Aulas de más de 9 años | 5 | 0,6 | 35 |
  | Assembly (aeropuerto) | Áreas de espera de transporte | 3,8 | 0,3 | 100 |
  | Assembly_Military | Aulas de más de 9 años | 5 | 0,6 | 35 |
  | Laboratory | Laboratorios universitarios | 5 | 0,9 | 25 |
  | Industrial, Industrial_Port | Manufactura en general | 5,0 | 0,9 | 7 |
  | Healthcare, Healthcare_Hospital | No está en la Tabla N° 01; EM.030 art. 13.5 remite a MINSA y ASHRAE 170. Se usan las renovaciones de la NTS 110, Tabla 6: áreas generales, 2-3 renovaciones/h; se toma 3 | — | — | — |

- **Supuestos declarados (`assumption`):**
  - la fracción del área techada que es zona ocupada: 1,0 por defecto, que sobredimensiona, por ejemplo, el aeropuerto;
  - la ganancia por ocupante, pendiente de una fuente primaria (ASHRAE Fundamentals es de pago);
  - la altura de techo para convertir renovaciones a caudal en los hospitales;
  - la correspondencia de tipos, en particular el uso de la fila de aulas para la escuela militar.

### Tarea 3b.2: reparto calibrado refrigeración y carga base (FR-016.1 y FR-016.2, D-V6-14 y D-V6-15)

- **Archivos:**
  - nuevo `uc3m/application/dataset/cooling_calibration.py`;
  - modificación de `tools/dataset/distill_building_loads.py`, que reemplaza el reparto residual `_allocate_residual_energy_block`.
- **Interfaces:**
  - **consume** `hvac_capacity_kw` de 3b.1;
  - **produce** `calibrate_cooling(capacity_kw, hourly_temp_c, schedule, monthly_bill_kwh) -> CalibrationResult`, con la serie horaria de refrigeración eléctrica, `cv_rmse_pct`, `nmbe_pct` y `passed`.
- **Pruebas** (`tests/fresh_training/test_cooling_calibration.py`):
  - la refrigeración más la carga base reproduce cada factura mensual (punta + fuera de punta) con tolerancia 1e-6;
  - la carga base es mayor que 0 en las 8 760 horas de los 17 edificios;
  - un caso sintético con capacidad y factura conocidas recupera la fracción de refrigeración;
  - un edificio que no cumple los criterios de ASHRAE G14 queda marcado y la puerta falla;
  - el lector de facturas descarta las filas vacías (`B_04.csv`) y registra en `quality_flags` cada mes en que `totalEnergiaActiva` difiere de punta + fuera de punta.
- **Forma horaria de la carga base:** los edificios de referencia del DOE y ASHRAE 90.1 por tipo, que reemplazan los 11 horarios `assumption` de `configs/dataset/building_types.yaml`.
- **Criterio de calibración:** mensual, NMBE ±5 % y CV(RMSE) ≤ 15 %, según ASHRAE Guideline 14 vía FEMP M&V 4.0, Tabla 4-2 (verificado en FEMP; el texto de G14 no se abrió).

### Tarea 3b.2b: control del aire acondicionado con confort (FR-016.4)

- **Pruebas:**
  - la dinámica térmica de cada edificio se valida antes de habilitar el control;
  - el límite de confort sale de una norma para clima cálido y húmedo.
- **Límite de confort:** 24 °C (D-V6-17).

### Tarea 3b.3: cargadores, vehículos, BESS y tarifa de potencia (FR-016.5 a FR-016.7)

- **Archivos:** `tools/dataset/dimension_ev_chargers.py`, `configs/dataset/ev_pilot.yaml`, `tools/dataset/size_bess_optimal.py`, `configs/dataset/bess_design_rule.yaml` y `tools/dataset/build_bill_tariffs.py`.
- **Reglas:**
  - plazas = `Area_Estacionamiento_m2` ÷ m² por plaza según el RNE (a verificar);
  - cargadores = 1 por cada 10 plazas (EPBD 2024, art. 14);
  - vehículos eléctricos = 5 % de los estacionados (MINEM 2030);
  - 220 V; potencia de carga por tipo de vehículo, con fuente citada;
  - BESS con energía = excedente FV diario + energía de los vehículos no cubierta por la FV, en el día de mayor excedente; potencia = máximo entre el excedente horario y la potencia de carga.
- **Pruebas:**
  - conservación anual del BESS: carga × eficiencia − descarga − variación del estado de carga = 0 ± 1e-6;
  - la energía de los vehículos se suma a la factura como demanda nueva;
  - la tarifa de potencia por edificio y mes vive dentro del dataset;
  - en la primera hora del mes, el aumento del cargo por potencia empieza desde un pico previo de 0;
  - la suma mensual de `P·precio + tarifa_potencia × max(0, P − pico_del_mes)` reproduce la factura sin el cargo fijo.

### Tarea 3b.4: contraste de picos y puertas (FR-016.8 y FR-016.9)

- **Archivos:** nuevo `tools/dataset/audit_peak_contrast.py`; modificación de `tools/dataset/build_fresh_campaign_dataset.py` para registrar las puertas nuevas.
- **Pruebas:**
  - por edificio y mes, la desviación entre el pico generado y el pico medido (factor de carga y máxima demanda de `resultados_preliminares.xlsx`) queda dentro del umbral declarado; si no, se destila para reproducir energía y pico;
  - las 10 puertas de `iquitos_v5` siguen activas;
  - en edificios sin algún equipo, la máscara de la Tarea 3.1 deja esa acción sin elegir.
- **Construcción:** `python tools/dataset/build_fresh_campaign_dataset.py`; resultado esperado: `dataset_acceptance.json` con `dataset_verified=true` y hash nuevo.

### Tarea 3b.5: adecuación a los 4 MADRL y tupla de CityLearn v3 (FR-016.10 y FR-016.11)

**Capa obligatoria (D-V6-25):** todo el comportamiento va en `CityLearn/citylearn/dec_pomdp.py`, `CityLearn/citylearn/v3/` (`reward.py`, `objectives.py`, `environment.py`, `marllib_env.py`) y `CityLearn/scripts/citylearn_v3_training_common.py`. Las pruebas usan el entorno v3; `uc3m/application/dataset/bill_tariff.incremental_bill_cost` es el oráculo de la recompensa con factura, y el V2G de las camionetas se ejerce con el cargador de la capa v3 (`max_discharging_power` > 0).

- **Archivos:**
  - recompensa con factura y observaciones (pico del mes, bloque de 18:00 a 23:00, tarifa de potencia, temperatura interior y confort) en `CityLearn/citylearn/v3/`;
  - `configs/evaluation/kpis.yaml` y `configs/objective_policies.yaml`;
  - nueva prueba `tests/fresh_training/test_v3_tuple_contract.py`.
- **Pruebas:**
  - cada término de recompensa tiene un eje y un KPI, y cada eje tiene un KPI primario medido;
  - cada acción corresponde a un equipo y cada observación que usa la recompensa está en `O_i`;
  - un término sin KPI hace fallar la prueba (caso falsificado);
  - `test_runtime_requirements.py` falla si quedan las cifras de memoria de `v5` y se recalcula con D-M3-3;
  - `test_author_capacity.py` sigue en verde;
  - humo: los 4 algoritmos completan un episodio corto real sobre `iquitos_v6` y guardan `training_state.pt`.
- **Cierre:** puerta `-Scope Repository`, CI, STATUS y publicación (submódulo primero).

---

## Módulo 3c: SPEC-017, universalidad (antes de cerrar 3b)

Cada tarea con prueba en rojo primero:

1. **FR-017.1:** configuración de sitio. Sacar de los módulos de dataset el `PEAK_HOURS` de `construction.py` y el `TOKEN_CLASS` de `ev_sizing`; prueba de que no quedan constantes de sitio.
2. **FR-017.3:** contrato de backend en la capa v3, con un backend mínimo de referencia registrado sin editar la capa.
3. **FR-017.4:** puerta de operatividad: cargar en v3 y dar un episodio corto con cada backend al final de cada construcción.
4. **FR-017.5:** origen `implementation_rule` y prueba de que ningún valor queda sin origen.
5. **Criterio 1:** sitio sintético de prueba con 2 edificios, otro clima, otra tarifa y otro bloque horario.

## Módulo 4: estadística y selección (SPEC-005 y SPEC-009)

### Tarea 4.1: reproducir los tres defectos y conciliar

Ya existe código que parece corregirlos: `iqm` con pesos fraccionarios (`uc3m/application/evaluation/fresh_analysis.py:94`), `decide_oe_winner(..., omnibus_p=...)` (`uc3m/multicriteria/stats_tests.py:1318`) y `select_best_model`, que separa candidato descriptivo y ganador inferencial (`uc3m/application/evaluation/model_selection.py:32`).

- **Archivos:** `tests/fresh_training/test_statistics_defects.py` (nuevo); si alguna afirmación falla, se corrige el archivo de origen correspondiente.
- [ ] **Paso 1: escribir las pruebas de reproducción.**
  - `compute_multiseed_stats([1.0, 2.0, 10.0])['iqm'] == pytest.approx((0.25*1 + 2 + 0.25*10)/1.5)`, distinto de la mediana 2,0;
  - `decide_oe_winner(...)` con `omnibus_p=0.2` devuelve `inferential_winner is None` y `winners == []`;
  - `select_best_model` con `campaign_complete=False` lanza `ValueError`;
  - con `n_seeds` desiguales lanza `ValueError`;
  - sin `inference` devuelve `selection_kind == 'descriptive'` e `inferential_winner is None`.
- [ ] **Paso 2: ejecutar.** Si todo pasa, el defecto está corregido: registrar en STATUS el commit que lo corrigió. Si algo falla, corregir y repetir.
- [ ] **Paso 3: verdad estadística única (SPEC-009).** Un único informe (`tools/eval/build_campaign_statistical_report.py`) es la fuente de toda cifra estadística de la tesis. Grep de los documentos que citan cifras de otra fuente y corrección documental. Las observaciones experimentales del jurado (J-01 a J-17) quedan para el módulo 8.
- [ ] **Paso 4:** puerta, STATUS y publicación.

---

## Módulo 5: flujo y herramientas (SPEC-011, SPEC-003 y SPEC-002)

Necesita plan detallado propio: `docs/plans/modulo5_flujo.md`.

- **Tarea 5.1: subcomandos por etapa en la CLI** (`uc3m/application/training/cli.py`). Una prueba por subcomando: salida en JSON en la última línea, exit 0 o 2 y rechazo si cambian las entradas.
- **Tarea 5.2: inventario de herramientas** (`data/audits/evaluation_tools_inventory.json`).
  - Retirar las 30 obsoletas, cada una registrada en `data/audits/repository_hygiene_manifest.json` (FR-012.5).
  - Presentar al propietario las 16 que requieren decisión, una por una, con recomendación.
- **Tarea 5.3: FR-003.1 y FR-003.4.**
  - `ExperimentTrackerPort` como `typing.Protocol` en el módulo de puertos existente.
  - Extraer reportes y tablas a `uc3m/application/evaluation/` y crear `uc3m/adapters/matplotlib_figures.py` (`FigureRenderer`).
  - Prueba del grafo de dependencias (FR-003.6): el dominio no importa CityLearn ni `external/`.
- **Tarea 5.4: FR-002.5 en la evaluación congelada.** Descomposición por paso de la recompensa en el episodio de evaluación, que cuadra con la recompensa con tolerancia 1e-12. Reutiliza `uc3m/reward/term_telemetry.py`.
- **Cierre:** puerta, STATUS (SPEC-002, SPEC-003 y SPEC-011 sin pendientes, salvo la ejecución real del módulo 8) y publicación.

---

## Módulo 6: artefactos e higiene (SPEC-008 y SPEC-012)

### Tarea 6.1: FR-008.4

- **Archivos:** `.gitignore` y nueva prueba `tests/contract/test_gitignore_rules.py`.
- **Prueba:** `git check-ignore` acepta `outputs/x/source_snapshot.zip`, `a.tmp` y `outputs/_tmp_x`, y rechaza los manifiestos y la evidencia promovida.

### Tarea 6.2: FR-012.1 a FR-012.5

- **Archivos:** nueva prueba `tests/contract/test_repository_hygiene_rules.py` y `data/audits/repository_hygiene_manifest.json`.
- **Pruebas:**
  - ninguna rama local o remota `codex/*` ni `cursor/*` (`git branch -a`);
  - la raíz solo tiene los archivos permitidos por FR-012.2;
  - no hay temporales en el índice;
  - cada duplicado del inventario tiene su copia canónica y su entrada en el manifiesto.
- **Ramas:** borrarlas requiere autorización del propietario rama por rama (operación remota, difícil de revertir); antes se registra el commit de cada una.
- **Cierre:** puerta, STATUS y publicación.

---

## Módulo 7: agentes, skills y licencias (SPEC-007 y SPEC-001)

- **Tarea 7.1: FR-007.6.**
  - Migrar los 4 skills antiguos a `tools/skills/` con fuente fijada a un commit, licencia y hashes en `tools/skills/registry.yaml`.
  - Validar con `python tools/skills/validate_skills.py` y registrar con `scripts/skills/register_local_skills.ps1`.
  - Decidir sobre el hook heredado `.claude/auto_save.sh`: recomendación, archivarlo fuera del árbol activo con registro en el manifiesto de higiene.
- **Tarea 7.2: invocación real y eficiencia.** Un registro por skill, cliente, tarea, tokens o tiempo y resultado, en `data/audits/skill_invocation_log.json`. La validación estática no cierra esta puerta.
- **Tarea 7.3: licencias (SPEC-001).** Con aprobación del propietario, publicar los pedidos de `docs/research/license_requests.md` (acción externa). Registrar la fecha y el enlace de cada pedido. La excepción vence el 2027-06-30: nunca se inventa una licencia.
- **Cierre:** puerta, STATUS y publicación. SPEC-001 queda en `verified_with_exceptions` hasta que lleguen las respuestas.

---

## Módulo 8: entrenamiento y evaluación (último; necesita autorización)

Necesita plan detallado propio (`docs/plans/modulo8_campana.md`) y la autorización explícita del propietario para cada etapa, que se lanza con `--owner-authorized` (sección 4 de ese plan).

- **Tarea 8.1: piloto en Colab.** Prueba real del cuaderno: instalación, bloqueo de Drive, desconexión y reanudación (SPEC-008, pendiente 4 de STATUS). Copia de los artefactos fuera de la máquina, con copia y restauración que verifican cada SHA-256 contra `drive_sync_manifest.json`. Los intentos de la campaña no generan `evidence.json`, y `backup_run` los rechaza.
- **Tarea 8.2: HPO, congelado y confirmación.** Selección sobre validación con los cargadores nativos (FR-N09) y `configuration_freezes.json` por etapa.
- **Tarea 8.3: sensibilidad** (escenarios; el propietario decidió el 2026-11-08 que los 17 edificios, incluido B01, entrenan en todas las etapas; no hay campaña sin B01 y la sensibilidad sin B01 queda solo en la evaluación (D-M2-4)) y evaluación congelada en `test`.
- **Tarea 8.4: informe estadístico multisemilla** (módulo 4) y selección.
- **Tarea 8.5: tesis.** SPEC-006 (vista multiobjetivo, §3.1.3, APA y los dos DOCX canónicos); observaciones experimentales del jurado (SPEC-009); D04 y los supuestos económicos con IRENA y la tasa social del MEF (SPEC-013 y SPEC-014); retirar `iquitos_v1` (D01).
- **Tarea 8.6: aceptación integral (fase 8 de STATUS).**
  - Se marca solo con todas las puertas acreditadas sobre la revisión que se integra.
  - Después: `scientific_acceptance` según la evidencia, SPEC-000 FR-005 y FR-007, y FR-N17 y FR-N18 (programación y GitHub).

---

## Decisiones del propietario, por el módulo que bloquean

| Decisión | Bloquea | Recomendación |
|---|---|---|
| Confort térmico y 18 000 BTU/h por split | 3b.2 | Norma para clima cálido y húmedo; el valor típico solo donde no haya norma |
| m² por plaza (RNE), 5 % de vehículos eléctricos, potencia por tipo de vehículo | 3b.3 | Usar RNE, MINEM y una fuente citada; declarar el escenario a 2030 |
| Facturas de B11, B09, B03, B14, B02, B12, B16, B17, B08 y B13 (D-V6-20) | Ya no bloquea | Cerrada por D-V6-58 (propietario, 2026-11-08): B11 se completa con su segundo suministro y los otros 9 se tratan como completos, bajo el tope de D-V6-19 |
| Umbral de desviación de picos | 3b.4 | Proponerlo con los datos de facturas en mano |
| 16 herramientas | 5.2 | Una por una, con recomendación |
| Borrar ramas `codex/*` y `cursor/*` | 6.2 | Registrar su commit y borrarlas |
| Hook heredado | 7.1 | Archivarlo |
| Publicar los pedidos de licencia | 7.3 | Publicarlos |
| Autorizar etapas en Colab | 8 | Solo tras cerrar los módulos 3 a 7 |

## Orden y paralelismo

`3 → 3b → 4 → 5 → 6 → 7 → 8`. Los módulos 4, 6 y 7 tocan archivos separados de 3b y podrían ir en paralelo, en worktrees propios y con responsables distintos. Pero la regla del propietario es cerrar uno por uno, así que el paralelismo solo se usa si él lo autoriza.
