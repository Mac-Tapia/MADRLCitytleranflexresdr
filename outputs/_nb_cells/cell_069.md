## Proximos pasos y referencias

### Para el entrenamiento de 50 episodios por corrida en A100 (reanudable)
1. Si Colab se desconecta, vuelve a ejecutar las celdas de configuracion y la celda **7.2**.
   `--skip-completed` evita repetir jobs ya completados y reanuda los jobs interrumpidos desde el ultimo checkpoint hasta completar los 50 episodios.
2. Para revisar estado sin entrenar: `CityLearn/scripts/colab_a100_live_monitor.py --output-root <OUTPUT_ROOT> --once`.

### Artefactos generados por corrida (12 corridas principales)
```
{OUTPUT_ROOT}/
  happo/  masac/  matd3/  maac/
    E1 / E2 / E3 /
      data/
        training_summary.json  — hiperparametros + KPIs finales
        results.json           — artefactos completos
        timeseries.csv         — metricas por episodio
        rewards.csv            — reward por episodio (generado en 8.1)
        training_monitor.csv   — monitor consolidado (generado en 8.1)
        config.json            — configuracion de la corrida (generado en 8.1)
        resource_usage.csv     — uso de RAM/VRAM (generado en 7.7)
      checkpoints/             — modelos .pt por agente
      figures/                 — graficos de KPIs vs baseline
```

### Para validez estadistica fuerte
- Repetir con seeds adicionales (--seed 1, 2, ...) cuando haya presupuesto GPU.
- Para benchmarks comparativos CityLearn v2 (PPO, SAC, A2C): activar la celda 7.6. MAPPO y MADDPG no son baseline oficial ni parte de los 12 entrenamientos principales.

### Repositorio
[Mac-Tapia/CityLearn](https://github.com/Mac-Tapia/CityLearn)
Tesis: *Diseno y validacion de un sistema electrico inteligente con control multiagente MADRL, Iquitos 2026*
Contacto: mac.tapia@unmsm.edu.pe
