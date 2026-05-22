"""
fix_solar_pvlib.py
==================
Regenera la columna solar_generation de los 17 Building_X.csv usando pvlib ModelChain SAPM.

Problema resuelto:
  - La caché de 2023.parquet estaba corrupta (GHI=0 en todos los registros)
  - El generador original usaba _calc_solar_simple (formula lineal) como fallback
    silencioso cuando pvlib no estaba instalado

Solución:
  - Re-descarga 2023 desde NASA POWER y valida los datos
  - Usa pvlib.modelchain.ModelChain con modelo SAPM (Sandia) para física completa:
    AOI losses + spectral correction + temperature derating
  - Actualiza SOLO la columna solar_generation en cada Building_X.csv
  - Preserva todas las demás columnas intactas

Dependencias:
  pip install pvlib requests pandas numpy pyarrow
"""

import math
import json
import logging
import time
import requests
from pathlib import Path

import numpy as np
import pandas as pd
import pvlib

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
CACHE_DIR   = BASE_DIR / ".cache" / "weather"
LOG_PATH    = DATASET_DIR / "solar_fix_log.json"

# ─── Configuración Iquitos ────────────────────────────────────────────────────
LAT, LON, ALT = -3.7491, -73.2538, 106
TZ = "America/Lima"
YEARS = [2023, 2024, 2025]
LOCATION = pvlib.location.Location(latitude=LAT, longitude=LON, tz=TZ, altitude=ALT)
TEMP_PARAMS = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]

# ─── Área techada por edificio (m²) ──────────────────────────────────────────
AREA_TECHADA = {
    1:  14000, 2:  8000,  3:  6000,  4:  2500,  5:  9000,
    6:  20637, 7:  8300,  8:  21000, 9:  3500,  10: 5000,
    11: 12000, 12: 6000,  13: 3000,  14: 5000,  15: 2500,
    16: 6500,  17: 5200,
}
MODULES_PER_STRING = 15  # Voc_string < 1000 V (IEC 61730): 15×64.60V=969V ≤ 1000V
AREA_UTIL_FACTOR   = 0.65  # 0.70 techo útil × 0.93 packing

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fix_solar")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DESCARGA DE DATOS METEOROLÓGICOS
# ═══════════════════════════════════════════════════════════════════════════════

def _download_pvgis(year: int) -> pd.DataFrame:
    """Descarga horario desde PVGIS-ERA5 via pvlib. Solo disponible hasta ~2023."""
    log.info(f"  Intentando PVGIS-ERA5 para {year}...")
    data, _, _ = pvlib.iotools.get_pvgis_hourly(
        latitude=LAT, longitude=LON,
        start=year, end=year,
        raddatabase="PVGIS-ERA5",
        components=True,
        outputformat="csv",
        pvcalculation=False,
        timeout=120,
    )
    df = data.rename(columns={
        "G(h)": "GHI", "Gd(h)": "DHI", "Gb(n)": "DNI",
        "T2m": "T2M", "WS10m": "WS",
    })
    df.index = df.index.tz_convert(TZ)
    # RH2M no lo provee PVGIS — poner NaN para rellenarlo luego
    if "RH2M" not in df.columns:
        df["RH2M"] = np.nan
    return df[["GHI", "DHI", "DNI", "T2M", "RH2M", "WS"]]


