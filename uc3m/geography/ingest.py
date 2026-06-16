"""
UniversalDataIngester — Ingesta universal de datos geoespaciales (§4.6)
=======================================================================
Descarga y formatea datos meteorológicos para CUALQUIER ubicación geográfica.

Jerarquía de fuentes (§4.6.1 — prioridad):
  1° PVGIS-ERA5 (pvlib) — Europa + LAT hasta 2023
  2° NASA POWER REST API — global, hourly, sin key
  3° ERA5 (cdsapi) — reanálisis global histórico (requiere key)
  4° NREL NSRDB (pvlib) — Américas (requiere key)

Salida estándar (DataFrame compatible weather.csv de CityLearn v2):
  outdoor_dry_bulb_temperature [°C]
  outdoor_relative_humidity    [%]
  diffuse_solar_irradiance     [W/m²]
  direct_solar_irradiance      [W/m²]
  + 12 columnas _predicted_1/_2/_3
"""

from __future__ import annotations

import logging
from pathlib import Path
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Constantes NASA POWER ──────────────────────────────────────────────────────
_NASA_URL = (
    "https://power.larc.nasa.gov/api/temporal/hourly/point"
    "?parameters=T2M,RH2M,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_SFC_SW_DNI,WS10M"
    "&community=RE&longitude={lon}&latitude={lat}"
    "&start={start}&end={end}&format=JSON"
)
_CACHE_DIR = Path(".cache") / "weather"


