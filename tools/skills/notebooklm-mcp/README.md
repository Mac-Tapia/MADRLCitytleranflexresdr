# NotebookLM MCP Server

Servidor [Model Context Protocol](https://modelcontextprotocol.io) para consultar **Google NotebookLM** desde Cursor u otros clientes MCP.

## Requisitos

- Python 3.10+
- Google Chrome instalado
- Cuenta Google con acceso a NotebookLM

## Instalación

```powershell
# Desde la raíz del repositorio
python tools/skills/notebooklm-mcp/run_server.py
```

La primera ejecución crea el venv en `tools/skills/notebooklm-mcp/.venv` e instala dependencias.

## Configuración en Cursor

El archivo `.cursor/mcp.json` ya registra este servidor. Reinicia Cursor o recarga MCP servers en Settings → MCP.

## Uso inicial

1. **Autenticación** (una vez): pide al agente que ejecute `setup_auth`. Se abre Chrome para login de Google.
2. **Añadir notebook**: `add_notebook` con la URL de NotebookLM, nombre, descripción y temas.
3. **Consultar**: `ask_question` con tu pregunta.

## Herramientas MCP

| Tool | Descripción |
|------|-------------|
| `get_health` | Estado de auth y biblioteca |
| `setup_auth` | Login inicial con Google |
| `check_auth` | Verificar sesión válida |
| `re_auth` | Cambiar cuenta Google |
| `list_notebooks` | Listar notebooks guardados |
| `add_notebook` | Añadir notebook a biblioteca |
| `select_notebook` | Establecer notebook activo |
| `search_notebooks` | Buscar por palabra clave |
| `remove_notebook` | Quitar de biblioteca local |
| `ask_question` | Preguntar al notebook |

## Datos locales

Credenciales y biblioteca se guardan en `tools/skills/notebooklm-mcp/data/` (ignorado por git).

## Alternativa npm

Si prefieres el servidor TypeScript oficial con más herramientas (audio, fuentes, sesiones):

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["notebooklm-mcp@latest"]
    }
  }
}
```

Ver: https://github.com/PleasePrompto/notebooklm-mcp
