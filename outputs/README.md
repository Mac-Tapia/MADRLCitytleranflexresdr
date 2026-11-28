# outputs/

Salidas locales de la campaña nueva. Nada de aquí es evidencia de entrenamiento
hasta que la CLI lo registre como intento verificado. Los resultados de campañas
anteriores se retiraron el 2026-11-01 (ver `specs/STATUS.md`).

```
outputs/
  README.md
  campaigns/<alias>/              # manifiestos de la campaña (CLI --stage prepare) e intentos
    campaign.json
    campaign_manifest.json
    stages/{pilot,hpo,confirm,sensitivity}.json
  colab_delivery/<alias>/         # paquete para Colab (no versionado, .gitignore)
    colab_modular_overlay.zip
```

- Campaña vigente: `configs/experiments/iquitos.yaml` (`storage_alias` = `iquitos_factura_v8`; dataset `iquitos_v6_trial13`).
- Único cuaderno de entrenamiento: `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb`.
  Piloto y etapas oficiales usan el mismo cuaderno; no se guardan copias por etapa aquí.
- El ZIP lo genera `python -B tools/colab/build_colab_bundle.py`. No se regenera durante
  una campaña preparada: cambiar las fuentes cambia su identidad.
- En Colab, los intentos terminados se copian a Drive (`MyDrive/MADRL_campaigns/`).

No van aquí:

- Temporales de pruebas (`pytest --basetemp`): usar `%TEMP%` o `.tmp/`.
- Auditorías de dataset: `data/dataset_audit/`.
- Caché CSV: `data/cache/` (no versionar).
