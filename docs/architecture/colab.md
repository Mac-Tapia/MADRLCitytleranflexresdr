# Preparación del nuevo entrenamiento para Google Colab

## Entregables

- Notebook nuevo: `examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb`.
- Paquete de cambios y dataset: `outputs/colab_delivery/colab_modular_overlay.zip`.
- Generador reproducible: `python -B tools/colab/build_modular_colab_notebook.py`.
- Pasos, puertas y limitaciones del piloto: [plan del módulo 8](../plans/modulo8_campana.md).

El tutorial original se conserva, pero esta campaña no lo usa. El cuaderno modular
reutiliza su celda de instalación Python 3.9, con dependencias fijadas, y llama a la
CLI `uc3m.application.training.cli` y a `uc3m.application.pipeline`.
El ZIP lleva las fuentes, las configuraciones y el dataset congelado, con el hash de cada
archivo. La celda C1 clona GitHub y hace checkout del commit del paquete, así que ese commit
y los de los submódulos deben estar publicados.
No contiene entornos virtuales, salidas de entrenamiento ni perfiles de navegador.

## Uso

1. Subir el notebook a Colab mediante Archivo → Subir notebook.
2. Seleccionar acelerador GPU disponible y ejecutar la primera celda; cuando
   lo solicite, subir `colab_modular_overlay.zip`.
3. Ejecutar la instalación original de Python 3.9 y dependencias.
4. Autorizar el montaje de tu Drive para los intentos y resultados.
5. Elegir `STAGE` en C5 y revisar el plan que imprime: presupuesto de la etapa,
   recursos medidos y trabajadores por fase.
6. Con la decisión escrita del propietario para esa etapa, poner `EXECUTE_STAGE = True`
   en C6. Esto pasa `--owner-authorized` a la CLI. La ejecución normal de todas las
   celdas prepara, pero no lanza entrenamiento.

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
real. C6 guarda el pico de VRAM de la etapa, pero el piloto no alcanza el lote de 32
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
reutilizar los intentos verificados. C3 comprueba campaña, dataset y fuentes antes de
lanzar. Ninguna celda del cuaderno prueba el bloqueo de Drive: la prueba es una celda
temporal descrita en la sección 5.4 del plan del módulo 8.

La preparación no demuestra paridad de optimizador/RNG/replay, validez de una
campaña multisemilla ni un mejor modelo final. El manifiesto mantiene esos
pendientes explícitos y no los cierra con un smoke.
