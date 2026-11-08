# Skills canónicos del proyecto

El registro `tools/skills/registry.yaml` distingue skills instalados, conectores legados y habilidades ya disponibles en el entorno. Fuentes fijadas a commits; licencias y hashes locales permiten detectar cambios. No se ejecutan automáticamente scripts descargados.

Validar: `python tools/skills/validate_skills.py`.
Registrar descubrimiento: `powershell -ExecutionPolicy Bypass -File scripts/skills/register_local_skills.ps1`.
Comprobar enlaces: añadir `-CheckOnly` al mismo comando.

La instalación canónica se conserva aquí. Los enlaces locales generados para los dos clientes no se versionan ni duplican los contenidos. Tras clonar hay que registrarlos otra vez. Reabrir la sesión si el cliente no actualiza su catálogo; el descubrimiento real en ambos clientes requiere verificación manual.

Guía de selección y roles: `docs/architecture/AGENT_HARNESS.md`. Los skills no instalan FastAPI, Docker, Playwright ni una plataforma de agentes: son instrucciones y recursos para tareas autorizadas. Tampoco garantizan mayor velocidad o precisión.

Los directorios google-drive-mcp y notebooklm-mcp son conectores heredados, no skills válidos; no se activan ni se requieren. No se han eliminado credenciales, sesiones o perfiles del usuario. The four legacy skills from the removed `agent-skills/` folder are not migrated: their license cannot be verified. Their pinned source, hashes, reasons and the pending owner decision are in `legacy_skills` and `legacy_skills_review` of the registry.
