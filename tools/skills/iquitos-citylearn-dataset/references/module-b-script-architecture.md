# Module B — Script Architecture (generate_iquitos_dataset.py)

Arquitectura completa del script generador de dataset. Un solo archivo Python con
10 secciones bien delimitadas, 8 clases con responsabilidades unicas, y un pipeline
de 10 etapas orquestado por IquitosDatasetPipeline.

---

## Dependencias

```
pip install pvlib requests pandas numpy scipy tqdm pathlib pyarrow
```

| Paquete | Version min | Uso |
|---------|------------|-----|
| pvlib | 0.10+ | ModelChain SAPM, SandiaMod, SandiaInverter, PVGIS |
| requests | 2.28+ | NASA POWER REST API |
| pandas | 2.0+ | DataFrames, DatetimeIndex |
| numpy | 1.24+ | Arrays, RNG determinista |
| scipy | 1.10+ | Interpolacion perfiles |
| tqdm | 4.65+ | Barras de progreso |
| pyarrow | 12+ | Parquet cache meteorologico |
| pathlib | stdlib | Rutas cross-platform |
| argparse | stdlib | CLI |
| json | stdlib | schema.json y metadata |
| logging | stdlib | Logging estructurado |

---

## Estructura de Modulos (un solo archivo)

```
tools/generate_iquitos_dataset.py
|
+-- SECCION 1  -- Constantes y configuracion
|   (MADRL_BUILDING_CONSTANTS, LOAD_PROFILES, DAY_FACTOR,
|    SETPOINTS, TAU, COP_BY_TYPE, DHW_KWH_THERMAL_DAY,
|    REFRIGERACION_COMERCIAL, EV_CONFIG, etc.)
|
+-- SECCION 2  -- class WeatherDataManager
|   (descarga, cachea y valida PVGIS-ERA5 + NASA POWER)
|
+-- SECCION 3  -- class SandiaModelSelector
|   (selecciona modulo e inversor optimos de base Sandia)
|
+-- SECCION 4  -- class BuildingDataGenerator
|   (genera las 12 columnas del Building_X.csv para UN edificio)
|
+-- SECCION 5  -- class SupportFilesGenerator
|   (weather.csv, carbon_intensity.csv, pricing.csv,
|    charger_X_Y.csv, Washing_Machine_1.csv)
|
+-- SECCION 6  -- class BESSDesigner
|   (sizing BESS por balance energetico -- Hesse et al. 2017)
|
+-- SECCION 7  -- class SchemaBuilder
|   (construye schema.json con todos los parametros CityLearn)
|
+-- SECCION 8  -- class DatasetValidator
|   (valida cada CSV con reglas fisicas + CityLearnEnv)
|
+-- SECCION 9  -- class IquitosDatasetPipeline
|   (orquestador principal: 10 etapas, tqdm, logging)
|
+-- SECCION 10 -- main()
    (CLI con argparse)
```

---

## Clase WeatherDataManager

```python
class WeatherDataManager:
    CACHE_DIR = Path(".cache/weather")
    LAT, LON, TZ, ALT = -3.7491, -73.2538, "America/Lima", 106

    def get(self, year: int) -> pd.DataFrame:
        """Retorna DataFrame [GHI, DHI, DNI, T2M, RH2M, WS] para el anio.
        Orden de intentos:
          1. Cache .cache/weather/{year}.parquet
          2. PVGIS-ERA5 via pvlib.iotools.get_pvgis_hourly (primario 2023)
          3. NASA POWER REST API (fallback + 2024-2025)
        Lanza WeatherFetchError si los 3 fallan."""

    def _from_pvgis(self, year) -> pd.DataFrame:
        """pvlib.iotools.get_pvgis_hourly raddatabase='PVGIS-ERA5', components=True"""

    def _from_nasa_power(self, year) -> pd.DataFrame:
        """REST API: T2M, RH2M, ALLSKY_SFC_SW_DWN, ALLSKY_SFC_SW_DIFF,
        ALLSKY_SFC_SW_DNI, WS10M. Endpoint documentado en module-c."""

    def get_full_index(self) -> pd.DatetimeIndex:
        """Indice horario 2023-01-01 00:00 -> 2025-12-31 23:00, tz=America/Lima.
        26 304 filas (2024 bisiesto = 8 784 h)."""

    def validate(self, df: pd.DataFrame, year: int):
        """Verifica n_filas exactas, sin NaN, GHI >= 0, T2M in [18,40], RH2M in [40,100]."""
```

