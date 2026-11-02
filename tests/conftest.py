"""Repository-wide test isolation (audit 2026-11-01, item 6).

The native common module (CityLearn/scripts/citylearn_v3_training_common.py)
pickles CityLearn CSVs into ``outputs/dataset_cache``, a retired output root
(R-06). Any test that builds a native adapter in-process would recreate it, so
the cache directory is redirected to a pytest temporary directory for the whole
session. Child processes are isolated separately: the fresh native entrypoint
redirects the cache into each attempt (``native_cache``).
"""
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session', autouse=True)
def _native_csv_cache_outside_repository(tmp_path_factory):
    scripts = str(_REPO/'CityLearn/scripts')
    if scripts not in sys.path:
        sys.path.append(scripts)  # appended: never shadow modules of the suite
    import citylearn_v3_training_common as common

    original = common._CSV_CACHE_DIR
    common._CSV_CACHE_DIR = tmp_path_factory.mktemp('native_dataset_cache')
    try:
        yield common._CSV_CACHE_DIR
    finally:
        common._CSV_CACHE_DIR = original
