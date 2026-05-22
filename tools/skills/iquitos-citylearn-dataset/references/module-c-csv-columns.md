# Module C — Analisis de Columnas por Tipo de CSV

Descripcion completa de cada columna de cada tipo de CSV del dataset Iquitos.
Todos los valores son reales y no-cero donde fisicamente corresponda.

---

## Building_X.csv — 12 columnas, 26 304 filas

### Premisa fundamental para los 4 backends MADRL

Los 4 algoritmos (HAPPO, MASAC, MATD3, MAAC) acceden al vector de observacion via CityLearnEnv.
Cada columna alimenta directamente ese vector. Para OE.1/OE.2/OE.3:

| Eje | KPI | Columnas criticas |
|-----|-----|------------------|
| OE.1 Flexibilidad | Pre-enfriamiento, carga desplazable | cooling_demand, indoor_dry_bulb_temperature, non_shiftable_load, solar_generation |
| OE.2 CO2 | kg CO2 evitados | carbon_intensity x (cooling_demand/COP + non_shiftable + dhw/COP_ACS) |
| OE.3 Costos | USD ahorrados | electricity_pricing x consumo neto de red |

---

### Columna 1: month (entero 1-12)

- **Fuente**: `datetime_index.month`
- **Propósito MADRL**: estacionalidad solar; en Iquitos variacion ~10% entre meses
- **Cálculo**: `df['month'] = index.month`
- **Validacion**: rango [1,12]; 8 784 filas en 2024 (bisiesto), 8 760 en 2023 y 2025

### Columna 2: hour (entero 0-23)

- **Fuente**: `datetime_index.hour`
- **Propósito MADRL**: perfil horario de carga, ventana tarifaria (punta 18:00-22:59), ciclo solar
- **Cálculo**: `df['hour'] = index.hour`

### Columna 3: day_type (entero 1=Lun ... 7=Dom)

- **Fuente**: `datetime_index.dayofweek + 1`
- **Propósito MADRL**: ocupacion diferenciada laboral vs fds -- critico para multiplicadores de carga
- **Cálculo**: `df['day_type'] = index.dayofweek + 1`

### Columna 4: daylight_savings_status (siempre 0)

- **Justificacion**: Peru (lat -3.75) no aplica horario de verano
- **Cálculo**: `df['daylight_savings_status'] = 0`

### Columna 5: indoor_dry_bulb_temperature [grados C] — NUEVA (no vacia)

- **Importancia MADRL**: el agente usa T_indoor para decidir si pre-enfriar (OE.1)
- **Modelo**: RC primer orden (Hesse et al. 2017 extension termica)
  - AC encendido: τ_eff = τ/4, target = T_set
  - AC apagado: τ_eff = τ, target = T_outdoor
  - Ruido gaussiano ±0.3°C, seed=bldg_id
- **Setpoints [°C]**: industrial 24, mall 23, salud_24h 22, universitario 25, deportivo 26,
  educacion 25, transporte_24h 24, portuario_24h 26, hotelero_24h 23, administrativo 24
- **Rango esperado**: 22-33°C dependiendo de ocupacion y hora
- **Validacion**: rango [15, 45]

### Columna 6: average_unmet_cooling_setpoint_difference [°C] — NUEVA (no vacia)

- **Importancia MADRL**: senal de discomfort para OE.1; si > 0 el agente fallo el pre-enfriamiento
- **Cálculo**: `max(0, T_indoor - T_set) * occupancy_mask`
- **occupancy_mask**: 1 cuando el edificio esta ocupado segun horario (L-V, clases, etc.)
- **Rango esperado**: 0.0 hospitales (AC oversized 24h); 0.5-2.5 escuelas/oficinas en madrugada
- **Validacion**: >= 0 siempre

### Columna 7: indoor_relative_humidity [%] — NUEVA (no vacia)

- **Importancia MADRL**: complementa T_indoor para confort; en Iquitos RH_ext 80-98%
- **Cálculo**: `RH_out * (1 - 0.35 * cooling_frac)`, clip(30, 98)
  - eta_dehum = 0.35 (split tropical elimina ~35% humedad absoluta)
  - Sin AC: RH_in -> RH_out (infiltracion)
- **Rango esperado**: 50-70% con AC activo; 80-95% sin AC
- **Validacion**: rango [20, 100]

### Columna 8: non_shiftable_load [kWh_elec/h] — DATO CENTRAL