**Estrategia por anio**:
- 2023: PVGIS-ERA5 (primario) -> si falla: NASA POWER
- 2024: NASA POWER directo (PVGIS no cubre anios recientes)
- 2025: NASA POWER directo

**Cache en disco**: `.cache/weather/{year}.parquet` (pyarrow). Evita re-descargas.

---

## Clase SandiaModelSelector

```python
class SandiaModelSelector:

    def select_module(self) -> tuple[str, dict]:
        """Filtra SandiaMod: eta >= 18%, Area in [1.7, 2.6] m2, Pmp >= 300 W.
        Ordena: mayor eta primero, luego menor |BVoco|.
        Cachea en atributo de instancia. Llama UNA sola vez para todos los edificios."""

    def select_inverter(self, pdc_kw: float) -> tuple[str, dict]:
        """Filtra SandiaInverter: Pdc0 in [pdc_kw*0.8, pdc_kw*1.3].
        Selecciona mayor eta_inv = Paco/Pdc0.
        Si no hay coincidencia: toma los 3 mas cercanos."""

    def n_modules_for_building(self, bldg_id: int) -> int:
        """n_modulos = floor(area_techada_m2 * 0.63 / module['Area'])"""

    def pdc_kw(self, n_mod: int) -> float:
        """Potencia DC array = n_mod * Vmpo * Impo / 1000 [kW]"""
```

**Parametros Sandia para Iquitos**:
- Tilt = 5 deg (optimo lat -3.75, casi horizontal)
- Azimuth = 0 deg (norte, hemisferio sur ecuatorial)
- Temp model: open_rack_glass_glass (SAPM, clima tropical humedo)
- Modules/string <= 20 (Voc_string <= 1 000 V, IEC 61730)
- Factor area util: 0.63 (0.70 area util x 0.90 packing)

---

## Clase BuildingDataGenerator

```python
class BuildingDataGenerator:

    def __init__(self, bldg_id: int, weather_df: pd.DataFrame,
                 solar_series: pd.Series, rng_seed: int = None):
        self.cfg   = MADRL_BUILDING_CONSTANTS[bldg_id]
        self.btype = self.cfg['bldg_type']
        self.index = weather_df.index
        self.rng   = np.random.default_rng(rng_seed or bldg_id)

    # Columnas de contexto temporal
    def month(self)               -> pd.Series  # index.month
    def hour(self)                -> pd.Series  # index.hour
    def day_type(self)            -> pd.Series  # dayofweek + 1
    def daylight_savings(self)    -> pd.Series  # constante 0 (Peru tropical)

    # Columnas de estado termico interior (NUEVAS -- no vacias como en demo)
    def cooling_frac(self)        -> pd.Series  # 0-1 fraccion AC por hora y dia
    def indoor_dry_bulb_temperature(self) -> pd.Series  # modelo RC primer orden
    def indoor_relative_humidity(self)    -> pd.Series  # RH_out*(1-0.35*frac)
    def average_unmet_cooling_setpoint_difference(self) -> pd.Series  # max(0,T-Tset)*occ

    # Columnas de carga energetica
    def non_shiftable_load(self) -> pd.Series  # base+equip(perfil)+refrig kWh_elec
    def dhw_demand(self)         -> pd.Series  # kWh_thermal (solo B5,B11,B12)
    def cooling_demand(self)     -> pd.Series  # P_AC*COP*perfil kWh_thermal
    def heating_demand(self)     -> pd.Series  # constante 0.0
    def solar_generation(self)   -> pd.Series  # ya calculada externamente

    def build(self) -> pd.DataFrame:
        """Ensambla 12 columnas en orden CityLearn v2. Llama DatasetValidator.validate_building_csv()."""
```

