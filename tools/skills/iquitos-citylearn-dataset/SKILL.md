---
name: iquitos-citylearn-dataset
description: Dataset CityLearn v2 para Iquitos 2023-2025 con 17 edificios institucionales/comerciales reales. Usar cuando se debe generar, actualizar o validar el dataset de Iquitos para entrenamiento MADRL (HAPPO, MASAC, MATD3, MAAC) en los tres ejes OE.1 flexibilidad, OE.2 CO2 y OE.3 costos energeticos. Involucra Building_X.csv, weather.csv, carbon_intensity.csv, pricing.csv, charger_X_Y.csv, Washing_Machine_1.csv y schema.json.
---

# Iquitos CityLearn Dataset Skill

Skill local para el proyecto MADRL CityLearn Iquitos. Guia la generacion del dataset
CityLearn v2 con datos reales de 17 edificios institucionales y comerciales de la ciudad
de Iquitos, Peru, para los anios 2023-2025 (26 304 horas totales).

## Contexto del Proyecto

> Dataset de entrenamiento para: "Multi-Agente de Aprendizaje por Refuerzo Profundo para
> la Gestion Coordinada de Flexibilidad Energetica, Emisiones de Carbono y Costos
> Energeticos en Comunidades Inteligentes"

- **Ubicacion**: lat=-3.7491, lon=-73.2538, Iquitos, Loreto, Peru, altitud=106 m
- **Sistema electrico**: aislado diesel (ELECTRO ORIENTE S.A. + GENRENT) -- NO conectado al SEIN
- **Clima**: tropical humedo, T=24-33 C, RH=75-98%, irradiancia alta
- **Algoritmos MADRL**: HAPPO, MASAC, MATD3, MAAC via CityLearnEnv API estandar
- **Tres ejes**: OE.1 Flexibilidad energetica | OE.2 Emisiones CO2 | OE.3 Costos energeticos
- **Anios**: 2023 (8 760 h) + 2024 (8 784 h, bisiesto) + 2025 (8 760 h) = 26 304 h
- **Scope emisiones**: Scope 2 (generacion diesel ELOR+GENRENT), factor 0.79 kg CO2/kWh (MINAM RAGEI 2019)
- **Tarifa electrica**: OSINERGMIN MT3/MT4 -- punta 0.38 USD/kWh (18:00-22:59), fuera punta 0.26 USD/kWh

## Reglas de Operacion

- **NUNCA implementar** codigo hasta que el usuario diga explicitamente "implementa"
- **NUNCA cambiar** datos ya confirmados de edificios (inventarios, potencias, tipos)
- **NUNCA inventar** DOI, links, datasets, repositorios, citaciones o resultados
- Generar columnas con **valores reales no-cero** (distinto al dataset demo original)
- Columnas indoor_dry_bulb_temperature, indoor_relative_humidity, average_unmet_cooling_setpoint_difference deben tener valores reales (no vacias)
- Usar **MADRL** (no MARL) para Multi-Agent Deep Reinforcement Learning
- Distinguir **CityLearn v2** (base existente) de **CityLearn v3 propuesto** (extension tesis)
- cooling_demand y dhw_demand son **no-cero** donde fisicamente corresponda

## Modulos de Referencia

1. Datos confirmados 17 edificios -> [module-a-building-configs.md](references/module-a-building-configs.md)
2. Arquitectura del script generador -> [module-b-script-architecture.md](references/module-b-script-architecture.md)
3. Analisis de columnas por CSV -> [module-c-csv-columns.md](references/module-c-csv-columns.md)
4. Modelos fisicos (RC, BESS, solar) -> [module-d-physical-models.md](references/module-d-physical-models.md)
5. Documentacion de decisiones de diseno -> [module-e-dataset-documentation.md](references/module-e-dataset-documentation.md)

## Workflow de Generacion

### Paso 1 -- Preparacion del entorno