def _download_nasa_power(year: int) -> pd.DataFrame:
    """Descarga desde NASA POWER REST API (fallback confiable para cualquier año)."""
    log.info(f"  Descargando NASA POWER para {year}...")
    n_hours = 8784 if year == 2024 else 8760
    url = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        "?parameters=T2M,RH2M,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_SFC_SW_DNI,WS10M"
        f"&community=RE&longitude={LON}&latitude={LAT}"
        f"&start={year}0101&end={year}1231&format=JSON"
    )
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=180)
            resp.raise_for_status()
            raw = resp.json()["properties"]["parameter"]
            break
        except Exception as e:
            log.warning(f"  NASA POWER intento {attempt+1}/3 fallido: {e}")
            if attempt == 2:
                raise
            time.sleep(10)

    idx = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h", tz=TZ)
    df = pd.DataFrame({
        "GHI":  list(raw["ALLSKY_SFC_SW_DWN"].values()),
        "DHI":  list(raw["ALLSKY_SFC_SW_DIFF"].values()),
        "DNI":  list(raw["ALLSKY_SFC_SW_DNI"].values()),
        "T2M":  list(raw["T2M"].values()),
        "RH2M": list(raw["RH2M"].values()),
        "WS":   list(raw["WS10M"].values()),
    }, index=idx)
    return df


def _validate_weather(df: pd.DataFrame, year: int) -> bool:
    """Valida que los datos meteorológicos sean físicamente razonables."""
    n_expected = 8784 if year == 2024 else 8760
    if len(df) != n_expected:
        log.error(f"  Longitud incorrecta: {len(df)} != {n_expected}")
        return False
    ghi_nonzero = (df["GHI"] > 0).sum()
    if ghi_nonzero < n_expected * 0.25:  # al menos 25% de horas con sol
        log.error(f"  GHI casi todo cero ({ghi_nonzero} horas no-cero). Datos inválidos.")
        return False
    if df["T2M"].max() < 20 or df["T2M"].min() > 40:
        log.error(f"  T2M fuera de rango Iquitos: {df['T2M'].min():.1f}–{df['T2M'].max():.1f}")
        return False
    log.info(f"  Validación OK: {ghi_nonzero} h con GHI>0, T2M {df['T2M'].mean():.1f}°C promedio")
    return True


