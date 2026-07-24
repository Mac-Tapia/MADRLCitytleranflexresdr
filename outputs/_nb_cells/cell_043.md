### 6.2 Prueba rápida de validación — 1 episodio por algoritmo

> **SOLO PARA VERIFICAR QUE EL PIPELINE FUNCIONA.**
> No usar como resultado de entrenamiento.
> El entrenamiento oficial usa **N_EPISODES = 50** por corrida (celda 7.2), reanudable con `--skip-completed`.

Esta prueba ejecuta **1 episodio corto de 168 pasos horarios** por algoritmo y escenario
para validar:

- que el launcher, los scripts y los módulos cargan correctamente;
- que CityLearn v3 conecta con el dataset Iquitos 2023-2025;
- que los hiperparámetros son aceptados por los backends HARL/off-policy;
- que el monitor genera artefactos (`results.json`, `training_summary.json`).

**No ejecutar esta celda para producción.** Pasar directamente a la Sección 7.
