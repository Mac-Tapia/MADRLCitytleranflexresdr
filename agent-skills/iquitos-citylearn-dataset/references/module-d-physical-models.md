# Module D — Modelos Fisicos (Codigo Python Completo)

Implementaciones de referencia para los modelos fisicos del dataset Iquitos.
Cada funcion esta documentada con su fuente bibliografica y parametros clave.

---

## 1. Modelo RC Termico -- indoor_dry_bulb_temperature

**Referencia**: Modelo de primer orden resistencia-capacitancia (RC).
Extension conceptual de Hesse et al. (2017, DOI:10.3390/en10122107), seccion 3.2 (thermal comfort).

```python
import numpy as np
import pandas as pd

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


def build_indoor_temperature(
    T_outdoor: pd.Series,
    cooling_frac: pd.Series,
    bldg_type: str,
    seed: int = 42,
) -> pd.Series:
    """
    Modelo RC primer orden para T_indoor.

    Cuando AC opera (cooling_frac > 0.05):
        tau_eff = tau / 4     -> convergencia rapida a T_set
    Cuando AC apagado:
        tau_eff = tau         -> deriva termica hacia T_outdoor

    alpha = exp(-1 / tau_eff)
    T_in[i] = alpha * T_in[i-1] + (1 - alpha) * target

    Mas ruido gaussiano N(0, 0.3 grados C) para realismo.

    Parametros
    ----------
    T_outdoor    : pd.Series -- temperatura exterior NASA POWER T2M [grados C]
    cooling_frac : pd.Series -- fraccion de operacion AC (0-1)
    bldg_type    : str -- tipo de edificio para setpoint y tau
    seed         : int -- semilla RNG para reproducibilidad

    Retorna pd.Series [grados C] con nombre 'indoor_dry_bulb_temperature'
    """
    T_set = SETPOINTS_C[bldg_type]
    tau   = TAU_HOURS[bldg_type]
    rng   = np.random.default_rng(seed)

    T_in  = np.full(len(T_outdoor), T_set, dtype=float)

    for i in range(1, len(T_in)):
        if cooling_frac.iloc[i] > 0.05:
            tau_eff = tau / 4.0
            target  = T_set
        else:
            tau_eff = tau
            target  = float(T_outdoor.iloc[i])

        alpha   = np.exp(-1.0 / tau_eff)
        T_in[i] = alpha * T_in[i - 1] + (1.0 - alpha) * target

    noise = rng.normal(0.0, 0.3, len(T_in))
    series = pd.Series(T_in + noise, index=T_outdoor.index,
                       name='indoor_dry_bulb_temperature')
    return series.clip(lower=15.0, upper=45.0)
```

**Valores tipicos Iquitos**:
- Hospitales (salud_24h, AC 24h): T_indoor ~22°C ± 0.3°C constante
- Escuelas fuera de horario (educacion, AC apagado): T_indoor -> T_outdoor (28-33°C)
- Mall: ciclo diario 23°C apertura -> 27°C cierre -> 23°C (AC enciende)

---

## 2. Humedad Relativa Interior -- indoor_relative_humidity

**Referencia**: modelo empirico de dehumidificacion de splits tropicales.
Los equipos split convencionales en clima tropical eliminan ~35% de la humedad absoluta
del aire que enfrían (ASHRAE 2022 Handbook HVAC Applications, capitulo 4).

```python
def build_indoor_humidity(
    RH_outdoor: pd.Series,
    cooling_frac: pd.Series,
    bldg_type: str,
) -> pd.Series:
    """
    Modelo de dehumidificacion para RH_indoor.

    RH_in = RH_out * (1 - eta_dehum * cooling_frac)

    eta_dehum = 0.35 (split tropical estandar elimina ~35% humedad absoluta)
    Sin AC: RH_in -> RH_out por infiltracion natural.

    Parametros
    ----------
    RH_outdoor   : pd.Series -- humedad relativa exterior NASA POWER RH2M [%]
    cooling_frac : pd.Series -- fraccion de operacion AC (0-1)
    bldg_type    : str -- tipo de edificio (no usado actualmente, para extension)

    Retorna pd.Series [%] con nombre 'indoor_relative_humidity'
    """
    eta_dehum = 0.35
    RH_in = RH_outdoor * (1.0 - eta_dehum * cooling_frac)
    return RH_in.clip(lower=30.0, upper=98.0).rename('indoor_relative_humidity')
```

