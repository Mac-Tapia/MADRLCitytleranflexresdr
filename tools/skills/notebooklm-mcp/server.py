#!/usr/bin/env python3
"""
NotebookLM MCP Server — consulta notebooks de Google NotebookLM desde Cursor.

Usa automatización de navegador (Patchright/Chrome) con sesión persistente.
Basado en el skill NotebookLM (PleasePrompto/notebooklm-mcp).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Asegurar que los scripts locales son importables
SKILL_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from mcp.server.fastmcp import FastMCP

from ask_question import ask_notebooklm
from auth_manager import AuthManager
from notebook_manager import NotebookLibrary

mcp = FastMCP(
    "notebooklm",
    instructions=(
        "Servidor MCP para Google NotebookLM. "
        "Consulta documentación con respuestas fundamentadas en fuentes. "
        "Ejecuta setup_auth una vez antes de preguntar. "
        "Usa list_notebooks para ver notebooks guardados."
    ),
)


def _library() -> NotebookLibrary:
    return NotebookLibrary()


def _auth() -> AuthManager:
    return AuthManager()


@mcp.tool()
def get_health() -> dict[str, Any]:
    """Estado de autenticación, biblioteca y configuración."""
    auth = _auth()
    info = auth.get_auth_info()
    stats = _library().get_stats()
    return {
        "authenticated": info.get("authenticated", False),
        "state_age_hours": info.get("state_age_hours"),
        "last_auth": info.get("authenticated_at_iso"),
        "library": {
            "total_notebooks": stats["total_notebooks"],
            "active_notebook": (
                stats["active_notebook"]["name"] if stats["active_notebook"] else None
            ),
        },
        "data_dir": str(SKILL_DIR / "data"),
    }


@mcp.tool()
def setup_auth(timeout_minutes: int = 10) -> str:
    """
    Autenticación inicial con Google (abre Chrome visible).
    Ejecutar una vez antes de consultar notebooks.
    """
    auth = _auth()
    if auth.setup_auth(headless=False, timeout_minutes=timeout_minutes):
        return "Autenticación completada. Ya puedes usar ask_question."
    return "Error: autenticación fallida. Reintenta setup_auth."


@mcp.tool()
def check_auth() -> dict[str, Any]:
    """Verifica si la sesión de Google sigue válida."""
    auth = _auth()
    info = auth.get_auth_info()
    valid = auth.validate_auth() if info.get("authenticated") else False
    return {
        "authenticated": info.get("authenticated", False),
        "valid": valid,
        "state_age_hours": info.get("state_age_hours"),
    }


@mcp.tool()
def re_auth(timeout_minutes: int = 10) -> str:
    """Borra credenciales y vuelve a autenticar (cambio de cuenta Google)."""
    auth = _auth()
    if auth.re_auth(headless=False, timeout_minutes=timeout_minutes):
        return "Re-autenticación completada."
    return "Error: re-autenticación fallida."


@mcp.tool()
def list_notebooks() -> list[dict[str, Any]]:
    """Lista todos los notebooks guardados en la biblioteca local."""
    notebooks = _library().list_notebooks()
    active_id = _library().active_notebook_id
    return [
        {
            "id": nb["id"],
            "name": nb["name"],
            "description": nb["description"],
            "topics": nb["topics"],
            "url": nb["url"],
            "active": nb["id"] == active_id,
            "use_count": nb.get("use_count", 0),
        }
        for nb in notebooks
    ]


@mcp.tool()
def add_notebook(
    url: str,
    name: str,
    description: str,
    topics: str,
) -> dict[str, Any]:
    """
    Añade un notebook a la biblioteca local.

    Args:
        url: URL de NotebookLM (https://notebooklm.google.com/notebook/...)
        name: Nombre descriptivo
        description: Qué contiene el notebook
        topics: Temas separados por coma (ej: "madrl,citylearn,energia")
    """
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    return _library().add_notebook(
        url=url,
        name=name,
        description=description,
        topics=topic_list,
    )


@mcp.tool()
def select_notebook(notebook_id: str) -> dict[str, Any]:
    """Establece el notebook activo por defecto para ask_question."""
    return _library().select_notebook(notebook_id)


@mcp.tool()
def search_notebooks(query: str) -> list[dict[str, Any]]:
    """Busca notebooks por nombre, descripción o temas."""
    return _library().search_notebooks(query)


@mcp.tool()
def remove_notebook(notebook_id: str) -> str:
    """Elimina un notebook de la biblioteca local (no borra el notebook en Google)."""
    if _library().remove_notebook(notebook_id):
        return f"Notebook '{notebook_id}' eliminado de la biblioteca."
    return f"Notebook '{notebook_id}' no encontrado."


@mcp.tool()
def ask_question(
    question: str,
    notebook_id: str | None = None,
    notebook_url: str | None = None,
    show_browser: bool = False,
) -> str:
    """
    Pregunta a NotebookLM y devuelve respuesta fundamentada en las fuentes del notebook.

    Args:
        question: Pregunta completa (incluye contexto; cada consulta abre sesión nueva)
        notebook_id: ID de la biblioteca local (opcional si hay notebook activo)
        notebook_url: URL directa del notebook (alternativa a notebook_id)
        show_browser: Mostrar ventana del navegador (útil para depurar)
    """
    auth = _auth()
    if not auth.is_authenticated():
        return (
            "Error: no autenticado. Ejecuta setup_auth primero "
            "(se abrirá Chrome para login de Google)."
        )

    library = _library()
    url = notebook_url

    if not url and notebook_id:
        notebook = library.get_notebook(notebook_id)
        if not notebook:
            return f"Error: notebook '{notebook_id}' no encontrado. Usa list_notebooks."
        url = notebook["url"]
        library.increment_use_count(notebook_id)

    if not url:
        active = library.get_active_notebook()
        if active:
            url = active["url"]
            library.increment_use_count(active["id"])
        else:
            notebooks = library.list_notebooks()
            if not notebooks:
                return (
                    "Error: no hay notebooks. Usa add_notebook o pasa notebook_url."
                )
            return (
                "Error: no hay notebook activo. Usa select_notebook o pasa "
                "notebook_id/notebook_url.\n"
                f"Disponibles: {json.dumps([n['id'] for n in notebooks])}"
            )

    answer = ask_notebooklm(
        question=question,
        notebook_url=url,
        headless=not show_browser,
    )

    if answer is None:
        return (
            "Error: no se obtuvo respuesta. Verifica auth (check_auth) "
            "o reintenta con show_browser=true."
        )

    return answer


@mcp.resource("notebooklm://library")
def library_resource() -> str:
    """Biblioteca de notebooks en formato JSON."""
    return json.dumps(list_notebooks(), indent=2, ensure_ascii=False)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
