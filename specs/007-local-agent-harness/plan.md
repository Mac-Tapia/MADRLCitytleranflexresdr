# Plan — SPEC-007

Contrato: [spec.md](spec.md). Secuencia: búsqueda y revisión de licencia → instalación canónica fijada → adaptaciones de seguridad/rutas → registro y hashes → pruebas negativas → enlaces → revisión independiente → aceptación en clientes.

Instalar recursos no ejecuta sus helpers ni cambia el stack. Los helpers se revisan antes de ejecutar; catálogos y perfiles no otorgan autoridad adicional. Codex consume AGENTS y skills; Claude añade perfiles locales con herramientas acotadas. Los junctions se regeneran tras clonar con `scripts/skills/register_local_skills.ps1`; no se suben a Git.

Validación: `python -m pytest tests/skills -q`, `python tools/skills/validate_skills.py --check-discovery`, `powershell -ExecutionPolicy Bypass -File scripts/skills/register_local_skills.ps1 -CheckOnly`. Revisar el índice Git explícito antes de publicar; no invocar el Stop hook heredado.

Pruebas de esquema no sustituyen ensayo de invocación: registrar por cliente versión, skill seleccionado, entrada, salida, herramientas usadas y límites respetados. Evaluar por tarea y comparar contra línea base, no por cantidad de agentes.
