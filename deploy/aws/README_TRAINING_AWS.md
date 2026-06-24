# Manual de entrenamiento MADRL en AWS desde cero

Este manual deja el proyecto listo para levantar una instancia GPU en AWS,
conectarse desde Windows usando PuTTY/WinSCP y ejecutar el entrenamiento
CityLearn v3 MADRL de los 4 algoritmos: HAPPO, MASAC, MATD3 y MAAC.

Repositorio esperado:

```text
https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
```

## 1. Alcance

Entrenamiento canonico:

- Dataset del proyecto: `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` (17 edificios, 2023-2025, 26304 pasos horarios).
- Schema usado por AWS: `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` — declarado en `deploy/aws/training/run_aws_training.sh` linea 8 como `SCHEMA_PATH` y pasado via `--schema-path` a cada script de entrenamiento; no se sobreescribe por `docker-compose.yml` ni el `Dockerfile`.
- Insumos trazables de facturas/buildingcsv: `CityLearn/data/buildingcsv/`.
- Escenarios: `E1`, `E2`, `E3`.
- Algoritmos: `happo`, `masac`, `matd3`, `maac`.
- Episodios: `75`.
- Pasos por episodio: `8760`.
- Salidas: `outputs/aws_citylearn_v3_madrl_<timestamp>/`.
- Estado visible: `official_full_status.json`, logs por algoritmo,
  `live_progress.json` por corrida y salida viva en `docker logs`.
- El arbol `algoritmo/escenario_seed_0` se crea al iniciar la corrida para
  todos los escenarios planificados; los artefactos `data/results.json`,
  `checkpoints/` y `figures/` aparecen cuando cada job avanza o finaliza.
- Logs en texto plano rotados automaticamente cada 10 MB (configurable con
  `--log-chunk-size`) y con retencion configurable (default:
  `--log-max-files 100`): `logs/<escenario>_<algoritmo>-00001.log`,
  `00002.log`, etc. en vez de un solo archivo que crece sin limite.
- Tambien se puede ejecutar empaquetado en Docker / Docker Compose (ver
  seccion 15) sin instalar Python directamente en la instancia.

La infraestructura de inferencia de `deploy/aws/iac` se mantiene separada.
Para entrenamiento GPU se usa `deploy/aws/iac-training`.

## 2. Recomendacion de instancia

Para entrenamiento con CUDA use una AMI GPU con drivers NVIDIA ya instalados.
AWS documenta que las instancias G5 usan GPU NVIDIA A10G con 24 GB de memoria
por GPU, y que las instancias GPU necesitan driver NVIDIA o una AMI que ya lo
incluya.

Configuracion inicial recomendada:

- AMI: `Deep Learning OSS Nvidia Driver AMI GPU PyTorch` o `Deep Learning AMI GPU PyTorch`.
- Sistema: Ubuntu 22.04 o Ubuntu 24.04 x86_64.
- Instancia: `g5.xlarge` para una corrida a la vez.
- Instancia para paralelo: `g5.2xlarge` o mayor, validar costo y cuota antes.
- Disco EBS: `300 GiB` minimo, `500 GiB` si se guardan trazas completas.

Referencias oficiales:

- EC2 G5: <https://aws.amazon.com/ec2/instance-types/g5/>
- Drivers NVIDIA en EC2: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/install-nvidia-driver.html>
- Deep Learning AMI PyTorch: <https://docs.aws.amazon.com/dlami/latest/devguide/tutorial-pytorch.html>
- Conexion PuTTY desde Windows: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-linux-inst-from-windows.html>

## 3. Crear llave para PuTTY y WinSCP

1. En AWS EC2 cree o seleccione un `Key pair`.
2. Si descarga `.pem`, abra PuTTYgen en Windows.
3. Use `Load` y seleccione el `.pem`.
4. Use `Save private key` y guarde un `.ppk`.
5. Ese `.ppk` se usa tanto en PuTTY como en WinSCP.

## 4. Provisionar EC2 con Terraform

Desde su maquina Windows, con AWS CLI y Terraform instalados:

