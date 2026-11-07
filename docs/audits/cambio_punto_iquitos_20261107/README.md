# Viabilidad del reparto por punto de cambio en Iquitos (2026-11-07)

**Spec:** [SPEC-016](../../../specs/016-iquitos-v6/spec.md), FR-016.1 original · **Decisión resultante:** D-V6-14
**Reproducción:** `.venv39-citylearn-v3/Scripts/python.exe docs/audits/cambio_punto_iquitos_20261107/reproductions.py`

## Pregunta

¿Puede la regresión con punto de cambio de ASHRAE Guideline 14 (modelo de 3 parámetros para refrigeración, `E/día = b0 + b1·max(0, T − Tb)`) separar la refrigeración de la carga base con las facturas mensuales de los 17 edificios?

## Datos

- **Energía:** punta + fuera de punta de `CityLearn/data/buildingcsv/B_*.csv` (D-V6-15), 2023-2025. Quedan 33 meses por edificio (25 en B06) con energía mayor que 0.
- **Temperatura:** media mensual de T2M de NASA POWER en `data/campaigns/iquitos_v5/raw/weather/`, en hora local (UTC−5).

## Resultado

La temperatura media mensual va de 24,98 a 26,92 °C: un rango de 1,94 °C en 36 meses. La refrigeración funciona todo el año, así que ningún mes queda por debajo de la temperatura de balance. La regresión solo estima la sensibilidad marginal por encima de `Tb`, no la energía total de refrigeración.

| Edificio | Pendiente (kWh/día·°C) | t | CV(RMSE) | Refrigeración estimada |
|---|---|---|---|---|
| B01 | +1 510 | +0,56 | 12,2 % | 1 % |
| B02 | −87 | −1,83 | 45,2 % | −13 % |
| B03 | −3 273 | −5,44 | 27,9 % | −17 % |
| B04 | +266 | +2,12 | 6,8 % | 3 % |
| B05 | +306 | +2,82 | 6,5 % | 3 % |
| B06 | +1 243 | +1,24 | 6,2 % | 4 % |
| B07 | +1 027 | +2,00 | 29,5 % | 3 % |
| B08 | −115 | −2,45 | 19,2 % | −5 % |
| B09 | −5 | −0,32 | 14,0 % | −1 % |
| B10 | +667 | +3,36 | 12,1 % | 7 % |
| B11 | −300 | −1,62 | 13,2 % | −3 % |
| B12 | +580 | +2,48 | 7,7 % | 4 % |
| B13 | +44 | +3,48 | 13,6 % | 9 % |
| B14 | +26 | +3,34 | 12,6 % | 8 % |
| B15 | −1 073 | −2,55 | 24,5 % | −3 % |
| B16 | +171 | +1,38 | 16,0 % | 5 % |
| B17 | +191 | +4,44 | 8,3 % | 7 % |

- **Pendiente negativa en 6 edificios** (B02, B03, B08, B09, B11 y B15): físicamente imposible para un modelo de refrigeración.
- **Estimación no significativa en 8 edificios** (|t| < 2).
- **Hospital B11:** con 120 splits, la regresión le atribuye −3 % de refrigeración.
- **Conclusión:** con un clima casi constante, la regresión no puede identificar la parte de la factura que corresponde a la refrigeración. FR-016.1 en su redacción original queda sustituido por D-V6-14.

## Otros hallazgos de los datos

- **`totalEnergiaActiva` no coincide con punta + fuera de punta** en B02 (36 de 37 meses), B09 (34), B11 (34), B16 (36) y B17 (36). Se usa la suma de punta y fuera de punta (D-V6-15), como ya documenta la destilación.
- **`B_04.csv` tiene 1 012 863 filas**, de las que solo 37 tienen datos; el resto son filas vacías de la exportación. Los lectores deben descartar las filas vacías.

## Límites

- Prueba de viabilidad, no modelo final.
- La rejilla de `Tb` cubre solo el rango observado.
- No se probaron los modelos de 4 o 5 parámetros: con un rango de 2 °C tampoco pueden identificar la temperatura de balance.