Verificar que existen:
- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` (directorio de salida)
- `tools/generate_iquitos_dataset.py` (script generador)
- Conexion a internet para NASA POWER / PVGIS

### Paso 2 -- Prueba de descarga meteorologica

```bash
python tools/generate_iquitos_dataset.py --buildings 1 --no-validate
```

Verifica que `.cache/weather/2023.parquet`, `2024.parquet`, `2025.parquet` se generaron.

### Paso 3 -- Generacion completa del dataset

```bash
python tools/generate_iquitos_dataset.py
```

Genera los 72 archivos en `CityLearn/data/datasets/citylearn_iquitos_2023_2025/`.

### Paso 4 -- Validacion con CityLearnEnv

```python
from citylearn.citylearn import CityLearnEnv
env = CityLearnEnv(
    schema="CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
)
obs, _ = env.reset()
assert obs is not None
print("Dataset validado correctamente -- 17 edificios, 26 304 pasos")
```

### Paso 5 -- Actualizacion incremental con datos reales

Cuando el usuario provea datos reales adicionales:
1. Actualizar la constante en `MADRL_BUILDING_CONSTANTS` o `LOAD_PROFILES`
2. Regenerar solo los edificios afectados: `--buildings X Y Z`
3. Re-validar con CityLearnEnv

## Archivos Generados (72 total)

| Tipo | Cantidad | Columnas | Filas | Notas |
|------|----------|----------|-------|-------|
| Building_X.csv | 17 | 12 | 26 304 | valores reales no-cero |
| weather.csv | 1 | 16 | 26 304 | PVGIS-ERA5 + NASA POWER |
| carbon_intensity.csv | 1 | 1 | 26 304 | 0.672-0.790 kg CO2/kWh |
| pricing.csv | 1 | 4 | 26 304 | OSINERGMIN MT3/MT4 TOU |
| charger_X_Y.csv | 50 | 6 | 26 304 | estocastico, seed determinista |
| Washing_Machine_1.csv | 1 | 5 | 26 304 | solo B1 ELOR |
| schema.json | 1 | -- | -- | 17 edificios + BESS + PV + EV |
| carbon_intensity_metadata.json | 1 | -- | -- | fuentes MINAM/RAGEI |

## Script -- Referencia Rapida CLI

```bash
# Dataset completo:
python tools/generate_iquitos_dataset.py

# Solo edificios seleccionados:
python tools/generate_iquitos_dataset.py --buildings 1 6 11 12

# Re-descargar datos meteorologicos (ignorar cache):
python tools/generate_iquitos_dataset.py --skip-cache

# Sin validacion CityLearnEnv (generacion rapida):
python tools/generate_iquitos_dataset.py --no-validate