---

## Clase SupportFilesGenerator

```python
class SupportFilesGenerator:

    def build_weather_csv(self, weather_dfs: dict) -> pd.DataFrame:
        """Concatena 2023+2024+2025. Genera 16 columnas:
        4 observadas + 12 predicciones (_1,_2,_3) por shift(-N).ffill()."""

    def build_carbon_intensity(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """0.79 * (1 - 0.15 * GHI/1000). Rango 0.672-0.790 kg CO2/kWh.
        Guarda carbon_intensity_metadata.json con fuentes MINAM/RAGEI."""

    def build_pricing(self, index: pd.DatetimeIndex) -> pd.DataFrame:
        """Intenta descarga OSINERGMIN MT mes a mes.
        Fallback: punta=0.38, fuera=0.26 USD/kWh.
        Genera 4 columnas: pricing + 3 predicciones."""

    def build_charger_csv(self, bldg_id: int, charger_idx: int,
                          index: pd.DatetimeIndex) -> pd.DataFrame:
        """Sesiones EV estocasticas: 90% prob. dias activos, Gaussian +/-1h.
        seed = bldg_id*100 + charger_idx. 6 columnas."""

    def build_washing_machine(self, index: pd.DatetimeIndex) -> pd.DataFrame:
        """Solo Building_1 (ELOR). 5 columnas. Ciclo 2.5 kWh, 06:00-08:00 o 12:00-14:00."""
```

---

## Clase BESSDesigner

```python
class BESSDesigner:
    """Sizing BESS por balance energetico acumulado.
    Referencia: Hesse et al. 2017, DOI:10.3390/en10122107"""
    DOD      = 0.80
    ETA_C    = 0.95
    ETA_D    = 0.95
    ETA_RT   = 0.9025
    LOSS     = 1e-5
    SOC_INI  = 0.50
    TARGET_SS = 0.70

    def size(self, load_kwh: pd.Series, solar_kwh: pd.Series) -> dict:
        """
        1. p_net = load - solar
        2. surplus = (-p_net).clip(0);  deficit = p_net.clip(0)
        3. soc_curve = cumsum(surplus*ETA_C - deficit/ETA_D)
        4. E_raw = soc_curve.max() - soc_curve.min()
        5. E_bess = (E_raw / DOD) * TARGET_SS
        6. P_bess = max(deficit.quantile(0.99), surplus.quantile(0.99))
        Retorna dict: capacity[kWh], nominal_power[kW],
        depth_of_discharge, efficiency, loss_coefficient, initial_charge."""
```

---

## Clase SchemaBuilder

```python
class SchemaBuilder:

    def build(self, bess_params: dict, solar_kw: dict,
              charger_map: dict, cop_map: dict) -> dict:
        """
        Genera dict completo para json.dump(). Por cada edificio:
        - energy_simulation: "Building_X.csv"
        - weather, carbon_intensity, pricing: archivos compartidos
        - cooling_device: type=AirConditioner, efficiency=COP, nominal_power=COOLING_PEAK_kW
        - dhw_device: solo B5 (hotel), B11, B12 (hospitales)
        - electrical_storage: parametros de BESSDesigner.size()
        - pv_system: nominal_power=kWp DC, efficiency=1.0
        - electric_vehicle_chargers: lista charger_X_Y.csv con nominal_power
        - inactive_observations: []  -- NUNCA desactivar (MADRL usa todas)
        - inactive_actions: []       -- HAPPO/MASAC/MATD3/MAAC usan todas las acciones
        """
```

---

## Clase DatasetValidator