**Rango esperado**:
- AC activo (cooling_frac ~ 0.90): RH_in ~ RH_out * 0.685 ~ 55-68% (Iquitos RH_out ~80%)
- AC apagado (madrugada, fines de semana): RH_in -> 80-98%

---

## 3. Discomfort Signal -- average_unmet_cooling_setpoint_difference

```python
def build_unmet_cooling(
    T_indoor: pd.Series,
    bldg_type: str,
    occupancy_mask: pd.Series,
) -> pd.Series:
    """
    Diferencia positiva entre T_indoor y T_set cuando el edificio esta ocupado.

    unmet = max(0, T_indoor - T_set) * occupancy_mask

    occupancy_mask: pd.Series booleana/binaria:
        - 1 cuando el edificio tiene ocupacion (segun horario laboral/escolar/etc.)
        - 0 cuando el edificio esta vacio (madrugada, fines semana para tipos no-24h)

    El agente MADRL usa esta senal para aprender a pre-enfriar ANTES de la ocupacion.
    Valores tipicos:
        - Hospitales (24h): 0.0 casi siempre (AC oversized 24h)
        - Escuelas: 0.5-2.5 grados C en las primeras horas tras apertura si no hay pre-enfriamiento
        - Oficinas: 0.2-1.5 grados C en hora pico si fallo el pre-enfriamiento

    Retorna pd.Series [grados C] con nombre 'average_unmet_cooling_setpoint_difference'
    """
    T_set = SETPOINTS_C[bldg_type]
    unmet = (T_indoor - T_set).clip(lower=0.0) * occupancy_mask
    return unmet.rename('average_unmet_cooling_setpoint_difference')


def build_occupancy_mask(index: pd.DatetimeIndex, bldg_type: str) -> pd.Series:
    """
    Mascara binaria de ocupacion por tipo de edificio.

    Reglas por tipo:
    - salud_24h: siempre 1 (hospitales 24h)
    - hotelero_24h: siempre 1 (hotel 24h)
    - transporte_24h: siempre 1 (aeropuerto 24h)
    - portuario_24h: 1 en 06:00-22:00
    - administrativo: 1 en L-V 07:00-15:00
    - universitario: 1 en L-V 07:00-18:00
    - industrial: 1 en L-V 07:00-17:00
    - educacion: 1 en L-V 07:00-15:00
    - deportivo: 1 en 08:00-22:00 (eventos tardes/noches fds)
    - mall: 1 en 10:00-21:00 todos los dias
    """
    hour = index.hour
    dow  = index.dayofweek  # 0=Lun...6=Dom
    mask = np.zeros(len(index), dtype=float)

    if bldg_type in ('salud_24h', 'hotelero_24h', 'transporte_24h'):
        mask[:] = 1.0
    elif bldg_type == 'portuario_24h':
        mask[(hour >= 6) & (hour < 22)] = 1.0
    elif bldg_type == 'administrativo':
        mask[(dow < 5) & (hour >= 7) & (hour < 15)] = 1.0
    elif bldg_type == 'universitario':
        mask[(dow < 5) & (hour >= 7) & (hour < 18)] = 1.0
    elif bldg_type == 'industrial':
        mask[(dow < 5) & (hour >= 7) & (hour < 17)] = 1.0
    elif bldg_type == 'educacion':
        mask[(dow < 5) & (hour >= 7) & (hour < 15)] = 1.0
    elif bldg_type == 'deportivo':
        mask[(hour >= 8) & (hour < 22)] = 1.0
    elif bldg_type == 'mall':
        mask[(hour >= 10) & (hour < 21)] = 1.0

    return pd.Series(mask, index=index)
```

---

## 4. BESS Sizing -- balance energetico acumulado

**Referencia**: Hesse et al. (2017). Lithium-Ion Battery Storage for the Grid.
Energies, 10(12), 2107. DOI:10.3390/en10122107 (Ecuaciones 5 y 6).
Complemento peak shaving: Oudalov et al. (2007). DOI:10.1109/TSTE.2012.2228541

