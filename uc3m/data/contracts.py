"""
Contratos de datos (capa de frontera)
======================================
Modelos de validación para el ingreso de datos. Se usan dataclasses puras
(sin dependencias externas como pydantic) para que el paquete sea importable
en cualquier máquina/entorno mínimo.

``DatasetManifest`` registra la *provenance* de un dataset (hash, versión,
origen), pieza clave para la reproducibilidad: cada corrida puede declarar
exactamente qué datos consumió.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict


class DatasetValidationError(ValueError):
    """Error de validación de un dataset o su manifest."""


@dataclass(frozen=True)
class DatasetManifest:
    """Metadatos de provenance de un dataset CityLearn v2/v3."""

    name: str
    source_uri: str
    buildings: int
    hours: int
    content_hash: str = ""
    schema_version: int = 1
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise DatasetValidationError("manifest.name no puede estar vacío")
        if self.buildings <= 0:
            raise DatasetValidationError(
                f"buildings debe ser > 0 (N arbitrario), recibido {self.buildings}"
            )
        if self.hours <= 0:
            raise DatasetValidationError(
                f"hours debe ser > 0, recibido {self.hours}"
            )
        if self.schema_version < 1:
            raise DatasetValidationError("schema_version debe ser >= 1")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = ["DatasetManifest", "DatasetValidationError"]
