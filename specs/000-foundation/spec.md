# SPEC-000 — Constitución y línea base

**Estado:** aprobado para implementación  
**Ámbito:** `D:\MADRLCitytleranflexresdr`  
**Exclusión absoluta:** `D:\madrl_lima`  
**Entrada auditable:** `data/audits/modernization_baseline.json`

## Propósito

Establecer una línea base inmutable y las reglas que permiten reestructurar el proyecto completo por módulos sin perder trabajo, evidencia ni compatibilidad de entrenamiento.

## Requisitos funcionales

- **FR-001 — Identidad:** capturar raíz, origin, rama y commit; cualquier raíz o remoto distinto debe fallar.
- **FR-002 — Custodia:** contar cambios versionados y no versionados sin limpiar, mover ni leer secretos.
- **FR-003 — Dependencias:** registrar commit y estado de cada submódulo sin inferir licencias.
- **FR-004 — Integridad:** calcular SHA-256 y tamaño de archivos canónicos declarados.
- **FR-005 — Arquitectura:** exigir flujo modular dataset → validación → entrenamiento → evaluación → selección → entrega.
- **FR-006 — Trazabilidad:** todo corte posterior debe enlazar spec, plan, tareas, pruebas y manifiestos.
- **FR-007 — Apertura:** bloquear dependencias requeridas cerradas, de pago, suscripción o licencia desconocida.

## Criterios de aceptación

1. El manifiesto usa esquema `1.0` y no contiene valores de tokens o secretos.
2. La constitución contiene los diez principios aprobados.
3. Plan y tareas consumen la misma línea base y no autorizan `D:\madrl_lima`.
4. Ningún cambio en `CityLearn/` o `external/` se realiza en SPEC-000.
5. Las pruebas de consistencia y captura pasan en Python 3.9.
