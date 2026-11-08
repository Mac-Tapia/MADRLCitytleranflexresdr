# Módulo 3b: constructor de `iquitos_v6` (plan TDD)

**Spec:** [SPEC-016](../../specs/016-iquitos-v6/spec.md) y [SPEC-017](../../specs/017-universalidad/spec.md) · **Plan general:** [implementacion_completa.md](implementacion_completa.md)
**Fecha:** 2026-11-07 · **Entrenar:** no (módulo 8)

## Qué hay y qué falta

Piezas ya publicadas, cada una con sus pruebas:

| Pieza | Módulo | Decisiones |
|---|---|---|
| Capacidad de climatización | `uc3m/application/dataset/hvac_capacity.py` | D-V6-14, D-V6-16, D-V6-17 |
| Calibración física con techo de factura | `uc3m/application/dataset/cooling_calibration.py`, `tools/dataset/distill_building_loads.py` (`calibrate_building_physical`) | D-V6-18, D-V6-19, D-V6-20 |
| Archivos de tarifa de factura | `uc3m/application/dataset/bill_tariff.py` | D-V6-8 |
| BESS con doble función | `uc3m/application/dataset/bess_sizing.py` | D-V6-7, D-V6-30 |
| Flota, cargadores y cola FIFO | `uc3m/application/dataset/ev_sizing.py`, `ev_queue.py` | D-V6-21 a D-V6-33 |
| Sitio, edificios y puerta de operatividad | `uc3m/application/dataset/site.py`, `CityLearn/citylearn/v3/backend_contract.py` | SPEC-017 |

Falta unirlas en un dataset. El constructor de `iquitos_v5` (`tools/dataset/build_fresh_campaign_dataset.py`) sigue siendo la base: conserva sus fuentes crudas, sus 10 puertas y la puerta de operatividad v3 (FR-016.9, FR-017.4).

## Tareas, en orden de dependencia

### T1: escritor de cargadores y vehículos (D-V6-27 a D-V6-35) — hecho

Hecho el 2026-11-07: `tools/dataset/write_ev_v6.py`, 4 pruebas en `tests/fresh_training/test_write_ev_v6.py` (RED→GREEN), incluida la carga en CityLearn v3.

- **Archivos:** nuevo `tools/dataset/write_ev_v6.py`; parámetros de batería y cargador por clase en `configs/dataset/ev_v6.yaml`.
- **Produce:** `write_ev_fleet(dataset_dir, schema, plans, *, registry, rules, days, inventory) -> dict`. Escribe un `charger_<edificio>_<n>.csv` por cargador (columnas `ChargerSimulation`), sus entradas `chargers` en el esquema y una entrada en `electric_vehicles_def` por vehículo. Devuelve el informe por clase: factor de carga, sesiones sin atender, recorridos sin energía, potencia instalada y tope de FC.
- **Pruebas:**
  - cada cargador del plan tiene su CSV y su entrada en el esquema;
  - cada id del CSV existe en `electric_vehicles_def`, con la batería de su clase;
  - solo las camionetas tienen `max_discharging_power` > 0, igual a 6,6 kW (D-V6-32);
  - modo, conector y norma de cada cargador salen de `classes.<clase>.charging` (D-V6-33);
  - CityLearn v3 carga un edificio de prueba con el esquema resultante.
- **Faltan valores con origen:** eficiencia y profundidad de descarga de la batería, eficiencia del cargador y potencia mínima de carga por clase. El piloto de B01 los tenía como `assumption` (0,92, 0,80, 0,95 y 6 A). Se proponen como P-V6-17, sin inventar valores nuevos.

### T2: carga base y refrigeración física en el constructor (FR-016.1 a FR-016.3)

- Reemplaza el reparto residual por `calibrate_building_physical` y escribe los meses recortados en `quality_flags` (D-V6-19).
- Retira las lavadoras del esquema y de las acciones (decisión de SPEC-016).
- **Pruebas:**
  - cada factura mensual se reproduce, punta más fuera de punta;
  - la carga base es positiva en todas las horas;
  - ningún edificio conserva `washing_machines`.

### T3: tarifa de factura y BESS doble en el constructor (FR-016.6 y FR-016.7)

- Escribe `bill_tariff_Building_<b>.csv` con `write_bill_tariff_files` y dimensiona el BESS con `size_bess` (excedente, vehículos y recorte de punta).
- **Prueba:** la conservación anual del BESS cierra en ±1e-6.

### T4: contraste de picos (FR-016.8)

- Nuevo `tools/dataset/audit_peak_contrast.py`: por edificio y mes, el pico generado frente al pico medido (factor de carga y máxima demanda de `resultados_preliminares.xlsx`).
- **Umbral:** lo fija el propietario con los datos a la vista (plan general, tabla de decisiones).

### T5: construcción y puertas (FR-016.9)

- `python tools/dataset/build_fresh_campaign_dataset.py --campaign-id <id> --storage-alias iquitos_v6`
- **Resultado esperado:** `dataset_acceptance.json` con `dataset_verified=true`, las 10 puertas de v5 más las nuevas y `v3_operational` en verde.
- **Riesgo:** el constructor descarga fuentes con red (NASA POWER, Osinergmin y Banco Mundial). Si no hay red, la construcción se detiene; no se reutilizan resultados viejos.

### T6: sitio sintético (SPEC-017, criterio 1)

- Un sitio de prueba con 2 edificios, otro clima, otra tarifa y otro bloque construye un dataset operativo sin tocar el código.
- Requiere que las fuentes crudas entren como archivos locales del sitio, sin descargas.

### T7: capa v3 (3b.5, FR-016.10 y FR-016.11)

