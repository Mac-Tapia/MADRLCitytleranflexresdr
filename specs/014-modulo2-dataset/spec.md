# SPEC-014 — Módulo 2: dataset físico y reconexión

**Estado:** `implemented` (no implica aceptación científica)
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Estado conciliado:** [STATUS](../STATUS.md)
**Revisión:** 2026-11-05

## Propósito

Tras las tarifas (SPEC-013), lo que impide pasar del dataset al entrenamiento es que el dataset vigente no es físicamente defendible y que la configuración activa no apunta a él. Este módulo construye `iquitos_v5` con una FV acotada, hace bloqueante la auditoría de integridad y reconecta configuración, pruebas y documentos. "Módulo 2" es el nombre que usó el propietario; el repositorio no lo definía. No autoriza etapas ni entrena.

## Evidencia (solo lectura, `iquitos_v4`)

| Hallazgo | Evidencia | Origen |
|---|---|---|
| FV/carga del distrito 1,30; 12 de 17 exportadores netos; B14 66,4; B8 36,5; B2 25,3 | `audit/der_sizing_microgrids.json` | D3-001 |
| 17 de 17 edificios en la cota de área, y ninguna puerta mira FV/carga | `roof_bound_binding`, `gates` de `dataset_acceptance.json` | D3-001 |
| `csv_integrity` da `failed` con `dataset_verified=true` | 3 incidencias en `csv_integrity_manifest.json`; no está en `gates` | D3-005 |
| Exige `pricing.csv`, que la campaña no usa, y no audita los 68 `pricing_N.csv` | `audit_citylearn_csv_integrity.py:315` | D3-005 |
| `electric_vehicle_departure_time` llega a 61 en `charger_1_1.csv`, contra un rango `[-1, 24]` | 5 764 filas | D3-005 |
| La configuración activa usa `iquitos_v1`, que no cierra facturas | `configs/experiments/iquitos.yaml:3-5` | S9, R-A-073, D3-002 |
| La sensibilidad de B01 2023 está declarada y ninguna herramienta la ejecuta | `build_fresh_campaign_dataset.py:1287-1288` | D3-009 |

## Decisiones

Tomadas con la opción recomendada por delegación expresa del propietario (2026-11-04). Ninguna es un dato medido.

- **D-M2-1, límite FV/carga = 1,0 por edificio.** La cota del LP pasa a `min(cota de área, carga anual 2023 / producción anual por kWp)`. **Acota dos decisiones del propietario del 2026-11-01, sin retirarlas:** el área utilizable sigue siendo 0,63 y la exportación sigue acreditada 1:1. Razón: con crédito 1:1 y sin otra cota, el LP llena el techo y el edificio pasa a ser una planta exportadora, esquema que hoy no existe en Iquitos. Es criterio de diseño del proyecto, sin norma que lo respalde; se declara `design_rule` y **el propietario puede revertirlo cambiando un valor** (`pv.max_pv_to_load_ratio`).
- **D-M2-2, integridad bloqueante.** `csv_integrity` entra en `gates`; audita los `pricing_N.csv` referenciados por el esquema y deja de exigir `pricing.csv`.
- **D-M2-3, campaña nueva.** `iquitos_v5`, con `campaign_id` propio. `iquitos_v1` a `iquitos_v4` no se tocan.
- **D-M2-4, sensibilidad de B01.** Implementada en la evaluación: el mismo episodio resumido sin B01 (`compare_campaign_baselines.py`, `sensitivity_without_modeled`). Mide cuánto pesa B01 en la evaluación; **no elimina la fuga al entrenar** con B01 2023, que requiere entrenar sin ese edificio y queda pendiente de una etapa autorizada.

## Requisitos funcionales

- **FR-014.1** — Cota FV: `tools/dataset/size_der_microgrids.py` expone una función pura que da la cota por carga. El constructor pasa al LP el mínimo de ambas cotas y registra cuál limita.
- **FR-014.2** — Puerta `pv_to_load_bounded`: falla si algún edificio supera el límite en 2023. Sin el valor en `der_economics.yaml`, falla.
- **FR-014.3** — Integridad: el auditor valida los `pricing_N.csv` del esquema con filas, columnas, NaN y negativos; la puerta `csv_integrity` exige `status == ok`.
- **FR-014.4** — Rango EV: `electric_vehicle_departure_time` es una cuenta atrás en horas (`dimension_ev_chargers.py`); 61 h es una estancia de viernes a lunes. Se corrigió el auditor, con tope de una semana.
- **FR-014.5** — Construcción real de `iquitos_v5` con las puertas de SPEC-013 y las nuevas; `dataset_verified=true` sin excepciones.
- **FR-014.6** — Reconexión: `configs/experiments/iquitos.yaml`, pruebas, runbook y cuadernos pasan a `iquitos_v5` (S9). Sin debilitar pruebas. `tools/dataset/build_bill_tariffs.py` y la tabla de factura se comprueban contra `iquitos_v5`.
- **FR-014.7** — Línea base: RBC frente a sin almacenamiento sobre `iquitos_v5`, como evidencia para S7, con `compare_campaign_baselines.py`.

