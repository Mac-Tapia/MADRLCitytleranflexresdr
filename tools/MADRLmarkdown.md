# MADRL Iquitos — Referencia del Proyecto

**Título de tesis:** Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión
Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en
Comunidades Inteligentes

**Universidad:** Universidad Nacional Mayor de San Marcos (UNMSM)  
**Dataset propio:** `citylearn_iquitos_2023_2025` — 17 edificios, 26 304 horas (2023–2025)  
**Framework:** CityLearn v2 (base) + CityLearn v3 propuesto (extensión MADRL)  
**Algoritmos MADRL:** HAPPO · MASAC · MATD3 · MAAC  
**Ubicación:** Iquitos, Loreto, Perú (lat -3.7491, lon -73.2538)

---

## 1. Dataset citylearn_iquitos_2023_2025

### 1.1 Estructura general

| Parámetro | Valor |
|-----------|-------|
| Total horas | 26 304 (8 760 + 8 784 + 8 760) |
| Años | 2023, 2024 (bisiesto), 2025 |
| Edificios | 17 institucionales/comerciales reales |
| Columnas por edificio | 12 (formato CityLearn v2) |
| Zona horaria | America/Lima (UTC-5, sin horario de verano) |
| Sistema eléctrico | Aislado diesel — ELECTRO ORIENTE S.A. + GENRENT |
| Factor de emisión | 0.671–0.790 kg CO2/kWh (varía con irradiancia solar) |
| Tarifa MT | 0.260 USD/kWh fuera punta / 0.380 USD/kWh punta (18:00–22:59) |
| Archivos totales | 72 (17 Building + weather + carbon + pricing + 50 charger + Washing_Machine + schema) |

### 1.2 Columnas Building_X.csv (12 columnas)

| # | Columna | Unidad | Descripción |
|---|---------|--------|-------------|
| 1 | `month` | 1–12 | Mes del año |
| 2 | `hour` | 0–23 | Hora del día |
| 3 | `day_type` | 1–7 | Día de semana (1=Lun, 7=Dom) |
| 4 | `daylight_savings_status` | 0 | Siempre 0 (Perú tropical) |
| 5 | `indoor_dry_bulb_temperature` | °C | Modelo RC primer orden |
| 6 | `average_unmet_cooling_setpoint_difference` | °C | Discomfort signal OE.1 |
| 7 | `indoor_relative_humidity` | % | Modelo dehumidificación AC |
| 8 | `non_shiftable_load` | kWh_elec/h | Iluminación + equipos + refrig. comercial |
| 9 | `dhw_demand` | kWh_term/h | Solo B5 (Hotel), B11–B12 (Hospitales) |
| 10 | `cooling_demand` | kWh_term/h | Carga AC = P_AC_kW × COP × perfil |
| 11 | `heating_demand` | kWh_term/h | 0.0 siempre (Iquitos tropical, T_min=24°C) |
| 12 | `solar_generation` | kWh_elec/h | pvlib ModelChain SAPM (Sandia) |

### 1.3 Estadísticas por edificio (calibrado con datos reales GD-Iquitos V3)

| B | Edificio | NSL media (kWh/h) | CD media (kWh/h) | Solar media (kWh/h) | Total/día (kWh) | Real/día | Ratio |
|---|---------|-------------------|------------------|---------------------|-----------------|---------|-------|
| 1 | Electro Oriente S.A. | 618.0 | 145.2 | 264.4 | 16 077 | 16 091 | 1.00 |
| 2 | Complejo Champios | 7.8 | 23.2 | 143.2 | 410 | — | — |
| 3 | Aeropuerto IQT | 99.6 | 152.5 | 107.8 | 3 610 | — | — |
| 4 | Hiperbodega Precio UNO | 32.4 | 43.1 | 44.8 | 1 122 | — | — |
| 5 | Hotel El Dorado Plaza | 57.2 | 359.1 | 169.0 | 5 104 | — | — |
| 6 | Mall Aventura Iquitos | 680.2 | 1 242.0 | 386.0 | 26 260 | — | — |
| 7 | UNAP Zungarococha | 15.9 | 91.4 | 153.0 | 1 164 | 436 | 2.67† |
| 8 | Escuela Técnica PNP | 23.7 | 153.6 | 392.6 | 2 042 | 297 | 6.88† |
| 9 | Complejo CNI | 5.5 | 15.6 | 65.7 | 281 | — | — |
| 10 | Gobierno Regional | 105.6 | 96.1 | 92.8 | 3 359 | 3 358 | 1.00 |
| 11 | Hospital Regional | 233.4 | 378.5 | 222.4 | 9 963 | 9 971 | 1.00 |
| 12 | EsSalud Hospital III | 146.7 | 247.4 | 107.8 | 6 407 | 6 407 | 1.00 |
| 13 | Fac. Economía UNAP | 5.1 | 34.0 | 54.3 | 414 | 412 | 1.01 |
| 14 | Terminal ENAPU | 19.0 | 54.2 | 92.8 | 976 | 973 | 1.00 |
| 15 | Colegio CNI | 7.5 | 33.2 | 44.8 | 498 | 472 | 1.06 |
| 16 | I.E. San Juan | 12.9 | 69.2 | 121.6 | 973 | — | — |
| 17 | IEST Pedro del Águila | 12.0 | 64.3 | 96.9 | 906 | — | — |