- **Importancia MADRL**: carga no controlable que el agente debe satisfacer siempre (OE.3)
- **Formula**:
  ```
  non_shiftable_load = base_critica + equipos_ofic(perfil*day_factor) + refrig_comercial(factor_noc)
  ```
- **Excluye**: cooling_demand (pasa a cooling_demand como kWh_termicos)
- **Incluye**: iluminacion + equipos + ventiladores + refrigeracion comercial
- **Ruido**: gaussiano ±2%, seed=bldg_id
- **Picos esperados**: B11 Hospital ~380 kW, B6 Mall ~1 000 kW apertura, B1 ELOR ~44 kW laboral
- **Validacion**: >= 0

### Columna 9: dhw_demand [kWh_thermal/h]

- **Solo B5 (Hotel El Dorado), B11 (Hospital Regional), B12 (EsSalud)**
- **Resto de edificios**: dhw_demand = 0.0
- **Valores diarios**:
  - B5: 614.0 kWh_th/dia (65 hab. x 50 L/dia x DeltaT=35°C / COP_ACS=0.85)
  - B11: 1 200.0 kWh_th/dia (~200 camas + cocina + esterilizacion)
  - B12: 780.0 kWh_th/dia (~120 camas + cocina)
- **Perfiles horarios**:
  - Hotel: pico 06:00-08:00 y 18:00-20:00
  - Hospitales: uniforme 24h (ciclos de esterilizacion y cocina)
- **CityLearn calcula**: E_elec_ACS = dhw_demand / COP_ACS (COP_ACS = 0.85)
- **Validacion**: >= 0

### Columna 10: cooling_demand [kWh_thermal/h] — DATO CENTRAL

- **Importancia MADRL**: carga termica que el HVAC debe cubrir; accion principal del pre-enfriamiento
- **Formula**: `P_AC_kW * COP * perfil_AC[h] * day_factor`
- **cooling_frac[t]** = `perfil_AC[t] * day_factor[t]` (reutilizado en cols 5, 6, 7)
- **COP por tipo**: ver constante COP_BY_TYPE en SKILL.md
- **CityLearn calcula**: E_elec_cooling = cooling_demand / COP
- **Validacion**: >= 0; suma mensual coherente con kWh/mes real donde disponible

### Columna 11: heating_demand [kWh_thermal/h]

- **Siempre 0.0** — Iquitos T_min = 24°C, no existe calefaccion
- `df['heating_demand'] = 0.0`

### Columna 12: solar_generation [kWh_elec/h] — DATO CENTRAL

- **Importancia MADRL**: generacion local -> carga BESS, reduccion compra red, reduccion CO2
- **Metodo**: pvlib ModelChain SAPM, modulo e inversor Sandia
- **Parametros**: tilt=5°, azimuth=0° (norte, hemisferio sur), open_rack_glass_glass
- **Resultado**: .results.ac [W] / 1000 -> kWh/h, clip(0).fillna(0)
- **Generacion tipica**: 4.2-4.8 kWh/kWp/dia (Iquitos ecuatorial)
- **Validacion**: >= 0; NaN -> 0

---

## weather.csv — 16 columnas, 26 304 filas

| # | Columna | Fuente | Notas |
|---|---------|--------|-------|
| 1 | outdoor_dry_bulb_temperature [°C] | NASA POWER T2M | Rango 26-33°C Iquitos |
| 2 | outdoor_relative_humidity [%] | NASA POWER RH2M | Rango 75-98% |
| 3 | diffuse_solar_irradiance [W/m2] | PVGIS DHI (2023) / NASA DHI (2024-25) | Componente difusa alta por nubosidad tropical |
| 4 | direct_solar_irradiance [W/m2] | PVGIS DNI / NASA DNI | Componente directa |
| 5 | outdoor_dry_bulb_temperature_predicted_1 [°C] | T.shift(-1).ffill() | Pronostico +1h |
| 6 | outdoor_dry_bulb_temperature_predicted_2 | T.shift(-2).ffill() | Pronostico +2h |
| 7 | outdoor_dry_bulb_temperature_predicted_3 | T.shift(-3).ffill() | Pronostico +3h |
| 8 | outdoor_relative_humidity_predicted_1 [%] | RH.shift(-1).ffill() | -- |
| 9 | outdoor_relative_humidity_predicted_2 | RH.shift(-2).ffill() | -- |
| 10 | outdoor_relative_humidity_predicted_3 | RH.shift(-3).ffill() | -- |
| 11 | diffuse_solar_irradiance_predicted_1 [W/m2] | DHI.shift(-1).ffill() | -- |
| 12 | diffuse_solar_irradiance_predicted_2 | DHI.shift(-2).ffill() | -- |
| 13 | diffuse_solar_irradiance_predicted_3 | DHI.shift(-3).ffill() | -- |
| 14 | direct_solar_irradiance_predicted_1 [W/m2] | DNI.shift(-1).ffill() | -- |
| 15 | direct_solar_irradiance_predicted_2 | DNI.shift(-2).ffill() | -- |
| 16 | direct_solar_irradiance_predicted_3 | DNI.shift(-3).ffill() | -- |

