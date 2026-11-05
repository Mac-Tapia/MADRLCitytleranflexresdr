# SPEC-013 — Módulo 1: tarifas oficiales del dataset

**Estado:** `implemented` (no implica aceptación científica ni construcción nueva)  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Estado conciliado:** [STATUS](../STATUS.md) · **Plan detallado:** [modulo1_tarifas.md](../../docs/plans/modulo1_tarifas.md)  
**Revisión:** 2026-11-04

## Propósito

El módulo 1 es la entrada tarifaria de la primera etapa del flujo de SPEC-011 (dataset). Incorpora los PDF oficiales de tarifas en barra de Osinergmin (PBA) como fuente trazable y los contrasta con los pliegos de usuario final que ya usa el dataset. No cambia ningún dataset ni el precio que ve el simulador.

"Módulo 1" es el nombre que el propietario usó el 2026-11-04. El repositorio no lo definía; este SPEC fija su alcance.

## Por qué hace falta

El dataset solo guarda el pliego de usuario final (HTML, `tools/dataset/osinergmin_pliegos.py`). Ese pliego no muestra el precio en barra del sistema aislado, y nada comprueba el precio con una segunda publicación oficial. El PDF PBA separa dos precios del mismo sistema que el proyecto no distinguía:

| Precio (Electro Oriente, MT, 04/07/2025) | Potencia S/./kW-mes | Energía ctm. S/./kWh | Significado |
|---|---|---|---|
| En barra (Cuadro 1) | 32,12 | 78,58 | Precio en barra del sistema aislado |
| Efectivo (Cuadro 10) | 32,12 | 34,71 | Precio efectivo de la misma publicación |

## Resultado de la ingesta real (2026-11-04)

Con `tools/dataset/ingest_osinergmin_pba.py` y `pypdf` 6.10.2. Datos en `data/tariffs/osinergmin/`.

- 37 vigencias PBA, de 2022-12-04 a 2025-12-04. En todas se extrajeron las dos filas de Electro Oriente.
- Punta y fuera de punta son iguales en las 37 vigencias, en barra y en efectivo. **No hay señal horaria oficial para Iquitos en esta fuente.**
- Energía en barra: 74,23 a 80,12 ctm/kWh. Efectiva: 26,45 a 40,83 ctm/kWh.
- Energía MT3 del pliego / energía efectiva, en las 34 vigencias comunes: 1,0226 a 1,0228 hasta 2023-10-04 y 1,0110 a 1,0114 desde 2023-11-04. El cambio de escalón no tiene causa identificada.
- Solo en PDF: 2023-05-04, 2024-03-04 y 2025-01-04. La primera tiene efectivo 36,89, y 36,89 × 1,0228 da los 37,73 de los pliegos de mayo de 2023, fechados 01 y 26 de mayo; las otras dos repiten los valores de la vigencia anterior.
- Solo en HTML, sin PDF localizado: 2023-05-01, 2023-05-26, 2023-11-01, 2024-05-01, 2024-11-01, 2025-01-01, 2025-05-01 y 2025-11-01.
- La fila de Electro Oriente se atribuye a Iquitos por inferencia: el pliego rotula el sector como aislado y la razón con el pliego es estable, pero el PDF no nombra Iquitos.

## Vínculos y conexiones

```text
Osinergmin PBA (PDF) ──> [MÓDULO 1: ingesta y contraste] ──> data/tariffs/osinergmin/ (manifiesto + CSV)
                                     ^
Osinergmin pliego (HTML) ──> tools/dataset/osinergmin_pliegos.py
                                     |
                                     v  (puerta tariff_crosscheck, solo construcciones nuevas)
tools/dataset/build_fresh_campaign_dataset.py
  ├─ tariff_signals ─> pricing_N.csv ─> split_campaign ─> schema.json
  │     └─> CityLearn scenario_manager (mode: flat) ─> recompensa y KPI de costo
  ├─ demand_usd_kw_month ─> size_der_microgrids (FV y BESS)
  └─ tariff_bill_validation ─> audit/ y provenance.json ─> dataset_acceptance.json
```

| Conexión | Archivo | Relación con el módulo |
|---|---|---|
| Pliego de usuario final | `tools/dataset/osinergmin_pliegos.py` | Solo lectura: `parse_sheet` da el lado HTML del contraste |
| Constructor | `tools/dataset/build_fresh_campaign_dataset.py` | Desbloqueado por el propietario el 2026-11-04 ([traspaso](../../docs/plans/traspaso_sesiones.md)); añade la puerta y no cambia el precio |
| Procedencia | `uc3m/application/dataset/provenance.py` | Se reutiliza `official_tariff_sheet`; no se añade tipo |
| Raíces permitidas | `governance/repository_layout.yaml`, `fresh_policy.py:174` | Se registra la raíz cruda nueva |
| Simulador | `CityLearn/citylearn/scenario_manager.py:332-334` | Sin cambios; el aplanado lo gobierna D02 |
| Evaluación | `tools/dataset/compare_campaign_baselines.py`, `kpi_contract.py` | Sin cambios; consumidores futuros de la decisión D02 |
| Puertas | SPEC-011, puerta D01 (S7, S10) | El contraste aporta evidencia a D02; no cumple S7 por sí solo |

