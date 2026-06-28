"""
Adaptador: dataset CityLearn descargado por HTTP(S) como .zip
=============================================================
Implementa el puerto ``DatasetSource`` para un dataset publicado como archivo
``.zip`` accesible por URL (HTTP/HTTPS o ``file://``). Descarga el zip a una
caché local, lo descomprime, localiza el directorio que contiene
``schema.json`` y delega toda la lógica de lectura en
``LocalCsvDatasetAdapter``.

Decisiones de diseño:
  - **Sin dependencias nuevas**: usa solo ``urllib.request`` + ``zipfile`` de
    la stdlib. El import es perezoso (dentro de los métodos) para no impactar
    el tiempo de import del paquete.
  - **Idempotente**: si el dataset ya fue descargado/extraído (existe un
    ``schema.json`` bajo la caché), no vuelve a descargar ni a descomprimir.
  - **Provenance**: ``describe()`` añade la URL de origen a los metadatos.
"""

from __future__ import annotations

from pathlib import Path

from uc3m.data.contracts import DatasetManifest, DatasetValidationError
from uc3m.data.adapters.local_csv import LocalCsvDatasetAdapter

# Raíz del repo (uc3m/data/adapters/remote_http.py -> parents[3]) para resolver
# la caché por defecto de forma portable (Windows/Linux/Mac).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CACHE_ROOT = _REPO_ROOT / "data" / "cache" / "datasets"


class RemoteHttpDatasetAdapter:
    """Origen de datos para un dataset CityLearn publicado como .zip por URL."""

    def __init__(
        self,
        url: str,
        *,
        name: str | None = None,
        cache_dir: str | Path | None = None,
    ):
        if not url:
            raise DatasetValidationError("RemoteHttpDatasetAdapter requiere 'url'")
        self._url = str(url)
        self._name = name or self._infer_name(self._url)
        root = Path(cache_dir).expanduser() if cache_dir else _DEFAULT_CACHE_ROOT
        self._cache_dir = (root / self._name).resolve()
        self._extract_dir = self._cache_dir / "extracted"
        self._zip_path = self._cache_dir / f"{self._name}.zip"

    # — puerto DatasetSource —
    def fetch(self) -> Path:
        dataset_dir = self._ensure_local()
        return dataset_dir

    def schema_path(self) -> Path:
        return self._delegate().schema_path()

    def describe(self) -> DatasetManifest:
        manifest = self._delegate().describe()
        # Sobrescribir provenance con la URL remota real.
        extra = dict(manifest.extra)
        extra["http_url"] = self._url
        return DatasetManifest(
            name=self._name,
            source_uri=self._url,
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
        """Descarga + descomprime (idempotente) y devuelve el dir con schema.json."""
        existing = self._find_schema_dir(self._extract_dir)
        if existing is not None:
            return existing

        import urllib.request
        import zipfile

        self._cache_dir.mkdir(parents=True, exist_ok=True)

        if not self._zip_path.is_file():
            try:
                with urllib.request.urlopen(self._url) as resp, open(
                    self._zip_path, "wb"
                ) as out:
                    out.write(resp.read())
            except Exception as exc:  # noqa: BLE001 — contexto claro para el usuario
                raise DatasetValidationError(
                    f"No se pudo descargar el dataset desde {self._url}: {exc}"
                ) from exc

        self._extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(self._zip_path) as zf:
                zf.extractall(self._extract_dir)
        except zipfile.BadZipFile as exc:
            raise DatasetValidationError(
                f"El archivo descargado desde {self._url} no es un .zip válido"
            ) from exc

        found = self._find_schema_dir(self._extract_dir)
        if found is None:
            raise DatasetValidationError(
                f"No se encontró schema.json dentro del zip descargado de {self._url}"
            )
        return found

    @staticmethod
    def _find_schema_dir(root: Path) -> Path | None:
        """Devuelve el directorio que contiene schema.json (o None)."""
        if not root.exists():
            return None
        direct = root / "schema.json"
        if direct.is_file():
            return root.resolve()
        for schema in sorted(root.rglob("schema.json")):
            return schema.parent.resolve()
        return None

    @staticmethod
    def _infer_name(url: str) -> str:
        tail = url.rstrip("/").split("/")[-1]
        for suffix in (".zip", ".tar.gz", ".tgz"):
            if tail.lower().endswith(suffix):
                return tail[: -len(suffix)]
        return tail or "remote_dataset"


__all__ = ["RemoteHttpDatasetAdapter"]