```python
def size_bess(
    load_kwh: pd.Series,
    solar_kwh: pd.Series,
    dod: float = 0.80,
    eta_c: float = 0.95,
    eta_d: float = 0.95,
    target_ss: float = 0.70,
) -> dict:
    """
    Dimensionamiento BESS por balance energetico acumulado.

    Metodologia (Hesse et al. 2017, Eq. 5-6):
      1. Potencia neta: p_net = load - solar
      2. Excedente FV (carga BESS): surplus = max(0, -p_net)
      3. Deficit (descarga BESS): deficit = max(0, p_net)
      4. Curva SOC acumulada: soc_curve = cumsum(surplus*eta_c - deficit/eta_d)
      5. Rango de SOC: E_raw = soc_curve.max() - soc_curve.min()
      6. Capacidad ajustada: E_bess = (E_raw / dod) * target_ss
      7. Potencia pico: P_bess = max(deficit.quantile(0.99), surplus.quantile(0.99))

    Parametros
    ----------
    load_kwh   : pd.Series -- carga electrica horaria [kWh/h]
    solar_kwh  : pd.Series -- generacion FV AC horaria [kWh/h]
    dod        : float -- depth of discharge LFP (0.80)
    eta_c      : float -- eficiencia de carga (0.95)
    eta_d      : float -- eficiencia de descarga (0.95)
    target_ss  : float -- target de autoabastecimiento (0.70 = 70%)

    Retorna dict con parametros para schema.json
    """
    p_net   = load_kwh - solar_kwh
    surplus = (-p_net).clip(lower=0.0)
    deficit = p_net.clip(lower=0.0)

    soc_curve = (surplus * eta_c - deficit / eta_d).cumsum()
    E_raw_kwh = float(soc_curve.max() - soc_curve.min())
    E_bess_kwh = (E_raw_kwh / dod) * target_ss

    P_discharge_kw = float(deficit.quantile(0.99))
    P_charge_kw    = float(surplus.quantile(0.99))
    P_bess_kw      = max(P_discharge_kw, P_charge_kw)

    return {
        'capacity':           round(E_bess_kwh, 1),
        'nominal_power':      round(P_bess_kw, 1),
        'depth_of_discharge': dod,
        'efficiency':         round(eta_c * eta_d, 4),
        'loss_coefficient':   1e-5,
        'initial_charge':     0.50,
    }
```

**Parametros Li-ion LFP fijos para todos los 17 edificios**:

| Parametro | Valor | Fuente |
|-----------|-------|--------|
| DoD | 0.80 | CATL/BYD LFP spec; Hesse et al. 2017 |
| eta_RT | 0.9025 (0.95 x 0.95) | LFP comercial; Nottrott et al. 2013 |
| loss_coefficient | 1e-5 /h | Self-discharge minimo LFP |
| initial_charge | 0.50 | Estado neutro al inicio |

---

## 5. Seleccion de Modulo Sandia

```python
import pvlib

def select_best_sandia_module() -> tuple[str, dict]:
    """
    Selecciona el modulo FV optimo de la base Sandia para clima tropical de Iquitos.

    Criterios:
    - Eficiencia STC >= 18% (mayor potencia por m2 de techo)
    - Area modulo 1.7-2.6 m2 (modulos 60-72 celdas comerciales)
    - Potencia STC >= 300 W
    - Mayor eficiencia primero; luego menor |BVoco| (menos perdida por calor 28-33 grados C)

    Retorna (module_key, module_params_dict)
    """
    mods = pvlib.pvsystem.retrieve_sam('SandiaMod')

    mods['Pmp_stc'] = mods['Vmpo'] * mods['Impo']
    mods['eta_stc'] = mods['Pmp_stc'] / (mods['Area'] * 1000.0)

    candidates = mods[
        (mods['eta_stc'] >= 0.18) &
        (mods['Area'].between(1.7, 2.6)) &
        (mods['Pmp_stc'] >= 300.0)
    ].copy()

    candidates['abs_BVoco'] = candidates['BVoco'].abs()
    best = candidates.sort_values(
        by=['eta_stc', 'abs_BVoco'], ascending=[False, True]
    )

    best_key = best.index[0]
    return best_key, mods[best_key].to_dict()


def select_best_sandia_inverter(pdc_kw: float) -> tuple[str, dict]:
    """
    Selecciona el inversor Sandia con Pdc0 mas cercano al target (±20-30%)
    y maxima eficiencia eta_inv = Paco / Pdc0.

    Retorna (inverter_key, inverter_params_dict)
    """
    invs = pvlib.pvsystem.retrieve_sam('SandiaInverter')
    pdc_w = pdc_kw * 1000.0

    candidates = invs[
        (invs['Pdc0'] >= pdc_w * 0.80) &
        (invs['Pdc0'] <= pdc_w * 1.30)
    ].copy()

    if candidates.empty:
        candidates = invs.iloc[(invs['Pdc0'] - pdc_w).abs().argsort()[:3]].copy()

    candidates['eta_inv'] = candidates['Paco'] / candidates['Pdc0']
    best_key = candidates.sort_values('eta_inv', ascending=False).index[0]
    return best_key, invs[best_key].to_dict()
```