- **Recompensa y observaciones:** la recompensa con factura y las observaciones (pico del mes, bloque, tarifa y confort) se implementan en `CityLearn/citylearn/v3/`.
- **V2B:** la descarga V2B se limita a la demanda del edificio (D-V6-28).
- **Pruebas:**
  - prueba de la tupla;
  - prueba de humo de los 4 MADRL.

## Decisiones del propietario para T1 (2026-11-07)

- **D-V6-34:** los parámetros de batería y cargador de las 3 clases son los supuestos del piloto (0,92; 0,80; 0,95; 6 A).
- **D-V6-35:** el agente modula la potencia de carga en las 3 clases; en el modo 2 es un supuesto declarado.

## Preguntas abiertas para el propietario

- **Umbral del contraste de picos (T4).**


## Cadena completa hasta los resultados (propietario, 2026-11-07)

Instrucción: todo implementado, sincronizado y vinculado en el proyecto, hasta los resultados. Cada decisión sigue la cadena **spec → configuración → código → prueba → dataset → KPI → resultados**, y una prueba de trazabilidad falla si un eslabón falta.

| # | Tarea | Decisiones | Capa | Estado |
|---|---|---|---|---|
| 1 | Nombres de los CSV de cargador `charger_*.csv` (falló la integridad en `iquitos_v6_trial2`) | D-V6-37, D-V6-38 | `tools/dataset/write_ev_v6.py` | hecho (commits `b9be9c9b` a `93591dbe`) |
| 2 | Llegadas Bernoulli por el factor del día y km lognormales truncados a la autonomía | D-V6-39, D-V6-40, P-V6-21 | `uc3m/application/dataset/ev_queue.py`, `ev_v6.yaml` | hecho (commits `b9be9c9b` a `93591dbe`) |
| 3 | Tiempo de carga con eficiencias y curvas de batería fijas; SOC pedido alcanzable | revisión de código, hallazgo 2 | `ev_queue.py`, `write_ev_v6.py` | hecho (commits `b9be9c9b` a `93591dbe`) |
| 4 | Un paso libre entre sesiones de una toma y los detalles del formato `ChargerSimulation` | revisión de código, hallazgos 5 y 6 | `ev_queue.py` | hecho (commits `b9be9c9b` a `93591dbe`) |
| 5 | Camioneta conectada hasta su salida | D-V6-42 | `ev_queue.py` | hecho (commits `b9be9c9b` a `93591dbe`) |
| 6 | Tomas al percentil 95 de 20 semillas | D-V6-43 | `ev_queue.py` | hecho (commits `b9be9c9b` a `93591dbe`) |
| 7 | SOC real de llegada en la capa v3 | D-V6-41 | `CityLearn/citylearn/internal/runtime.py` (fork) | hecho (commits `b9be9c9b` a `93591dbe`) |
| 8 | Descarga V2B acotada a la demanda del edificio, sin exportación | D-V6-28, D-V6-32 | capa v3 del fork | hecho (commits `b9be9c9b` a `93591dbe`) |
| 9 | BESS de doble función en el constructor | D-V6-7, D-V6-30 | `bess_sizing.py` → constructor | hecho (commits `b9be9c9b` a `93591dbe`) |
| 10 | Construcción `iquitos_v6_trial3` con todas sus puertas en verde; después `iquitos_v6` | FR-016.9, FR-017.4 | constructor | hecho: `iquitos_v6` (12/12); sustituido como activo por `iquitos_v6_trial7` (12/12, hash `ca01c2f3…`, tarifas en los splits) |
| 11 | Recompensa con factura y observaciones (pico del mes, bloque, tarifa) | D04, D-V6-8 | `CityLearn/citylearn/v3/reward.py` | hecho (CityLearn `5e62c5f5`, principal `064c3345`; D-V6-50, P-V6-24) |
| 12 | Misma rejilla de acciones para los 4 MADRL | D-M3-7, P-M3-1, P-M3-2 | capa v3 y adaptadores | pendiente, a confirmar |
| 13 | Contrato de la tupla de v3: término de recompensa → eje → KPI; los 26 KPI comparables (12/5/9) medidos para los 4; `bill_cost_total` con los archivos de tarifa de v6; `price_signal_deviation` aplicable o no aplicable; V2B en lugar de `ev_v2g_export_total` | FR-016.11 | `tests/fresh_training/test_v3_tuple_contract.py` | hecho: `tests/fresh_training/test_v3_tuple_contract.py` y `uc3m/application/evaluation/tuple_contract.py`; aire acondicionado aplazado por D-V6-51. Pendiente: KPI comparables medidos para los 4 (requiere la fila 15) |
| 14 | Prueba de trazabilidad: cada decisión del propietario de SPEC-015, 016 y 017 aparece en configuración o código | SPEC-017 FR-017.5 | `tests/fresh_training/test_decision_traceability.py` | hecho: `governance/decision_traceability.yaml` (113 identificadores: 63 con código, 43 pendientes de los que 35 están implementados sin etiqueta, 6 sustituidos, 1 de proceso) y `tests/fresh_training/test_decision_traceability.py` |
| 15 | Prueba de humo de los 4 MADRL sobre `iquitos_v6` y requisitos de memoria recalculados | FR-016.10 | — | hecho: requisitos de memoria recalculados sobre `iquitos_v6_trial7` (MASAC 25 GiB RAM, 53 GiB VRAM); `test_real_learning.py` sobre la campaña activa (antes fijo en `iquitos_v5`): los 4 MADRL actualizan, cambian parámetros y guardan `training_state.pt` (8 pruebas) |
| 16 | Estadística por hipótesis (HE1 a HE3, H-G) y selección del mejor global (OG) | módulo 4 | — | pendiente |
| 17 | Entrenamiento y resultados | módulo 8 | — | pendiente, necesita autorización |
