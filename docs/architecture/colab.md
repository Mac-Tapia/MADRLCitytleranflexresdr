# Preparación del nuevo entrenamiento para Google Colab

## Entregables

- Único notebook de entrenamiento: `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb`.
  Piloto, HPO, confirmación y sensibilidad usan este mismo cuaderno; solo cambia
  `RUN_STAGE` en la celda 7.2. No se guardan copias por etapa ("piloto", "oficial").
- Paquete de cambios y dataset: `outputs/colab_delivery/colab_modular_overlay.zip`.
- Generador reproducible del paquete: `python -B tools/colab/build_colab_bundle.py`.
- Pasos, puertas y limitaciones del piloto: [plan del módulo 8](../plans/modulo8_campana.md).

El cuaderno modular (`madrl_citylearn_v3_modular_colab.ipynb`) y su generador se
retiraron el 2026-11-28 por decisión del propietario; sus celdas de evaluación,
congelado, análisis y entrega ya están en el tutorial (C9, C8, C10, C11).

El botón **Open in Colab** del tutorial abre la revisión publicada en GitHub. El
tutorial también se puede abrir localmente en VS Code y ejecutar con el kernel de
Colab. Llama a la CLI `uc3m.application.training.cli` y sincroniza los intentos
finalizados.
El ZIP lleva las fuentes, las configuraciones y el dataset congelado, con el hash de cada
archivo. La celda 1.2 hace checkout del commit del paquete, así que ese commit
y los de los submódulos deben estar publicados.
No contiene entornos virtuales, salidas de entrenamiento ni perfiles de navegador.

## Usar el tutorial

1. Abre **Open in Colab** con la cuenta Pro. En un entorno con GPU, ejecuta
   **0.verify** y **1.1** para comprobar la memoria antes de instalar.
2. Sube `colab_modular_overlay.zip` a `/content` y continúa con **1.2**.
3. Monta Drive en **1.5**, restaura los intentos en **2.1** y revisa los
   recursos en **7.1** y **7.2**. El entrenamiento está desactivado por defecto.
4. Elige `RUN_STAGE` en **7.2** (`pilot`, `hpo`, `confirm` o `sensitivity`) y revisa
   el plan que imprime: presupuesto, recursos medidos y trabajadores por fase.
5. Con la decisión escrita del propietario para esa etapa, pon `EXECUTE_STAGE = True`
   y escribe la referencia en `OWNER_DECISION`. Esto pasa `--owner-authorized` a la CLI.
   La ejecución normal de todas las celdas prepara, pero no lanza entrenamiento.
   Al terminar, vuelve a `EXECUTE_STAGE = False` y `OWNER_DECISION = ''`.

La primera reconstrucción usa el commit del paquete. No se cambia de revisión
ni se borra un checkout preexistente incompatible; en ese caso usar un runtime
limpio. Cada corrida registra argumentos nativos, dataset y fuentes por hash.

## Recursos

Episodios de 8760 pasos, cuatro algoritmos y los tratamientos de cada etapa
(`configs/experiments/iquitos.yaml`). Se mantiene la agrupación por fases: HAPPO+MASAC
y después MATD3+MAAC. `uc3m/application/training/phases.py` calcula los trabajos
simultáneos con las CPU, la RAM y la VRAM medidas: cada trabajador reserva el mayor
requisito de su fase, según `configs/algorithms/native.yaml`.

Ese reparto no recorta buffers ni capacidad. Si los recursos no alcanzan, la fase queda
con 0 trabajadores y la etapa se detiene incompleta. Los requisitos son estimaciones y no
prueban ausencia de OOM: CUDA, buffers en CPU y fragmentación deben validarse en el runtime
real. La celda 7.2 guarda el pico de VRAM de la etapa, pero el piloto no alcanza el lote de 32
episodios de MASAC. No mezclar estadísticas de tratamientos con hiperparámetros efectivos
distintos.

MASAC pide 50 GiB de RAM y 74 GiB de VRAM, así que la campaña necesita una GPU que
ofrezca esa memoria. El cuaderno indica Colab Pro con RAM alta. La disponibilidad, tipo de GPU y
tiempo de sesión no están garantizados por Colab:
https://research.google.com/colaboratory/faq.html .

## Fronteras y estado real

Colab/Drive se habilitan por la petición explícita del usuario como destino
opcional; no se reinstalan sus MCP ni se hacen obligatorios para las pruebas
locales. Son servicios externos, no componentes que se declaren software OSI.
Las pruebas locales no necesitan cuenta ni suscripción; el entrenamiento de esta
campaña se ejecuta solo en Colab.

En desarrollo rige exclusivamente D:/MADRLCitytleranflexresdr. En Colab se
autoriza exclusivamente /content/MADRLCitytleranflexresdr con el mismo origin;
la entrada Linux no intenta ejecutar PowerShell. No se usa otro proyecto.

Probado localmente: construcción de argumentos 4×3, presupuesto de recursos,
identidad, compilación de todas las celdas, preservación de fuentes y smokes
nativos de los cuatro algoritmos. NO ejecutado todavía en un runtime real de
Colab: instalación de wheels, GPU/CUDA, bloqueo sobre Drive y reanudación tras
desconexión real. Aquí «reanudación» significa repetir desde cero lo interrumpido y
reutilizar los intentos verificados. La celda 2.1 comprueba campaña, dataset y fuentes antes de
lanzar. Ninguna celda del cuaderno prueba el bloqueo de Drive: la prueba es una celda
temporal descrita en la sección 5.4 del plan del módulo 8.

La preparación no demuestra paridad de optimizador/RNG/replay, validez de una
campaña multisemilla ni un mejor modelo final. El manifiesto mantiene esos
pendientes explícitos y no los cierra con un smoke.
