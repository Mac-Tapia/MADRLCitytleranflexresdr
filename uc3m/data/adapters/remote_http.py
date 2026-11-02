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
  - **Caché por contenido**: el archivo se guarda bajo
    ``<cache>/<name>/<sha256>/``; un nombre igual con contenido distinto nunca
    reutiliza lo extraído antes. Con ``expected_sha256`` la descarga debe
    coincidir y lo ya extraído con ese digest se reutiliza sin red.
  - **Entradas no confiables**: timeout explícito, cuota de bytes descargados,
    cuota de bytes y de miembros expandidos, rechazo de rutas absolutas, de
    unidad, ``..`` y enlaces dentro del zip, y verificación CRC antes de
    publicar el directorio (escritura en ``.partial`` y renombrado).
  - **Provenance**: ``describe()`` añade la URL y el sha256 del archivo.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import stat
from pathlib import Path, PurePosixPath, PureWindowsPath

from uc3m.data.contracts import DatasetManifest, DatasetValidationError
from uc3m.data.adapters.local_csv import LocalCsvDatasetAdapter

# Raíz del repo (uc3m/data/adapters/remote_http.py -> parents[3]) para resolver
# la caché por defecto de forma portable (Windows/Linux/Mac).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CACHE_ROOT = _REPO_ROOT / "data" / "cache" / "datasets"

# Límites por defecto del proyecto (no de la literatura); configurables por llamada.
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_DOWNLOAD_BYTES = 2 * 1024**3
DEFAULT_MAX_EXTRACTED_BYTES = 8 * 1024**3
DEFAULT_MAX_MEMBERS = 20_000
_CHUNK = 1024 * 1024
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMPLETE = ".complete"


class RemoteHttpDatasetAdapter:
    """Origen de datos para un dataset CityLearn publicado como .zip por URL."""

    def __init__(
        self,
        url: str,
        *,
        name: str | None = None,
        cache_dir: str | Path | None = None,
        expected_sha256: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_download_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
        max_extracted_bytes: int = DEFAULT_MAX_EXTRACTED_BYTES,
        max_members: int = DEFAULT_MAX_MEMBERS,
    ):
        if not url:
            raise DatasetValidationError("RemoteHttpDatasetAdapter requiere 'url'")
        self._url = str(url)
        self._name = name if name is not None else self._infer_name(self._url)
        if not _NAME.fullmatch(self._name) or ".." in self._name:
            raise DatasetValidationError(
                f"nombre de dataset no válido para la caché: {self._name!r}"
            )
        if expected_sha256 is not None and not _SHA256.fullmatch(str(expected_sha256)):
            raise DatasetValidationError("expected_sha256 debe ser un sha256 hexadecimal en minúsculas")
        if timeout_seconds <= 0 or max_download_bytes <= 0 or max_extracted_bytes <= 0 or max_members <= 0:
            raise DatasetValidationError("timeout y cuotas deben ser positivos")
        root = Path(cache_dir).expanduser() if cache_dir else _DEFAULT_CACHE_ROOT
        self._cache_dir = (root / self._name).resolve()
        self._expected = expected_sha256
        self._digest = expected_sha256
        self._timeout = float(timeout_seconds)
        self._max_download = int(max_download_bytes)
        self._max_extracted = int(max_extracted_bytes)
        self._max_members = int(max_members)

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
        extra["archive_sha256"] = self._digest
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

    def _extracted(self, digest: str) -> Path:
        return self._cache_dir / digest / "extracted"

    def _cached(self, digest: str | None) -> Path | None:
        if digest is None:
            return None
        extracted = self._extracted(digest)
        if not (extracted / _COMPLETE).is_file():
            return None
        return self._find_schema_dir(extracted)

    def _ensure_local(self) -> Path:
        """Descarga, verifica y descomprime; reutiliza solo lo extraído con el mismo digest."""
        existing = self._cached(self._digest)
        if existing is not None:
            return existing

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        download = self._cache_dir / "download.partial"
        try:
            digest = self._download(download)
            if self._expected is not None and digest != self._expected:
                raise DatasetValidationError(
                    f"sha256 de {self._url} es {digest}, se esperaba {self._expected}"
                )
            self._digest = digest
            existing = self._cached(digest)
            if existing is not None:
                return existing
            self._extract(download, self._extracted(digest))
        finally:
            download.unlink(missing_ok=True)

        found = self._cached(self._digest)
        if found is None:
            raise DatasetValidationError(
                f"No se encontró schema.json dentro del zip descargado de {self._url}"
            )
        return found

    def _download(self, target: Path) -> str:
        import urllib.request

        digest = hashlib.sha256()
        received = 0
        try:
            with urllib.request.urlopen(self._url, timeout=self._timeout) as resp, open(target, "wb") as out:
                while True:
                    chunk = resp.read(_CHUNK)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > self._max_download:
                        raise DatasetValidationError(
                            f"la descarga de {self._url} supera la cuota de {self._max_download} bytes"
                        )
                    digest.update(chunk)
                    out.write(chunk)
        except DatasetValidationError:
            raise
        except Exception as exc:  # noqa: BLE001 — contexto claro para el usuario
            raise DatasetValidationError(
                f"No se pudo descargar el dataset desde {self._url}: {exc}"
            ) from exc
        return digest.hexdigest()

    @staticmethod
    def _member_path(name: str) -> PurePosixPath:
        windows = PureWindowsPath(name)
        posix = PurePosixPath(name.replace("\\", "/"))
        if not name or windows.drive or windows.root or posix.is_absolute() or ".." in posix.parts:
            raise DatasetValidationError(f"miembro del zip fuera de la raíz de extracción: {name!r}")
        return posix

    def _extract(self, archive: Path, destination: Path) -> None:
        import zipfile

        partial = destination.with_name(destination.name + ".partial")
        shutil.rmtree(partial, ignore_errors=True)
        try:
            with zipfile.ZipFile(archive) as zf:
                members = zf.infolist()
                if len(members) > self._max_members:
                    raise DatasetValidationError(
                        f"el zip de {self._url} tiene {len(members)} miembros (cuota {self._max_members})"
                    )
                declared = 0
                for info in members:
                    self._member_path(info.filename)
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise DatasetValidationError(f"el zip contiene un enlace: {info.filename!r}")
                    declared += info.file_size
                if declared > self._max_extracted:
                    raise DatasetValidationError(
                        f"la expansión del zip de {self._url} ({declared} bytes) supera la cuota "
                        f"de {self._max_extracted} bytes"
                    )
                written = 0
                for info in members:
                    target = partial / Path(*self._member_path(info.filename).parts)
                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as source, open(target, "wb") as out:
                        while True:
                            chunk = source.read(_CHUNK)
                            if not chunk:
                                break
                            written += len(chunk)
                            if written > self._max_extracted:
                                raise DatasetValidationError(
                                    f"la expansión real del zip de {self._url} supera la cuota"
                                )
                            out.write(chunk)
        except zipfile.BadZipFile as exc:
            shutil.rmtree(partial, ignore_errors=True)
            raise DatasetValidationError(
                f"El archivo descargado desde {self._url} no es un .zip válido o está truncado"
            ) from exc
        except BaseException:
            shutil.rmtree(partial, ignore_errors=True)
            raise
        (partial / _COMPLETE).write_text("ok\n", encoding="utf-8")
        shutil.rmtree(destination, ignore_errors=True)
        partial.rename(destination)

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