# Directorio de salida personalizado:
python tools/generate_iquitos_dataset.py --output-dir ruta/al/directorio
```

## Constante Consolidada MADRL_BUILDING_CONSTANTS (17 edificios)

```python
MADRL_BUILDING_CONSTANTS = {
    1:  {'name': 'Electro Oriente S.A.',         'non_shiftable_base': 17.7,  'cooling_peak': 126.86, 'shiftable': 14.8,  'bldg_type': 'industrial',    'area_techada_m2': 14000},
    2:  {'name': 'Complejo Champios',             'non_shiftable_base': 3.76,  'cooling_peak': 29.0,   'shiftable': 35.6,  'bldg_type': 'deportivo',     'area_techada_m2': 8000},
    3:  {'name': 'Aeropuerto IQT',                'non_shiftable_base': 55.3,  'cooling_peak': 67.0,   'shiftable': 95.0,  'bldg_type': 'transporte_24h','area_techada_m2': 6000},
    4:  {'name': 'Hiperbodega Precio UNO',        'non_shiftable_base': 14.8,  'cooling_peak': 29.5,   'shiftable': 22.2,  'bldg_type': 'mall',          'area_techada_m2': 2500},
    5:  {'name': 'Hotel El Dorado Plaza',         'non_shiftable_base': 5.4,   'cooling_peak': 150.5,  'shiftable': 99.0,  'bldg_type': 'hotelero_24h',  'area_techada_m2': 9000},
    6:  {'name': 'Mall Aventura Iquitos',         'non_shiftable_base': 78.5,  'cooling_peak': 850.0,  'shiftable': 176.0, 'bldg_type': 'mall',          'area_techada_m2': 20637},
    7:  {'name': 'UNAP Zungarococha',             'non_shiftable_base': 9.5,   'cooling_peak': 167.0,  'shiftable': 39.2,  'bldg_type': 'universitario', 'area_techada_m2': 8300},
    8:  {'name': 'Escuela Tecnica PNP',           'non_shiftable_base': 6.9,   'cooling_peak': 222.0,  'shiftable': 99.3,  'bldg_type': 'educacion',     'area_techada_m2': 21000},
    9:  {'name': 'Complejo CNI',                  'non_shiftable_base': 2.18,  'cooling_peak': 19.5,   'shiftable': 10.7,  'bldg_type': 'deportivo',     'area_techada_m2': 3500},
    10: {'name': 'Gobierno Regional Loreto',      'non_shiftable_base': 12.43, 'cooling_peak': 117.5,  'shiftable': 22.2,  'bldg_type': 'administrativo','area_techada_m2': 5000},
    11: {'name': 'Hospital Regional Loreto',      'non_shiftable_base': 195.0, 'cooling_peak': 366.6,  'shiftable': 73.0,  'bldg_type': 'salud_24h',     'area_techada_m2': 12000},
    12: {'name': 'EsSalud Hospital III',          'non_shiftable_base': 125.0, 'cooling_peak': 222.0,  'shiftable': 34.5,  'bldg_type': 'salud_24h',     'area_techada_m2': 6000},
    13: {'name': 'Facultad Economia UNAP',        'non_shiftable_base': 1.75,  'cooling_peak': 62.5,   'shiftable': 14.8,  'bldg_type': 'universitario', 'area_techada_m2': 3000},
    14: {'name': 'Terminal Portuario ENAPU',      'non_shiftable_base': 15.7,  'cooling_peak': 49.5,   'shiftable': 47.0,  'bldg_type': 'portuario_24h', 'area_techada_m2': 5000},
    15: {'name': 'Colegio Nacional CNI',          'non_shiftable_base': 2.76,  'cooling_peak': 48.0,   'shiftable': 22.2,  'bldg_type': 'educacion',     'area_techada_m2': 2500},
    16: {'name': 'I.E. San Juan',                 'non_shiftable_base': 4.55,  'cooling_peak': 100.0,  'shiftable': 51.54, 'bldg_type': 'educacion',     'area_techada_m2': 6500},
    17: {'name': 'IEST Pedro del Aguila Hidalgo', 'non_shiftable_base': 4.2,   'cooling_peak': 93.0,   'shiftable': 26.3,  'bldg_type': 'educacion',     'area_techada_m2': 5200},
}
```

## Constantes Complementarias

```python
# Refrigeracion comercial (kW base electrico, factor nocturno 00-05h)
REFRIGERACION_COMERCIAL = {
    3:  (30.0,  0.70),   # Aeropuerto -- catering + carga fria
    4:  (12.0,  0.85),   # Hiperbodega Precio UNO -- frescos + bebidas
    5:  (18.0,  0.90),   # Hotel El Dorado -- cocina + bar + frigobar
    6:  (515.0, 0.85),   # Mall Aventura -- Tottus + food court
    11: (180.0, 1.00),   # Hospital Regional -- banco sangre + morgue (CRITICO)
    12: (90.0,  1.00),   # EsSalud -- banco sangre + farmacia (CRITICO)
}

SHORE_POWER_B14 = {'kw_per_vessel': 15.0, 'max_vessels': 4}
EVENT_LOAD_B9   = {'event_kw': 70.0, 'event_hours': [19, 20, 21, 22]}

