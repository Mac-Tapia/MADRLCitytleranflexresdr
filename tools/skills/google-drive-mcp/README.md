# Google Drive MCP Server

Servidor [Model Context Protocol](https://modelcontextprotocol.io) para acceder a **Google Drive en línea** desde Cursor u otros clientes MCP.

Útil para listar, buscar, descargar y subir artefactos de entrenamiento MADRL (por ejemplo `MyDrive/MADRLCitytleranflexresdr/outputs/`).

## Requisitos

- Python 3.10+
- Cuenta Google con acceso a la carpeta en Drive
- Proyecto en [Google Cloud Console](https://console.cloud.google.com/) con **Google Drive API** habilitada
- OAuth 2.0 Client ID tipo **Aplicación de escritorio**

## Instalación

```powershell
# Desde la raíz del repositorio
powershell -ExecutionPolicy Bypass -File tools/skills/google-drive-mcp/setup.ps1
```

O:

```powershell
python tools/skills/google-drive-mcp/run_server.py
```

La primera ejecución crea el venv en `tools/skills/google-drive-mcp/.venv`.

## Credenciales OAuth (una vez)

1. En Google Cloud Console → **APIs y servicios** → **Biblioteca** → habilita **Google Drive API**.
2. **Credenciales** → **Crear credenciales** → **ID de cliente OAuth**.
3. Tipo de aplicación: **Escritorio**.
4. Descarga el JSON y guárdalo como:

   `tools/skills/google-drive-mcp/data/credentials.json`

   (Plantilla: `data/credentials.example.json`)

5. Si la app está en modo **Prueba**, añade tu cuenta Google en **Usuarios de prueba** del consentimiento OAuth.

## Configuración en Cursor

`.cursor/mcp.json` registra este servidor junto a NotebookLM. Reinicia Cursor o recarga MCP en **Settings → MCP**.

## Uso inicial

1. Coloca `credentials.json` en `data/`.
2. Pide al agente que ejecute **`setup_auth`** (se abre el navegador para autorizar Drive).
3. Usa **`list_files`** con `folder_path: MADRLCitytleranflexresdr/outputs` o busca con **`search_files`**.

## Herramientas MCP

| Tool | Descripción |
|------|-------------|
| `get_health` | Estado de auth y configuración |
| `setup_auth` | Login OAuth inicial |
| `check_auth` | Verificar token válido |
| `re_auth` | Cambiar cuenta Google |
| `list_files` | Listar carpeta en Drive |
| `search_files` | Buscar por nombre |
| `get_file_info` | Metadatos por file ID |
| `resolve_folder_path` | Ruta → ID de carpeta |
| `download_file` | Descargar a disco local |
| `read_file_content` | Leer texto/JSON pequeño inline |
| `upload_file` | Subir archivo local |
| `create_folder` | Crear carpeta |

## Datos locales (gitignored)

- `data/credentials.json` — OAuth client secret (no subir a git)
- `data/token.json` — token de acceso/refresh tras `setup_auth`

## Carpeta por defecto del proyecto

`MADRLCitytleranflexresdr` bajo **Mi unidad**, alineado con el notebook Colab y la tesis.