---

## 6. Generacion Solar FV con pvlib ModelChain SAPM

```python
def calc_solar_generation(
    weather_df: pd.DataFrame,
    n_modules: int,
    modules_per_string: int,
    module_params: dict,
    inverter_params: dict,
) -> pd.Series:
    """
    Calcula generacion AC horaria [kWh/h] para un edificio.

    Modelo: Sandia Array Performance Model (SAPM) via pvlib.ModelChain.
    Localizacion: Iquitos (lat=-3.7491, lon=-73.2538, alt=106m, tz=America/Lima)
    Montaje: tilt=5 grados, azimuth=0 grados (norte, hemisferio sur ecuatorial)
    Temperatura: open_rack_glass_glass (SAPM, clima tropical humedo)

    Parametros
    ----------
    weather_df      : DataFrame con columnas [ghi, dhi, dni, temp_air, wind_speed]
    n_modules       : numero total de modulos del array
    modules_per_string: modulos en serie por string (<= 20 para Voc <= 1000V)
    module_params   : dict del modulo Sandia seleccionado
    inverter_params : dict del inversor Sandia seleccionado

    Retorna pd.Series [kWh/h] con nombre 'solar_generation'
    """
    LOCATION = pvlib.location.Location(
        latitude=-3.7491, longitude=-73.2538,
        tz='America/Lima', altitude=106,
    )

    TEMP_PARAMS = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
        'sapm']['open_rack_glass_glass']

    n_strings = int(np.ceil(n_modules / modules_per_string))

    array = pvlib.pvsystem.Array(
        mount=pvlib.pvsystem.FixedMount(surface_tilt=5, surface_azimuth=0),
        module_parameters=module_params,
        temperature_model_parameters=TEMP_PARAMS,
        modules_per_string=modules_per_string,
        strings=n_strings,
    )
    system = pvlib.pvsystem.PVSystem(
        arrays=[array],
        inverter_parameters=inverter_params,
    )

    mc = pvlib.modelchain.ModelChain(
        system, LOCATION,
        aoi_model='sapm',
        spectral_model='sapm',
    )

    weather = weather_df.rename(columns={
        'GHI': 'ghi', 'DHI': 'dhi', 'DNI': 'dni',
        'T2M': 'temp_air', 'WS': 'wind_speed',
    })[['ghi', 'dhi', 'dni', 'temp_air', 'wind_speed']]

    mc.run_model(weather)

    ac_kwh = (mc.results.ac / 1000.0).clip(lower=0.0).fillna(0.0)
    ac_kwh.name = 'solar_generation'
    return ac_kwh
```

**Generacion tipica Iquitos**:

| Periodo | GHI W/m2 | Generacion kW/kWp |
|---------|----------|------------------|
| Noche | 0 | 0 |
| Amanecer/atardecer (06-07h, 17-18h) | 10-150 | 0.005-0.10 |
| Maniana/tarde (08-09h, 16-17h) | 300-600 | 0.20-0.45 |
| Mediodia solar (09:30-14:30) | 700-1 000 | 0.55-0.82 |
| Generacion tipica diaria/kWp | -- | 4.2-4.8 kWh/kWp/dia |
| Perdida termica tropical (+32°C celda) | -- | -3 a -5% vs STC |

---

## 7. Carbon Intensity (Scope 2 -- ELECTRO ORIENTE + GENRENT)