```powershell
cd D:\MADRLCitytleranflexresdr\deploy\aws\iac-training
terraform init
terraform plan `
  -var "aws_region=us-east-1" `
  -var "key_pair_name=SU_KEY_PAIR_EC2" `
  -var "ami_id=AMI_GPU_DEEP_LEARNING_ACTUAL" `
  -var "allowed_ssh_cidr=SU_IP_PUBLICA/32"
terraform apply `
  -var "aws_region=us-east-1" `
  -var "key_pair_name=SU_KEY_PAIR_EC2" `
  -var "ami_id=AMI_GPU_DEEP_LEARNING_ACTUAL" `
  -var "allowed_ssh_cidr=SU_IP_PUBLICA/32"
```

Notas:

- No use `0.0.0.0/0` para SSH salvo prueba temporal controlada.
- El `ami_id` debe ser de una AMI GPU actual en la misma region.
- Al terminar, anote `training_public_ip` y `training_ssh_user`.

## 5. Entrar por PuTTY

En PuTTY:

- `Host Name`: `ubuntu@IP_PUBLICA`.
- `Port`: `22`.
- `Connection > SSH > Auth > Credentials > Private key file`: seleccione su `.ppk`.
- Guarde la sesion como `madrl-aws-training`.
- Abra la sesion.

Si la AMI no usa `ubuntu`, use el usuario que muestra `terraform output training_ssh_user`
o el usuario indicado por AWS para esa AMI.

## 6. Clonar el proyecto en EC2

En PuTTY, dentro de la instancia:

```bash
cd ~
git clone --recurse-submodules https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd MADRLCitytleranflexresdr
git submodule update --init --recursive
```

No use ZIP de GitHub para entrenamiento: el ZIP no trae submodulos completos.

## 7. Preparar entorno Python/CUDA

Ejecute el bootstrap:

```bash
cd ~/MADRLCitytleranflexresdr
bash deploy/aws/training/bootstrap_ubuntu_gpu.sh
```

El script:

- Instala herramientas base si hay `apt`.
- Crea `.venv39-citylearn-v3`.
- Instala el proyecto y `CityLearn/` en modo editable.
- Instala dependencias de entrenamiento.
- Instala PyTorch CUDA si `INSTALL_TORCH=1`.
- Ejecuta una verificacion basica de GPU y Torch.

Si la AMI ya trae PyTorch CUDA y quiere evitar reinstalarlo:

```bash
INSTALL_TORCH=0 bash deploy/aws/training/bootstrap_ubuntu_gpu.sh
```

Si necesita cambiar el wheel CUDA de PyTorch:

```bash
PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu126 \
bash deploy/aws/training/bootstrap_ubuntu_gpu.sh
```

## 8. Validar antes de entrenar

```bash
cd ~/MADRLCitytleranflexresdr
bash deploy/aws/training/check_aws_training_ready.sh
```

La compuerta revisa:

- Raiz del proyecto y submodulos externos.
- `schema.json`, dataset Iquitos y `CityLearn/data/buildingcsv`.
- Manifiesto de dataset listo.
- Importacion de los backends HAPPO/MASAC/MATD3/MAAC.
- CUDA visible por `nvidia-smi` y `torch.cuda`.

Si esta compuerta falla, no lance entrenamiento todavia.

## 9. Ejecutar entrenamiento visible con tmux

Abra una sesion persistente:

```bash
cd ~/MADRLCitytleranflexresdr
tmux new -s madrl
```

Dentro de `tmux`, lance la corrida canonica:

```bash
bash deploy/aws/training/run_aws_training.sh \
  --scenario ALL \
  --algorithms happo,masac,matd3,maac \
  --episodes 75 \
  --episode-time-steps 8760 \
  --max-parallel-jobs 1 \
  --log-chunk-size 10M \
  --log-max-files 100 \
  --cuda
```

Para una instancia mas grande, puede probar paralelo:

```bash
bash deploy/aws/training/run_aws_training.sh \
  --scenario ALL \
  --algorithms happo,masac,matd3,maac \
  --episodes 75 \
  --episode-time-steps 8760 \
  --max-parallel-jobs 2 \
  --log-chunk-size 10M \
  --log-max-files 100 \
  --cuda
```

Recomendacion: empiece con `--max-parallel-jobs 1` en `g5.xlarge`. Suba a `2`
solo si `nvidia-smi`, RAM y disco permanecen estables.