† B7 y B8: medidor parcial en campo. Ratio >1 esperado (modelo incluye campus completo).

**Edificios calibrados con datos reales GD-Iquitos V3:** B1, B10, B11, B12, B13, B14, B15  
**Edificios con datos reales (metro parcial):** B7, B8  
**Edificios sin datos reales (benchmark técnico):** B2, B3, B4, B5, B6, B9, B16, B17

### 1.4 Validación CityLearnEnv

```
env.reset() → 17 agentes, obs[0].shape = 47
100 pasos   → 293 KPIs calculados
Estado      → VALIDADO OK
```

---

## 2. Configuración del sistema MADRL

### 2.1 Formulación Dec-POMDP

| Parámetro | Valor |
|-----------|-------|
| Número de agentes | 17 (uno por edificio) |
| Formulación | Dec-POMDP (`central_agent = false`) |
| Esquema entrenamiento | CTDE: crítico centralizado, actor descentralizado |
| Estado global S | Concatenación de 17 observaciones locales |
| Obs. local oi | Demanda, SoC BESS, PV, SoC EV, precio, carbono (47 dim.) |
| Espacio acción | [-1, 1] continuo (HAPPO, MATD3) / 3 bins discretizados (MASAC, MAAC) |
| Pasos por episodio | 8 760 pasos (1 año horario) |
| Episodios | 5 episodios = 43 800 pasos totales |
| Aggregation reward | Team mean (promedio 17 agentes) |
| Semilla | seed = 0 |

### 2.2 DER por edificio (schema.json)

Cada edificio incluye: BESS (Li-ion LFP, DoD=0.80, η_RT=0.9025) + PV (Sandia SAPM) + cargadores EV (3.3–22 kW) + carga flexible.

| Tipo | COP | DoD BESS | Nota |
|------|-----|----------|------|
| Oficina/Admin | 2.8 | 0.80 | Split VRF tropical |
| Mall | 3.0 | 0.80 | VRF central alta eficiencia |
| Hospital 24h | 2.5 | 0.80 | Chiller central + redundancia N+1 |
| Hotelero | 3.0 | 0.80 | VRF + calefón solar-eléctrico |
| Universitario | 2.8 | 0.80 | VRF universitario |
| Educación | 2.5 | 0.80 | Split básico |
| Deportivo | 2.5 | 0.80 | Split ventana/pared |
| Portuario | 2.5 | 0.80 | Split industrial |
| Transporte 24h | 3.0 | 0.80 | VRF aeropuerto |

### 2.3 Cargadores EV por edificio (50 archivos charger_X_Y.csv)

| Edificio | N° chargers | kW/charger | Tipo EV |
|---------|-------------|-----------|---------|
| B1 ELOR | 2 | 7.4 | Mediano |
| B2 Champios | 4 | 7.4 | Mediano/ligero |
| B3 Aeropuerto | 4 | 22.0 | DC fast |
| B4 Precio UNO | 3 | 7.4 | Mediano |
| B5 Hotel | 3 | 11.0 | Mediano |
| B6 Mall | 8 | 22.0 | DC fast |
| B7 UNAP | 3 | 7.4 | Mediano |
| B8 PNP | 2 | 7.4 | Mediano |
| B9 CNI | 2 | 3.3 | Ligero |
| B10 GobReg | 3 | 7.4 | Mediano |
| B11 HospReg | 4 | 11.0 + 22.0 | Mediano + ambulancia |
| B12 EsSalud | 3 | 7.4 | Mediano |
| B13 FACEN | 2 | 7.4 | Mediano |
| B14 ENAPU | 2 | 11.0 | Mediano |
| B15 ColegioC | 2 | 3.3 | Ligero |
| B16 SanJuan | 1 | 3.3 | Ligero |
| B17 IEST | 2 | 7.4 | Mediano |

---

## 3. Resultados MADRL — corrida official_full_cuda_v2

