# Refrigeración física con tope en la factura, datos de 2023 (2026-11-07)

**Spec:** [SPEC-016](../../../specs/016-iquitos-v6/spec.md), D-V6-16, D-V6-18 y D-V6-19
**Reproducción:** `.venv39-citylearn-v3/Scripts/python.exe docs/audits/calibracion_refrigeracion_20261107/reproductions.py`, que usa `calibrate_building_physical` sin escribir archivos.

**Corrección:** una primera versión de esta auditoría usaba 24 °C como objetivo del COP de CityLearn. Ese parámetro es la temperatura del refrigerante (la del esquema, 8,5 °C por defecto), no el setpoint de la sala. Con 24 °C el COP quedaba recortado a 20 y la refrigeración física salía unas 5 veces más baja. Las cifras de abajo usan el COP correcto.

## Método

| Elemento | Origen |
|---|---|
| Capacidad | `hvac_capacity_kw` (D-V6-16) |
| Carga parcial | Diferencia de entalpía horaria de `weather.csv` de `train_2023` respecto al percentil 99, multiplicada por el horario de `configs/dataset/building_types.yaml` |
| COP | El de la bomba de calor de CityLearn, con `eta` y objetivo de refrigerante del esquema |
| Facturas | Bloques de punta y fuera de punta de 2023 (D-V6-15) |
| Tope | 70 % de cada bloque |

## Resultado

| Edificio | kW térmicos | COP de diseño | kW eléctricos | Física / factura | Refrigeración final | Meses recortados |
|---|---|---|---|---|---|---|
| B01 | — | — | — | — | — | Sin factura medida (`B_01.csv` lo genera el proyecto); la función falla cerrada |
| B02 | 211 | 2,51 | 84 | 325,7 % | 61,9 % | 12 |
| B03 | 2 043 | 2,69 | 760 | 380,8 % | 70,0 % | 12 |
| B04 | 152 | 2,69 | 56 | 12,2 % | 12,2 % | 0 |
| B05 | 280 | 2,69 | 104 | 49,1 % | 49,1 % | 2 |
| B06 | 3 473 | 2,69 | 1 291 | 40,4 % | 38,6 % | 1 |
| B07 | 90 | 2,24 | 40 | 43,3 % | 41,5 % | 3 |
| B08 | 158 | 2,24 | 71 | 124,7 % | 60,0 % | 12 |
| B09 | 257 | 2,51 | 102 | 806,0 % | 70,0 % | 12 |
| B10 | 798 | 2,51 | 318 | 46,9 % | 46,9 % | 0 |
| B11 | 5 700 | 2,24 | 2 544 | 1 194,7 % | 70,0 % | 12 |
| B12 | 2 505 | 2,24 | 1 118 | 219,5 % | 70,0 % | 12 |
| B13 | 69 | 2,24 | 31 | 87,3 % | 68,7 % | 12 |
| B14 | 116 | 2,24 | 52 | 389,6 % | 70,0 % | 12 |
| B15 | 53 | 2,24 | 24 | 23,6 % | 23,6 % | 0 |
| B16 | 804 | 2,51 | 320 | 170,6 % | 70,0 % | 12 |
| B17 | 292 | 2,24 | 130 | 145,4 % | 70,0 % | 12 |

## Lectura

- **La física supera la factura en 11 de los 16 edificios con factura**, en los 12 meses. En ellos la fracción de refrigeración la fija el tope (70 %, `design_rule`) y no la física.
- **Solo 5 edificios conservan su física en su mayor parte:** B04, B10 y B15 sin ningún mes recortado; B05, B06 y B07 con entre 1 y 3 meses recortados.
- **Las facturas parecen bajas para el inventario.**
  - B11, el hospital regional, factura entre 1 666 y 3 035 kWh/día: unos 100 kW de media en 42 649 m², o 2,3 W/m².
  - B09, el COER con centro de datos, factura entre 94 y 176 kWh/día.
  - Dos explicaciones posibles: las facturas cubren solo uno de varios suministros, o el inventario sobreestima los equipos. Solo el propietario puede confirmarlo.
- **Tamaño del equipo en el esquema:** `nominal_power_kw` (kW eléctricos = térmicos ÷ COP de diseño) sale de la capacidad del inventario. Con facturas tan bajas, el equipo queda muy por encima de su uso medio.
- **Límite:** la carga parcial depende solo del aire exterior (`assumption` de D-V6-18). No incluye envolvente ni ganancias solares.