Para salir de `tmux` sin detener el entrenamiento:

```text
Ctrl+B, luego D
```

Para volver:

```bash
tmux attach -t madrl
```

## 10. Monitorear por PuTTY

En otra ventana PuTTY:

```bash
cd ~/MADRLCitytleranflexresdr
bash deploy/aws/training/tail_aws_training.sh
```

Tambien puede ver GPU:

```bash
nvidia-smi -l 10
```

El ultimo directorio de salida queda registrado en:

```text
outputs/latest_visible_training_output_root.txt
```

## 11. Usar WinSCP

Configure WinSCP:

- Protocolo: `SFTP`.
- Host: `IP_PUBLICA`.
- Usuario: `ubuntu`.
- Llave privada: el mismo `.ppk`.
- Directorio remoto recomendado: `/home/ubuntu/MADRLCitytleranflexresdr`.

Rutas utiles para descargar:

- `outputs/latest_visible_training_output_root.txt`
- `outputs/aws_citylearn_v3_madrl_*/official_full_status.json`
- `outputs/aws_citylearn_v3_madrl_*/logs/*.log`
- `outputs/aws_citylearn_v3_madrl_*/<algoritmo>/<escenario>_seed_0/training_summary.json`
- `outputs/aws_citylearn_v3_madrl_*/<algoritmo>/<escenario>_seed_0/data/`
- `outputs/aws_citylearn_v3_madrl_*/<algoritmo>/<escenario>_seed_0/checkpoints/`
- `outputs/aws_citylearn_v3_madrl_*/<algoritmo>/<escenario>_seed_0/figures/`

## 12. Sincronizar resultados a S3

Si usa el bucket creado por Terraform:

```bash
cd ~/MADRLCitytleranflexresdr
OUTPUT_ROOT=$(cat outputs/latest_visible_training_output_root.txt)
bash deploy/aws/training/sync_outputs_s3.sh "$OUTPUT_ROOT" "s3://NOMBRE_BUCKET_RESULTS/$(basename "$OUTPUT_ROOT")/"
```

Para bajar a Windows despues:

```powershell
aws s3 sync s3://NOMBRE_BUCKET_RESULTS/aws_citylearn_v3_madrl_FECHA/ D:\madrl_results\aws_citylearn_v3_madrl_FECHA\
```

## 13. Reinicio o reanudacion

Si se corta PuTTY, el entrenamiento sigue dentro de `tmux`.

```bash
tmux attach -t madrl
```

Si la instancia se reinicio, revise el ultimo estado:

```bash
cd ~/MADRLCitytleranflexresdr
cat outputs/latest_visible_training_output_root.txt
bash deploy/aws/training/tail_aws_training.sh
```

Para relanzar solo un escenario o algoritmo:

```bash
bash deploy/aws/training/run_aws_training.sh \
  --scenario E1 \
  --algorithms matd3 \
  --episodes 75 \
  --episode-time-steps 8760 \
  --log-chunk-size 10M \
  --log-max-files 100 \
  --output-root outputs/aws_citylearn_v3_madrl_reintento_E1_matd3 \
  --cuda
```

## 14. Apagar o destruir recursos

Cuando termine y haya guardado resultados:

```bash
sudo shutdown -h now
```

Para destruir la infraestructura:

```powershell
cd D:\MADRLCitytleranflexresdr\deploy\aws\iac-training
terraform destroy `
  -var "aws_region=us-east-1" `
  -var "key_pair_name=SU_KEY_PAIR_EC2" `
  -var "ami_id=AMI_GPU_DEEP_LEARNING_ACTUAL" `
  -var "allowed_ssh_cidr=SU_IP_PUBLICA/32"
```

Revise manualmente S3 si quiere conservar o eliminar los resultados.

## 15. Alternativa: entrenamiento con Docker / Docker Compose

Si prefiere no instalar Python directamente en la instancia EC2, puede
construir una imagen Docker que ejecuta exactamente el mismo
`run_aws_training.sh` de las secciones 7-10, con sus logs rotados
automaticamente en archivos de texto plano de ~10 MB. La instancia EC2 ya
debe tener el driver NVIDIA (seccion 2); esta seccion agrega lo necesario
para que Docker tambien pueda usar la GPU.