> Dataset de entrenamiento: `citylearn_challenge_2022_phase_all_plus_evs` (dataset oficial)
> Corrida: `citylearn_v3_madrl_official_full_cuda_v2`

### 3.1 Checkpoints por algoritmo

| Algoritmo | Checkpoints | Observación |
|-----------|------------|-------------|
| HAPPO | 19 | Bien entrenado |
| MASAC | 3 | Sub-entrenado (pocos checkpoints) |
| MATD3 | 34 | Bien entrenado |
| MAAC | 6 | Entrenado razonablemente |

### 3.2 KPIs comparados por eje

#### OE.1 — Flexibilidad energética (Escenario E1)

| KPI (ratio ↓mejor salvo †) | HAPPO | MASAC | MATD3 | MAAC | Mejor |
|----------------------------|-------|-------|-------|------|-------|
| peak_average | 1.844 | 2.130 | 4.155 | **1.198** | MAAC |
| ramping_average | 2.856 | 4.040 | 6.408 | **1.906** | MAAC |
| one_minus_load_factor_avg | 1.317 | **0.967** | 1.831 | 1.084 | MASAC |
| grid_import | 1.721 | 3.910 | 1.744 | **1.517** | MAAC |
| zero_net_energy † | 0.965 | -1.512 | -10.449 | **3.497** | MAAC |
| price_signal_deviation | **0.962** | 1.052 | 0.983 | 1.052 | HAPPO |
| ev_v2g_export_total (kWh) | 67.6 | **122 051** | 93.4 | 76 785 | MASAC/MAAC: V2G activo |
| battery_capacity_fade | **4.5e-6** | 0.01031 | 2.7e-6 | 0.00388 | MATD3/HAPPO |
| **KPIs mejorados vs baseline** | **1/12** | **2/12** | **1/11** | **4/12** | **MAAC** |

#### OE.2 — Emisiones CO2 (Escenario E2)

| KPI | HAPPO | MASAC | MATD3 | MAAC | Mejor |
|-----|-------|-------|-------|------|-------|
| carbon_emissions (ratio) | **1.702** | 3.781 | 1.806 | 1.733 | HAPPO |
| carbon_emissions_control | 21.36 | 47 743.0 | 36.75 | 26 508.0 | — |
| carbon_emissions_baseline | 10.35 | 17 316.4 | 13.51 | 17 455.9 | — |
| daily_average_delta | 52.86 | 83.37 | 79.65 | **24.80** | MAAC |
| **KPIs mejorados vs baseline** | **0/5** | **0/5** | **0/5** | **0/5** | Ninguno |

#### OE.3 — Costos energéticos (Escenario E3)

| KPI | HAPPO | MASAC | MATD3 | MAAC | Mejor |
|-----|-------|-------|-------|------|-------|
| electricity_cost (ratio) | 1.256 | 2.547 | 1.674 | **-0.002** | MAAC |
| electricity_cost_delta | 7.563 | 3 669.5 | 19.549 | **-2 485.4** | MAAC |
| daily_average_delta | 12.518 | 20.054 | 30.270 | **-13.583** | MAAC |
| cost_peak_average | 1.784 | 2.127 | 4.443 | **1.225** | MAAC |
| cost_ramping_average | 2.992 | 4.031 | 2.490 | **2.005** | MAAC |
| cost_one_minus_load_factor | 1.289 | **0.968** | 1.941 | 1.097 | MASAC |
| price_signal_deviation | **0.965** | 1.051 | 1.125 | 1.092 | HAPPO |
| ev_departure_success_rate † | N/A | **0.118** | N/A | 0.005 | MASAC |
| **KPIs mejorados vs baseline** | **1/9** | **1/9** | **0/9** | **5/9** | **MAAC** |

### 3.3 Ranking integrado

| Rank | Algoritmo | OE.1 | OE.2 | OE.3 | Global | Comentario |
|------|-----------|------|------|------|--------|-----------|
| 1 | **MAAC** | 1° | 2° | 1° | **1°** | Mejor OE.1 y OE.3; 4/12 y 5/9 KPIs mejorados |
| 2 | **HAPPO** | 3° | 1° | 2° | 2° | Mejor OE.2 (ratio 1.702); price_signal <1 |
| 3 | **MASAC** | 2° | 4° | 3° | 3° | Segundo OE.1; penalizado por sub-entrenamiento (3 ckpts) |
| 4 | **MATD3** | 4° | 3° | 4° | 4° | Ningún KPI de costo mejorado |

### 3.4 Contrastes estadísticos (Kruskal-Wallis)

