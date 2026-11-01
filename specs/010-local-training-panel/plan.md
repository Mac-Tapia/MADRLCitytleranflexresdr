# Plan — SPEC-010: monitor local de entrenamiento

Contrato: [spec.md](spec.md). Estado global: [STATUS.md](../STATUS.md).

## Diseño implementado

`uc3m/application/training/monitor.py` lee manifiestos y verifica archivos.
`uc3m/presentation/training_panel.py` publica GET `/` y `/api/runs` con
biblioteca estándar en `127.0.0.1`. HTML sin CDN, datos como texto y sin
descarga de rutas arbitrarias. La CLI conserva el mando de ejecución;
la demo Streamlit de inferencia no se modifica.

## Verificación y límites

La prueba HTTP real usa puerto efímero. Un estado `verified` acredita el
contrato operativo del manifiesto, no aprendizaje, significancia estadística,
aceptación energética o mejor modelo. No habilitar acceso remoto, escritura
o lanzamiento HTTP en este corte.

Desde la raíz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
.venv39-citylearn-v3/Scripts/python.exe -m pytest -q tests/integration/test_training_panel.py tests/contract/test_spec_kit_consistency.py
```

Resultado observado el 2026-10-31: tres pruebas aprobadas en ese conjunto
(monitor HTTP y consistencia SPEC-000). No es la suite completa. Una revisión
visual nueva es independiente y no se sustituye por HTTP 200.

## Operación

```powershell
.venv39-citylearn-v3/Scripts/python.exe -m uc3m.presentation.training_panel --output-root outputs/modular_smoke --port 18765
```

Puerto y servidor dependen de la sesión local. No se añade autoinicio, túnel,
publicación o autenticación de producción. Colab usa su monitor embebido y
necesita aceptación separada.

## Sustento

Fuentes verificadas y referencias APA en [STATUS.md](../STATUS.md):
Costea (2026), Charbonnier (2023) y Pineau et al. (2021) fundamentan separar
evaluación y reproducibilidad. La arquitectura concreta es una decisión
local, no una prescripción ni garantía de esas investigaciones.