### 15.1 Requisitos en el host: Docker, Compose V2 y NVIDIA Container Toolkit

```bash
docker --version
docker compose version
nvidia-smi
```

Si `docker compose version` falla, instale el plugin Compose V2 (no el
binario legado `docker-compose`):

```bash
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
```

`nvidia-smi` confirma el driver NVIDIA en el host, pero Docker necesita
ADEMAS el NVIDIA Container Toolkit para exponer la GPU dentro de los
contenedores (tener CUDA en el host no implica que Docker ya pueda usarla):

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Verifique que un contenedor ya puede ver la GPU (comando estandar de
NVIDIA, no depende de ninguna imagen del proyecto):

```bash
docker run --rm --gpus all ubuntu:22.04 nvidia-smi
```

Si esto no muestra la GPU, no continue: revise el toolkit antes de construir
la imagen de entrenamiento.

### 15.2 Construir la imagen

```bash
cd ~/MADRLCitytleranflexresdr
git submodule update --init --recursive
docker build -f deploy/aws/training/Dockerfile -t madrl-training:latest .
```

El build context es la raiz del repo (no `deploy/aws/training/`), porque la
imagen necesita `CityLearn/`, `external/`, `data/` y `requirements.txt`
completos. `deploy/aws/training/Dockerfile` y el `.dockerignore` de la raiz
ya estan configurados para esto.

### 15.3 Lanzar 75 episodios con Docker Compose (recomendado)

```bash
cd ~/MADRLCitytleranflexresdr
mkdir -p outputs
docker compose -f deploy/aws/training/docker-compose.yml up -d --build
```

El `command:` de `deploy/aws/training/docker-compose.yml` ya trae
`--episodes 75 --algorithms happo,masac,matd3,maac --scenario ALL
--max-parallel-jobs 1 --log-chunk-size 10M --log-max-files 100 --cuda`.
Edite ese archivo para cambiar escenario, algoritmos, retencion de logs o
paralelismo sin tocar el `Dockerfile`.

### 15.4 Alternativa equivalente con `docker run`

```bash
cd ~/MADRLCitytleranflexresdr
mkdir -p outputs
docker run -d \
  --name madrl-training \
  --gpus all \
  --shm-size=8g \
  -v "$(pwd)/outputs:/workspace/outputs" \
  madrl-training:latest \
  --scenario ALL \
  --algorithms happo,masac,matd3,maac \
  --episodes 75 \
  --episode-time-steps 8760 \
  --max-parallel-jobs 1 \
  --log-chunk-size 10M \
  --log-max-files 100 \
  --cuda
```

Para relanzar solo un escenario/algoritmo, sobrescriba los argumentos (igual
que en la seccion 13, pero pasados al contenedor):

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$(pwd)/outputs:/workspace/outputs" \
  madrl-training:latest \
  --scenario E1 --algorithms matd3 --episodes 75 \
  --log-chunk-size 10M --log-max-files 100 \
  --output-root outputs/aws_citylearn_v3_madrl_reintento_E1_matd3 --cuda
