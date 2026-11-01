# Constitución del proyecto MADRL–CityLearn Iquitos

**Versión:** 1.0.0  
**Ratificada:** 2026-10-31  
**Ámbito obligatorio:** `D:\MADRLCitytleranflexresdr`  
**Fuera de alcance:** `D:\madrl_lima`

## Principios no negociables

1. **Código abierto verificable:** toda dependencia requerida debe declarar una licencia OSI compatible; una licencia ausente, ambigua o propietaria bloquea su integración.
2. **Local primero:** construcción del dataset, entrenamiento, evaluación, selección y entrega deben funcionar localmente sin SaaS, pago o suscripción.
3. **Dependencias externas aisladas:** `CityLearn/` y `external/` se consumen mediante adaptadores y solo cambian con autorización explícita y registro de contribución.
4. **Una decisión, una fuente:** dataset, ejes, pesos, tarifas, restricciones, semillas y estados se definen una vez y se proyectan hacia backend, launchers, interfaz y tesis.
5. **Recompensa no equivale a aceptación:** el retorno no reemplaza KPI físicos, ambientales, económicos, de seguridad ni de servicio EV/BESS.
6. **Resultados históricos inmutables:** cada resultado conserva dataset, commit, submódulos, política, semilla y hashes; no se reetiqueta para una política nueva.
7. **Fallo cerrado:** configuración incompleta, licencia desconocida, hash ausente, artefacto faltante, fuga temporal o inferencia inválida impiden promoción.
8. **Pruebas proporcionales al riesgo:** dominio, dataset, contratos, backends, integración, artefactos, selección y entrega tienen puertas separadas sin `skip` o `xfail` como aceptación.
9. **Sin secretos en el repositorio:** tokens, credenciales, perfiles OAuth y sesiones viven fuera del árbol; las auditorías nunca imprimen sus valores.
10. **Especificación antes del cambio:** cada corte atraviesa `Specify → Clarify → Plan → Tasks → Analyze → Implement → Converge` y enlaza requisito, prueba y evidencia.

## Arquitectura obligatoria

El sistema evoluciona como monolito modular con dominio independiente, aplicación, puertos y adaptadores. El flujo de nuevo entrenamiento se considera integral únicamente cuando recorre:

`dataset → validación → escenarios → entrenamiento → artefactos → KPI/estadística → selección del mejor MADRL → paquete de entrega`.

Cada etapa consume contratos versionados, emite un manifiesto y puede bloquear la siguiente. El frontend o panel local solo consulta backend y manifiestos; no redefine pesos, estados ni resultados.

## Gobierno y cambio

- La especificación aprobada prevalece sobre planes y tareas.
- Una excepción requiere ADR, evidencia, prueba y aprobación explícita; nunca se aplica de forma silenciosa.
- Los estados válidos son `implemented`, `verified`, `partial`, `blocked`, `pending` y `rejected`.
- Solo `verified` puede promoverse como evidencia científica o mejor modelo entregable.
- Toda modificación u operación Git se precede con `scripts/verify_project_context.ps1`.

## Cumplimiento

Las puertas locales son autoritativas y CI solo las refleja. Una salida exitosa de proceso, convergencia numérica o archivo existente no demuestra por sí sola completitud científica, operativa o documental.
