#!/usr/bin/env python3
"""
Google Drive MCP Server — acceso a archivos en Google Drive desde Cursor.

Usa Google Drive API v3 con OAuth2 (cuenta de escritorio).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from mcp.server.fastmcp import FastMCP

from auth_manager import AuthManager
from config import CREDENTIALS_FILE, DEFAULT_DRIVE_ROOT, DATA_DIR
from drive_client import DriveClient

mcp = FastMCP(
    "google-drive",
    instructions=(
        "Servidor MCP para Google Drive en línea. "
        "Requiere data/credentials.json (OAuth Desktop de Google Cloud) "
        "y setup_auth una vez para obtener token. "
        f"Carpeta por defecto del proyecto: {DEFAULT_DRIVE_ROOT}."
    ),
)


def _auth() -> AuthManager:
    return AuthManager()


def _client() -> DriveClient:
    return DriveClient(_auth())


@mcp.tool()
def get_health() -> dict[str, Any]:
    """Estado de autenticación y rutas de configuración."""
    auth = _auth()
    info = auth.get_auth_info()
    return {
        "authenticated": info.get("authenticated", False),
        "token_valid": auth.validate_auth() if info.get("authenticated") else False,
        "token_age_hours": info.get("token_age_hours"),
        "credentials_present": CREDENTIALS_FILE.exists(),
        "data_dir": str(DATA_DIR),
        "default_drive_root": DEFAULT_DRIVE_ROOT,
    }


@mcp.tool()
def setup_auth() -> str:
    """
    Autenticación OAuth con Google (abre el navegador).
    Requiere data/credentials.json descargado de Google Cloud Console.
    """
    if not CREDENTIALS_FILE.exists():
        return (
            f"Error: falta {CREDENTIALS_FILE}. "
            "Crea un OAuth Client ID (Desktop) en Google Cloud Console, "
            "habilita Google Drive API, descarga JSON y guárdalo como "
            "tools/skills/google-drive-mcp/data/credentials.json"
        )
    try:
        _auth().setup_auth()
        return "Autenticación completada. Ya puedes usar list_files, search_files, etc."
    except Exception as exc:
        return f"Error en autenticación: {exc}"


@mcp.tool()
def check_auth() -> dict[str, Any]:
    """Verifica si el token OAuth sigue válido."""
    auth = _auth()
    info = auth.get_auth_info()
    valid = auth.validate_auth() if info.get("authenticated") else False
    return {
        "authenticated": info.get("authenticated", False),
        "valid": valid,
        "token_age_hours": info.get("token_age_hours"),
    }


@mcp.tool()
def re_auth() -> str:
    """Borra el token y vuelve a autenticar (cambio de cuenta Google)."""
    try:
        _auth().re_auth()
        return "Re-autenticación completada."
    except Exception as exc:
        return f"Error: {exc}"


@mcp.tool()
def list_files(
    folder_id: str | None = None,
    folder_path: str | None = None,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """
    Lista archivos y carpetas en una carpeta de Drive.

    Args:
        folder_id: ID de carpeta en Drive (opcional)
        folder_path: Ruta bajo My Drive, ej. MADRLCitytleranflexresdr/outputs
        page_size: Máximo de resultados (default 50)
    """
    try:
        path = folder_path or DEFAULT_DRIVE_ROOT
        return _client().list_files(
            folder_id=folder_id,
            folder_path=None if folder_id else path,
            page_size=page_size,
        )
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
def search_files(
    query: str,
    folder_path: str | None = None,
    folder_id: str | None = None,
    page_size: int = 25,
) -> list[dict[str, Any]]:
    """
    Busca archivos por nombre en Drive (o dentro de una carpeta).

    Args:
        query: Texto a buscar en el nombre del archivo
        folder_path: Limitar búsqueda a esta ruta bajo My Drive
        folder_id: ID de carpeta contenedora (alternativa a folder_path)
        page_size: Máximo de resultados
    """
    try:
        return _client().search_files(
            query=query,
            folder_id=folder_id,
            folder_path=folder_path,
            page_size=page_size,
        )
    except Exception as exc:
        return [{"error": str(exc)}]


@mcp.tool()
def get_file_info(file_id: str) -> dict[str, Any]:
    """Metadatos de un archivo o carpeta por su ID de Drive."""
    try:
        return _client().get_file_info(file_id)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def resolve_folder_path(folder_path: str) -> dict[str, Any]:
    """
    Resuelve una ruta bajo My Drive a su ID y metadatos.

    Ejemplo: MADRLCitytleranflexresdr/outputs/madrl_v3_20260618
    """
    try:
        return _client().resolve_path(folder_path)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def download_file(file_id: str, local_path: str) -> dict[str, Any]:
    """
    Descarga un archivo de Drive al disco local.

    Args:
        file_id: ID del archivo en Drive
        local_path: Ruta local de destino (se crean carpetas padre si hace falta)
    """
    try:
        return _client().download_file(file_id, local_path)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def read_file_content(file_id: str, max_bytes: int = 512000) -> dict[str, Any]:
    """
    Lee contenido de texto/JSON/CSV pequeño directamente (sin guardar en disco).

    Para archivos grandes usa download_file.
    """
    try:
        return _client().read_file_content(file_id, max_bytes=max_bytes)
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def upload_file(
    local_path: str,
    folder_path: str | None = None,
    folder_id: str | None = None,
    drive_name: str | None = None,
) -> dict[str, Any]:
    """
    Sube un archivo local a Google Drive.

    Args:
        local_path: Ruta del archivo en el equipo
        folder_path: Carpeta destino bajo My Drive (default: MADRLCitytleranflexresdr)
        folder_id: ID de carpeta destino (alternativa a folder_path)
        drive_name: Nombre en Drive (default: nombre del archivo local)
    """
    try:
        return _client().upload_file(
            local_path=local_path,
            folder_id=folder_id,
            folder_path=folder_path,
            drive_name=drive_name,
        )
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def create_folder(
    name: str,
    parent_folder_path: str | None = None,
    parent_folder_id: str | None = None,
) -> dict[str, Any]:
    """Crea una carpeta en Drive."""
    try:
        return _client().create_folder(
            name=name,
            parent_folder_id=parent_folder_id,
            parent_folder_path=parent_folder_path or DEFAULT_DRIVE_ROOT,
        )
    except Exception as exc:
        return {"error": str(exc)}


@mcp.resource("gdrive://health")
def health_resource() -> str:
    return json.dumps(get_health(), indent=2, ensure_ascii=False)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
