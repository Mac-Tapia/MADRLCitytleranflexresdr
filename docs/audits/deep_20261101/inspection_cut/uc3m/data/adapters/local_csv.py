"""
Adaptador: dataset CityLearn en CSV local
==========================================
Implementa el puerto ``DatasetSource`` para un directorio local que ya
contiene ``schema.json`` y sus CSV (caso del dataset Iquitos). Es el camino
por defecto y no requiere red.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from uc3m.data.contracts import DatasetManifest, DatasetValidationError


class LocalCsvDatasetAdapter:
    """Origen de datos para un dataset CityLearn ya presente en disco."""

    def __init__(self, dataset_dir: str | Path, *, name: str | None = None):
        self._dir = Path(dataset_dir).expanduser().resolve()
        self._name = name or self._dir.name

    def fetch(self) -> Path:
        schema = self._dir / "schema.json"
        if not schema.is_file():
            raise DatasetValidationError(
                f"No se encontró schema.json en {self._dir}"
            )
        return self._dir

    def schema_path(self) -> Path:
        return self._dir / "schema.json"

    def describe(self) -> DatasetManifest:
        schema_file = self.schema_path()
        if not schema_file.is_file():
            raise DatasetValidationError(
                f"No se encontró schema.json en {self._dir}"
            )

        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        buildings = self._count_buildings(schema)
        hours = self._infer_hours(schema)

        return DatasetManifest(
            name=self._name,
            source_uri=self._dir.as_uri(),
            buildings=buildings,
            hours=hours,
            content_hash=self._hash_schema(schema_file),
            schema_version=int(schema.get("schema_version", 1) or 1),
            extra={"root_directory": str(self._dir)},
        )

    # — internos —
    @staticmethod
    def _count_buildings(schema: dict) -> int:
        buildings = schema.get("buildings", {}) or {}
        if isinstance(buildings, dict):
            return len(buildings)
        if isinstance(buildings, Iterable):
            return len(list(buildings))
        return 0

    @staticmethod
    def _infer_hours(schema: dict) -> int:
        for key in ("simulation_end_time_step", "simulation_time_steps", "time_steps"):
            val = schema.get(key)
            if isinstance(val, (int, float)) and val > 0:
                return int(val) + (1 if key == "simulation_end_time_step" else 0)
        # Valor por defecto seguro (no rompe la validación) si el schema no lo declara.
        return 8760

    @staticmethod
    def _hash_schema(schema_file: Path) -> str:
        return hashlib.sha256(schema_file.read_bytes()).hexdigest()[:16]


__all__ = ["LocalCsvDatasetAdapter"]