```python
def build_carbon_intensity(
    ghi_series: pd.Series,
    fe_diesel: float = 0.79,
    solar_penetracion: float = 0.15,
) -> pd.Series:
    """
    Intensidad de carbono de la red electrica de Iquitos [kg CO2/kWh].

    Scope 2 (GHG Protocol): emision indirecta por generacion electrica consumida.
    Generadores: ELECTRO ORIENTE S.A. + GENRENT (diesel base) + FV (0 CO2).

    Formula:
        carbon_intensity[t] = FE_diesel * (1 - solar_pen * GHI[t] / 1000)

    Donde:
        FE_diesel = 0.79 kg CO2/kWh (MINAM RAGEI 2019 -- sistemas aislados diesel Peru)
        solar_pen = 0.15 (15% penetracion solar actual ELOR+GENRENT+FV)
        GHI[t]   = irradiancia global horizontal en W/m2

    Rango resultante: 0.672 (mediodia soleado) -- 0.790 (noche, 100% diesel)

    Fuente oficial:
        MINAM INFOCARBONO: https://infocarbono.minam.gob.pe/
        RAGEI 2019 Energia: FE diesel aislado = 0.79 tCO2/MWh
    """
    ghi_frac = (ghi_series / 1000.0).clip(0.0, 1.0)
    ci = fe_diesel * (1.0 - solar_penetracion * ghi_frac)
    return ci.clip(lower=0.0).rename('carbon_intensity')
```

---

## 8. non_shiftable_load -- Composicion por Edificio

```python
def build_non_shiftable_load(
    bldg_id: int,
    index: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> pd.Series:
    """
    Carga electrica no desplazable horaria [kWh_elec/h].

    Composicion:
        load = (base_critica + equip_oficina(perfil*day_f) + refrig_comercial(factor_noc))
               * ruido_gaussian(mu=1.0, sigma=0.02)

    Donde:
        base_critica    = NON_SHIFTABLE_BASE_kW (carga critica 24h constante)
        equip_oficina   = (pico_total - base - refrig) * perfil[h] * day_factor
        refrig_comercial= solo B3,B4,B5,B6,B11,B12 (alimentos + farmacia)
        factor_noc      = multiplicador nocturno 00:00-05:00 para refrigeracion

    EXCLUYE: cooling_demand (va aparte como kWh_termicos)
    INCLUYE: iluminacion + equipos + ventiladores + refrigeracion comercial
    """
    from module_b import (MADRL_BUILDING_CONSTANTS, LOAD_PROFILES,
                          DAY_FACTOR_MAP, REFRIGERACION_COMERCIAL,
                          TOTAL_NSL_PEAK)

    cfg    = MADRL_BUILDING_CONSTANTS[bldg_id]
    btype  = cfg['bldg_type']
    prof   = np.array(LOAD_PROFILES[btype])
    dof, ds, dd = DAY_FACTOR_MAP[btype]  # laboral, sabado, domingo

    hours = index.hour.values
    dows  = index.dayofweek.values  # 0=Lun...6=Dom

    day_f = np.where(dows < 5, dof, np.where(dows == 5, ds, dd))

    base = cfg['non_shiftable_base']

    refrig_kw, factor_noc = REFRIGERACION_COMERCIAL.get(bldg_id, (0.0, 1.0))
    refrig = np.where(hours < 6, refrig_kw * factor_noc, refrig_kw)

    equip_peak = TOTAL_NSL_PEAK.get(bldg_id, base * 2.0) - base - refrig_kw
    equip_peak = max(equip_peak, 0.0)
    equip = equip_peak * prof[hours] * day_f

    noise = rng.normal(1.0, 0.02, len(index))
    load  = (base + equip + refrig) * noise

    return pd.Series(load.clip(min=0.0), index=index, name='non_shiftable_load')
```

---

## 9. cooling_demand -- kWh_thermal/h

```python
COP_BY_TYPE = {
    'industrial': 2.8, 'mall': 3.0, 'salud_24h': 2.5, 'hotelero_24h': 3.0,
    'deportivo': 2.5, 'universitario': 2.8, 'educacion': 2.5,
    'portuario_24h': 2.5, 'transporte_24h': 3.0, 'administrativo': 2.8,
}

def build_cooling_demand(
    bldg_id: int,
    cooling_frac: pd.Series,
) -> pd.Series:
    """
    Carga termica de enfriamiento [kWh_thermal/h].

    cooling_demand[t] = P_AC_kW * COP * cooling_frac[t]

    Donde:
        P_AC_kW     = COOLING_PEAK (carga AC electrica pico del edificio)
        COP         = coeficiente de rendimiento por tipo de edificio
        cooling_frac = perfil_AC[h] * day_factor (de 0 a 1)

    CityLearn convierte: E_elec_cooling = cooling_demand / COP al optimizar.
    """
    cfg      = MADRL_BUILDING_CONSTANTS[bldg_id]
    btype    = cfg['bldg_type']
    p_ac_kw  = cfg['cooling_peak']
    cop      = COP_BY_TYPE[btype]

    cd = p_ac_kw * cop * cooling_frac
    return cd.clip(lower=0.0).rename('cooling_demand')
```