```

### 15.5 Estructura de artefactos generados

El dataset canonico esta declarado en `run_aws_training.sh` linea 8:

```bash
SCHEMA_PATH="CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
```

Esta ruta se pasa via `--schema-path` a cada script de entrenamiento y nunca
se sobreescribe por `docker-compose.yml` ni por el `Dockerfile`. El script
verifica que el archivo exista antes de lanzar cualquier job (linea 88-91).

La configuracion activa en Docker AWS es:
`--artifact-profile efficient`, `--trace-record-interval 24`,
`--trace-detail compact`, `--live-progress-interval 1000`.
Con `legacy_root_artifacts=False` (por defecto) todos los artefactos canonicos
van solo a `data/`; no se crean espejos en la raiz del run.

Arbol completo de `outputs/` al terminar un entrenamiento exitoso:

```text
outputs/
├── .training_completed                        ← marcador; el contenedor queda idle en reinicio
├── .training_failed                           ← marcador de fallo (solo si hay jobs fallidos)
├── latest_visible_training_output_root.txt    ← apunta al output root activo
├── dataset_cache/                             ← cache pickle del dataset Iquitos (TTL 24 h)
│   ├── citylearn_csv_<sha20>.pkl
│   └── citylearn_csv_<sha20>.meta.json
└── aws_citylearn_v3_madrl_<YYYYMMDD_HHMMSS>/   ← OUTPUT ROOT
    ├── official_full_status.json              ← estado de todos los jobs (running/completed/failed)
    ├── official_full_manifest.json            ← copia del status.json
    ├── logs/
    │   ├── E1_happo-00001.log                 ← rotados cada 10 MB, max 100 archivos
    │   ├── E1_happo-00002.log  ...
    │   ├── E1_masac-00001.log
    │   └── E2_happo-00001.log  ...
    ├── happo/
    │   ├── E1_seed_0/
    │   │       ├── data/
    │   │       │   ├── results.json                          ← resultado tecnico completo
    │   │       │   ├── training_summary.json                 ← resumen con artifact_layout
    │   │       │   ├── timeseries.csv                        ← 1 fila/paso (75ep×8760=656250 filas)
    │   │       │   ├── trace.csv                             ← 1 fila/24 pasos/agente (compact)
    │   │       │   ├── checkpoint_manifest.json              ← inventario de .pt con tamanos
    │   │       │   ├── artifact_audit.json                   ← auditoria pasos grabados vs plan
    │   │       │   ├── building_behavior_summary.csv         ← KPIs agregados por edificio
    │   │       │   ├── building_kpis.csv                     ← frame KPI nivel building
    │   │       │   ├── building_observation_action_schema.csv ← schema obs/action por agente
    │   │       │   ├── building_trace_sample.csv             ← muestra 120 filas head+tail
    │   │       │   ├── tensorboard_finite_filter.jsonl       ← solo HAPPO
    │   │       │   └── happo_finite_gradient_guard.jsonl     ← NaN/Inf por optimizador
    │   │       ├── checkpoints/                              ← modelos HARL (actor/critic .pt)
    │   │       └── figures/
    │   │           ├── figures_manifest.json
    │   │           ├── reward_timeseries.png
    │   │           ├── convergence_returns.png
    │   │           ├── episode_reward_summary.png
    │   │           ├── learning_efficiency.png
    │   │           ├── citylearn_v2_district_timeseries.png
    │   │           ├── exploration_action_l2.png
    │   │           ├── agent_reward_contribution.png
    │   │           ├── axis_baseline_comparison.png
    │   │           ├── baseline_gain_by_kpi.png
    │   │           ├── core_kpis.png
    │   │           ├── OE1_flexibility_kpis.png
    │   │           ├── OE2_co2_kpis.png
    │   │           ├── OE3_cost_kpis.png
    │   │           └── tables/                              ← 12 tablas × CSV + Markdown
    │   │               ├── episode_summary.csv / .md
    │   │               ├── objective_kpis.csv / .md         ← leido por comparador v2 vs v3
    │   │               ├── axis_baseline_comparison.csv / .md
    │   │               ├── core_kpis.csv / .md
    │   │               ├── training_efficiency.csv / .md
    │   │               ├── exploration_summary.csv / .md
    │   │               ├── agent_reward_summary.csv / .md
    │   │               ├── checkpoint_inventory.csv / .md
    │   │               ├── building_behavior_summary.csv / .md
    │   │               ├── building_kpis.csv / .md
    │   │               ├── building_observation_action_schema.csv / .md
    │   │               └── building_trace_sample.csv / .md
    │   ├── E2_seed_0/
    │   │   └── [misma estructura que E1_seed_0]
    │   └── E3_seed_0/
    │       └── [misma estructura que E1_seed_0]
    ├── masac/
    │   ├── E1_seed_0/
    │   │       ├── data/
    │   │       │   ├── [mismos canonicos que happo]
    │   │       │   ├── masac_finite_gradient_guard.jsonl    ← NaN/Inf por optimizador
    │   │       │   └── backend_results/                     ← resultados internos del runner QMIX
    │   │       ├── checkpoints/
    │   │       │   └── models/                              ← modelos QMIX del backend MASAC
    │   │       └── figures/ ...
    │   ├── E2_seed_0/ ...
    │   └── E3_seed_0/ ...
    ├── matd3/
    │   ├── E1_seed_0/
    │   │       ├── data/
    │   │       │   ├── [mismos canonicos que happo]
    │   │       │   ├── tensorboard_finite_filter.jsonl      ← MATD3 tambien tiene esto
    │   │       │   └── matd3_finite_gradient_guard.jsonl
    │   │       ├── checkpoints/
    │   │       │   └── offpolicy_run/                       ← directorio del runner off-policy
    │   │       └── figures/ ...
    │   ├── E2_seed_0/ ...
    │   └── E3_seed_0/ ...
    └── maac/
        ├── E1_seed_0/
        │   ├── data/
        │   │   ├── [mismos canonicos que happo]
        │   │   └── maac_finite_gradient_guard.jsonl
        │   ├── checkpoints/
        │   │   ├── checkpoint_episode_1.pt  ← uno por episodio (75 archivos)
        │   │   ├── checkpoint_episode_2.pt  ...
        │   │   └── model.pt                 ← modelo final
        │   └── figures/ ...
        ├── E2_seed_0/ ...
        └── E3_seed_0/ ...