COP_BY_TYPE = {
    'industrial': 2.8, 'mall': 3.0, 'salud_24h': 2.5, 'hotelero_24h': 3.0,
    'deportivo': 2.5, 'universitario': 2.8, 'educacion': 2.5,
    'portuario_24h': 2.5, 'transporte_24h': 3.0, 'administrativo': 2.8,
}

DHW_KWH_THERMAL_DAY = {5: 614.0, 11: 1200.0, 12: 780.0}  # Solo B5, B11, B12

SETPOINTS_C = {
    'industrial': 24.0, 'mall': 23.0, 'salud_24h': 22.0, 'universitario': 25.0,
    'deportivo': 26.0, 'educacion': 25.0, 'transporte_24h': 24.0,
    'portuario_24h': 26.0, 'hotelero_24h': 23.0, 'administrativo': 24.0,
}

TAU_HOURS = {
    'industrial': 4.0, 'mall': 3.0, 'salud_24h': 5.0, 'universitario': 3.0,
    'deportivo': 2.0, 'educacion': 2.5, 'transporte_24h': 2.0,
    'portuario_24h': 2.0, 'hotelero_24h': 4.0, 'administrativo': 3.5,
}

# Carbon intensity Scope 2 (MINAM RAGEI 2019 -- ELECTRO ORIENTE + GENRENT)
FE_DIESEL_KG_KWH   = 0.79   # factor emision diesel generacion aislada
SOLAR_PENETRACION  = 0.15   # penetracion solar actual sistema Iquitos
# carbon_intensity[t] = FE_DIESEL_KG_KWH * (1 - SOLAR_PENETRACION * GHI[t]/1000)
# Rango: 0.672-0.790 kg CO2/kWh

# Tarifas OSINERGMIN MT (todos los 17 edificios son clientes MT)
TARIFA_PUNTA_USD      = 0.38   # USD/kWh hora punta 18:00-22:59
TARIFA_FUERA_PUNTA_USD = 0.26  # USD/kWh fuera punta resto del dia

# BESS sizing (Hesse et al. 2017, DOI:10.3390/en10122107)
BESS_DOD       = 0.80   # Li-ion LFP depth of discharge
BESS_ETA_C     = 0.95   # eficiencia de carga
BESS_ETA_D     = 0.95   # eficiencia de descarga
BESS_ETA_RT    = 0.9025 # round-trip = ETA_C * ETA_D
BESS_LOSS      = 1e-5   # self-discharge LFP por hora
BESS_SOC_INI   = 0.50   # SOC inicial neutro
BESS_TARGET_SS = 0.70   # target autoabastecimiento 70%
```

## Clasificacion de Control MADRL por Equipo

| Icono | Categoria | Descripcion | Ejemplo |
|-------|-----------|-------------|---------|
| CRITICO | No desplazable | Carga vital constante, no apagable | UCI, SCADA, refrigeracion alimentos |
| PARCIAL | Modulable HVAC | El agente puede pre-enfriar o modular | Aire acondicionado, iluminacion |
| DESPLAZABLE | Programable | El agente decide cuando activar | Lavanderia, autoclave, EV, piscina |

## Datos Reales Confirmados -- GD-Iquitos V3

| # | Edificio | kWh/mes real | kWh/dia real | Demanda max kW |
|---|---------|-------------|-------------|----------------|
| 1 | Electro Oriente | 482 735 | 16 091 | n/d |
| 7 | UNAP Zungarococha | 13 089 | 436 | 139 |
| 8 | Escuela PNP | 8 925 | 297 | 37 |
| 10 | Gobierno Regional | 100 751 | 3 358 | 597 |
| 11 | Hospital Regional | 299 141 | 9 971 | 809 |
| 12 | EsSalud Hospital III | 192 207 | 6 407 | 540 |
| 13 | Facultad Economia | 12 367 | 412 | 78 |
| 14 | ENAPU | 29 203 | 973 | 96 |
| 15 | Colegio CNI | 14 171 | 472 | 92 |

Fuente: Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx -- datos de facturacion ELECTRO ORIENTE 2023-2025
