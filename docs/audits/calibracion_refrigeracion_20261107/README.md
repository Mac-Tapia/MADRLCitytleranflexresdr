# Refrigeración física con tope en la factura, datos de 2023 (2026-11-07)

**Spec:** [SPEC-016](../../../specs/016-iquitos-v6/spec.md), D-V6-16, D-V6-18 y D-V6-19
**Reproducción:** `.venv39-citylearn-v3/Scripts/python.exe docs/audits/calibracion_refrigeracion_20261107/reproductions.py`

## Método

| Elemento | Origen |
|---|---|
| Capacidad | `hvac_capacity_kw` (D-V6-16) |
| Carga parcial | Diferencia de entalpía horaria de NASA POWER 2023 respecto a la de diseño (percentil 99), multiplicada por el horario de `configs/dataset/building_types.yaml` |
| COP | El de CityLearn, con el `eta` de cada edificio y el objetivo de 24 °C |
| Facturas | Punta + fuera de punta de 2023 |
| Piso de carga base | 30 % de la factura |

## Resultado

| Edificio | Física / factura | Refrigeración final | Meses recortados | CV de la base | Estado |
|---|---|---|---|---|---|
| B01 | 1,5 % | 1,5 % | 0 | 12,2 % | física |
| B02 | 64,4 % | 55,5 % | 8 | 95,6 % | recortada, declarada |
| B03 | 72,7 % | 60,7 % | 5 | 44,0 % | recortada, declarada |
| B04 | 2,4 % | 2,4 % | 0 | 7,8 % | física |
| B05 | 9,4 % | 9,4 % | 0 | 8,9 % | física |
| B06 | 9,2 % | 9,2 % | 0 | 50,2 % | física (solo 4 meses facturados en 2023) |
| B07 | 8,2 % | 8,2 % | 0 | 44,1 % | física |
| B08 | 24,2 % | 24,2 % | 0 | 14,8 % | física |
| B09 | 148,7 % | 70,0 % | 12 | 16,3 % | recortada, declarada |
| B10 | 9,3 % | 9,3 % | 0 | 16,8 % | física |
| B11 | 211,3 % | 70,0 % | 12 | 13,2 % | recortada, declarada |
| B12 | 38,8 % | 38,8 % | 0 | 12,0 % | física |
| B13 | 16,6 % | 16,6 % | 0 | 21,7 % | física |
| B14 | 69,3 % | 63,5 % | 4 | 30,7 % | recortada, declarada |
| B15 | 4,6 % | 4,6 % | 0 | 25,8 % | física |
| B16 | 32,1 % | 32,1 % | 0 | 21,1 % | física |
| B17 | 25,7 % | 25,7 % | 0 | 14,1 % | física |

## Lectura

- **CV de la carga base:** reproduce el CV diario de la propia factura de 2023. Por ejemplo, B02 va de 45 a 233 kWh/día, con un CV de 47 %, y B06 va de 8 697 a 34 881 kWh/día. Por eso se informa sin bloquear (D-V6-19).
- **Sobreestimación, detectada por el tope:** en B11 y B09 la capacidad del inventario supera con mucho lo facturado. Su refrigeración queda en el 70 % de la factura, y el propietario revisará sus datos.
- **Posible subestimación, que el método no detecta:** B01 (1,5 %), B04 (2,4 %) y B15 (4,6 %) tienen poca capacidad frente a su consumo.
  - B01 factura unos 15 000 kWh/día con 50 splits y un centro de datos.
  - En esos edificios la refrigeración controlable será pequeña.
  - La factura solo acota por arriba, así que una capacidad baja no se corrige. Queda para la revisión del propietario.
- **Límite:** la carga parcial depende solo del aire exterior (`assumption` de D-V6-18). No incluye la envolvente ni las ganancias solares.
