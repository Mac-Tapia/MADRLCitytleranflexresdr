"""Adaptadores concretos del puerto ``DatasetSource``."""

from __future__ import annotations

from uc3m.data.adapters.local_csv import LocalCsvDatasetAdapter
from uc3m.data.adapters.remote_http import RemoteHttpDatasetAdapter
from uc3m.data.adapters.s3 import S3DatasetAdapter

__all__ = [
    "LocalCsvDatasetAdapter",
    "RemoteHttpDatasetAdapter",
    "S3DatasetAdapter",
]