def get_weather(year: int) -> pd.DataFrame:
    """Carga año de datos. Caché en .cache/weather/{year}.parquet."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{year}.parquet"

    if cache_path.exists():
        df = pd.read_parquet(cache_path)
        if _validate_weather(df, year):
            log.info(f"  Usando caché: {cache_path}")
            return df
        else:
            log.warning(f"  Caché inválida para {year} — re-descargando...")
            cache_path.unlink()

    # Estrategia: PVGIS primero para 2023, NASA POWER para todos los años
    df = None
    if year <= 2023:
        try:
            df = _download_pvgis(year)
            if not _validate_weather(df, year):
                df = None
        except Exception as e:
            log.warning(f"  PVGIS falló ({e}) — usando NASA POWER")

    if df is None:
        df = _download_nasa_power(year)
        if not _validate_weather(df, year):
            raise RuntimeError(f"NASA POWER también falló para {year}")

    df.to_parquet(cache_path)
    log.info(f"  Caché guardada: {cache_path}")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SELECCIÓN DE MÓDULO E INVERSOR SANDIA
# ═══════════════════════════════════════════════════════════════════════════════

def select_sandia_module() -> tuple[str, dict]:
    """Selecciona el mejor módulo de SandiaMod para clima tropical Iquitos."""
    mods = pvlib.pvsystem.retrieve_sam("SandiaMod")
    if mods.shape[0] < mods.shape[1]:
        mods = mods.T  # pvlib 0.13: shape (params × modules) → transpose

    mods["Pmp_stc"]   = mods["Vmpo"] * mods["Impo"]
    mods["eta_stc"]   = mods["Pmp_stc"] / (mods["Area"] * 1000)
    mods["abs_Bvoco"] = mods["Bvoco"].abs()

    cands = mods[
        ~mods.index.str.contains("CPV", case=False, na=False) &
        (mods["eta_stc"] >= 0.15) &
        (mods["Area"].between(1.5, 2.6)) &
        (mods["Pmp_stc"] >= 250)
    ].sort_values(by=["eta_stc", "abs_Bvoco"], ascending=[False, True])

    if cands.empty:
        raise RuntimeError("No se encontraron módulos Sandia con los criterios dados")

    best_key = cands.index[0]
    params   = mods.loc[best_key].to_dict()
    pmp = params["Vmpo"] * params["Impo"]
    log.info(
        f"Módulo seleccionado: {best_key} | "
        f"Pmp={pmp:.0f}W Area={params['Area']:.3f}m² "
        f"η={pmp/(params['Area']*1000):.1%} |Bvoco|={abs(params['Bvoco']):.5f}"
    )
    return best_key, params


def select_sandia_inverter(pdc_kw: float) -> tuple[str, dict, int]:
    """
    Selecciona inversor Sandia y calcula n_inverters paralelos.

    Estrategia:
    1. Busca inversores con Pdco ∈ [pdc_kw × 0.5, pdc_kw × 1.5] (rango ±50%)
    2. Entre los candidatos, prioriza el de mayor Pdco (minimiza clipping)
    3. Si no hay candidatos, escala hacia abajo y usa n_inverters > 1

    Retorna (key, params_dict, n_inverters)
    """
    invs = pvlib.pvsystem.retrieve_sam("SandiaInverter")
    if invs.shape[0] < invs.shape[1]:
        invs = invs.T

    pdc_w = pdc_kw * 1000

    # Rango estrecho: inversor unitario que cubra sin clipping severo
    cands = invs[
        (invs["Pdco"] >= pdc_w * 0.5) &
        (invs["Pdco"] <= pdc_w * 1.5)
    ].copy()

    n_inverters = 1

    if cands.empty:
        # Fallback: usa el inversor de mayor Pdco disponible (≤ pdc_kw)
        # y determina cuántos en paralelo se necesitan
        smaller = invs[invs["Pdco"] <= pdc_w].copy()
        if smaller.empty:
            smaller = invs.copy()
        best_single = smaller.nlargest(1, "Pdco")
        cands = best_single
        unit_pdco = best_single["Pdco"].iloc[0]
        n_inverters = max(1, math.ceil(pdc_w / unit_pdco))
        log.warning(
            f"  Sin inversor único para {pdc_kw:.0f} kW → "
            f"{n_inverters}× inversor {unit_pdco/1000:.0f} kW en paralelo"
        )

    # Entre los candidatos: mayor Pdco primero (evita clipping), luego mayor eta
    cands["eta_inv"] = cands["Paco"] / cands["Pdco"]
    best_key = cands.sort_values(
        ["Pdco", "eta_inv"], ascending=[False, False]
    ).index[0]
    params = invs.loc[best_key].to_dict()

    eff = params["Paco"] / params["Pdco"]
    log.info(
        f"  Inversor: {best_key} | "
        f"Pdc0={params['Pdco']/1000:.1f} kW η={eff:.1%} × {n_inverters} unidades"
    )
    return best_key, params, n_inverters


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CÁLCULO SOLAR CON PVLIB MODELCHAIN SAPM
# ═══════════════════════════════════════════════════════════════════════════════

def calc_solar_pvlib(
    weather_full: pd.DataFrame,
    n_modules: int,
    modules_per_string: int,
    module_params: dict,
    inverter_params: dict,
    n_inverters: int,
    bldg_id: int,
) -> pd.Series:
    """
    Calcula generación AC horaria (kWh/h) con pvlib ModelChain SAPM.

    Física aplicada:
    - AOI losses: penalización por ángulo de incidencia (coseno + reflexión AR)
    - Spectral correction: AM y AOI para módulo c-Si
    - Temperature derating: celdas más calientes → menor Voc y Vmp
    - Inverter clipping: limita potencia a Paco cuando Pdc > Pdc0
    - n_inverters > 1: modela cada inversor con su fracción del array y escala linealmente
    """
    n_strings_total = max(1, math.ceil(n_modules / modules_per_string))
    # Strings asignados a cada inversor en paralelo
    n_strings_per_inv = max(1, math.ceil(n_strings_total / n_inverters))

    array = pvlib.pvsystem.Array(
        mount=pvlib.pvsystem.FixedMount(surface_tilt=5, surface_azimuth=0),
        module_parameters=module_params,
        temperature_model_parameters=TEMP_PARAMS,
        modules_per_string=modules_per_string,
        strings=n_strings_per_inv,
    )
    system = pvlib.pvsystem.PVSystem(arrays=[array], inverter_parameters=inverter_params)
    mc = pvlib.modelchain.ModelChain(
        system, LOCATION, aoi_model="sapm", spectral_model="sapm"
    )

    weather = weather_full.rename(columns={
        "GHI": "ghi", "DHI": "dhi", "DNI": "dni",
        "T2M": "temp_air", "WS": "wind_speed",
    })[["ghi", "dhi", "dni", "temp_air", "wind_speed"]]

    mc.run_model(weather)

    # Escalar por n_inverters (generación aditiva de inversores en paralelo)
    ac_unit = (mc.results.ac / 1000.0).clip(lower=0.0).fillna(0.0)
    ac = (ac_unit * n_inverters).rename("solar_generation")

    nonzero = int((ac > 0).sum())
    pmax    = ac.max()
    pmean   = ac[ac > 0].mean() if nonzero > 0 else 0.0
    log.info(
        f"  B{bldg_id}: {n_modules} módulos | {n_inverters} inv. | "
        f"{nonzero} h no-cero | max={pmax:.1f} kWh | mean_solar={pmean:.2f} kWh"
    )
    return ac


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ACTUALIZACIÓN DE BUILDING_X.CSV (SOLO solar_generation)
# ═══════════════════════════════════════════════════════════════════════════════

def update_building_solar(bldg_id: int, solar: pd.Series) -> dict:
    """
    Actualiza SOLO la columna solar_generation en Building_{bldg_id}.csv.
    Preserva todas las demás columnas intactas.

    Retorna dict con estadísticas del cambio.
    """
    csv_path = DATASET_DIR / f"Building_{bldg_id}.csv"
    if not csv_path.exists():
        log.error(f"  No encontrado: {csv_path}")
        return {"error": "file_not_found"}

    df = pd.read_csv(csv_path)
    n_rows = len(df)

    if n_rows != len(solar):
        raise ValueError(
            f"B{bldg_id}: CSV tiene {n_rows} filas pero solar tiene {len(solar)} valores"
        )

    old_max  = df["solar_generation"].max()
    old_sum  = df["solar_generation"].sum()
    old_nz   = int((df["solar_generation"] > 0).sum())

    df["solar_generation"] = solar.values

    new_max  = df["solar_generation"].max()
    new_sum  = df["solar_generation"].sum()
    new_nz   = int((df["solar_generation"] > 0).sum())

    df.to_csv(csv_path, index=False)
    log.info(f"  B{bldg_id} guardado: max {old_max:.1f}→{new_max:.1f} kWh | "
             f"non-zero {old_nz}→{new_nz} h | annual_gen {new_sum:.0f} kWh")

    return {
        "old_max_kwh":  round(old_max, 2),
        "new_max_kwh":  round(new_max, 2),
        "old_nz_hours": old_nz,
        "new_nz_hours": new_nz,
        "annual_gen_kwh": round(new_sum, 1),
        "method": "pvlib_SAPM",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def run(buildings=None):  # list[int] | None — compatible Python 3.9
    """
    Pipeline completo de corrección solar.

    1. Descarga/valida meteorología de los 3 años
    2. Selecciona módulo e inversor Sandia
    3. Por cada edificio: calcula solar con pvlib SAPM y actualiza CSV
    4. Guarda log JSON con detalles de cada edificio
    """
    if buildings is None:
        buildings = list(range(1, 18))

    log.info("=" * 70)
    log.info("fix_solar_pvlib.py — Corrección solar con pvlib ModelChain SAPM")
    log.info(f"Edificios: {buildings}")
    log.info("=" * 70)

    # ── Paso 1: datos meteorológicos ──────────────────────────────────────────
    log.info("\n[1/4] Cargando datos meteorológicos (3 años)...")
    weather_parts = []
    for yr in YEARS:
        log.info(f"  Año {yr}...")
        df_yr = get_weather(yr)
        weather_parts.append(df_yr)
    weather_full = pd.concat(weather_parts)
    log.info(f"  Total: {len(weather_full)} filas | "
             f"GHI max={weather_full['GHI'].max():.1f} W/m² | "
             f"GHI non-zero={(weather_full['GHI']>0).sum()} h")

    # ── Paso 2: selección de módulo e inversor ────────────────────────────────
    log.info("\n[2/4] Seleccionando módulo e inversor Sandia...")
    mod_key, mod_params = select_sandia_module()

    # ── Paso 3: generación solar por edificio ─────────────────────────────────
    log.info(f"\n[3/4] Calculando solar_generation para {len(buildings)} edificios...")
    results = {}

    for bldg_id in buildings:
        log.info(f"\n  --- Building_{bldg_id} ---")
        area_util = AREA_TECHADA[bldg_id] * AREA_UTIL_FACTOR
        n_mod     = max(1, int(area_util // mod_params["Area"]))
        pdc_kw    = n_mod * mod_params["Vmpo"] * mod_params["Impo"] / 1000

        _, inv_params, n_inv = select_sandia_inverter(pdc_kw)

        solar = calc_solar_pvlib(
            weather_full=weather_full,
            n_modules=n_mod,
            modules_per_string=MODULES_PER_STRING,
            module_params=mod_params,
            inverter_params=inv_params,
            n_inverters=n_inv,
            bldg_id=bldg_id,
        )

        stats = update_building_solar(bldg_id, solar)
        results[f"Building_{bldg_id}"] = {
            "module":       mod_key,
            "n_modules":    n_mod,
            "n_inverters":  n_inv,
            "pdc_kw":       round(pdc_kw, 1),
            "area_util_m2": round(area_util, 0),
            **stats,
        }

    # ── Paso 4: log JSON ──────────────────────────────────────────────────────
    log.info("\n[4/4] Guardando log de corrección solar...")
    log_data = {
        "fix_date":       pd.Timestamp.now().isoformat(),
        "pvlib_version":  pvlib.__version__,
        "method":         "pvlib_ModelChain_SAPM",
        "module_key":     mod_key,
        "weather_source": "PVGIS-ERA5 (2023 si disponible) + NASA POWER",
        "total_hours":    len(weather_full),
        "buildings":      results,
    }
    LOG_PATH.write_text(json.dumps(log_data, indent=2, ensure_ascii=False))
    log.info(f"  Log guardado: {LOG_PATH}")

    log.info("\n" + "=" * 70)
    log.info(f"Corrección completa: {len(buildings)} edificios actualizados con pvlib SAPM")
    log.info("=" * 70)

    # Resumen final
    total_annual = sum(v.get("annual_gen_kwh", 0) for v in results.values())
    log.info(f"Generación anual total del distrito: {total_annual:,.0f} kWh/año")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Corrige solar_generation con pvlib SAPM")
    parser.add_argument(
        "--buildings", nargs="+", type=int, default=None,
        help="IDs de edificios a procesar (default: 1-17)"
    )
    parser.add_argument(
        "--skip-cache", action="store_true",
        help="Forzar re-descarga de datos meteorológicos"
    )
    args = parser.parse_args()

    if args.skip_cache:
        for yr in YEARS:
            p = CACHE_DIR / f"{yr}.parquet"
            if p.exists():
                p.unlink()
                log.info(f"Caché eliminada: {p}")

    run(buildings=args.buildings)
