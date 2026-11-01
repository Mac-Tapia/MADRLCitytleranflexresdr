# Entrenamiento modular local

## Entradas y límites

Usar Python de `.venv39-citylearn-v3`. No se requieren nube, cuentas ni
suscripciones. El panel es un monitor local de lectura, no un servicio expuesto.
La demo Streamlit existente se conserva separada.

La nueva entrada es `python -m uc3m.application.training.cli`, no el bucle
experimental antiguo de `uc3m.train` que usa acciones aleatorias. No se ha
promovido ese bucle como entrenador válido.

## Preparar y ejecutar

```powershell
& '.venv39-citylearn-v3/Scripts/python.exe' -m uc3m.application.training.cli --algorithm HAPPO --scenario E1 --schema CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json --episodes 50 --seed 0
```

Por defecto solo escribe un plan; no consume entrenamiento. Añadir `--execute`
para lanzar el backend nativo. Añadir `--resume` para una identidad ya existente.
Cada combinación de algoritmo, escenario, semilla, horizonte, dataset, commits
y código local tiene carpeta propia. No reutilizar corridas históricas por nombre.

Los cuatro algoritmos admitidos son HAPPO, MASAC, MATD3 y MAAC. E1–E3 usan el
catálogo canónico con tarifa constante; los lanzadores antiguos sin la variable
UC3M_SCENARIO_CATALOG conservan las tarifas compuestas históricas. Tratamientos
de pesos alternativos y restricciones deshabilitadas son rechazados por el
adaptador hasta verificar su semántica nativa.

Un smoke usa `--episodes 1 --episode-time-steps 8` y una raíz separada. MATD3
llena primero su búfer: puede ejecutar numerosos episodios de calentamiento.
MAAC puede no alcanzar su umbral de actualización con un episodio corto. Un
smoke prueba construcción, recorrido y artefactos; no demuestra aprendizaje.

## Monitor

```powershell
& '.venv39-citylearn-v3/Scripts/python.exe' -m uc3m.presentation.training_panel --output-root outputs/modular_training --port 18765
```

Abrir http://127.0.0.1:18765 . El puerto predeterminado 8765 puede estar
reservado en Windows; seleccionar otro puerto no requiere modificar seguridad.
El panel no permite iniciar procesos ni servir archivos arbitrarios.

## Recuperación y pruebas

El bloqueo de corrida pertenece al sistema operativo y se libera si muere el
proceso. Reanudar requiere identidad coincidente y archivos íntegros. Una corrida
RUNNING interrumpida puede recuperar archivos durables nuevos; una VERIFIED
alterada nunca se rehashea para ocultar corrupción. Solo cargar checkpoints
locales de confianza: algunos formatos nativos usan serialización pickle.

La precarga actual vuelve a materializar filas históricas para mantener el
contador coherente: evita perder episodios, pero consume memoria proporcional
al histórico. Optimizarla sin perder filas requiere un corte posterior.

Ejecutar `scripts/quality/run_orchestration_gates.ps1` para las pruebas y la
auditoría de smoke. Estado verified significa integridad técnica de corrida,
no superioridad científica. El ganador requiere campaña multisemilla,
evaluación independiente, baselines, Pareto y pruebas estadísticas.

## Sustento y alcance

Pineau et al. (2021), *JMLR, 22*, https://www.jmlr.org/papers/v22/20-303.html,
fundamentan trazabilidad experimental. Charbonnier (2023), tesis doctoral,
https://doi.org/10.5287/ora-ovzyxredj, y Costea (2026), tesis de maestría,
https://webthesis.biblio.polito.it/40396/, sustentan evaluación de coordinación
energética y KPI. Estas fuentes no certifican este código ni prescriben sus
pesos numéricos, bloqueo de procesos o diseño de frontend.
