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

### T1: escritor de cargadores y vehículos (D-V6-27 a D-V6-33)

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
