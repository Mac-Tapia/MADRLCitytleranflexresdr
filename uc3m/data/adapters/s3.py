"""
Adaptador: dataset CityLearn alojado en Amazon S3
==================================================
Implementa el puerto ``DatasetSource`` para un dataset cuyos archivos viven
bajo un prefijo S3 (``s3://bucket/prefix/...``). Descarga el prefijo completo a
una caché local, localiza el directorio que contiene ``schema.json`` y delega
en ``LocalCsvDatasetAdapter``.

Decisiones de diseño:
  - **Dependencia opcional**: ``boto3`` se importa de forma perezosa dentro de
    los métodos. Si no está instalado se lanza un error claro indicando
    ``pip install boto3`` — el resto del paquete ``uc3m.data`` sigue importable
    en entornos sin boto3.
  - **Idempotente**: si el prefijo ya fue descargado (existe ``schema.json``
    bajo la caché), no vuelve a descargar.
"""

from __future__ import annotations

from pathlib import Path
import os

from uc3m.application.dataset.provenance import contained_path
from uc3m.data.contracts import DatasetManifest, DatasetValidationError
from uc3m.data.adapters.local_csv import LocalCsvDatasetAdapter

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CACHE_ROOT = _REPO_ROOT / "data" / "cache" / "datasets"


class S3DatasetAdapter:
    """Origen de datos para un dataset CityLearn alojado bajo un prefijo S3."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        *,
        name: str | None = None,
        cache_dir: str | Path | None = None,
        region_name: str | None = None,
    ):
        if not bucket:
            raise DatasetValidationError("S3DatasetAdapter requiere 'bucket'")
        self._bucket = str(bucket)
        self._prefix = str(prefix).lstrip("/")
        self._region = region_name
        self._name = name if name is not None else (self._prefix.rstrip("/").split("/")[-1] or self._bucket)
        root = Path(cache_dir).expanduser() if cache_dir else _DEFAULT_CACHE_ROOT
        if self._name in ("", ".") or "/" in self._name or "\\" in self._name:
            raise DatasetValidationError("S3 dataset name must be a single relative component")
        self._cache_dir = contained_path(root, self._name)

    @property
    def uri(self) -> str:
        return f"s3://{self._bucket}/{self._prefix}"

    # — puerto DatasetSource —
    def fetch(self) -> Path:
        return self._ensure_local()

    def schema_path(self) -> Path:
        return self._delegate().schema_path()

    def describe(self) -> DatasetManifest:
        manifest = self._delegate().describe()
        extra = dict(manifest.extra)
        extra["s3_uri"] = self.uri
        return DatasetManifest(
            name=self._name,
            source_uri=self.uri,
            buildings=manifest.buildings,
            hours=manifest.hours,
            content_hash=manifest.content_hash,
            schema_version=manifest.schema_version,
            extra=extra,
        )

    # — internos —
    def _delegate(self) -> LocalCsvDatasetAdapter:
        return LocalCsvDatasetAdapter(self._ensure_local(), name=self._name)

    def _ensure_local(self) -> Path:
        existing = self._find_schema_dir(self._cache_dir)
        if existing is not None:
            return existing

        client = self._make_client()
        paginator = client.get_paginator("list_objects_v2")
        # Validate the entire listing before any mkdir or download. S3 keys are
        # flat identifiers: a valid S3 key can be an unsafe filesystem path.
        pending = []
        destinations = set()
        for page in paginator.paginate(Bucket=self._bucket, Prefix=self._prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not isinstance(key, str) or not key.startswith(self._prefix):
                    raise DatasetValidationError("S3 key is outside the requested prefix")
                rel = key[len(self._prefix):] if self._prefix else key
                # With prefix 'data' the normal key 'data/schema.json' has one delimiter.
                if self._prefix and not self._prefix.endswith('/') and rel.startswith('/'):
                    rel = rel[1:]
                if not rel and key.endswith('/'):
                    continue
                dest = contained_path(self._cache_dir, rel)
                if key.endswith("/"):
                    continue
                identity = str(dest).casefold()
                if identity in destinations or dest.exists():
                    raise DatasetValidationError("S3 keys collide with another destination or an existing file")
                destinations.add(identity)
                pending.append((key, rel))

        if not pending:
            raise DatasetValidationError(
                f"No se encontraron objetos en {self.uri}"
            )
        for _, rel in pending:
            dest = contained_path(self._cache_dir, rel)
            if any(str(parent).casefold() in destinations or parent.is_file()
                   for parent in dest.parents):
                raise DatasetValidationError("S3 keys collide as files and directories")
        for key, rel in pending:
            dest = contained_path(self._cache_dir, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest = contained_path(self._cache_dir, rel)
            client.download_file(self._bucket, key, str(dest))

        found = self._find_schema_dir(self._cache_dir)
        if found is None:
            raise DatasetValidationError(
                f"No se encontró schema.json bajo el prefijo S3 {self.uri}"
            )
        return found

    def _make_client(self):
        try:
            import boto3  # noqa: F401  (import perezoso: dependencia opcional)
        except ImportError as exc:
            raise DatasetValidationError(
                "S3DatasetAdapter requiere 'boto3'. Instálalo con: pip install boto3"
            ) from exc
        if self._region:
            return boto3.client("s3", region_name=self._region)
        return boto3.client("s3")

    @staticmethod
    def _find_schema_dir(root: Path) -> Path | None:
        root = contained_path(root, '.')
        if not root.exists():
            return None
        schemas = []
        for directory, dirs, files in os.walk(root, followlinks=False):
            for name in sorted(dirs + files):
                candidate = contained_path(root, (Path(directory)/name).relative_to(root).as_posix())
                if name == 'schema.json' and candidate.is_file():
                    schemas.append(candidate)
        if root/'schema.json' in schemas:
            return root
        return min(schemas).parent if schemas else None


__all__ = ["S3DatasetAdapter"]
