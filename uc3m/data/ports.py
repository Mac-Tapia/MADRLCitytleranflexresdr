"""
Puertos de ingreso de datos (arquitectura hexagonal)
=====================================================
El dominio declara *qué* necesita para alimentar un entorno UC3M mediante el
puerto ``DatasetSource``. La infraestructura provee el *cómo* mediante
adaptadores concretos (CSV local, HTTP/ZIP, S3, ...), que se registran en
``uc3m.data.registry``.

Contrato (Strategy / Adapter):  ``fetch -> schema_path -> describe``

  - ``fetch()``       materializa el dataset localmente (idempotente) y
                      devuelve el directorio que contiene ``schema.json``.
  - ``schema_path()`` ruta al ``schema.json`` (contrato canónico CityLearn).
  - ``describe()``    ``DatasetManifest`` con metadatos de provenance.

Cualquier objeto que implemente estos tres métodos satisface el puerto
(tipado estructural vía ``Protocol``), sin necesidad de heredar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from uc3m.data.contracts import DatasetManifest


@runtime_checkable
class DatasetSource(Protocol):
    """Puerto universal de ingreso de datos para entornos CityLearn v2/v3."""

    def fetch(self) -> Path:
        """Materializa el dataset y devuelve el directorio con schema.json."""
        ...

    def schema_path(self) -> Path:
        """Ruta absoluta al schema.json del dataset."""
        ...

    def describe(self) -> DatasetManifest:
        """Metadatos de provenance del dataset."""
        ...


__all__ = ["DatasetSource"]
