"""
Registro de orígenes de datos (selección por configuración)
============================================================
Mapea ``dataset.source`` (del YAML/manifest) a un adaptador concreto del
puerto ``DatasetSource``. Permite cambiar de origen de datos sin tocar el
código del dominio ni del entrenamiento:

    dataset:
      source: local            # local | http | s3 (extensible)
      args:
        dataset_dir: CityLearn/data/datasets/citylearn_iquitos_2023_2025

Adaptadores opcionales (http/s3) se importan de forma perezosa para no exigir
dependencias (requests/boto3) en entornos mínimos u offline.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from uc3m.data.adapters.local_csv import LocalCsvDatasetAdapter
from uc3m.data.ports import DatasetSource


def _build_http(**kwargs: Any) -> DatasetSource:
    """Builder perezoso: importa el adaptador HTTP solo al usarse."""
    from uc3m.data.adapters.remote_http import RemoteHttpDatasetAdapter

    return RemoteHttpDatasetAdapter(**kwargs)


def _build_s3(**kwargs: Any) -> DatasetSource:
    """Builder perezoso: importa el adaptador S3 solo al usarse (boto3 opcional)."""
    from uc3m.data.adapters.s3 import S3DatasetAdapter

    return S3DatasetAdapter(**kwargs)


_BUILDERS: Dict[str, Callable[..., DatasetSource]] = {
    "local": LocalCsvDatasetAdapter,
    "http": _build_http,
    "https": _build_http,
    "s3": _build_s3,
}


def register_source(kind: str, builder: Callable[..., DatasetSource]) -> None:
    """Registra (o sobreescribe) un adaptador para un tipo de origen."""
    _BUILDERS[kind.strip().lower()] = builder


def available_sources() -> list[str]:
    return sorted(_BUILDERS)


def build_source(cfg: Mapping[str, Any]) -> DatasetSource:
    """Construye un ``DatasetSource`` desde la sección ``dataset`` de la config.

    Acepta tanto ``{"dataset": {"source": ..., "args": {...}}}`` como
    directamente ``{"source": ..., "args": {...}}``.
    """
    section = dict(cfg.get("dataset", cfg))
    kind = str(section.get("source", "local")).strip().lower()
    args = dict(section.get("args", {}))

    if kind not in _BUILDERS:
        raise KeyError(
            f"Origen de datos '{kind}' no registrado. "
            f"Disponibles: {available_sources()}"
        )
    return _BUILDERS[kind](**args)


__all__ = ["build_source", "register_source", "available_sources"]
