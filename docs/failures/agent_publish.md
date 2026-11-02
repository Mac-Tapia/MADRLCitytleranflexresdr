# Publicación automática sin propiedad de cambios

## Summary

El hook Stop heredado de Claude llama un script que agrega todo el árbol sucio y publica. En un trabajo con varios agentes puede incluir cambios ajenos, binarios o documentación no aceptada. No fue creado por esta instalación.

## Root Cause

La exclusión de Git no identifica propiedad ni aceptación de cada cambio. El hook también modifica README y no ejecuta el verificador de contexto exigido por AGENTS.

## Prevention

No invocar el hook ni usarlo como prueba de aceptación. Implementadores no publican; el principal prepara una lista explícita de archivos, revisa el índice y verifica contexto antes de Git. El comportamiento heredado permanece sin cambios: se necesita decisión explícita para desactivarlo o sustituirlo. Mientras siga activo, no ejecutar turnos de Claude concurrentes con cambios no revisados.

## Evidence

`.claude/settings.json`, `.claude/auto_save.sh`, `AGENTS.md`, `docs/architecture/AGENT_HARNESS.md`. Punto de revisión manual: inspeccionar archivos preparados inmediatamente antes del commit. Un validador de skills no protege por sí solo contra un hook de publicación.
