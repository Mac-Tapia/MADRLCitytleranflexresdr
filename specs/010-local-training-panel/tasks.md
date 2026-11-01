# Tareas — SPEC-010

Contrato: [spec.md](spec.md). Ejecución: [plan.md](plan.md).
Conciliación: [STATUS.md](../STATUS.md).

## Implementación acreditada por archivos y prueba local

- [x] Separar lectura/validación en `uc3m/application/training/monitor.py`.
- [x] Implementar monitor HTTP de lectura en `uc3m/presentation/training_panel.py`.
- [x] Mantener GET `/` y `/api/runs`, sin lanzamiento ni servidor de archivos arbitrarios.
- [x] Limitar escucha a `127.0.0.1` y preservar la demo de inferencia existente.
- [x] Ejecutar `tests/integration/test_training_panel.py` y `tests/contract/test_spec_kit_consistency.py`: conjunto de tres pruebas aprobado el 2026-10-31.
- [x] Crear plan y tareas enlazados con el índice de estado.

Los checks acreditan estado presente, no RED histórico ni commits individuales.
No se declara aquí una revisión visual nueva o campaña científica.

## Pendientes fuera del cierre operativo

- [ ] Registrar aceptación visual reproducible cuando cambie HTML/contrato de datos.
- [ ] Incorporar evidencia de campaña completa cuando exista; no reinterpretar smokes.
- [ ] Evaluar nuevas necesidades de UI mediante otro corte; acceso remoto, escritura y lanzamiento HTTP quedan fuera de SPEC-010.

Colab real, reanudación exacta, modelo ganador y jurado conservan pendientes
independientes en [STATUS.md](../STATUS.md).
