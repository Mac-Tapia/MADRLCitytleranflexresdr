"""
uc3m.data — Interfaces de ingreso de datos (Ports & Adapters)
==============================================================
Capa de ingreso de datos universal y reproducible para entornos CityLearn.

  - ``DatasetSource``  — puerto (contrato) de ingreso de datos.
  - ``DatasetManifest`` — provenance del dataset (hash, versión, origen).
  - ``build_source``   — selección del adaptador por configuración.
  - adaptadores        — ``LocalCsvDatasetAdapter`` (extensible a http/s3).
"""

from __future__ import annotations

from uc3m.data.adapters.local_csv import LocalCsvDatasetAdapter
from uc3m.data.contracts import DatasetManifest, DatasetValidationError
from uc3m.data.ports import DatasetSource
from uc3m.data.registry import available_sources, build_source, register_source

__all__ = [
    "DatasetSource",
    "DatasetManifest",
    "DatasetValidationError",
    "LocalCsvDatasetAdapter",
    "build_source",
    "register_source",
    "available_sources",
]