## Arquitectura

Sigue el monolito modular de puertos y adaptadores (`uc3m/`), con la herramienta como raíz de composición. No se crea un puerto: hay una sola implementación y `docs/plans/entrenamiento.md` pide no crear jerarquías para funciones puras.

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Dominio | `uc3m/domain/tariffs.py` | `BusbarPrice`, `BusbarSheet`; sin E/S |
| Adaptador | `uc3m/adapters/osinergmin/pba_pdf.py` | Nombres de URL, descarga, texto de PDF a `BusbarSheet` |
| Aplicación | `uc3m/application/dataset/tariff_crosscheck.py` | Cobertura y contraste, puro |
| Herramienta | `tools/dataset/ingest_osinergmin_pba.py` | Compone lo anterior y escribe los artefactos |

## Requisitos funcionales

- **FR-013.1** — Descarga: guarda cada PBA tal como llega en `data/tariffs/osinergmin/raw/`, con URL, SHA-256 y fecha de obtención. Un 404 en todas las variantes de nombre es `missing`. Cualquier otro error HTTP detiene la ingesta: un servidor que bloquea se informa, no se elude.
- **FR-013.2** — Identidad: rechaza una respuesta que no empiece por `%PDF` o cuya fecha impresa («ACTUALIZADO AL …») difiera de la vigencia pedida.
- **FR-013.3** — Extracción: obtiene exactamente dos filas del sistema pedido (barra y efectivo), de la columna actualizada. Si falta una fila o un número, falla; nunca rellena con cero.
- **FR-013.4** — Inmutabilidad: un archivo ya registrado cuyo SHA-256 cambie se rechaza con `source_changed` sin sobrescribir.
- **FR-013.5** — Contraste: para cada vigencia común exige punta = fuera de punta en PDF y pliego, y energía MT3 / energía efectiva dentro de `[1,005; 1,030]`. Esa banda es criterio del proyecto, derivado de lo observado, no de una norma.
- **FR-013.6** — Cobertura: declara `pdf_only` y `sheet_only`; nunca interpola una vigencia sin PDF.
- **FR-013.7** — Artefactos: `data/tariffs/osinergmin/busbar_electro_oriente.csv` y `pba_manifest.json` se versionan; los PDF no. `--offline` regenera ambos desde los PDF y verifica hashes, sin red.
- **FR-013.8** — Conexión: el constructor escribe `audit/tariff_crosscheck.json`, añade la puerta `tariff_crosscheck` y falla si un pliego usado tiene punta distinta de fuera de punta (D3-035). Sin el CSV de barra, la puerta falla. Afecta solo a construcciones nuevas y no depende de D02, porque no cambia el precio.

## Fuera de alcance

- Modificar `iquitos_v1` a `iquitos_v4`, reconectar la configuración o autorizar etapas.
- Cambiar el precio del simulador, la recompensa o el KPI de costo (D02).
- Inventar una tarifa horaria: las fuentes oficiales revisadas no la dan para este sistema.
- Dimensionamiento FV, tratado aparte, y la corrección general de `csv_integrity` (D3-005).

## Decisión del propietario que este módulo informa (D02)

| Opción para el costo evaluado | Precio de energía | Consecuencia |
|---|---|---|
| Factura del usuario (vigente) | Pliego / efectivo | Refleja lo que paga el edificio; costo y CO₂ casi colineales |
| Costo del sistema aislado | En barra | Otra magnitud, unas 2,3 veces mayor en 2025; no es lo que factura el edificio |
| Factura con cargo por potencia | Pliego + potencia | Único camino oficial con incentivo temporal claro; el componente sigue `unverified` en `tariff_bill_validation` |

## Criterios de aceptación

1. `tests/fresh_training/test_tariff_busbar.py` pasa, sin red y sin omisiones.
2. `--offline` sobre los PDF reales termina con salida 0 y cero fallos, reporta 37 vigencias y reproduce las listas `pdf_only` y `sheet_only` de arriba.
3. Las huellas de `data/campaigns/` son idénticas antes y después.
4. Ningún estado científico cambia: `scientific_acceptance=false`, `authorized_stages=[]`.

## Dependencias

- Requiere: SPEC-001 (procedencia).
- Informa: D02 y S7 de la puerta D01; SPEC-011.
- Lo que cambie el precio del simulador sigue dependiendo de D02, fuera de este módulo.

## Fuentes

Documentos oficiales consultados el 2026-11-04. Son fuente de los valores, no de la banda de contraste.

- Osinergmin. (2025). *Precios en barra del SEIN, precios en barra y precios efectivos de sistemas aislados, actualizado al 04/julio/2025*. <https://www.osinergmin.gob.pe/seccion/centro_documental/gart/PliegosTarifarios/1%20PBA04072025.pdf>
- Osinergmin. (2025). *Resolución N.° 048-2025-OS/CD*. <https://www.osinergmin.gob.pe/Resoluciones/pdf/2025/Osinergmin-048-2025-OS-CD.pdf>. Citada por el PBA; su texto no se revisó en detalle.