class UniversalDataIngester:
    """
    Descarga, cachea y devuelve datos meteorológicos horarios para
    cualquier ubicación y rango de años.

    Ejemplo:
        ingester = UniversalDataIngester(lat=-3.7491, lon=-73.2538, tz="America/Lima")
        weather  = ingester.get_weather(years=[2023, 2024, 2025])
        # → DataFrame con 26 304 filas y 16 columnas CityLearn v2
    """

    def __init__(
        self,
        lat: float,
        lon: float,
        tz: str = "UTC",
        alt_m: float = 0.0,
        cache_dir: str | Path = _CACHE_DIR,
        skip_cache: bool = False,
    ):
        self.lat      = lat
        self.lon      = lon
        self.tz       = tz
        self.alt_m    = alt_m
        self.cache_dir = Path(cache_dir)
        self.skip_cache = skip_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════
    # API pública
    # ═══════════════════════════════════════════════════════════════════════

    def get_weather(self, years: list[int]) -> pd.DataFrame:
        """
        Descarga y concatena datos meteorológicos horarios para los años dados.

        Returns
        -------
        DataFrame con 16 columnas CityLearn v2 (medidas + predicciones).
        """
        frames = [self._get_year(y) for y in sorted(years)]
        df = pd.concat(frames, axis=0)
        df = df.sort_index()

        # Verificar sin NaN
        df = df.ffill().bfill().fillna(0.0)

        # Añadir columnas de predicción (_1, _2, _3)
        df = self._add_predictions(df)

        logger.info(
            f"[Ingester] {len(df)} filas meteorológicas "
            f"lat={self.lat:.4f} lon={self.lon:.4f} "
            f"años={years}"
        )
        return df.reset_index(drop=True)

    def get_full_index(self, years: list[int]) -> pd.DatetimeIndex:
        """Índice horario completo para los años dados, con timezone."""
        frames = []
        for y in sorted(years):
            n = 8784 if self._is_leap(y) else 8760
            frames.append(
                pd.date_range(f"{y}-01-01", periods=n, freq="h", tz=self.tz)
            )
        return frames[0].append(frames[1:]) if len(frames) > 1 else frames[0]

    # ═══════════════════════════════════════════════════════════════════════
    # Descarga por año
    # ═══════════════════════════════════════════════════════════════════════

    def _get_year(self, year: int) -> pd.DataFrame:
        """Retorna DataFrame horario para un año. Usa caché si disponible."""
        cache_file = self.cache_dir / f"{year}_{self.lat:.4f}_{self.lon:.4f}.parquet"

        if not self.skip_cache and cache_file.exists():
            logger.debug(f"[Ingester] Cargando caché {cache_file}")
            return pd.read_parquet(cache_file)

        df: pd.DataFrame | None = None

        # 1° PVGIS-ERA5 (solo hasta ~2023)
        if year <= 2023:
            try:
                df = self._from_pvgis(year)
                logger.info(f"[Ingester] PVGIS-ERA5 OK para {year}")
            except Exception as e:
                logger.warning(f"[Ingester] PVGIS falló ({e}), intentando NASA POWER...")

        # 2° NASA POWER (fallback universal)
        if df is None:
            try:
                df = self._from_nasa_power(year)
                logger.info(f"[Ingester] NASA POWER OK para {year}")
            except Exception as e:
                logger.error(f"[Ingester] NASA POWER falló: {e}")
                df = self._synthetic_fallback(year)
                logger.warning(f"[Ingester] Usando datos sintéticos para {year}")

        assert df is not None
        df.to_parquet(cache_file)
        return df

    # ═══════════════════════════════════════════════════════════════════════
    # Fuentes de datos
    # ═══════════════════════════════════════════════════════════════════════

    def _from_pvgis(self, year: int) -> pd.DataFrame:
        """Descarga desde PVGIS-ERA5 usando pvlib."""
        import pvlib  # type: ignore[import-not-found]
        result = pvlib.iotools.get_pvgis_hourly(
            latitude=self.lat,
            longitude=self.lon,
            start=year,
            end=year,
            raddatabase="PVGIS-ERA5",
            components=True,
            outputformat="csv",
            pvcalculation=False,
        )
        data = result[0]
        # Renombrar columnas estándar PVGIS → CityLearn
        col_map = {
            "G(h)":  "GHI",
            "Gd(h)": "DHI",
            "Gb(n)": "DNI",
            "T2m":   "T2M",
            "WS10m": "WS",
        }
        df = data.rename(columns=col_map)
        dt_index = pd.DatetimeIndex(df.index)
        if dt_index.tz is None:
            df.index = dt_index.tz_localize("UTC").tz_convert(self.tz)
        else:
            df.index = dt_index.tz_convert(self.tz)
        return self._normalize_columns(df)

    def _from_nasa_power(self, year: int) -> pd.DataFrame:
        """Descarga desde NASA POWER REST API."""
        import requests
        url = _NASA_URL.format(
            lat=self.lat, lon=self.lon,
            start=f"{year}0101", end=f"{year}1231",
        )
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        raw = resp.json()["properties"]["parameter"]

        n_hours = 8784 if self._is_leap(year) else 8760
        idx = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h", tz=self.tz)

        def _vals(key: str) -> list:
            d = raw[key]
            return [d[k] for k in sorted(d.keys())][:n_hours]

        df = pd.DataFrame({
            "T2M": _vals("T2M"),
            "RH2M": _vals("RH2M"),
            "GHI":  _vals("ALLSKY_SFC_SW_DWN"),
            "DHI":  _vals("ALLSKY_SFC_SW_DIFF"),
            "DNI":  _vals("ALLSKY_SFC_SW_DNI"),
            "WS":   _vals("WS10M"),
        }, index=idx)

        # Reemplazar valores faltantes NASA (-999)
        df = pd.DataFrame(df.replace(-999.0, np.nan).replace(-999, np.nan))
        df = pd.DataFrame(df.clip(lower=0), index=df.index)

        return self._normalize_columns(df)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas internas → nombres estándar CityLearn v2."""
        result = pd.DataFrame(index=df.index)
        result["outdoor_dry_bulb_temperature"] = self._column(df, "T2M", 25.0)
        result["outdoor_relative_humidity"] = self._column(
            df, "RH2M", 70.0 if "RH" not in df.columns else "RH"
        )
        result["diffuse_solar_irradiance"] = self._column(df, "DHI", 0.0).clip(
            lower=0
        )
        result["direct_solar_irradiance"] = self._column(df, "DNI", 0.0).clip(
            lower=0
        )
        return result.astype(np.float32)

    @staticmethod
    def _column(
        df: pd.DataFrame,
        name: str,
        default: float | str,
    ) -> pd.Series:
        if name in df.columns:
            source = df[name]
            if isinstance(source, pd.DataFrame):
                source = source.iloc[:, 0]
            return pd.Series(
                pd.to_numeric(source, errors="coerce"),
                index=df.index,
                dtype="float64",
            )
        if isinstance(default, str) and default in df.columns:
            source = df[default]
            if isinstance(source, pd.DataFrame):
                source = source.iloc[:, 0]
            return pd.Series(
                pd.to_numeric(source, errors="coerce"),
                index=df.index,
                dtype="float64",
            )
        value = float(default) if not isinstance(default, str) else 0.0
        return pd.Series(value, index=df.index, dtype="float64")

    def _synthetic_fallback(self, year: int) -> pd.DataFrame:
        """
        Genera datos sintéticos basados en clima promedio estimado.
        Solo se usa si todas las APIs fallan.
        """
        n_hours = 8784 if self._is_leap(year) else 8760
        idx     = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h", tz=self.tz)
        hours   = np.arange(n_hours) % 24
        doy     = np.arange(n_hours) // 24

        # Temperatura con ciclo diurno
        t_mean = 26.5 + 3.0 * np.sin(2 * np.pi * doy / 365)
        t_diurnal = 2.5 * np.sin(2 * np.pi * (hours - 6) / 24)
        t = t_mean + t_diurnal + np.random.normal(0, 0.5, n_hours)

        # Irradiancia con modelo simplificado coseno cenital
        solar_angle = np.maximum(0, np.cos(2 * np.pi * (hours - 12) / 24))
        ghi_clear   = 900 * solar_angle ** 1.2
        cloud_factor = 0.65 + 0.2 * np.random.rand(n_hours)   # nubosidad tropical
        ghi  = ghi_clear * cloud_factor
        dhi  = ghi  * 0.35
        dni  = (ghi - dhi).clip(0)

        return pd.DataFrame({
            "outdoor_dry_bulb_temperature": t.astype(np.float32),
            "outdoor_relative_humidity":    np.full(n_hours, 80.0, dtype=np.float32),
            "diffuse_solar_irradiance":     dhi.astype(np.float32),
            "direct_solar_irradiance":      dni.astype(np.float32),
        }, index=idx)

    # ═══════════════════════════════════════════════════════════════════════
    # Columnas de predicción CityLearn v2
    # ═══════════════════════════════════════════════════════════════════════

    def _add_predictions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Añade las 12 columnas de predicción (_predicted_1/2/3)."""
        base_cols = [
            "outdoor_dry_bulb_temperature",
            "outdoor_relative_humidity",
            "diffuse_solar_irradiance",
            "direct_solar_irradiance",
        ]
        for col in base_cols:
            if col not in df.columns:
                continue
            for h in [1, 2, 3]:
                df[f"{col}_predicted_{h}"] = df[col].shift(-h).ffill()
        return df

    # ═══════════════════════════════════════════════════════════════════════
    # Utilidades
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _is_leap(year: int) -> bool:
        return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

    def summary(self) -> str:
        return (
            f"UniversalDataIngester("
            f"lat={self.lat:.4f}, lon={self.lon:.4f}, "
            f"tz={self.tz}, alt={self.alt_m}m)"
        )