```python
class DatasetValidator:

    RULES = {
        'month':                       lambda s: s.between(1, 12).all(),
        'hour':                        lambda s: s.between(0, 23).all(),
        'day_type':                    lambda s: s.between(1, 7).all(),
        'daylight_savings_status':     lambda s: (s == 0).all(),
        'indoor_dry_bulb_temperature': lambda s: s.between(15, 45).all(),
        'average_unmet_cooling_setpoint_difference': lambda s: (s >= 0).all(),
        'indoor_relative_humidity':    lambda s: s.between(20, 100).all(),
        'non_shiftable_load':          lambda s: (s >= 0).all(),
        'dhw_demand':                  lambda s: (s >= 0).all(),
        'cooling_demand':              lambda s: (s >= 0).all(),
        'heating_demand':              lambda s: (s == 0).all(),
        'solar_generation':            lambda s: (s >= 0).all(),
    }

    def validate_building_csv(self, df, bldg_id):
        """Aplica RULES, verifica n_filas=26304, sin NaN.
        Verifica coherencia energetica: sum(cooling_demand) razonable dado COP y area."""

    def validate_weather_csv(self, df):
        """16 columnas, 26304 filas, GHI>=0, T in [18,40], RH in [40,100]."""

    def validate_charger_csv(self, df, bldg_id, charger_idx):
        """6 columnas, state in {0,1}, SOC in [0,1], departure > arrival."""

    def validate_with_citylearn(self, schema_path: Path):
        """from citylearn.citylearn import CityLearnEnv
        env = CityLearnEnv(schema=str(schema_path))
        obs, _ = env.reset()
        assert obs is not None"""
```

---

## Clase IquitosDatasetPipeline (Orquestador)

```python
class IquitosDatasetPipeline:
    OUTPUT_DIR = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
    YEARS      = [2023, 2024, 2025]
    N_HOURS    = 26_304

    def run(self):
        """10 etapas con tqdm y logging:

        Etapa 1  -- Descarga meteorologica (WeatherDataManager)
                    weather_dict[2023], weather_dict[2024], weather_dict[2025]

        Etapa 2  -- Seleccion modulo Sandia (SandiaModelSelector.select_module)
                    -> module_key, module_params (una vez para todos)

        Etapa 3  -- Generacion solar FV por edificio [tqdm 17 iter]
                    pvlib.ModelChain.run_model(weather_full).results.ac
                    -> solar_dict[bldg_id] = pd.Series kWh/h AC

        Etapa 4  -- Sizing BESS por edificio [tqdm 17 iter]
                    BESSDesigner().size(load_proxy, solar[bldg_id])
                    -> bess_dict[bldg_id]

        Etapa 5  -- Generacion Building_X.csv [tqdm 17 iter]
                    BuildingDataGenerator(bldg_id).build()
                    DatasetValidator.validate_building_csv()
                    -> Building_{bldg_id}.csv

        Etapa 6  -- Generacion charger_X_Y.csv base
                    SupportFilesGenerator.build_charger_csv()
                    -> charger_{bldg_id}_{i}.csv
                    Luego la orquestacion ejecuta dimension_ev_chargers.py
                    para producir los 185 charger vigentes.

        Etapa 7  -- Washing_Machine_X.csv por edificio

        Etapa 8  -- Archivos meteorologicos y de red
                    weather.csv (16 cols)
                    carbon_intensity.csv (0.672-0.790 kg CO2/kWh)
                    pricing.csv (OSINERGMIN MT + fallback)

        Etapa 9  -- schema.json (17 edificios + BESS + PV + EV chargers)

        Etapa 10 -- Validacion final con CityLearnEnv
                    DatasetValidator.validate_with_citylearn(schema_path)
                    -> imprime resumen del dataset sincronizado"""
```

---

## main() -- CLI argparse

```bash
python tools/generate_iquitos_dataset.py [opciones]

Opciones:
  --output-dir DIR      Directorio de salida (default: CityLearn/data/datasets/citylearn_iquitos_2023_2025)
  --years N [N ...]     Anios a generar (default: 2023 2024 2025)
  --buildings N [N ...] IDs de edificios a procesar (default: 1-17)
  --skip-cache          Forzar re-descarga de datos meteorologicos
  --no-validate         Omitir validacion con CityLearnEnv
```

---

## Archivos de Salida Vigentes