```

Nota: `live_progress.json` se escribe durante el entrenamiento y se elimina
automaticamente al completar cada run. Si el entrenamiento falla, permanece
con el ultimo estado para diagnostico.
Las carpetas `E2_seed_0` y `E3_seed_0` pueden estar vacias al principio si
`--max-parallel-jobs 1` aun esta ejecutando jobs de `E1`; revise
`official_full_status.json` para verlos como `pending`.

### 15.5.1 Post-entrenamiento: benchmark v2 y comparacion (paso manual)

`run_aws_training.sh` solo ejecuta el entrenamiento MADRL. Los scripts de
benchmark y comparacion son pasos **post-entrenamiento** que el investigador
ejecuta por separado una vez descargados los resultados de S3:

```bash
# Paso 1 — benchmark de agentes originales CityLearn v2
python -B CityLearn/scripts/benchmark_citylearn_v2_agents.py \
  --scenario ALL \
  --episode-time-steps 8760 \
  --agents baseline hour_rbc \
  --output-dir outputs/citylearn_v2_original_benchmark \
  --continue-on-error

# Paso 2 — comparacion v2 vs v3 MADRL
OUTPUT_ROOT=$(cat outputs/latest_visible_training_output_root.txt)
python -B CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py \
  --v2-root outputs/citylearn_v2_original_benchmark \
  --v3-root "$OUTPUT_ROOT" \
  --output-dir outputs/comparison_citylearn_v2_vs_v3_madrl \
  --scenario ALL \
  --auto-benchmark-v2 \
  --v2-agents baseline hour_rbc \
  --weights OE1=0.34,OE2=0.33,OE3=0.33
```

El flag `--auto-benchmark-v2` hace que el comparador ejecute el paso 1
automaticamente si faltan artefactos v2. Sin ese flag (o sin `--allow-missing-v2`)
el comparador aborta si no encuentra resultados v2, evitando comparaciones
incompletas. El archivo clave que consume el comparador es
`figures/tables/objective_kpis.csv` de cada run.

### 15.6 Monitorear logs rotados y stdout visible

`outputs/` esta montado como volumen, asi que los resultados son visibles en
el host exactamente igual que en el flujo bare-metal. El entrenamiento tambien
se ve por stdout del contenedor (`docker compose logs -f`) mientras el mismo
stream se escribe en archivos rotados:

```bash
# Listar todos los logs del ultimo entrenamiento
find outputs/aws_citylearn_v3_madrl_* -path "*/logs/*.log" | sort

# Seguir el primer log rotado de happo/E1
tail -f outputs/aws_citylearn_v3_madrl_*/logs/E1_happo-00001.log

# Monitor interactivo (refresca cada 10 s, sin entrar al contenedor):
bash deploy/aws/training/tail_aws_training.sh
```

Para ver la salida viva del contenedor:

```bash
docker compose -f deploy/aws/training/docker-compose.yml logs -f
# o, con docker run:
docker logs -f madrl-training
```

La retencion por job se controla con `--log-max-files`. Use `0` para no
borrar partes antiguas. Con el default `100` y `--log-chunk-size 10M`, cada
job conserva hasta ~1 GB de logs rotados.

### 15.7 Estado del contenedor y acceso directo

```bash
# Estado de todos los contenedores
docker ps

