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
        self._name = name or (self._prefix.rstrip("/").split("/")[-1] or self._bucket)
        root = Path(cache_dir).expanduser() if cache_dir else _DEFAULT_CACHE_ROOT
        self._cache_dir = (root / self._name).resolve()

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
        downloaded = 0
        for page in paginator.paginate(Bucket=self._bucket, Prefix=self._prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                rel = key[len(self._prefix):].lstrip("/") if self._prefix else key
                dest = self._cache_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                client.download_file(self._bucket, key, str(dest))
                downloaded += 1

        if downloaded == 0:
            raise DatasetValidationError(
                f"No se encontraron objetos en {self.uri}"
            )

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
        if not root.exists():
            return None
        direct = root / "schema.json"
        if direct.is_file():
            return root.resolve()
        for schema in sorted(root.rglob("schema.json")):
            return schema.parent.resolve()
        return None


__all__ = ["S3DatasetAdapter"]
