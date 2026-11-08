"""Download the raw data of the CU-BEMS 5R1C validation into data/validation/cubems/raw/ (gitignored).

The 14 CSV of figshare 10.6084/m9.figshare.11726517, version 6, each checked against the MD5 published by the figshare
API (``computed_md5``), and the NASA POWER hourly weather at the site. Downloads are data: nothing here executes them.
Usage: python tools/validation/fetch_cubems_raw.py [--delete]   (--delete removes the raw folder afterwards).
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'data/validation/cubems/raw'
NASA_NAME = 'nasa_power_bangkok_2018_2019_utc.json'
NASA_URL = ('https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,ALLSKY_SFC_SW_DWN'
            '&community=RE&longitude=100.532&latitude=13.738&start=20180630&end=20191231&time-standard=UTC&format=JSON')
# name: (figshare file id, computed_md5), from https://api.figshare.com/v2/articles/11726517/versions/6
FILES = {
    '2018Floor1.csv': (21350142, '3ae4902c359a74167963dff758406487'),
    '2018Floor2.csv': (21350166, 'c0fb626a0149c29fd00a0d0d06e3472d'),
    '2018Floor3.csv': (21350151, 'e1f2385af5dabefd63b1f98caf44fe18'),
    '2018Floor4.csv': (21350157, '1397b807889337451bc0deba79dd5333'),
    '2018Floor5.csv': (21350148, 'b394e07b6f9245becc0dbc34544334c8'),
    '2018Floor6.csv': (21350154, 'e4074802fd7973a87e620a9ea1a381b6'),
    '2018Floor7.csv': (21350145, '9ff3859e4b0fd74e142b81ddfaac50a9'),
    '2019Floor1.csv': (21350208, 'e51d1cbf5642c53656e6a4e6d997ff18'),
    '2019Floor2.csv': (21350226, '2fa6b68e788afaf55f4395a6b918092b'),
    '2019Floor3.csv': (21350193, 'f34d43850bcb042355495b0275b5428c'),
    '2019Floor4.csv': (21350172, '4b9d738c05555edcaadd9173c7b2e1cc'),
    '2019Floor5.csv': (21350205, '2422f2d7864ac6889c2ad2d68a086a28'),
    '2019Floor6.csv': (21350169, '4f2446b38b566f2c1a07bf0e44587b42'),
    '2019Floor7.csv': (21350217, '05b7920ed3dc3c478fbc172571ef8cca'),
}


def md5_of(path: Path) -> str:
    digest = hashlib.md5()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={'User-Agent': 'madrl-5r1c-validation'})
    partial = target.with_suffix(target.suffix + '.part')
    with urllib.request.urlopen(request, timeout=300) as response, partial.open('wb') as out:
        shutil.copyfileobj(response, out, 1 << 20)
    partial.replace(target)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--delete', action='store_true', help='remove the raw folder instead of downloading')
    args = parser.parse_args(argv)
    if args.delete:
        shutil.rmtree(RAW, ignore_errors=True)
        print('deleted', RAW, 'exists:', RAW.exists())
        return 0
    RAW.mkdir(parents=True, exist_ok=True)
    for name, (file_id, md5) in FILES.items():
        target = RAW/name
        if not (target.exists() and md5_of(target) == md5):
            fetch(f'https://ndownloader.figshare.com/files/{file_id}', target)
        actual = md5_of(target)
        if actual != md5:
            raise SystemExit(f'MD5 mismatch for {name}: {actual} != {md5}')
        print('ok', name, md5, flush=True)
    if not (RAW/NASA_NAME).exists():
        fetch(NASA_URL, RAW/NASA_NAME)
    print('ok', NASA_NAME, md5_of(RAW/NASA_NAME), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