# Estado del contenedor de entrenamiento
docker ps --filter name=madrl-training

# Entrar al contenedor (shell interactivo)
docker exec -it madrl-training bash

# Verificar GPU dentro del contenedor
docker exec -it madrl-training nvidia-smi

# Verificar que el proceso de entrenamiento esta activo
docker exec -it madrl-training ps aux | grep python

# Ver GPU en el host
nvidia-smi -l 10
```

### 15.8 Verificar estado y detener

```bash
# Estado del entrenamiento (status JSON)
cat outputs/aws_citylearn_v3_madrl_*/official_full_status.json

# Detener el contenedor (no elimina artefactos; Docker no lo reinicia)
docker compose -f deploy/aws/training/docker-compose.yml stop

# Detener y eliminar el contenedor (artefactos en outputs/ intactos)
docker compose -f deploy/aws/training/docker-compose.yml down

# Con docker run:
docker stop madrl-training && docker rm madrl-training
```

### 15.9 Comportamiento ante reinicios de EC2 (restart: unless-stopped)

El contenedor usa `restart: unless-stopped`, `init: true` y
`stop_grace_period: 5m`:

- **SSH/VS Code/Jupyter/terminal se cierra**: el contenedor sigue corriendo
  en modo detached, el entrenamiento no se interrumpe.
- **EC2 se reinicia**: Docker daemon se recupera y relanza el contenedor
  automaticamente; el entrenamiento continua desde el inicio en un nuevo
  directorio con timestamp (los resultados previos quedan intactos).
- **Entrenamiento completa con exito**: se crea el marcador
  `outputs/.training_completed`. El contenedor se reinicia pero al detectar
  el marcador queda en modo inactivo (`sleep infinity`) sin relanzar el
  entrenamiento.
- **Entrenamiento falla**: se crea `outputs/.training_failed` con la ruta del
  `official_full_status.json`. Si Docker relanza el contenedor, este detecta
  el marcador y queda inactivo, evitando un bucle infinito de reintentos.
- **Para detener el contenedor inactivo**: `docker compose -f deploy/aws/training/docker-compose.yml stop`
- **Para lanzar un nuevo entrenamiento** despues de que el anterior completo:

```bash
rm outputs/.training_completed
docker compose -f deploy/aws/training/docker-compose.yml up -d
```

Para relanzar despues de un fallo, revise primero el status y los logs:

```bash
cat outputs/.training_failed
OUTPUT_ROOT=$(grep '^output_root=' outputs/.training_failed | cut -d= -f2-)
cat "$OUTPUT_ROOT/official_full_status.json"
find "$OUTPUT_ROOT" -path "*/logs/*.log" | sort

