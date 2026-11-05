"""
UniversalDataIngester — Ingesta universal de datos geoespaciales (§4.6)
=======================================================================
Descarga y formatea datos meteorológicos para CUALQUIER ubicación geográfica.

Jerarquía de fuentes (§4.6.1 — prioridad):
  1° PVGIS-ERA5 (pvlib) — Europa + LAT hasta 2023
  2° NASA POWER REST API — global, hourly, sin key
Sin proveedor válido, falla; el modo de demostración sintética exige permiso y semilla.

Salida estándar (DataFrame compatible weather.csv de CityLearn v2):
  outdoor_dry_bulb_temperature [°C]
  outdoor_relative_humidity    [%]
  diffuse_solar_irradiance     [W/m²]
  direct_solar_irradiance      [W/m²]
  + 12 columnas _predicted_1/_2/_3
"""

from __future__ import annotations

import logging
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from uc3m.application.dataset.provenance import contained_path

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
        *,
        allow_synthetic: bool = False,
        synthetic_seed: int | None = None,
    ):
        if allow_synthetic and (isinstance(synthetic_seed, bool) or
                                not isinstance(synthetic_seed, int) or synthetic_seed < 0):
            raise ValueError('Synthetic weather requires an explicit nonnegative integer seed')
        self.lat      = lat
        self.lon      = lon
        self.tz       = tz
        self.alt_m    = alt_m
        self.cache_dir = contained_path(Path(cache_dir), '.')
        self.skip_cache = skip_cache
        self.allow_synthetic = allow_synthetic
        self.synthetic_seed = synthetic_seed
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════
    # API pública
    # ═══════════════════════════════════════════════════════════════════════

    def get_weather(self, years: list[int]) -> pd.DataFrame:
        """
        Descarga y concatena datos meteorológicos horarios para los años dados.

        Returns
        -------
        DataFrame con 16 columnas CityLearn v2: reanálisis o demostración explícita.
        ``attrs['weather_provenance']`` conserva la fuente, hash y elegibilidad.
        Las columnas predicted son desplazamientos históricos, no pronósticos validados.
        """
        frames = [self._get_year(y) for y in sorted(years)]
        provenance = [dict(frame.attrs['weather_provenance']) for frame in frames]
        df = pd.concat(frames, axis=0)
        df = df.sort_index()

        # Missing observations are an error, never an implicit imputed measurement.
        if not np.isfinite(df.to_numpy(dtype=float)).all():
            raise RuntimeError('Incomplete weather: missing values require an explicit imputation protocol')

        # Añadir columnas de predicción (_1, _2, _3)
        df = self._add_predictions(df)

        logger.info(
            f"[Ingester] {len(df)} filas meteorológicas "
            f"lat={self.lat:.4f} lon={self.lon:.4f} "
            f"años={years}"
        )
        df = df.reset_index(drop=True)
        df.attrs['weather_provenance'] = provenance
        df.attrs['scientific_eligible'] = all(p['scientific_eligible'] for p in provenance)
        df.attrs['prediction_method'] = 'historical_shift_not_validated_forecast'
        return df

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
        """Return proven reanalysis or explicitly seeded, ineligible synthetic weather.

        Cache data and provenance are immutable. Unproven legacy caches are
        preserved and rejected; use a fresh cache_dir to retrieve new evidence.
        """
        filename = f"{year}_{self.lat:.4f}_{self.lon:.4f}.parquet"
        cache_file = contained_path(self.cache_dir, filename)

        if not self.skip_cache and cache_file.exists():
            return self._read_cache(cache_file, year, synthetic=False)

        df: pd.DataFrame | None = None
        source = ''
        errors = []

        # 1° PVGIS-ERA5 (solo hasta ~2023)
        if year <= 2023:
            try:
                df = self._from_pvgis(year)
                self._validate_frame(df, year)
                source = 'PVGIS_ERA5'
                logger.info(f"[Ingester] PVGIS-ERA5 OK para {year}")
            except Exception as e:
                df = None
                errors.append(f'PVGIS_ERA5: {e}')
                logger.warning(f"[Ingester] PVGIS falló ({e}), intentando NASA POWER...")

        # 2° NASA POWER (fallback universal)
        if df is None:
            try:
                df = self._from_nasa_power(year)
                self._validate_frame(df, year)
                source = 'NASA_POWER'
                logger.info(f"[Ingester] NASA POWER OK para {year}")
            except Exception as e:
                df = None
                errors.append(f'NASA_POWER: {e}')
                logger.error(f"[Ingester] NASA POWER falló: {e}")
                if not self.allow_synthetic:
                    raise RuntimeError(f'No proven weather available for {year}: {"; ".join(errors)}') from e

        if df is None:
            cache_file = contained_path(self.cache_dir, f'synthetic/seed_{self.synthetic_seed}/{filename}')
            if not self.skip_cache and cache_file.exists():
                return self._read_cache(cache_file, year, synthetic=True)
            df = self._synthetic_fallback(year)
            source = 'synthetic'

        assert df is not None
        self._validate_frame(df, year)
        metadata = self._provenance(year, source)
        metadata['provider_errors'] = errors
        self._write_cache(cache_file, df, metadata)
        df.attrs['weather_provenance'] = metadata
        return df

    def _provenance(self, year: int, source: str) -> dict:
        synthetic = source == 'synthetic'
        return {'schema_version': 1, 'year': year, 'latitude': self.lat,
                'longitude': self.lon, 'timezone': self.tz, 'altitude_m': self.alt_m,
                'source': source, 'source_type': 'synthetic' if synthetic else 'weather_reanalysis',
                'measured': False, 'scientific_eligible': not synthetic,
                'eligibility_scope': 'weather_source_only_not_campaign_acceptance',
                'seed': self.synthetic_seed if synthetic else None}

    def _validate_frame(self, df: pd.DataFrame, year: int) -> None:
        required = ['outdoor_dry_bulb_temperature', 'outdoor_relative_humidity',
                    'diffuse_solar_irradiance', 'direct_solar_irradiance']
        n_hours = 8784 if self._is_leap(year) else 8760
        if (not isinstance(df, pd.DataFrame) or list(df.columns) != required or len(df) != n_hours
                or not np.isfinite(df.to_numpy(dtype=float)).all()):
            raise RuntimeError(f'Incomplete weather frame for {year}: missing columns, hours or values')
        if not isinstance(df.index, pd.DatetimeIndex) or df.index.has_duplicates:
            raise RuntimeError(f'Invalid weather time index for {year}')

    def _read_cache(self, path: Path, year: int, *, synthetic: bool) -> pd.DataFrame:
        proof = contained_path(self.cache_dir, str(path.relative_to(self.cache_dir)) + '.provenance.json')
        if not proof.is_file():
            raise RuntimeError(f'Untrusted legacy weather cache without provenance; preserved: {path}')
        try:
            metadata = json.loads(proof.read_text(encoding='utf-8'))
            source = metadata['source']
            if source not in (('synthetic',) if synthetic else ('PVGIS_ERA5', 'NASA_POWER')):
                raise ValueError('unapproved weather source')
            expected = self._provenance(year, source)
            if any(metadata.get(key) != value for key, value in expected.items()):
                raise ValueError('weather identity or eligibility mismatch')
            if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['sha256']:
                raise ValueError('weather content hash mismatch')
            df = pd.read_parquet(path)
            self._validate_frame(df, year)
        except Exception as exc:
            raise RuntimeError(f'Invalid weather provenance; cache preserved: {path}: {exc}') from exc
        df.attrs['weather_provenance'] = metadata
        return df

    def _write_cache(self, path: Path, df: pd.DataFrame, metadata: dict) -> None:
        proof = contained_path(self.cache_dir, str(path.relative_to(self.cache_dir)) + '.provenance.json')
        if path.exists() or proof.exists():
            raise RuntimeError(f'Weather cache is immutable; use a fresh cache_dir: {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents truncating legacy data. A crash leaves an
        # unproven file, which _read_cache rejects without deleting it.
        with path.open('xb') as stream:
            df.to_parquet(stream)
        metadata['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        with proof.open('x', encoding='utf-8') as stream:
            json.dump(metadata, stream, sort_keys=True, indent=2)

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
        nonnegative = ['RH2M', 'GHI', 'DHI', 'DNI', 'WS']
        df[nonnegative] = df[nonnegative].clip(lower=0)

        return self._normalize_columns(df)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas internas → nombres estándar CityLearn v2."""
        result = pd.DataFrame(index=df.index)
        result["outdoor_dry_bulb_temperature"] = self._column(df, "T2M", float('nan'))
        result["outdoor_relative_humidity"] = self._column(
            df, "RH2M", float('nan') if "RH" not in df.columns else "RH"
        )
        result["diffuse_solar_irradiance"] = self._column(df, "DHI", float('nan')).clip(
            lower=0
        )
        result["direct_solar_irradiance"] = self._column(df, "DNI", float('nan')).clip(
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
        Generate a deterministic demo fixture, never a measured climate source.
        Requires explicit permission and a seed; scientifically ineligible.
        """
        if not self.allow_synthetic or self.synthetic_seed is None:
            raise RuntimeError('Synthetic weather requires explicit opt-in and seed')
        rng = np.random.default_rng(np.random.SeedSequence([self.synthetic_seed, year]))
        n_hours = 8784 if self._is_leap(year) else 8760
        idx     = pd.date_range(f"{year}-01-01", periods=n_hours, freq="h", tz=self.tz)
        hours   = np.arange(n_hours) % 24
        doy     = np.arange(n_hours) // 24

        # Temperatura con ciclo diurno
        t_mean = 26.5 + 3.0 * np.sin(2 * np.pi * doy / 365)
        t_diurnal = 2.5 * np.sin(2 * np.pi * (hours - 6) / 24)
        t = t_mean + t_diurnal + rng.normal(0, 0.5, n_hours)

        # Irradiancia con modelo simplificado coseno cenital
        solar_angle = np.maximum(0, np.cos(2 * np.pi * (hours - 12) / 24))
        ghi_clear   = 900 * solar_angle ** 1.2
        cloud_factor = 0.65 + 0.2 * rng.random(n_hours)   # demo tropical, not observation
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
