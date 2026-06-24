#!/usr/bin/env python3
"""Post-auth bootstrap: add CityLearn notebook and run a test query."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from ask_question import ask_notebooklm
from auth_manager import AuthManager
from notebook_manager import NotebookLibrary

DEFAULT_NOTEBOOK = {
    "url": "",
    "name": "MADRL CityLearn Iquitos",
    "description": (
        "Tesis MADRL CityLearn v3: HAPPO multi-agente, dataset Iquitos 2023-2025, "
        "17 edificios, flexibilidad energética, recompensas E1/E2/E3, benchmarks."
    ),
    "topics": "madrl,citylearn,happo,iquitos,flexibilidad,energia,bess,ev",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap NotebookLM MCP library")
    parser.add_argument("--url", required=True, help="NotebookLM notebook URL")
    parser.add_argument("--name", default=DEFAULT_NOTEBOOK["name"])
    parser.add_argument("--description", default=DEFAULT_NOTEBOOK["description"])
    parser.add_argument("--topics", default=DEFAULT_NOTEBOOK["topics"])
    parser.add_argument("--test-question", default="¿Cuáles son los temas principales de este notebook?")
    args = parser.parse_args()

    auth = AuthManager()
    if not auth.is_authenticated():
        print("No autenticado. Ejecuta primero: python scripts/auth_manager.py setup")
        return 1

    library = NotebookLibrary()
    existing = library.get_notebook("madrl-citylearn-iquitos")
    if not existing:
        nb = library.add_notebook(
            url=args.url,
            name=args.name,
            description=args.description,
            topics=[t.strip() for t in args.topics.split(",") if t.strip()],
        )
        library.select_notebook(nb["id"])
        print(f"Notebook añadido: {nb['id']}")
    else:
        library.select_notebook(existing["id"])
        print(f"Notebook ya existe: {existing['id']}")

    print("Consulta de prueba...")
    answer = ask_notebooklm(args.test_question, args.url, headless=True)
    if answer:
        print("\n" + "=" * 60)
        print(answer[:2000])
        if len(answer) > 2000:
            print("... [truncado]")
        return 0

    print("Error en consulta de prueba.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
