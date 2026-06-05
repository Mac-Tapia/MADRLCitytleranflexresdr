# Documentación: Construcción del Dataset CityLearn v3 — Iquitos 2023-2025

**Proyecto:** MADRL para Gestión Energética de Edificios en Sistema Aislado Diesel  
**Dataset:** `citylearn_iquitos_2023_2025`  
**Versión CityLearn:** v2 schema / v3 MADRL training layer  
**Autor:** MADRLCitytleranflexresdr  
**Fecha generación:** 2026-05-15

---

## Índice

1. [Visión General](#1-vision-general)
2. [Arquitectura del Sistema Eléctrico de Iquitos](#2-arquitectura-del-sistema-electrico)
3. [Los 17 Edificios del Dataset](#3-los-17-edificios)
4. [Dependencias y Requisitos](#4-dependencias-y-requisitos)
5. [Paso 1 — Adquisición de Datos Meteorológicos](#5-paso-1--adquisicion-meteorologica)
6. [Paso 2 — Intensidad de Carbono](#6-paso-2--intensidad-de-carbono)
7. [Paso 3 — Tarifas de Electricidad (RTP)](#7-paso-3--tarifas-de-electricidad)
8. [Paso 4 — Generación Solar Fotovoltaica](#8-paso-4--generacion-solar-pv)
9. [Paso 5 — Dimensionado de BESS](#9-paso-5--dimensionado-de-bess)
10. [Paso 6 — Demanda de Enfriamiento](#10-paso-6--demanda-de-enfriamiento)
11. [Paso 7 — Agua Caliente Sanitaria (DHW)](#11-paso-7--agua-caliente-sanitaria-dhw)
12. [Paso 8 — Perfiles de Carga EV (Cargadores)](#12-paso-8--perfiles-ev-cargadores)
13. [Paso 9 — Máquina de Lavado](#13-paso-9--maquina-de-lavado)
14. [Paso 10 — Carga No Desplazable (Non-Shiftable Load)](#14-paso-10--non-shiftable-load)
15. [Paso 11 — Destilación desde Mediciones Reales](#15-paso-11--destilacion-desde-mediciones-reales)
16. [Paso 12 — Condiciones Interiores (Temperatura y Humedad)](#16-paso-12--condiciones-interiores)
17. [Paso 13 — Corrección del Schema de Enfriamiento](#17-paso-13--correccion-del-schema)
18. [Paso 14 — Validación Final con CityLearnEnv](#18-paso-14--validacion-final)
19. [Estructura de Archivos Generados](#19-estructura-de-archivos-generados)
20. [Schema.json — Configuración para CityLearn v3](#20-schemajson--configuracion-citylearn-v3)
21. [Cómo Ejecutar el Pipeline Completo](#21-como-ejecutar-el-pipeline)
22. [Parámetros Globales de Referencia](#22-parametros-globales)

---

## 1. Visión General

El dataset Iquitos 2023-2025 es una simulación de 3 años a resolución horaria (26,304 horas) de 17 edificios institucionales y comerciales reales ubicados en Iquitos, Perú. El sistema eléctrico de Iquitos es **aislado de la red nacional** y opera con generadores diésel de Electro Oriente S.A. más una creciente penetración de energía solar fotovoltaica (~15%).

### Objetivo del dataset

Proveer datos de entrenamiento para algoritmos MADRL (HAPPO, MASAC, MATD3, MAAC) que aprendan a coordinar los recursos energéticos flexibles de los 17 edificios para optimizar tres objetivos simultáneos:

| Eje | Objetivo | KPI Principal |
|-----|----------|---------------|
| **OE.1** | Flexibilidad energética | `peak_average` — reducción de picos |
| **OE.2** | Emisiones de CO₂ | `carbon_emissions` — reducción intensidad |
| **OE.3** | Costo energético | `electricity_cost` — optimización tarifaria |

### Recursos flexibles por edificio

Cada edificio dispone de una combinación de:
- **BESS** — Batería de almacenamiento electroquímico
- **PV** — Generación solar fotovoltaica en techo
- **EV chargers** — Cargadores de vehículos eléctricos (mototaxis, motolineales, V2G)
- **Cooling** — Bomba de calor para enfriamiento (autosize CityLearn)
- **Washing Machine** — Máquina de lavado controlable (solo Edificio 1)
- **DHW** — Agua caliente sanitaria (Edificios 5, 11, 12)

---

## 2. Arquitectura del Sistema Eléctrico

```
ELECTRO ORIENTE S.A.
┌─────────────────────────────────────────────┐
│  Termoeléctrica Diesel + GENRENT Privados   │
│  Factor Emisión: 0.79 kgCO₂/kWh            │
│  (MINAM RAGEI 2019 — Scope 2 GHG)          │
│  Penetración Solar: ~15% del sistema        │
└─────────────┬───────────────────────────────┘
              │ Red Aislada
              │ Tarifa Punta (18-22h):  $0.38/kWh
              │ Tarifa Fuera Punta:     $0.26/kWh
              │
    ┌─────────┴────────────────────────────────┐
    │         17 Edificios Iquitos             │
    │  Cada uno con: BESS + PV + EV + Control  │
    └──────────────────────────────────────────┘
```

La intensidad de carbono varía entre **0.671 y 0.790 kg CO₂/kWh** según la mezcla diésel/solar en cada hora, calculada como:

```
CO2_t = FE_diesel × (1 - penetracion_solar_t) + 0  ×  penetracion_solar_t
```

donde `FE_diesel = 0.79 kgCO₂/kWh` (IPCC Guidelines 2006 — diésel estacionario).

---

## 3. Los 17 Edificios

### 3.1 Inventario con parámetros físicos

| ID | Nombre Real | Tipo | Área (m²) | Carga Base (kW) | Pico AC (kW) | Shiftable (kW) | DHW |
|----|-------------|------|----------:|----------------:|-------------:|---------------:|-----|
| 1  | Electro Oriente S.A.          | industrial       | 14,000 | 17.70 | 126.86 | 14.8  | No |
| 2  | Complejo Champios             | deportivo        |  8,000 |  3.76 |  29.00 | 35.6  | No |
| 3  | Aeropuerto Francisco Secada   | transporte_24h   |  6,000 | 55.30 |  67.00 | 95.0  | No |
| 4  | Hiperbodega Precio UNO        | mall             |  2,500 | 14.80 |  29.50 | 22.2  | No |
| 5  | Hotel El Dorado Plaza         | hotelero_24h     |  9,000 |  5.40 | 150.50 | 99.0  | Sí |
| 6  | Mall Aventura Iquitos         | mall             | 20,637 | 78.50 | 850.00 | 176.0 | No |
| 7  | UNAP Zungarococha             | universitario    |  8,300 |  9.50 | 167.00 | 39.2  | No |
| 8  | Escuela Técnica PNP           | educacion        | 21,000 |  6.90 | 222.00 | 99.3  | No |
| 9  | Complejo CNI                  | institucional    |  3,500 |  2.18 |  19.50 | 12.1  | No |
| 10 | Gobierno Regional Loreto      | administrativo   |  5,000 | 12.43 | 117.50 | 22.2  | No |
| 11 | Hospital Regional Loreto      | salud_24h        | 12,000 |195.00 | 366.60 | 73.0  | Sí |
| 12 | EsSalud Hospital III          | salud_24h        |  6,000 |125.00 | 222.00 | 34.5  | Sí |
| 13 | Facultad Economía UNAP        | universitario    |  3,000 |  1.75 |  62.50 | 14.8  | No |
| 14 | Terminal Portuario ENAPU      | portuario_24h    |  5,000 | 15.70 |  49.50 | 47.0  | No |
| 15 | Colegio Nacional CNI          | educacion        |  2,500 |  2.76 |  48.00 | 23.4  | No |
| 16 | I.E. San Juan                 | educacion        |  6,500 |  4.55 | 100.00 | 51.24 | No |
| 17 | IEST Pedro del Águila Hidalgo | educacion        |  5,200 |  4.20 |  93.00 | 26.3  | No |

### 3.2 Dimensionado BESS por edificio

**Metodología:** Balance energético acumulado (Hesse et al. 2017).  
**Parámetros fijos:** DOD=0.80 · η_carga=0.95 · η_descarga=0.95 · η_roundtrip=0.9025 · SOC₀=0.50 · target_autosuficiencia=0.70

```
E_BESS = percentil_95(variacion_energia_diaria) / DOD
P_BESS = E_BESS / 4   (4 horas de autonomía)
```

| ID | Cap. BESS (kWh) | Pot. BESS (kW) | ID | Cap. BESS (kWh) | Pot. BESS (kW) |
|----|----------------:|---------------:|----|----------------:|---------------:|
| 1  | 4,122.0 | 1,030.5 | 10 | 1,354.3 |   338.6 |
| 2  | 2,573.8 |   643.5 | 11 | 3,327.6 |   831.9 |
| 3  | 1,349.1 |   337.3 | 12 | 1,973.7 |   493.4 |
| 4  |   578.4 |   144.6 | 13 |   831.3 |   207.8 |
| 5  | 2,224.9 |   556.2 | 14 | 1,413.9 |   353.5 |
| 6  | 6,563.0 | 1,640.8 | 15 |   704.1 |   176.0 |
| 7  | 2,315.6 |   578.9 | 16 | 1,893.3 |   473.3 |
| 8  | 6,353.1 | 1,588.3 | 17 | 1,489.0 |   372.3 |
| 9  | 1,110.4 |   277.6 |    |         |         |

**Total sistema:** 37,299.6 kWh · 9,325 kW

### 3.3 Dimensionado PV por edificio

**Módulo:** SunPower SPR-315E-WHT-2007 (Pmp=315 W · Vmp=54.7 V · η_stc=20.5%)  
**Cobertura útil:** 63% del área techada (factor_ocupación=0.70 × factor_sombreado=0.90)  
**Ubicación:** -3.7491°, -73.2538°, 106 m · tilt=5° · azimuth=0° (Norte hemisferio Sur)

```
N_modulos = floor(Area_util / 1.63)   [m² por módulo SunPower]
kWp_DC    = N_modulos × 0.315
```

| ID | kWp DC  | N Módulos | Área Útil (m²) | Gen. Anual (MWh) |
|----|--------:|----------:|---------------:|-----------------:|
| 1  | 1,703.6 |  5,579    |  9,100         |  7,078           |
| 2  |   973.6 |  3,188    |  5,200         |  4,006           |
| 3  |   730.0 |  2,391    |  3,900         |  3,031           |
| 4  |   304.0 |    996    |  1,625         |  1,260           |
| 5  | 1,095.2 |  3,586    |  5,850         |  4,597           |
| 6  | 2,511.4 |  8,224    | 13,414         | 10,365           |
| 7  | 1,010.1 |  3,306    |  5,397         |  4,165           |
| 8  | 2,555.5 |  8,367    | 13,656         | 10,556           |
| 9  |   425.7 |  1,392    |  2,275         |  1,756           |
| 10 |   608.4 |  1,992    |  3,254         |  2,510           |
| 11 | 1,460.4 |  4,779    |  7,809         |  6,024           |
| 12 |   730.0 |  2,391    |  3,903         |  3,031           |
| 13 |   364.9 |  1,194    |  1,950         |  1,508           |
| 14 |   608.4 |  1,992    |  3,254         |  2,510           |
| 15 |   304.0 |    996    |  1,625         |  1,260           |
| 16 |   790.8 |  2,590    |  4,225         |  3,261           |
| 17 |   632.7 |  2,071    |  3,381         |  2,609           |

**Total sistema:** 16,808 kWp DC · 69,527 MWh/año

### 3.4 Cargadores EV por edificio

**Tipos de vehículos eléctricos en Iquitos:**

| Tipo | Potencia (kW) | Batería (kWh) | DOD | Días activos |
|------|:-------------:|:-------------:|:---:|:------------:|
| Mototaxi eléctrico | 4.0 | 6.0 | 0.80 | L-D |
| Motolineal eléctrica | 3.0 | 4.0 | 0.80 | L-V |
| Van/Camioneta V2G | 7.4 | 40.0 | 0.85 | L-V |

| ID | Tipo Mix         | Cant. | kW Total | Ventana Carga |
|----|-----------------|------:|--------:|:-------------:|
| 1  | V2G             | 2     | 14.8    | 07-17h |
| 2  | Mototaxi        | 4     | 16.0    | 15-22h |
| 3  | V2G + Motolineal| 4     | 20.4    | 05-21h |
| 4  | Mototaxi        | 3     | 12.0    | 10-20h |
| 5  | V2G + Mototaxi  | 3     | 19.4    | 08-12h |
| 6  | V2G + Mototaxi  | 8     | 37.2    | 10-21h |
| 7  | V2G + Motolineal| 3     | 13.4    | 08-17h |
| 8  | V2G             | 2     | 14.8    | 07-16h |
| 9  | Mototaxi        | 2     |  8.0    | 07-16h |
| 10 | V2G             | 3     | 22.2    | 08-17h |
| 11 | V2G + Motolineal| 4     | 20.4    | 07-19h |
| 12 | V2G + Motolineal| 3     | 19.4    | 08-17h |
| 13 | Motolineal      | 2     |  6.0    | 08-17h |
| 14 | V2G             | 2     | 14.8    | 06-18h |
| 15 | Mototaxi        | 2     |  8.0    | 07-15h |
| 16 | Motolineal      | 1     |  3.0    | 07-15h |
| 17 | Motolineal      | 2     |  6.0    | 07-16h |

**Total:** 50 archivos `charger_X_Y.csv` · 267.2 kW instalados

---

## 4. Dependencias y Requisitos

```python
# Entorno Python 3.9 (.venv39-citylearn-v3)
pvlib >= 0.10.0          # Cálculo solar fotovoltaico
pandas >= 1.5.0          # Manipulación de series temporales
numpy >= 1.23.0          # Cálculos numéricos
requests >= 2.28.0       # API NASA POWER
citylearn >= 2.1.0       # Validación final del entorno
```

**Fuentes de datos externas:**
- **PVGIS-ERA5 API:** `https://re.jrc.ec.europa.eu/api/v5_2/seriescalc` (año 2023)
- **NASA POWER API:** `https://power.larc.nasa.gov/api/temporal/hourly/point` (2024-2025)
- **Mediciones reales:** `CityLearn/data/buildingcsv/B_02.csv … B_17.csv` (16 edificios)

---

## 5. Paso 1 — Adquisición Meteorológica

### Objetivo
Construir la serie temporal de 26,304 horas de variables climáticas para Iquitos y agregarla al archivo `weather.csv`.

### 5.1 Ubicación geográfica

```python
LAT    = -3.7491    # Latitud Sur
LON    = -73.2538   # Longitud Oeste
ALT    = 106        # Altitud en metros
TZ     = "America/Lima"  # UTC-5 sin DST
PERIOD = 2023-01-01 / 2025-12-31   # 3 años completos
```

### 5.2 Fuentes por año

| Año | API Primaria | Fallback | Razón |
|-----|-------------|---------|-------|
| 2023 | PVGIS-ERA5 | NASA POWER | PVGIS tiene mejor cobertura histórica reciente |
| 2024 | NASA POWER | — | PVGIS no tiene 2024 aún disponible |
| 2025 | NASA POWER | — | Idem 2024 (datos estimados/proyectados) |

### 5.3 Variables descargadas

| Variable PVGIS/NASA | Columna CityLearn | Unidad |
|--------------------|-------------------|--------|
| `G(h)` / `ALLSKY_SFC_SW_DWN` | `diffuse_solar_irradiance` | W/m² |
| `Gb(n)` / `ALLSKY_SFC_SW_DNI` | `direct_solar_irradiance` | W/m² |
| `T2m` / `T2M` | `outdoor_dry_bulb_temperature` | °C |
| `RH` / `RH2M` | `outdoor_relative_humidity` | % |

### 5.4 Predicciones (+1h, +2h, +3h)

CityLearn v2 requiere columnas de predicción `_predicted_1/2/3`. Se generan por desplazamiento temporal:

```python
for lag in [1, 2, 3]:
    df[f"{col}_predicted_{lag}"] = df[col].shift(-lag).fillna(method="ffill")
```

### 5.5 Clips de validación aplicados

```python
GHI  = max(GHI, 0)              # Irradiancia siempre >= 0
DHI  = max(DHI, 0)
DNI  = max(DNI, 0)
Temp = clip(Temp, 18, 42)       # Rango climatológico Iquitos
RH   = clip(RH, 40, 100)        # Humedad tropical
```

### 5.6 Caché local

Los datos se guardan en `.cache/weather/{year}.parquet` para evitar re-descarga. El flag `--skip-cache` fuerza nueva descarga.

---

## 6. Paso 2 — Intensidad de Carbono

### Objetivo
Generar `carbon_intensity.csv` con el factor de emisión horario del sistema eléctrico de Iquitos.

### 6.1 Factor base

```
FE_base = 0.790 kgCO₂/kWh
Fuente: MINAM INFOCARBONO — RAGEI 2019 Energía (Perú)
Validación: IPCC Guidelines 2006, diésel estacionario
Alcance GHG: Scope 2 (emisiones indirectas por consumo)
```

### 6.2 Variación por penetración solar

```python
def carbon_intensity_t(hora_t, mes_t):
    solar_fraction = irradiancia_t / irradiancia_pico_mes
    penetracion    = SOLAR_PENETRATION_BASE * solar_fraction
    # penetracion max ~15% en hora pico solar
    return FE_base * (1.0 - penetracion)
    # Rango: 0.671 (mediodía soleado) — 0.790 (noche/cloudy)
```

### 6.3 Columna generada

El archivo `carbon_intensity.csv` contiene una sola columna:

```
carbon_intensity
0.790000
0.790000
...
0.671234   ← hora pico solar
...
```

**26,304 filas · rango [0.671, 0.790] kgCO₂/kWh**

---

## 7. Paso 3 — Tarifas de Electricidad (RTP)

### Objetivo
Generar `pricing.csv` con la tarifa horaria de Electro Oriente S.A. más predicciones.

### 7.1 Estructura tarifaria

```
Tarifa Punta   (18:00 - 22:00 h): $0.38/kWh
Tarifa Fuera Punta (resto):        $0.26/kWh
Aplicación: Todos los días del año
```

### 7.2 Señal de tiempo real (RTP)

Se agrega ruido gaussiano pequeño para simular variabilidad de mercado:

```python
base_price = 0.38 if hora in range(18, 22) else 0.26
pricing[t] = base_price * (1 + Normal(0, 0.02))
pricing[t] = max(pricing[t], 0.01)   # mínimo positivo
```

### 7.3 Columnas generadas

```
electricity_pricing, electricity_pricing_predicted_1,
electricity_pricing_predicted_2, electricity_pricing_predicted_3
```

Las predicciones son desplazamientos temporales (igual que variables meteorológicas).

---

## 8. Paso 4 — Generación Solar PV

### Objetivo
Calcular la serie de generación solar horaria (kWh) para cada edificio usando `pvlib` con el modelo SAPM (Sandia Array Performance Model).

### 8.1 Módulo fotovoltaico

```python
modulo = pvlib.pvsystem.retrieve_sam("SandiaMod")["SunPower_SPR_315E_WHT__2007__E__"]
# Pmp    = 315 W
# Vmp    = 54.7 V
# Voc    = 64.2 V
# Isc    = 6.14 A
# η_stc  = 20.5%
# NOCT   = 45°C
```

### 8.2 Configuración del sistema

```python
location = pvlib.location.Location(lat=-3.7491, lon=-73.2538, altitude=106, tz="America/Lima")
mount    = pvlib.pvsystem.FixedMount(surface_tilt=5, surface_azimuth=0)
system   = pvlib.pvsystem.PVSystem(
    arrays=[pvlib.pvsystem.Array(mount=mount, module_parameters=modulo,
                                  modules_per_string=N_modulos, strings=1)],
    inverter_parameters={"pdc0": kWp_DC * 1000, "eta_inv_nom": 0.96}
)
mc = pvlib.modelchain.ModelChain(system, location,
                                  aoi_model="physical",
                                  spectral_model="no_loss")
```

### 8.3 Proceso por edificio

```python
for edificio_i in range(1, 18):
    N_mod    = inventario[i]["n_modulos"]
    weather  = pvlib_weather_df   # GHI, DNI, DHI, Temp, WindSpeed
    mc.run_model(weather)
    gen_kWh  = mc.results.ac.clip(lower=0) / 1000   # W → kWh/h
    Building_i["solar_generation"] = gen_kWh.values
```

### 8.4 Resultados

- **Horas con generación > 0:** ~12,880 h/año por edificio (49% del año)
- **Máximo horario:** 1-2,301 kWh/h (según kWp instalado)
- **Pico diario:** mediodía solar (~12:30-13:00 hora local)
- **Factor de capacidad:** 18-21% según mes

---

## 9. Paso 5 — Dimensionado de BESS

### Objetivo
Calcular la capacidad y potencia del sistema de almacenamiento para cada edificio que garantice el target de autosuficiencia.

### 9.1 Metodología (Hesse et al. 2017)

```python
# Para cada edificio i:
demanda_diaria  = non_shiftable_load[i].resample("D").sum()   # kWh/día
solar_diaria    = solar_generation[i].resample("D").sum()      # kWh/día
excedente_diario = max(solar_diaria - demanda_diaria, 0)       # kWh/día
deficit_diario   = max(demanda_diaria - solar_diaria, 0)       # kWh/día

# Capacidad necesaria = percentil 95 de la variación neta diaria
delta_diario = abs(excedente_diario - deficit_diario)
E_BESS = percentil(delta_diario, 95) / DOD               # DOD = 0.80
P_BESS = E_BESS / 4                                       # 4 horas autonomía
```

### 9.2 Parámetros operativos en schema.json

```json
{
  "type": "ElectricStorage",
  "autosize": false,
  "capacity": E_BESS,
  "nominal_power": P_BESS,
  "depth_of_discharge": 0.80,
  "efficiency": 0.9025,
  "loss_coefficient": 0.0001,
  "initial_soc": 0.50
}
```

---

## 10. Paso 6 — Demanda de Enfriamiento

### Objetivo
Generar la columna `cooling_demand` (kWh) para cada edificio simulando la carga de climatización según tipo de edificio, hora y día de la semana.

### 10.1 Fórmula base

```python
cooling_demand[t] = peak_kW_ac[i] / COP[tipo] * fraction[t] * noise[t]

# Donde:
#   peak_kW_ac = pico de refrigeración del edificio (MADRL_BUILDING_CONSTANTS)
#   COP        = Coefficient of Performance por tipo
#   fraction   = factor horario × factor diario ∈ [0, 1]
#   noise      = Normal(μ=1.0, σ=0.015) ruido gaussiano leve
```

### 10.2 COP por tipo de edificio

| Tipo | COP | Setpoint (°C) | τ térmica (h) |
|------|----:|:-------------:|:-------------:|
| industrial | 2.8 | 24 | 3.0 |
| deportivo | 2.5 | 26 | 2.0 |
| transporte_24h | 2.8 | 24 | 2.5 |
| mall | 3.0 | 23 | 3.5 |
| hotelero_24h | 2.8 | 22 | 4.0 |
| universitario | 2.5 | 25 | 2.0 |
| educacion | 2.5 | 25 | 2.0 |
| salud_24h | 2.8 | 22 | 5.0 |
| administrativo | 2.8 | 24 | 2.5 |
| portuario_24h | 2.5 | 25 | 2.5 |

### 10.3 Factores horarios por tipo (ejemplos)

**Mall (6, 4):** pico en tarde-noche, activo fines de semana  
`{8:0.30, 10:0.70, 12:0.85, 14:0.90, 18:0.95, 20:0.90, 22:0.60, 0:0.10}`

**Hospitales 24h (11, 12):** operación continua  
`{0:0.65, 8:0.90, 12:0.85, 16:0.90, 20:0.80, 22:0.75}`

**Educación (8, 13, 15, 16, 17):** solo horario escolar  
`{0:0.01, 8:0.90, 12:0.85, 14:0.90, 17:0.10, 20:0.01}`

**Factor día semana:**
- Educación: Lun-Vie=1.0, Sab=0.10, Dom=0.01
- Hospitales: Lun-Vie=1.0, Sab=0.95, Dom=0.90
- Malls: Lun-Vie=1.0, Sab=1.05, Dom=1.03

### 10.4 Autosize en CityLearn

El schema configura `autosize: true` para el dispositivo de enfriamiento, permitiendo que CityLearn calcule automáticamente la potencia máxima del HeatPump a partir del pico de `cooling_demand` en la serie histórica. Se aplica un factor de seguridad `1.000001` para evitar errores de comparación float-point (ver Paso 13).

---

## 11. Paso 7 — Agua Caliente Sanitaria (DHW)

### Objetivo
Generar `dhw_demand` (kWh) para los 3 edificios con demanda de agua caliente sanitaria real (Edificios 5, 11, 12).

### 11.1 Perfiles por edificio

**Edificio 5 — Hotel El Dorado Plaza**
```
Consumo total: 614 kWh/día
Perfil: 30% en 6-9h (madrugada-mañana), 25% en 18-22h (noche)
Distribución: Gaussiana truncada centrada en 7h y 20h
```

**Edificio 11 — Hospital Regional Loreto**
```
Consumo total: 1,200 kWh/día
Perfil: distribución uniforme 1/24 h por hora (operación 24h)
Ajuste: +10% en 6-9h por higiene matutina
```

**Edificio 12 — EsSalud Hospital III**
```
Consumo total: 780 kWh/día
Perfil: igual a Hospital Regional (1/24 + 10% mañana)
```

**Resto de edificios:** `dhw_demand = 0.0` (sin ACS)

---

## 12. Paso 8 — Perfiles EV (Cargadores)

### Objetivo
Generar el archivo `charger_X_Y.csv` para cada cargador de vehículo eléctrico.

### 12.1 Estructura del archivo charger

Cada `charger_X_Y.csv` tiene 26,304 filas y columnas:

```
time_step, connected, soc_init, soc_target, energy_requirement,
charging_power_limit, discharging_power_limit, charge_efficiency,
discharge_efficiency
```

### 12.2 Lógica de conexión

```python
for t in range(26304):
    hora    = t % 24
    dow     = (t // 24) % 7       # 0=Lunes, 6=Domingo
    en_ventana = (WIN_START <= hora < WIN_END)
    dia_activo = (dow < 5)        # L-V para motolineales/V2G
                                   # L-D para mototaxis

    if en_ventana and dia_activo:
        connected[t]   = 1
        soc_init[t]    = Uniform(0.2, 0.6)    # llega parcialmente cargado
        soc_target[t]  = Uniform(0.85, 1.0)   # quiere quedar cargado
        energy_req[t]  = bateria_kWh * (soc_target - soc_init) / η_carga
        P_max_carga[t] = P_cargador_kW
        P_max_descarga[t] = P_cargador_kW if V2G else 0.0
    else:
        connected[t]  = 0
        # Resto = 0
```

### 12.3 Capacidades por tipo

| Tipo | Batería (kWh) | P_carga (kW) | V2G |
|------|:-------------:|:------------:|:---:|
| Mototaxi | 6.0 | 4.0 | No |
| Motolineal | 4.0 | 3.0 | No |
| Van/V2G | 40.0 | 7.4 | Sí |

---

## 13. Paso 9 — Máquina de Lavado

### Objetivo
Generar `Washing_Machine_1.csv` para el Edificio 1 (Electro Oriente — lavado de uniformes industriales).

### 13.1 Parámetros

```
Edificio:      1 (Electro Oriente S.A.)
Ciclo:         2.5 kWh en 2 pasos = [1.5 kWh, 1.0 kWh]
Ventana:       06:00 - 09:00 horas (horas 7-9 en base-1 CityLearn)
Días activos:  Lunes a Viernes (dow < 5)
Prob. uso:     90% en cada día laboral elegible
```

### 13.2 Estructura del archivo

```
day_type (1-7), hour (1-24 base-1),
wm_start_time_step, wm_end_time_step, load_profile
```

Ejemplo de una fila con ventana activa un lunes:
```
1, 7, 144, 146, "[1.5, 1.0]"
```

Fila sin ventana (sábado, hora noche):
```
6, 23, -1, -1, -1
```

---

## 14. Paso 10 — Non-Shiftable Load (Carga No Desplazable)

### Objetivo
Generar la columna `non_shiftable_load` (kW) que representa el consumo eléctrico base no controlable (iluminación, equipos, servidores, procesos continuos).

### 14.1 Edificio 1 — Perfil sintético puro

El Edificio 1 (Electro Oriente) no dispone de medición mensual en el repositorio. Se genera con:

```python
NSL_1[t] = base_kW + equipo_kW * hour_factor[hora] * day_factor[dow]
          + refrigeracion_24h_kW
          + Normal(0, 0.03 * base_kW)  # ruido 3%
NSL_1[t] = max(NSL_1[t], min_kW)
```

### 14.2 Edificios 2-17 — Destilación desde medición real

**Fuente:** Archivos `CityLearn/data/buildingcsv/B_02.csv … B_17.csv`  
Contienen lecturas mensuales de energía activa facturada (kWh/mes) en tarifa punta y fuera punta, para 1 a 3 años.

**Regla física de destilación:**

```
NSL_mes = E_total_medido_mes
        - E_cooling_mes / COP
        - E_DHW_mes / COP_DHW

Donde:
  E_cooling_mes = suma(cooling_demand) del mes × dt
  E_DHW_mes     = suma(dhw_demand) del mes × dt
  NSL ≥ 0 siempre (validado estrictamente)
```

Ver detalle completo en el **Paso 11 (Destilación)**.

---

## 15. Paso 11 — Destilación desde Mediciones Reales

### Objetivo
Calibrar la serie horaria de `non_shiftable_load` para Edificios 2-17 usando mediciones mensuales reales, garantizando que el balance energético mensual coincida con los recibos de Electro Oriente.

### 15.1 Datos de entrada

```
CityLearn/data/buildingcsv/B_02.csv   # Complejo Champios — 36 meses
CityLearn/data/buildingcsv/B_03.csv   # Aeropuerto — 24 meses (2023-2024)
...
CityLearn/data/buildingcsv/B_17.csv   # IEST Pedro del Águila — 12 meses
```

Cada archivo contiene columnas como:
```
year, month, energia_activa_punta_kwh, energia_activa_fuera_punta_kwh,
energia_activa_total_kwh, demanda_maxima_kw, ...
```

### 15.2 Predicción de meses faltantes

Cuando un edificio no tiene medición en un mes específico se usa el método `calendar_month_mean_overlap_scaled`:

```python
def forecast_missing_month(building, year, month):
    # Paso 1: Media del mismo mes calendario en años con medición
    E_ref = mean(E[yr, month] for yr in años_medidos)

    # Paso 2: Factor de escala desde overlap con año objetivo
    overlap_scale = sum(E_medido[yr_obj, overlap_months]) /
                    sum(E_ref_profile[overlap_months])

    # Predicción
    E_hat = E_ref * overlap_scale
    return E_hat
```

### 15.3 Calibración del perfil horario

Para cada mes de cada edificio:

```python
# 1. Calcular energía mensual objetivo
E_obj_mes = E_medido_mes  # o E_hat si es predicción

# 2. Calcular energía de componentes controladas en el mes
E_ctrl_mes = sum(cooling_demand[mes] / COP +
                  dhw_demand[mes] / COP_DHW) * dt_h

# 3. Energía residual = NSL target mensual
E_NSL_target = E_obj_mes - E_ctrl_mes

# 4. Factor de escala del perfil horario base
NSL_base_mes = sum(NSL_base[mes])
scale = E_NSL_target / NSL_base_mes

# 5. Aplicar escala con clip mínimo
NSL_calibrado[mes] = max(NSL_base[mes] * scale, min_kW)

# 6. Validación: delta energético ≤ 0.1%
delta_pct = |sum(NSL_cal) - E_NSL_target| / E_NSL_target
assert delta_pct <= 0.001
```

### 15.4 Reporte de auditoría

El script genera `tools/dataset_docs/distillation_report.csv` con 66 columnas de auditoría por cada edificio × mes:

| Grupo de columnas | Descripción |
|------------------|-------------|
| Energía medida vs calculada | 5 variantes: medido, calculado, delta, delta_%, status |
| Tarifación | ratio_punta/fuera, precio_reconstruido, delta_monetario |
| Calidad | record_type (measured/forecast), flag, método_predicción |
| Proxies físicos | área, splits_instalados, sistemas_refrigeración |

---

## 16. Paso 12 — Condiciones Interiores

### Objetivo
Generar las columnas `indoor_dry_bulb_temperature`, `indoor_relative_humidity` y `average_unmet_cooling_setpoint_difference`.

### 16.1 Temperatura interior — Modelo RC de primer orden

```python
def T_interior(t, T_ext, cooling_active, setpoint, tau):
    # Modelo resistencia-capacitancia
    T_libre = T_ext + delta_T_solar(t)        # sin climatización
    if cooling_active:
        T_target = setpoint
    else:
        T_target = T_libre

    # Dinámica exponencial con constante τ
    T_int[t] = T_int[t-1] + dt/tau * (T_target - T_int[t-1])
    T_int[t] += Normal(0, 0.15)              # ruido ±0.15°C
    return clip(T_int[t], 14, 46)
```

### 16.2 Humedad relativa interior

```python
cooling_fraction_t = cooling_demand[t] / (peak_kW_ac / COP)
RH_int[t] = RH_ext[t] * (1 - 0.35 * cooling_fraction_t) + Normal(0, 1.5)
RH_int[t] = clip(RH_int[t], 20, 98)
```

### 16.3 Diferencia de setpoint no satisfecha

```python
setpoint = SETPOINT_BY_TYPE[bldg_type]
ocupancia = hour_factor[hora] * day_factor[dow]
unmet[t] = max(T_int[t] - setpoint, 0) * ocupancia
```

---

## 17. Paso 13 — Corrección del Schema de Enfriamiento

### Objetivo
Aplicar un factor de seguridad mínimo al autosize del dispositivo de enfriamiento para evitar fallos numéricos en CityLearn.

### 17.1 Problema

CityLearn usa comparación float-point estricta para validar que la potencia del HeatPump sea `>= max(cooling_demand)`. Pequeñas variaciones de precisión pueden causar error de validación.

### 17.2 Fix aplicado (`tools/fix_schema_cooling.py`)

```python
SAFETY_FACTOR = 1.000001   # 0.0001% extra de margen

for building in schema["buildings"].values():
    if building.get("cooling_device", {}).get("autosize"):
        building["cooling_device"]["safety_factor"] = SAFETY_FACTOR
```

Este script se ejecuta **después** de `generate_iquitos_dataset.py` y **antes** de `evaluate_dataset.py`.

---

## 18. Paso 14 — Validación Final con CityLearnEnv

### Objetivo
Verificar que el dataset completo puede cargarse y ejecutarse correctamente en CityLearn v2/v3 sin errores.

### 18.1 Carga del entorno

```python
from citylearn.citylearn import CityLearnEnv

env = CityLearnEnv(schema="CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json")
obs, _ = env.reset()

# Verificaciones básicas:
assert len(obs) == 17                          # 17 agentes
assert all(len(o) == 39 for o in obs)          # 39 observaciones por agente
assert env.observation_space[0].shape == (39,)
assert env.action_space[0].shape == (3,)       # 3 acciones continuas [-1,1]
```

### 18.2 Secciones de validación (`evaluate_dataset.py`)

| Sección | Qué verifica |
|---------|-------------|
| 1. Energía diaria | `Σ(NSL) = E_medido` por mes · intensidad kWh/m²/año vs benchmark |
| 2. Perfil horario | Pico/valle en horas 8, 12, 18, 22 por tipo de edificio |
| 3. Factor día semana | Ratio Lun/Sab/Dom por tipo de uso |
| 4. Confort interior | T_int ∈ [14, 46]°C · RH ∈ [20, 100]% |
| 5. Solar generación | Max diario · promedio diario · ratio vs demanda |
| 6. NSL no negativo | `min(NSL) >= 0` · `max(delta_mensual) <= 0.1%` |
| 7. DHW y Heating | DHW > 0 en B5/B11/B12 · Heating = 0 en todos |
| 8. Pricing balance | `max_delta_factura <= 0.01%` vs recibos reales |
| 9. Paso completo | Reset + 10 pasos aleatorios sin excepción |

### 18.3 Simulación de prueba (10 pasos)

```python
for step in range(10):
    actions = [env.action_space[i].sample() for i in range(17)]
    obs, rewards, done, truncated, info = env.step(actions)
    assert len(rewards) == 17
    assert not any(np.isnan(r) for r in rewards)
```

---

## 19. Estructura de Archivos Generados

```
CityLearn/data/datasets/citylearn_iquitos_2023_2025/
│
├── weather.csv                    # 26,304 × 16 cols — Meteorología + predicciones
├── carbon_intensity.csv           # 26,304 × 1 col  — 0.671-0.790 kgCO₂/kWh
├── pricing.csv                    # 26,304 × 4 cols  — RTP + predicciones
│
├── Building_1.csv                 # 26,304 × 12 cols — Electro Oriente (sintético)
├── Building_2.csv                 # 26,304 × 12 cols — Complejo Champios (destilado)
├── Building_3.csv                 # (...) Aeropuerto
├── Building_4.csv                 # (...) Hiperbodega
├── Building_5.csv                 # (...) Hotel El Dorado
├── Building_6.csv                 # (...) Mall Aventura
├── Building_7.csv                 # (...) UNAP
├── Building_8.csv                 # (...) Escuela PNP
├── Building_9.csv                 # (...) CNI
├── Building_10.csv                # (...) Gobierno Regional
├── Building_11.csv                # (...) Hospital Regional
├── Building_12.csv                # (...) EsSalud
├── Building_13.csv                # (...) Facultad Economía
├── Building_14.csv                # (...) Terminal ENAPU
├── Building_15.csv                # (...) Colegio CNI
├── Building_16.csv                # (...) I.E. San Juan
├── Building_17.csv                # (...) IEST Pedro del Águila
│
├── Washing_Machine_1.csv          # 26,304 × 5 cols — Lavadora B1
│
├── charger_1_1.csv                # 26,304 × 9 cols — EV B1-cargador1
├── charger_1_2.csv                # EV B1-cargador2
├── charger_2_1.csv ... charger_2_4.csv
├── charger_3_1.csv ... charger_3_4.csv
├── charger_4_1.csv ... charger_4_3.csv
├── charger_5_1.csv ... charger_5_3.csv
├── charger_6_1.csv ... charger_6_8.csv   # 8 cargadores en Mall
├── charger_7_1.csv ... charger_7_3.csv
├── charger_8_1.csv ... charger_8_2.csv
├── charger_9_1.csv ... charger_9_2.csv
├── charger_10_1.csv ... charger_10_3.csv
├── charger_11_1.csv ... charger_11_4.csv
├── charger_12_1.csv ... charger_12_3.csv
├── charger_13_1.csv ... charger_13_2.csv
├── charger_14_1.csv ... charger_14_2.csv
├── charger_15_1.csv ... charger_15_2.csv
├── charger_16_1.csv
├── charger_17_1.csv ... charger_17_2.csv
│                                  # Total: 50 archivos de cargadores EV
│
├── building_metadata.json         # Metadatos: tipo, área, BESS, PV, EV por edificio
├── carbon_intensity_metadata.json # Fuente CO₂, factor diesel, metodología RAGEI
├── solar_fix_log.json             # Log pvlib SAPM por edificio
├── dataset_generation_log.json    # Metadatos globales de la corrida de generación
└── schema.json                    # Configuración CityLearn v2/v3

tools/dataset_docs/
├── distillation_report.csv        # 216 filas × 66 cols — Auditoría de destilación
├── dataset_generation_log.json    # Copia del log global
├── carbon_intensity_metadata.json # Copia metadatos CO₂
└── solar_fix_log.json             # Copia log solar
```

### 19.1 Estructura de cada Building_X.csv

```
month, hour, day_type, daylight_savings_status,
indoor_dry_bulb_temperature, average_unmet_cooling_setpoint_difference,
indoor_relative_humidity,
non_shiftable_load,
dhw_demand,
cooling_demand,
heating_demand,
solar_generation
```

- **Filas:** 26,305 (1 encabezado + 26,304 horas de datos)
- **Rango temporal:** 2023-01-01 00:00 → 2025-12-31 23:00
- **Resolución:** 1 hora (3,600 segundos por paso)

---

## 20. Schema.json — Configuración para CityLearn v3

El `schema.json` es el archivo de configuración central que CityLearn usa para construir el entorno de simulación. Estructura principal:

```json
{
  "simulation_start_time_step": 0,
  "simulation_end_time_step": 26303,
  "seconds_per_time_step": 3600,
  "random_seed": 2024,
  "central_agent": false,

  "buildings": {
    "Building_1": {
      "include": true,
      "energy_simulation": "Building_1.csv",
      "weather": "weather.csv",
      "carbon_intensity": "carbon_intensity.csv",
      "pricing": "pricing.csv",

      "electrical_storage": {
        "type": "ElectricStorage",
        "autosize": false,
        "capacity": 4122.0,
        "nominal_power": 1030.5,
        "depth_of_discharge": 0.80,
        "efficiency": 0.9025,
        "loss_coefficient": 0.0001,
        "initial_soc": 0.50
      },

      "pv": {
        "type": "PV",
        "nominal_power": 1703.6
      },

      "cooling_device": {
        "type": "HeatPump",
        "autosize": true,
        "safety_factor": 1.000001
      },

      "chargers": [
        {"filename": "charger_1_1.csv", "nominal_power": 7.4},
        {"filename": "charger_1_2.csv", "nominal_power": 7.4}
      ],

      "washing_machines": [
        {"filename": "Washing_Machine_1.csv"}
      ]
    },
    "Building_2": { "..." },
    "...": { "..." },
    "Building_17": { "..." }
  },

  "observations": {
    "hour":                                   {"active": true, "shared_in_central_agent": true},
    "month":                                  {"active": true, "shared_in_central_agent": true},
    "outdoor_dry_bulb_temperature":           {"active": true, "shared_in_central_agent": true},
    "carbon_intensity":                       {"active": true, "shared_in_central_agent": true},
    "electricity_pricing":                    {"active": true, "shared_in_central_agent": true},
    "non_shiftable_load":                     {"active": true},
    "solar_generation":                       {"active": true},
    "electrical_storage_soc":                 {"active": true},
    "net_electricity_consumption":            {"active": true},
    "electric_vehicle_storage_soc":           {"active": true},
    "electric_vehicles_chargers_dict":        {"active": true}
  },

  "actions": {
    "electrical_storage":        {"active": true},
    "electric_vehicle_storage":  {"active": true},
    "washing_machine":           {"active": true}
  }
}
```

**Espacio de observación por agente:** 39 variables  
**Espacio de acción por agente:** 3 acciones continuas en [-1, 1]  
**Modo:** Descentralizado (`central_agent: false`) — un agente por edificio

---

## 21. Cómo Ejecutar el Pipeline Completo

### Prerrequisitos

```powershell
# Activar entorno virtual del proyecto
.\.venv39-citylearn-v3\Scripts\Activate.ps1
```

### Paso a paso

```powershell
# 1. Generar dataset completo (descarga weather, genera todos los CSV)
python -B tools/generate_iquitos_dataset.py `
    --output-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025 `
    --buildings 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 `
    --verbose

# 2. Destilar cargas reales (calibra B2-B17 con mediciones mensuales)
python -B tools/distill_building_loads.py `
    --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025 `
    --buildingcsv-dir CityLearn/data/buildingcsv `
    --output-report tools/dataset_docs/distillation_report.csv

# 3. Corregir schema de enfriamiento (float safety factor)
python -B tools/fix_schema_cooling.py `
    --schema CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json

# 4. Validar dataset completo
python -B tools/evaluate_dataset.py `
    --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025 `
    --report-path tools/dataset_docs/dataset_generation_log.json

# 5. [Opcional] Regenerar forzando re-descarga de datos meteorológicos
python -B tools/generate_iquitos_dataset.py --skip-cache --verbose
```

### Verificación rápida

```python
from citylearn.citylearn import CityLearnEnv

env = CityLearnEnv("CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json")
obs, _ = env.reset()
print(f"Agentes: {len(obs)}")       # → 17
print(f"Obs/agente: {len(obs[0])}") # → 39
print("Dataset listo para MADRL")
```

---

## 22. Parámetros Globales de Referencia

| Parámetro | Valor | Fuente/Estándar |
|-----------|:-----:|:---------------:|
| Factor emisión diésel | 0.790 kgCO₂/kWh | MINAM RAGEI 2019 · IPCC 2006 |
| Penetración solar máx. | 15% | Escenario 2030 Iquitos |
| Tarifa punta (18-22h) | $0.38/kWh | Electro Oriente S.A. 2024 |
| Tarifa fuera punta | $0.26/kWh | Electro Oriente S.A. 2024 |
| BESS DOD | 0.80 | Práctica industrial |
| BESS η_roundtrip | 0.9025 | 0.95 × 0.95 |
| BESS SOC inicial | 0.50 | Condición neutra |
| COP enfriamiento | 2.5 – 3.0 | Por tipo de edificio |
| Setpoint enfriamiento | 22 – 26 °C | Por tipo de edificio |
| Constante térmica τ | 2.0 – 5.0 h | Por tipo de edificio |
| Módulo PV | SunPower SPR-315E | η_stc=20.5%, Pmp=315W |
| Tilt PV | 5° | Techos planos Iquitos |
| Azimuth PV | 0° (Norte) | Hemisferio Sur |
| Cobertura útil PV | 63% | 0.70 × 0.90 del área techada |
| Safety factor cooling | 1.000001 | Tolerancia float CityLearn |
| Resolución temporal | 3,600 s (1 hora) | CityLearn v2 estándar |
| Total horas | 26,304 | 3 años × 8,760 h/año (2023 no bisiesto) |
| Ruido NSL | σ = 3% | Variabilidad operacional |
| Ruido cooling | σ = 1.5% | Variabilidad climática |

---

*Documento generado automáticamente desde el código fuente del proyecto.*  
*Última actualización: 2026-06-03*  
*Run de referencia: `citylearn_v3_madrl_full_20260603_200533` (tesis oficial)*
