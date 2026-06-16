# deploy/ — Demo de despliegue (Docker + AWS) y camino a producción física

Implementa la Fase 8 de `docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`:
un demo de operatividad para el mejor agente MADRL seleccionado
(checkpoint ganador entre HAPPO/HARL, MASAC, MATD3, MAAC sobre los
escenarios E1/E2/E3), con un camino claro hacia producción y despliegue
físico en campo.

## Componentes

```
deploy/
├── inference/        # Servicio de inferencia (FastAPI + ONNX Runtime)
├── plant-adapter/     # Adaptador planta <-> servicio (replay / Modbus / OPC-UA / MQTT)
├── dashboard/         # Dashboard de monitoreo (Streamlit)
├── docker-compose.yml         # Stack local (laptop / servidor on-prem)
├── docker-compose.aws.yml     # Variante para ECS Fargate / EC2
├── aws/iac/            # Infraestructura como código (Terraform) para AWS
├── aws/README_DEPLOY_AWS.md   # Guía de despliegue en AWS
├── aws/README_TRAINING_AWS.md # Manual de entrenamiento AWS desde cero
├── aws/iac-training/          # Terraform EC2 GPU para entrenamiento
├── aws/training/              # Bootstrap, launcher, monitor y sync S3
├── edge/README_DESPLIEGUE_FISICO.md  # Puente a despliegue físico (EMS/BMS real)
└── .env.example
```

## Arquitectura

```
                 +-------------------+
                 |  inference-service |  FastAPI + ONNX Runtime
                 |  (modelo MADRL     |  POST /act  {observations} -> {actions}
                 |   ganador)         |  GET  /health, /model/info
                 +---------+---------+
                           ^
                           | HTTP (acciones/observaciones)
                           v
+----------------+   +-----+------+   +-------------------+
|  CityLearn      |   |  plant-    |   |  dashboard-service |
|  replay / o     |<->|  adapter   |-->|  (Streamlit)       |
|  planta real    |   |  (Modbus/  |   |  KPIs en vivo      |
|  (EMS/BMS)      |   |   OPC-UA/  |   +-------------------+
+----------------+    |   MQTT)    |
                       +------------+
```

## Estado de esta fase

Esta es una pasada de **scaffolding local**: código funcional mínimo,
Dockerfiles y plantillas de IaC, pero **sin ejecutar** `docker build`,
`docker compose up`, ni `terraform apply` (requieren Docker Desktop y
credenciales AWS del usuario). Ver cada subcarpeta para detalles y los
pasos 8.1-8.7 del plan original.

## Selección del modelo a desplegar

El `model_loader.py` espera un checkpoint exportado a ONNX desde el run
canónico (`outputs/latest_visible_training_output_root.txt` ->
`data/checkpoint_manifest.json`). Una vez que las 12 corridas
(4 algoritmos x 3 escenarios E1/E2/E3) terminen y se seleccione el mejor
agente vía `KPIEvaluator`/HPHI, exportar su checkpoint con
`tools/export_winning_model_onnx.py` (pendiente de implementar — ver
`deploy/inference/model_loader.py` para el contrato esperado del export).

## Entrenamiento en AWS

El entrenamiento GPU en AWS esta documentado en
`deploy/aws/README_TRAINING_AWS.md`. Ese flujo es independiente del stack de
inferencia: crea/usa una instancia EC2 GPU, prepara `.venv39-citylearn-v3`,
valida dataset y backends, lanza HAPPO/MASAC/MATD3/MAAC y guarda resultados en
`outputs/aws_citylearn_v3_madrl_*` con sincronizacion opcional a S3.