| Eje | H | p-valor | Brown-Forsythe p | Mejor (mediana) | Resultado |
|-----|---|---------|-----------------|-----------------|-----------|
| OE.1 Flexibilidad | 14.91 | 0.0019 | 0.1089 | MAAC | **Significativo** |
| OE.2 CO2 | 24.81 | 1.70×10⁻⁵ | 0.0025 | MAAC | **Significativo** |
| OE.3 Costos | 41.10 | 6.23×10⁻⁹ | 0.5417 | MAAC | **Significativo** |
| OG Integral | 58.53 | 1.21×10⁻¹² | 0.0939 | MAAC | **Significativo** |

> Todos los contrastes rechazan H₀ (p < 0.05). MAAC consistentemente mejor por mediana de ganancia.

---

## 4. Arquitectura CityLearn v3 propuesto

```
CityLearn v2 (base)
└── CityLearn/citylearn/v3/
    ├── environment.py          — CityLearnV3Env (Dec-POMDP wrapper)
    ├── objectives.py           — CityLearnV3MADRLRewardFunction (OE.1/2/3)
    └── config.py               — Configuración por algoritmo y escenario

citylearn_v3_training_common.py — Adaptador MADRL común (CTDE, artefactos)
train_citylearn_v3_happo.py     — Backend HARL (HAPPO)
train_citylearn_v3_masac.py     — Backend MARL (MASAC)
train_citylearn_v3_matd3.py     — Backend off-policy (MATD3)
train_citylearn_v3_maac.py      — Backend MAAC (atención multi-agente)
```

### Escenarios de entrenamiento

| Escenario | Eje | Reward principal | KPIs monitoreados |
|-----------|-----|-----------------|------------------|
| E1 | OE.1 Flexibilidad | Peak reduction + load factor | 12 KPIs flexibilidad |
| E2 | OE.2 CO2 | Carbon intensity weighted | 5 KPIs emisiones |
| E3 | OE.3 Costos | Price signal deviation + cost | 9 KPIs costos |

---

## 5. Dataset Iquitos — herramientas disponibles en `tools/`

| Script | Función |
|--------|---------|
| `generate_iquitos_dataset.py` | Generador completo del dataset (weather + buildings + chargers + schema) |
| `calibrate_buildings.py` | Calibración con datos reales GD-Iquitos V3 |
| `dataset_report.py` | Informe final de estadísticas por edificio |
| `evaluate_dataset.py` | Validación exhaustiva de intensidades energéticas |
| `rebuild_per_building_profiles.py` | Reconstrucción de perfiles horarios individuales |
| `fix_solar_pvlib.py` | Corrección de generación solar (pvlib ModelChain SAPM) |
| `verify_solar.py` | Verificación de coherencia solar por edificio |
| `check_schema.py` | Validación del schema.json contra edificios |
| `check_weather.py` / `check_weather2.py` | Verificación del weather.csv |

### Comandos de validación rápida

```powershell
# Activar entorno virtual
. d:/MADRLCitytleranflexresdr/scripts/activate_citylearn_v3.ps1

# Validar dataset completo
cd d:/MADRLCitytleranflexresdr
python tools/dataset_report.py

# Validar CityLearnEnv
python -c "
import sys; sys.path.insert(0, 'CityLearn')
from citylearn.citylearn import CityLearnEnv
env = CityLearnEnv('CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json')
obs, _ = env.reset()
print(f'OK: {len(obs)} agentes, obs shape={len(obs[0])}')
"
```

---

## 6. Fuentes de datos meteorológicos

| Fuente | Cobertura | Uso |
|--------|-----------|-----|
| PVGIS-ERA5 (`pvlib.iotools.get_pvgis_hourly`) | Hasta ~2023 | Primario año 2023 |
| NASA POWER REST API | 2023–2025 | Fallback + años 2024–2025 |

Caché local: `.cache/weather/{year}.parquet`

---

## 7. Estado actual del proyecto

| Componente | Estado |
|------------|--------|
| Dataset `citylearn_iquitos_2023_2025` | ✅ Generado, calibrado y validado |
| CityLearnEnv | ✅ reset() + 100 pasos + 293 KPIs OK |
| Resultados MADRL (corrida oficial) | ✅ Embebidos en `_thesis_capitulo_iii.py` |
| Contrastes estadísticos | ✅ Kruskal-Wallis + Mann-Whitney U |
| Informe de tesis (docx) | ✅ `docs/INFORME_TESIS_MADRL_V1_COMPLETO.docx` |
| Plan de tesis (docx) | ✅ `docs/PLAN_TESIS_MADRL_V4_COMPLETO.docx` |
| Skills del proyecto | ✅ `tools/skills/iquitos-citylearn-dataset/` |

---

*Última actualización: 2026-05-17*