```
CityLearn/data/datasets/citylearn_iquitos_2023_2025/
+-- Building_1.csv  ... Building_17.csv          (17 archivos, 12 cols, 26 304 filas)
+-- weather.csv                                   (16 cols, 26 304 filas)
+-- carbon_intensity.csv                          (1 col, 26 304 filas)
+-- pricing.csv                                   (4 cols, 26 304 filas)
+-- charger_*.csv                                  (185 archivos, 6 cols, 26 304 filas)
+-- Washing_Machine_*.csv                          (17 archivos, 5 cols, 26 304 filas)
+-- schema.json                                    (17 edificios + BESS + PV + EV)
+-- carbon_intensity_metadata.json                 (trazabilidad MINAM/RAGEI)
---
  222 CSV auditados sin NaN/Inf
```

---

## Diagrama de Flujo

```
python tools/generate_iquitos_dataset.py
  |
  +-> [Etapa 1] WeatherDataManager
  |     +- Cache? -> .cache/weather/{year}.parquet
  |     +- 2023: PVGIS-ERA5 -> si falla: NASA POWER
  |     +- 2024: NASA POWER directo
  |     +- 2025: NASA POWER directo
  |
  +-> [Etapa 2] SandiaModelSelector
  |     +- SandiaMod: eta>=18%, Area in [1.7,2.6], Pmp>=300W
  |     -> module_key, module_params (una sola llamada)
  |
  +-> [Etapa 3] Solar FV x 17 [tqdm 17/17]
  |     +- pvlib ModelChain SAPM -> solar_dict[bldg_id]
  |
  +-> [Etapa 4] BESS sizing x 17 [tqdm 17/17]
  |     +- BESSDesigner.size() -> bess_dict[bldg_id]
  |
  +-> [Etapa 5] Building_X.csv x 17 [tqdm 17/17]
  |     +- BuildingDataGenerator.build() -> 12 columnas reales
  |     +- DatasetValidator.validate_building_csv() -- falla = STOP
  |     -> Building_{N}.csv
  |
  +-> [Etapa 6] charger_X_Y.csv base
  +-> [Sync EV] dimension_ev_chargers.py -> 185 charger_X_Y.csv
  |
  +-> [Etapa 7] Washing_Machine_X.csv x 17
  |
  +-> [Etapa 8] weather + carbon_intensity + pricing
  |
  +-> [Etapa 9] schema.json
  |
  +-> [Etapa 10] Validacion CityLearnEnv
        -> dataset sincronizado y validado sin NaN/Inf
```

---

## Perfiles Horarios LOAD_PROFILES (24 valores, factor 0-1)