# cuando el problema ya este corregido:
rm outputs/.training_failed
docker compose -f deploy/aws/training/docker-compose.yml up -d
```

### 15.10 Sincronizar a S3 (igual que el flujo bare-metal, seccion 12)

```bash
OUTPUT_ROOT=$(cat outputs/latest_visible_training_output_root.txt)
bash deploy/aws/training/sync_outputs_s3.sh "$OUTPUT_ROOT" "s3://NOMBRE_BUCKET_RESULTS/$(basename "$OUTPUT_ROOT")/"
```

### 15.11 Validacion final contra el pedido Docker/AWS

Estado validado para entrenar con el mismo dataset del proyecto:

- Dataset canonico: `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`.
- Insumos trazables: `CityLearn/data/buildingcsv/`.
- Dockerfile: `deploy/aws/training/Dockerfile`, build context = raiz del repo, sin instalar drivers NVIDIA/CUDA de sistema dentro del contenedor.
- Docker Compose: `deploy/aws/training/docker-compose.yml`, GPU por NVIDIA Container Toolkit del host y volumen persistente `outputs:/workspace/outputs`.
- Launcher: `deploy/aws/training/run_aws_training.sh`, 75 episodios por defecto, 8760 pasos por episodio, logs rotados `logs/E1_happo-00001.log`, `E1_happo-00002.log`, etc.
- Readiness: `deploy/aws/training/check_aws_training_ready.sh`, valida schema, dataset, `buildingcsv`, CUDA/Torch y smoke estricto CityLearn v3.
- Monitor: `deploy/aws/training/tail_aws_training.sh`, lee `official_full_status.json`, `live_progress.json` y logs rotados sin entrar al contenedor.
- Sincronizacion: `deploy/aws/training/sync_outputs_s3.sh`, copia el `OUTPUT_ROOT` completo a S3.

Comandos de validacion usados antes de dar por listo el flujo:

```bash
bash -n deploy/aws/training/run_aws_training.sh
bash -n deploy/aws/training/check_aws_training_ready.sh
bash -n deploy/aws/training/bootstrap_ubuntu_gpu.sh
bash -n deploy/aws/training/tail_aws_training.sh
bash -n deploy/aws/training/sync_outputs_s3.sh
python -m py_compile deploy/aws/training/rotate_training_log.py
docker compose -f deploy/aws/training/docker-compose.yml config
```

Compuertas de dataset/CityLearn v3 ejecutadas en el entorno del proyecto:

```bash
python -B tools/check_training_dataset_ready.py \
  --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025 \
  --buildingcsv-dir CityLearn/data/buildingcsv \
  --audit-dir outputs/dataset_audit \
  --manifest-out outputs/dataset_audit/training_dataset_ready_manifest.json \
  --skip-citylearn-load

python -B CityLearn/scripts/check_citylearn_v3_training_ready.py \
  --schema-path CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json \
  --scenario E1 --strict
python -B CityLearn/scripts/check_citylearn_v3_training_ready.py \
  --schema-path CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json \
  --scenario E2 --strict
python -B CityLearn/scripts/check_citylearn_v3_training_ready.py \
  --schema-path CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json \
  --scenario E3 --strict
```

Resultado esperado de esas compuertas: dataset `READY`, 17 agentes, 185 cargadores EV, 31 cargadores V2G y `python39_core_ready=true`.

## 16. Problemas frecuentes

`nvidia-smi: command not found`

- La AMI no trae driver NVIDIA o no es una instancia GPU.
- Use una Deep Learning AMI GPU o instale driver segun la guia oficial AWS.

`torch.cuda.is_available() = False`

- Active/reinstale PyTorch CUDA.
- Revise `PYTORCH_INDEX_URL` en el bootstrap.
- Verifique que `nvidia-smi` funcione antes.

`Permission denied (publickey)` en PuTTY

- Revise usuario `ubuntu`.
- Revise que el `.ppk` corresponde al key pair de la instancia.
- Revise que el security group permite su IP en puerto 22.

`No space left on device`

- Aumente `root_volume_size_gib` en Terraform.
- Use `--artifact-profile efficient --trace-detail compact`.
- Sincronice a S3 y limpie salidas antiguas.

`Dataset is not ready`

- Ejecute `bash deploy/aws/training/check_aws_training_ready.sh`.
- Confirme que el clone fue con `--recurse-submodules`.
- Confirme que existe `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`.
- Confirme que existe `CityLearn/data/buildingcsv/`; esta es la ruta usada por la compuerta AWS.

`could not select device driver "" with capabilities: [[gpu]]` (Docker)

- El NVIDIA Container Toolkit no esta instalado o no esta configurado como
  runtime de Docker. Repita la seccion 15.1 (`nvidia-ctk runtime configure
  --runtime=docker` y `systemctl restart docker`).
- Confirme con `docker run --rm --gpus all ubuntu:22.04 nvidia-smi` antes de
  reintentar `docker compose up`.

`docker build` falla por espacio o tarda demasiado en "transferring context"

- El build context es la raiz del repo completa (CityLearn, external,
  dataset incluidos). Confirme que `outputs/` y `.venv39-citylearn-v3/` NO
  existen pesados en esa raiz, o que el `.dockerignore` de la raiz los esta
  excluyendo (`docker build` debe imprimir un contexto de pocos GB, no
  decenas).
- Aumente `root_volume_size_gib` en Terraform si el disco se llena durante
  el build (la imagen final pesa varios GB por el dataset + PyTorch CUDA).