---

## 10. dhw_demand -- kWh_thermal/h (solo B5, B11, B12)

```python
DHW_KWH_THERMAL_DAY = {5: 614.0, 11: 1200.0, 12: 780.0}

DHW_PROFILE_HOTEL = [
    0.02, 0.01, 0.01, 0.01, 0.02, 0.06,
    0.10, 0.12, 0.08, 0.05, 0.04, 0.04,
    0.05, 0.04, 0.04, 0.04, 0.05, 0.08,
    0.10, 0.08, 0.06, 0.04, 0.03, 0.02,
]
DHW_PROFILE_HOSPITAL = [0.04167] * 24  # uniforme 24h (suma = 1.0)

def build_dhw_demand(bldg_id: int, index: pd.DatetimeIndex) -> pd.Series:
    """
    Demanda de agua caliente sanitaria [kWh_thermal/h].
    Solo para edificios B5 (hotel), B11 (Hospital Regional), B12 (EsSalud).
    Resto de edificios: retorna serie de ceros.

    COP_ACS = 0.85 (calefon electrico resistivo estandar Peru)
    CityLearn calcula: E_elec_ACS = dhw_demand / COP_ACS
    """
    if bldg_id not in DHW_KWH_THERMAL_DAY:
        return pd.Series(0.0, index=index, name='dhw_demand')

    daily = DHW_KWH_THERMAL_DAY[bldg_id]
    profile = DHW_PROFILE_HOTEL if bldg_id == 5 else DHW_PROFILE_HOSPITAL
    factor = pd.Series([profile[h] for h in index.hour], index=index)
    return (daily * factor).rename('dhw_demand')
```

---

## 11. Sesiones EV Estocasticas -- charger_X_Y.csv

```python
def build_charger_csv(
    bldg_id: int,
    charger_idx: int,
    index: pd.DatetimeIndex,
    ev_config: dict,
) -> pd.DataFrame:
    """
    Genera sesiones EV estocasticas reproducibles para un cargador.

    ev_config: tupla (arrival_h, depart_h, soc_min, soc_max, soc_req, bat_kwh, kw, days)
    seed = bldg_id * 100 + charger_idx (reproducibilidad entre ejecuciones)

    Probabilidad EV dia activo: 90%
    Variabilidad hora llegada: N(arrival_h, 1.0) clip a entero
    Variabilidad SOC llegada: U(soc_min, soc_max)
    """
    rng = np.random.default_rng(seed=bldg_id * 100 + charger_idx)
    arr_h, dep_h, soc_min, soc_max, soc_req, bat_kwh, kw, days = ev_config

    n = len(index)
    state   = np.zeros(n, dtype=int)
    ev_id   = np.full(n, np.nan)
    dep_t   = np.full(n, np.nan)
    req_soc = np.full(n, np.nan)
    arr_t   = np.full(n, np.nan)
    arr_soc = np.full(n, np.nan)

    current_ev = 0
    dates = pd.date_range(index[0].date(), index[-1].date(), freq='D')

    for d in dates:
        dow = d.dayofweek
        if days == 'laboral' and dow >= 5:
            continue
        if rng.random() >= 0.90:
            continue

        actual_arr = int(np.clip(rng.normal(arr_h, 1.0), 0, 23))
        actual_dep = int(np.clip(rng.normal(dep_h, 0.5), actual_arr + 1, 23))
        actual_soc = float(rng.uniform(soc_min, soc_max))
        current_ev += 1

        day_slice = index[index.date == d.date()]
        for ts in day_slice:
            if actual_arr <= ts.hour <= actual_dep:
                pos = index.get_loc(ts)
                state[pos]   = 1
                ev_id[pos]   = current_ev
                dep_t[pos]   = actual_dep
                req_soc[pos] = soc_req
                arr_t[pos]   = actual_arr
                arr_soc[pos] = actual_soc

    return pd.DataFrame({
        'electric_vehicle_charger_state':          state,
        'electric_vehicle_id':                     ev_id,
        'electric_vehicle_departure_time':          dep_t,
        'electric_vehicle_required_soc_departure':  req_soc,
        'electric_vehicle_estimated_arrival_time':  arr_t,
        'electric_vehicle_estimated_soc_arrival':   arr_soc,
    }, index=index)
```
