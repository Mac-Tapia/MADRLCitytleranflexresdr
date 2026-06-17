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

- Dataset: `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`.
- Escenarios: `E1`, `E2`, `E3`.
- Algoritmos: `happo`, `masac`, `matd3`, `maac`.
- Episodios: `75`.
- Pasos por episodio: `8760`.
- Salidas: `outputs/aws_citylearn_v3_madrl_<timestamp>/`.
- Estado visible: `official_full_status.json`, logs por algoritmo y
  `live_progress.json` por corrida.
- Logs en texto plano rotados automaticamente cada 10 MB (configurable con
  `--log-chunk-size`): `logs/<algoritmo>_<escenario>-00001.log`,
  `logs/<algoritmo>_<escenario>-00002.log`, etc. en vez de un solo archivo
  que crece sin limite.
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
- `schema.json` y dataset Iquitos.
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
- `outputs/aws_citylearn_v3_madrl_*/<escenario>/<algoritmo>/logs/*.log`
- `outputs/aws_citylearn_v3_madrl_*/<escenario>/<algoritmo>/<escenario>_seed_0/training_summary.json`
- `outputs/aws_citylearn_v3_madrl_*/<escenario>/<algoritmo>/<escenario>_seed_0/data/`
- `outputs/aws_citylearn_v3_madrl_*/<escenario>/<algoritmo>/<escenario>_seed_0/checkpoints/`
- `outputs/aws_citylearn_v3_madrl_*/<escenario>/<algoritmo>/<escenario>_seed_0/figures/`

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
--max-parallel-jobs 1 --log-chunk-size 10M --cuda`. Edite ese archivo para
cambiar escenario, algoritmos o paralelismo sin tocar el `Dockerfile`.

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
  --cuda
```

Para relanzar solo un escenario/algoritmo, sobrescriba los argumentos (igual
que en la seccion 13, pero pasados al contenedor):

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$(pwd)/outputs:/workspace/outputs" \
  madrl-training:latest \
  --scenario E1 --algorithms matd3 --episodes 75 \
  --output-root outputs/aws_citylearn_v3_madrl_reintento_E1_matd3 --cuda
```

### 15.5 Estructura de artefactos generados

Los artefactos se organizan por escenario y luego por algoritmo dentro del
directorio de salida con timestamp:

```text
outputs/aws_citylearn_v3_madrl_<timestamp>/
├── official_full_status.json
├── official_full_manifest.json
├── E1/
│   ├── happo/
│   │   ├── E1_seed_0/
│   │   │   ├── checkpoints/   ← modelos guardados (*.pt)
│   │   │   ├── data/          ← timeseries_*.csv, trace_*.csv
│   │   │   ├── figures/
│   │   │   └── live_progress.json
│   │   └── logs/
│   │       ├── happo_E1-00001.log
│   │       └── happo_E1-00002.log
│   ├── masac/
│   │   └── ...
│   ├── matd3/
│   │   └── ...
│   └── maac/
│       └── ...
├── E2/
│   └── ...
└── E3/
    └── ...
```

### 15.6 Monitorear logs rotados (texto plano, ~10 MB cada uno)

`outputs/` esta montado como volumen, asi que los resultados son visibles en
el host exactamente igual que en el flujo bare-metal:

```bash
# Listar todos los logs del ultimo entrenamiento
find outputs/aws_citylearn_v3_madrl_* -path "*/logs/*.log" | sort

# Seguir el log mas reciente de happo/E1
tail -f outputs/aws_citylearn_v3_madrl_*/E1/happo/logs/happo_E1-00001.log

# Monitor interactivo (refresca cada 10 s, sin entrar al contenedor):
bash deploy/aws/training/tail_aws_training.sh
```

Para ver solo los banners de inicio/fin del contenedor (el detalle paso a
paso vive en los archivos rotados, no en la salida del contenedor):

```bash
docker compose -f deploy/aws/training/docker-compose.yml logs -f
# o, con docker run:
docker logs -f madrl-training
```

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

El contenedor usa `restart: unless-stopped`:

- **SSH/VS Code/Jupyter/terminal se cierra**: el contenedor sigue corriendo
  en modo detached, el entrenamiento no se interrumpe.
- **EC2 se reinicia**: Docker daemon se recupera y relanza el contenedor
  automaticamente; el entrenamiento continua desde el inicio en un nuevo
  directorio con timestamp (los resultados previos quedan intactos).
- **Entrenamiento completa con exito**: se crea el marcador
  `outputs/.training_completed`. El contenedor se reinicia pero al detectar
  el marcador queda en modo inactivo (`sleep infinity`) sin relanzar el
  entrenamiento.
- **Para detener el contenedor inactivo**: `docker compose -f deploy/aws/training/docker-compose.yml stop`
- **Para lanzar un nuevo entrenamiento** despues de que el anterior completo:

```bash
rm outputs/.training_completed
docker compose -f deploy/aws/training/docker-compose.yml up -d
```

### 15.10 Sincronizar a S3 (igual que el flujo bare-metal, seccion 12)

```bash
OUTPUT_ROOT=$(cat outputs/latest_visible_training_output_root.txt)
bash deploy/aws/training/sync_outputs_s3.sh "$OUTPUT_ROOT" "s3://NOMBRE_BUCKET_RESULTS/$(basename "$OUTPUT_ROOT")/"
```

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
