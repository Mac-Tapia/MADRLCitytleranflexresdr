"""Audit 2026-11-01 (item 6): the test suite never regenerates the retired cache.

The native common module pickles CityLearn CSVs into outputs/dataset_cache
(retired R-06). tests/conftest.py redirects that cache to a pytest temporary
directory for the whole session, so any test that builds a native adapter
in-process writes there instead.
"""
from pathlib import Path

from uc3m.adapters.algorithms import native_entrypoint as ne

REPO = Path(__file__).resolve().parents[2]


def test_session_redirects_native_csv_cache_out_of_the_repository():
    common = ne.load_native_common(REPO)
    cache = Path(common._CSV_CACHE_DIR).resolve()
    assert REPO.resolve() not in cache.parents, cache
    assert cache != (REPO/'outputs/dataset_cache').resolve()