```python
LOAD_PROFILES = {
    'industrial':      [0.20,0.18,0.18,0.18,0.18,0.20,0.35,0.65,0.90,0.95,0.95,0.92,
                        0.85,0.90,0.95,0.90,0.80,0.60,0.35,0.25,0.22,0.20,0.20,0.20],
    'mall':            [0.08,0.06,0.06,0.06,0.06,0.08,0.10,0.15,0.25,0.40,0.70,0.85,
                        0.90,0.88,0.85,0.88,0.90,0.92,0.95,0.88,0.75,0.50,0.20,0.10],
    'salud_24h':       [0.70,0.68,0.67,0.67,0.68,0.70,0.75,0.82,0.90,0.95,0.98,0.98,
                        0.95,0.95,0.95,0.92,0.90,0.88,0.85,0.80,0.78,0.75,0.72,0.70],
    'universitario':   [0.10,0.08,0.08,0.08,0.08,0.10,0.20,0.55,0.85,0.90,0.90,0.88,
                        0.80,0.88,0.90,0.85,0.75,0.60,0.40,0.25,0.15,0.12,0.10,0.10],
    'deportivo':       [0.10,0.08,0.08,0.08,0.08,0.10,0.15,0.20,0.25,0.30,0.35,0.35,
                        0.35,0.35,0.40,0.50,0.75,0.90,0.95,0.90,0.75,0.50,0.25,0.12],
    'educacion':       [0.05,0.05,0.05,0.05,0.05,0.08,0.15,0.55,0.88,0.92,0.90,0.90,
                        0.80,0.88,0.90,0.80,0.55,0.20,0.10,0.08,0.07,0.06,0.05,0.05],
    'transporte_24h':  [0.55,0.50,0.48,0.48,0.50,0.65,0.85,0.95,0.92,0.88,0.85,0.82,
                        0.80,0.80,0.80,0.82,0.85,0.88,0.90,0.85,0.78,0.70,0.65,0.58],
    'portuario_24h':   [0.50,0.48,0.45,0.45,0.48,0.65,0.88,0.95,0.92,0.85,0.80,0.78,
                        0.75,0.78,0.85,0.88,0.82,0.75,0.68,0.62,0.58,0.55,0.52,0.50],
    'hotelero_24h':    [0.58,0.55,0.52,0.50,0.52,0.60,0.70,0.82,0.88,0.85,0.82,0.80,
                        0.80,0.82,0.85,0.88,0.92,0.95,0.98,0.95,0.88,0.80,0.72,0.65],
    'administrativo':  [0.08,0.07,0.07,0.07,0.07,0.08,0.12,0.35,0.78,0.88,0.90,0.88,
                        0.80,0.88,0.90,0.85,0.70,0.40,0.18,0.12,0.10,0.09,0.08,0.08],
}

# Multiplicadores dia de semana por tipo
DAY_FACTOR_MAP = {
    # tipo: {laboral(1-5): mult, sabado(6): mult, domingo(7): mult}
    'industrial':     (1.0, 0.40, 0.20),
    'mall':           (1.0, 1.05, 1.03),
    'salud_24h':      (1.0, 0.95, 0.90),
    'universitario':  (1.0, 0.15, 0.05),
    'deportivo':      (0.7, 1.50, 1.30),
    'educacion':      (1.0, 0.05, 0.02),
    'transporte_24h': (1.0, 1.10, 1.05),
    'portuario_24h':  (1.0, 0.70, 0.50),
    'hotelero_24h':   (1.0, 1.15, 1.20),
    'administrativo': (1.0, 0.10, 0.05),
}
```

---

## Configuracion de Cargadores EV (EV_CONFIG)

```python
EV_CONFIG = {
    # bldg_id: [(arrival_h, depart_h, soc_arr_min, soc_arr_max, soc_req, bat_kwh, kw, days)]
    1:  [(7,  17, 0.20, 0.40, 0.85,  40, 7.4,  'laboral')] * 2,
    2:  [(15, 22, 0.25, 0.45, 0.80,  40, 7.4,  'todos')] * 4,
    3:  [(5,  21, 0.30, 0.50, 0.85,  60, 22.0, 'todos')] * 4,
    4:  [(10, 20, 0.20, 0.40, 0.75,  40, 7.4,  'todos')] * 3,
    5:  [(8,  12, 0.30, 0.50, 0.85,  40, 11.0, 'todos')] * 3,
    6:  [(10, 21, 0.20, 0.35, 0.85,  60, 22.0, 'todos')] * 8,
    7:  [(8,  17, 0.25, 0.40, 0.80,  40, 7.4,  'laboral')] * 3,
    8:  [(7,  16, 0.20, 0.40, 0.90,  40, 7.4,  'laboral')] * 2,
    9:  [(7,  16, 0.25, 0.45, 0.80,  15, 3.3,  'laboral')] * 2,
    10: [(8,  17, 0.20, 0.40, 0.85,  40, 7.4,  'laboral')] * 3,
    11: [(7,  19, 0.20, 0.40, 0.80,  60, 11.0, 'todos')] * 4,
    12: [(8,  17, 0.25, 0.45, 0.80,  40, 7.4,  'laboral')] * 3,
    13: [(8,  17, 0.20, 0.40, 0.85,  40, 7.4,  'laboral')] * 2,
    14: [(6,  18, 0.20, 0.35, 0.85,  60, 11.0, 'todos')] * 2,
    15: [(7,  15, 0.20, 0.40, 0.80,  15, 3.3,  'laboral')] * 2,
    16: [(7,  15, 0.20, 0.40, 0.80,  15, 3.3,  'laboral')] * 1,
    17: [(7,  16, 0.20, 0.40, 0.80,  15, 7.4,  'laboral')] * 2,
}
```