## Fuera de alcance

- Entrenar, Colab real, autorizar etapas. `authorized_stages=[]` y `scientific_acceptance=false` no cambian.
- Recompensar la factura (D04): decisión del propietario.
- Verificar CAPEX, tasa de descuento y demás supuestos `assumption_pending_user_verification`: requieren fuentes del propietario.
- Picos horarios sin contraste (D3-008) y refrigeración residual (D3-006): se registran como pendientes.

## Criterios de aceptación

1. Pruebas enfocadas nuevas en rojo antes de implementar y en verde después.
2. `iquitos_v5` construida, con `dataset_verified=true` y FV/carga ≤ 1,0 en los 17 edificios.
3. Puerta `-Scope Repository` aprobada sobre el commit final.
4. Huellas de `iquitos_v1` a `iquitos_v4` idénticas antes y después.
5. Ningún estado científico cambia.

## Resultado (2026-11-05)

**Construcción:** `iquitos_v5`, `fresh_iquitos_20261105_v5`, `dataset_hash` `3c693d93…`, 10 de 10 puertas, `dataset_verified=true`. Una primera construcción falló su propia puerta `pv_to_load_bounded` (B14 llegó a 1,165): el límite usaba el rendimiento de un sistema de referencia de 100 kWp y los sistemas pequeños rinden más por kWp con su propio inversor. Se corrigió con `fit_pv_modules`, que ajusta con el sistema real; la construcción rechazada se conserva en `data/maintenance/dataset_builds/failed/iquitos_v5_20261105T1350/`.

| Medida | `iquitos_v4` | `iquitos_v5` |
|---|---|---|
| FV/carga del distrito | 1,30 | 0,51 |
| FV/carga máxima por edificio | 66,4 (B14) | 0,999 |
| Exportadores netos en el año | 12 de 17 | 0 |
| `csv_integrity` | `failed`, sin bloquear | `ok`, bloqueante |
| BESS total | 6 796 kWh | 6 796 kWh (dimensionado en 18:00-23:00, sin sol) |

**Línea base** (`validation_2024`, semilla 0, RBC frente a sin almacenamiento; `data/maintenance/integracion/c20261101i01/S10/baselines_v5_v4_validation_2024.json`):

| Medida | `iquitos_v4` | `iquitos_v5` | `iquitos_v5` sin B01 |
|---|---|---|---|
| Factura sin almacenamiento | 161 272 USD | 1 758 631 USD | — |
| Factura | −4,80 % | −0,44 % | −0,50 % |
| CO₂ | +1,71 % | +0,69 % | +0,78 % |
| Pico del distrito | −2,02 % | −1,95 % | −2,00 % |

Los valores de `iquitos_v4` reproducen exactamente la evidencia D02. El −4,8 % de `v4` estaba inflado por una base casi anulada por el crédito de exportación. Factura y CO₂ siguen en sentidos opuestos: apoya S7 sin cumplirlo (una semilla, RBC). Sin B01 las conclusiones cambian menos de 0,1 puntos. Hay 3 356 MWh exportados en horas de sol aunque ningún edificio exporte en el balance anual.

**Reconexión:** configuración, pruebas, cuadernos, runbook y README apuntan a `iquitos_v5`. Se conservan con su nombre las líneas que registran medidas sobre `iquitos_v1`, y la prueba de velocidad de deriva EV sigue en `iquitos_v1`, la única con flota de 1 850 vehículos. La prueba de facturación neta ahora exige el crédito por exportación que `iquitos_v1` no tenía.

**Defecto encontrado de paso:** `fresh_policy._under` rechazaba toda entrada de campaña en Linux, donde entrena Colab. Lo destapó el primer CI que llegó a ejecutarse; corregido con prueba.

**Puerta completa (2026-11-06):** `-Scope Repository` aprobada sobre `f27b8592`: 1 612 pruebas, 0 fallos, 0 omitidas, `software_acceptance=true`, `scientific_acceptance=false` (`data/maintenance/gates/Repository_profile_20261106T000821675Z.json`). Una corrida anterior sobre `98a94e95` se rechazó por un identificador de campaña viejo en tres pruebas (`Repository_profile_20261105T214556131Z.json`); corregido en `f27b8592`.
