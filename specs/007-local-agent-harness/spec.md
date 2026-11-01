# SPEC-007 — Skills abiertos y harness local

Estado: instalación implementada; aceptación de comportamiento/eficiencia parcial.
Deriva del [diseño aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md), sin sustituir las tareas de tesis o campaña.

## Requisitos

- FR-007.1: fuente canónica local `tools/skills/`, sin instalaciones globales de proyecto ni duplicados activos.
- FR-007.2: inventario de cada skill con fuente fijada a commit, licencia abierta y hashes de todos sus archivos distribuibles. Rechazar inventario vacío, rutas externas, nombres duplicados, cambios de hash y skills no registrados.
- FR-007.3: descubrimiento de una única copia mediante enlaces locales de Codex/Claude; rechazar enlaces sobrantes o desviados, sin eliminar contenidos ajenos.
- FR-007.4: cubrir backend, frontend, arquitectura, despliegue, pruebas y harness sin contratar servicios, instalar runtime/frameworks o autorizar exposición remota implícitamente.
- FR-007.5: separar implementador, auditor de solo lectura y coordinador. Encargos con requisito, propiedad de archivos y evidencia, no escritura concurrente ni auto-publicación.
- FR-007.6: mantener pendientes de migración/licencias de skills legados, decisión del hook heredado, invocación real en clientes y medición de eficiencia. La validación estática no cierra esas puertas.

## Aceptación

Pruebas del registro y validación bidireccional de fuentes/enlaces pasan; fuentes y licencias quedan versionadas. Para cerrar el SPEC deben añadirse sesiones reales de invocación en ambos clientes, un ensayo de roles sin conflictos ni escrituras de auditor y comparación medida de tiempo/costo/retrabajo frente a línea base. No se exige suscripción nueva ni se cambian configuraciones globales.

Fundamento, fuentes APA y límites científicos: [AGENT_HARNESS.md](../../docs/architecture/AGENT_HARNESS.md). Estos estudios justifican reproducibilidad y evaluación; no certifican rendimiento de los skills.
