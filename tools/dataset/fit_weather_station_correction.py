"""Fit configs/dataset/weather_station_correction.yaml from the open NOAA record of the Iquitos airport (D-V6-59).

    python tools/dataset/fit_weather_station_correction.py --station-dir DIR --reanalysis data/.../weather.csv

--station-dir holds the yearly files of station 84377099999 (Coronel FAP Francisco Secada Vignetta):
https://noaa-global-hourly-pds.s3.amazonaws.com/<year>/84377099999.csv. --reanalysis is a weather.csv written WITHOUT
the correction. The fit uses 2023, the training year, and the later years only score it.
"""
import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from uc3m.application.dataset.weather_correction import TABLE, correct_weather, fit_month_hour_deltas  # noqa: E402

GOOD_QUALITY = ['1', '5', '9', 'A', 'C', 'I', 'M', 'P', 'R', 'U']
STATION = '84377099999'
UTC_OFFSET_H = 5


def station_hourly(folder: Path) -> pd.Series:
    frames = [pd.read_csv(path, usecols=['DATE', 'TMP'], low_memory=False) for path in sorted(Path(folder).glob(f'{STATION}_*.csv'))]
    frame = pd.concat(frames)
    parts = frame['TMP'].astype(str).str.split(',', expand=True)
    value = pd.to_numeric(parts[0], errors='coerce')/10
    frame['t'] = value.where((value < 99) & parts[1].isin(GOOD_QUALITY))
    frame['local'] = pd.to_datetime(frame['DATE']) - pd.Timedelta(hours=UTC_OFFSET_H)
    return frame.dropna(subset=['t']).set_index('local')['t'].resample('H').mean()


def scores(observed: pd.Series, series: pd.Series) -> dict:
    both = pd.DataFrame({'o': observed, 's': series}).dropna()
    day = both.resample('D').max().dropna()
    return {'hours': int(len(both)), 'bias_c': round(float((both.s - both.o).mean()), 3),
            'rmse_c': round(float(np.sqrt(((both.s - both.o)**2).mean())), 3),
            'mean_daily_max_c': round(float(day.s.mean()), 2), 'station_mean_daily_max_c': round(float(day.o.mean()), 2)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--station-dir', type=Path, required=True)
    parser.add_argument('--reanalysis', type=Path, required=True)
    args = parser.parse_args(argv)
    observed = station_hourly(args.station_dir)
    weather = pd.read_csv(args.reanalysis)
    index = pd.date_range('2023-01-01', periods=len(weather), freq='H')
    frame = pd.DataFrame({'T2M': weather['outdoor_dry_bulb_temperature'].to_numpy(float),
                          'RH2M': weather['outdoor_relative_humidity'].to_numpy(float)}, index=index)
    train = index.year == 2023
    deltas = fit_month_hour_deltas(observed.reindex(index[train]), frame['T2M'][train])
    corrected = correct_weather(frame, deltas)['T2M']
    payload = {
        'schema_version': 1, 'origin': 'measured',
        'source': f'NOAA Global Hourly, station {STATION} (Coronel FAP Francisco Secada Vignetta, Iquitos), TMP with good quality flags',
        'source_uri': f'https://noaa-global-hourly-pds.s3.amazonaws.com/<year>/{STATION}.csv',
        'source_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted(args.station_dir.glob(f'{STATION}_*.csv'))},
        'fitted_on': 'calendar 2023, local time UTC-5', 'method': 'mean of station minus NASA POWER per month and hour; dew point kept',
        'out_of_sample': {str(year): {'reanalysis': scores(observed, frame['T2M'][index.year == year]),
                                      'corrected': scores(observed, corrected[index.year == year])} for year in (2024, 2025)},
        'deltas_c_month_hour': deltas}
    TABLE.write_text(yaml.safe_dump(payload, sort_keys=False, width=200), encoding='utf-8')
    print(yaml.safe_dump(payload['out_of_sample'], sort_keys=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
