# Entrega integral al auditor local

Fecha: 2026-10-31. Repositorio exclusivo: `D:/MADRLCitytleranflexresdr`.
Origen esperado: `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`.
Rama de entrega: `codex/fix-madrl-traceability-docs`.
Base anterior a este corte: `236f98f00dc29e56fa2cb70eeb6659f82b32813c`.

## Qué se conserva

Por solicitud expresa del usuario se incluyen todos los cambios y archivos nuevos versionables del repositorio principal, no solo los creados en la instalación de skills. Incluye fuentes, documentos, resultados, respaldos y temporales no ignorados para evitar perder el contexto del auditor. Un commit de conservación **no aprueba la validez científica ni atribuye la autoría de cada cambio a este agente**. Auditar el diff completo desde la base indicada.

Se instalaron siete skills de terceros MIT/Apache-2.0 y cuatro propios, con fuente fijada y hashes; tres perfiles Claude y enlaces de descubrimiento locales. Ver `tools/skills/registry.yaml`, `docs/architecture/AGENT_HARNESS.md` y `specs/007-local-agent-harness/`. Los enlaces son locales e ignorados: regenerarlos con `scripts/skills/register_local_skills.ps1` tras clonar. No se instalaron servicios de pago, suscripciones, MCP remotos ni frameworks por añadir skills.

## Verificación ejecutada

- Suite principal `python -m pytest`: 307 aprobadas, 15 advertencias y ninguna omisión, 313.65 s.
- Corte skills/SPEC/panel: 12 aprobadas; registro y descubrimiento local verificados. Tras ajuste menor de formato/hash, nueve pruebas de skills repetidas y aprobadas.
- Revisión independiente detectó dos fallos de gobernanza del registro; corregidos y cubiertos por pruebas negativas.
- Ruff sobre validador y tests de skills: sin hallazgos.
- Inventario previo a la conservación: aproximadamente 860 MiB de cambios/archivos nuevos, ningún archivo individual mayor de 100 MiB. Búsqueda de patrones de credenciales sin indicios; no sustituye auditoría exhaustiva de seguridad. ZIP Colab revisado por nombres de entradas sensibles sin coincidencias.

Las pruebas no equivalen a render nuevo de los DOCX, aceptación de todos los resultados históricos, entrenamiento largo ni mejor modelo validado.

## Exclusiones protegidas y límites de custodia

No se fuerzan archivos ignorados: entornos, credenciales, perfiles de navegador, cachés, pesos/checkpoints y datos grandes siguen sus exclusiones existentes. Se preservan localmente, no se borran. Los manifiestos de smokes quedan en Git; sus checkpoints ignorados no quedan por ello publicados ni disponibles al clonar. El auditor local puede revisarlos en sus rutas originales con las precauciones de confianza correspondientes.

No se modifican ni se confirman contenidos dentro de dependencias externas. En `external/MAAC` se observó únicamente un temporal no rastreado `.git_commit_msg.tmp`; no es código pendiente del repositorio principal. No se alteró para simular limpieza del checkout.

## Pendientes que el auditor debe mantener abiertos

1. `specs/STATUS.md`: licencias/procedencia aún bloqueadas, reportes completos, continuidad de optimizador/RNG/replay y cancelación de hijos.
2. Validación real de instalación/CUDA/Drive y desconexión/reanudación en Colab; no confundir el notebook preparado con entrenamiento ejecutado.
3. Campaña multisemilla de horizonte completo, evaluación independiente, selección/entrega del mejor modelo y promoción de evidencia.
4. Consistencia documental única de §3.1.3, APA, render de ambos DOCX y observaciones J-01–J-17.
5. Invocación real de skills en nuevas sesiones de Codex/Claude, eficiencia medida y migración segura de skills legados.
6. El Stop hook heredado de Claude autoagrega y publica todo; continúa sin cambios y requiere decisión explícita antes de usar Claude de forma concurrente. Véase `docs/failures/agent-auto-publish-unscoped.md`.

Sustento científico, fuentes primarias APA y límites de las inferencias: `docs/architecture/AGENT_HARNESS.md`. Las fuentes sustentan reproducibilidad y evaluación; no prueban coeficientes exactos, ganancias de agentes ni cierre de tesis.
