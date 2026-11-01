# Plan — SPEC-000

**Entrada:** `data/audits/modernization_baseline.json`  
**Repositorio:** `D:\MADRLCitytleranflexresdr`  
**Repositorio prohibido:** `D:\madrl_lima`

## Correspondencia de requisitos

| Requisito | Implementación | Verificación |
|---|---|---|
| FR-001 | `tools/ops/capture_modernization_baseline.py` | rechazo de raíz/remoto inesperado |
| FR-002 | conteo de `git status --porcelain` | prueba sobre repositorio real |
| FR-003 | inventario `git submodule status --recursive` | SHA-1 y rutas relativas |
| FR-004 | hash de lista canónica acotada | SHA-256 y tamaño |
| FR-005 | constitución y specs posteriores | puertas end-to-end de entrenamiento |
| FR-006 | estructura `.specify/` y `specs/` | prueba contractual |
| FR-007 | SPEC-001 y política abierta | puerta de fundación |

## Secuencia

1. Capturar línea base sin mutar Git.
2. Ratificar constitución.
3. Implementar política open source y auditorías.
4. Ejecutar puerta local de fundación.
5. Permitir SPEC-002 únicamente cuando el manifiesto no oculte bloqueos.