**Validacion critica**: total_rows = 26 304; sin NaN excepto ultimas 3 filas de predicciones (rellenar con ffill).

**NASA POWER API endpoint**:
```
https://power.larc.nasa.gov/api/temporal/hourly/point
  ?parameters=T2M,RH2M,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_SFC_SW_DNI,WS10M
  &community=RE&longitude=-73.2538&latitude=-3.7491
  &start={year}0101&end={year}1231&format=JSON
```

---

## carbon_intensity.csv — 1 columna, 26 304 filas

| Columna | Valores | Importancia MADRL OE.2 |
|---------|---------|----------------------|
| carbon_intensity [kg CO2/kWh] | 0.672-0.790 | Senal de recompensa directa para OE.2 |

**Formula**:
```python
carbon_intensity = FE_DIESEL * (1 - SOLAR_PENETRACION * GHI/1000)
# FE_DIESEL = 0.79 kg CO2/kWh (MINAM RAGEI 2019 -- sistemas aislados diesel)
# SOLAR_PENETRACION = 0.15 (15% penetracion solar ELECTRO ORIENTE + GENRENT + FV)
# Rango: 0.672 (mediodia soleado) -- 0.790 (noche, 100% diesel)
```

**Fuente oficial**: MINAM INFOCARBONO (https://infocarbono.minam.gob.pe/)
RAGEI 2019 Energia: FE diesel generacion aislada = 0.79 tCO2/MWh

**Alcance GHG**: Scope 2 (generacion electrica consumida, no emision directa)

Cuando el solar penetra -> baja intensidad -> el agente aprende no-comprar-red en horas solares.

**Archivo metadata**: carbon_intensity_metadata.json con referencias MINAM/RAGEI completas.

---

## pricing.csv — 4 columnas, 26 304 filas

| # | Columna | Valores | Importancia MADRL OE.3 |
|---|---------|---------|----------------------|
| 1 | electricity_pricing [USD/kWh] | 0.26-0.38 | Senal principal OE.3 |
| 2 | electricity_pricing_predicted_1 | price.shift(-1).ffill() | Planificacion BESS +1h |
| 3 | electricity_pricing_predicted_2 | price.shift(-2).ffill() | -- |
| 4 | electricity_pricing_predicted_3 | price.shift(-3).ffill() | -- |

**Patron TOU (Time-of-Use)**:
- Punta: 18:00-22:59 cualquier dia = **0.38 USD/kWh**
- Fuera punta: 00:00-17:59 y 23:00-23:59 = **0.26 USD/kWh**
- Diferencia: 46% -> senal clara para estrategia BESS

**Nota**: todos los 17 edificios son clientes en MEDIA TENSION (MT) -- hospitales, universidades,
mall, aeropuerto, instituciones grandes con acometida MT, no BT.

**Fuente**: OSINERGMIN Pliegos Tarifarios MT3/MT4 -- Empresa ELECTRO ORIENTE S.A. Loreto.
Script intenta descarga mensual; si falla usa fallback hardcoded.

---

## charger_X_Y.csv — 6 columnas, 26 304 filas (50 archivos)

| # | Columna | Tipo | Descripcion |
|---|---------|------|-------------|
| 1 | electric_vehicle_charger_state | int 0/1 | 0=disponible, 1=EV conectado |
| 2 | electric_vehicle_id | float (NaN cuando state=0) | ID unico del EV por sesion |
| 3 | electric_vehicle_departure_time | float (hora) | Hora a la que el EV debe partir |
| 4 | electric_vehicle_required_soc_departure | float 0-1 | SOC requerido al partir (restriccion dura) |
| 5 | electric_vehicle_estimated_arrival_time | float (hora) | Hora estimada de llegada proximo EV |
| 6 | electric_vehicle_estimated_soc_arrival | float 0-1 | SOC estimado al llegar |

**El agente MADRL solo puede actuar cuando state=1** (EV conectado).
La restriccion dura es: SOC(departure_time) >= required_soc_departure.
El agente decide la tasa de carga para cumplir este requisito con minimo costo.

**Sesiones estocasticas**:
```python
# 90% probabilidad de que llegue un EV en dias activos
# Hora llegada: N(arrival_h, 1.0) -- variabilidad ±1h
# SOC llegada: U(soc_arr_min, soc_arr_max) -- aleatorio uniforme
# seed = bldg_id * 100 + charger_idx -- reproducibilidad
```

**Validacion**: state in {0,1}, SOC in [0,1], departure > arrival.

---

## Washing_Machine_1.csv — 5 columnas, 26 304 filas (solo Building_1)

| # | Columna | Tipo | Descripcion |
|---|---------|------|-------------|
| 1 | day_type | int 1-7 | dia de semana |
| 2 | hour | int 0-23 | hora del dia |
| 3 | wm_start_time_step | int | hora de inicio del ciclo (06:00-08:00 o 12:00-14:00) |
| 4 | wm_end_time_step | int | hora de fin (start + 2h) |
| 5 | load_profile | float kWh | consumo del ciclo (2.5 kWh/ciclo) |

**Justificacion**: representa lavadora de mamelucos/uniformes del personal tecnico ELOR.
Dispositivo desplazable representativo. Solo B1 lo tiene (replica estructura demo original).

---

## schema.json — Campos Criticos para MADRL

```json
{
  "buildings": [
    {
      "name": "Building_1",
      "energy_simulation": "Building_1.csv",
      "weather": "weather.csv",
      "carbon_intensity": "carbon_intensity.csv",
      "pricing": "pricing.csv",
      "inactive_observations": [],
      "inactive_actions":      [],
      "cooling_device": {
        "type": "AirConditioner",
        "efficiency": 2.8,
        "autosize": false,
        "nominal_power": 127
      },
      "dhw_device": null,
      "electrical_storage": {
        "type": "Battery",
        "capacity": 4000,
        "nominal_power": 800,
        "depth_of_discharge": 0.80,
        "efficiency": 0.9025,
        "loss_coefficient": 0.00001,
        "initial_charge": 0.50
      },
      "pv_system": {
        "type": "PV",
        "nominal_power": 2117,
        "efficiency": 1.0
      },
      "electric_vehicle_chargers": [
        {"charger_id": "charger_1_1.csv", "nominal_power": 7.4},
        {"charger_id": "charger_1_2.csv", "nominal_power": 7.4}
      ]
    }
  ]
}
```

**Importante**:
- `inactive_observations: []` -- NUNCA desactivar; todos los campos necesarios para MADRL
- `inactive_actions: []` -- HAPPO/MASAC/MATD3/MAAC usan todas las acciones
- `dhw_device` solo para B5 (hotel), B11 y B12 (hospitales)
- `efficiency` en cooling_device = COP del tipo de edificio
- `nominal_power` en pv_system = kWp DC del array Sandia (efficiency=1.0 ya incluida en solar_generation CSV)

---

## Separacion de Cargas: non_shiftable_load vs cooling_demand

```
non_shiftable_load [kWh_elec] = iluminacion + equipos + refrigeradores + ventiladores
cooling_demand     [kWh_term] = carga_AC_electrica x COP_dispositivo
dhw_demand         [kWh_term] = consumo ACS electrico x COP_ACS  (solo Hotel, Hospitales)
heating_demand     [kWh_term] = 0.0 (Iquitos tropical)
```

**CityLearn v2 calcula energia electrica total**:
```
E_total_elec = non_shiftable_load + cooling_demand/COP + dhw_demand/COP_ACS
```

El agente MADRL gestiona BESS y EV para cubrir este E_total_elec minimizando costo/CO2.

| Tipo edificio | COP_cooling | COP_ACS | Fuente |
|-------------|------------|--------|--------|
| Oficina/Admin/Industrial | 2.8 | -- | ASHRAE 55-2020 Split VRF tropical |
| Mall / Hotel / Transporte | 3.0 | 0.85 | VRF central alta eficiencia |
| Hospital 24h | 2.5 | 0.85 | Chiller central + calefon ACS |
| Deportivo / Educacion | 2.5 | -- | Split basico tropical |
| Universitario | 2.8 | -- | VRF universitario |
| Portuario | 2.5 | -- | Split industrial |
