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
- Episodios: `5`.
- Pasos por episodio: `8760`.
- Salidas: `outputs/aws_citylearn_v3_madrl_<timestamp>/`.
- Estado visible: `official_full_status.json`, logs por algoritmo y
  `live_progress.json` por corrida.

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
  --episodes 5 \
  --episode-time-steps 8760 \
  --max-parallel-jobs 1 \
  --cuda
```

Para una instancia mas grande, puede probar paralelo:

```bash
bash deploy/aws/training/run_aws_training.sh \
  --scenario ALL \
  --algorithms happo,masac,matd3,maac \
  --episodes 5 \
  --episode-time-steps 8760 \
  --max-parallel-jobs 2 \
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
- `outputs/aws_citylearn_v3_madrl_*/*/*/training_summary.json`
- `outputs/aws_citylearn_v3_madrl_*/*/*/results.json`
- `outputs/aws_citylearn_v3_madrl_*/*/*/data/`
- `outputs/aws_citylearn_v3_madrl_*/*/*/checkpoints/`
- `outputs/aws_citylearn_v3_madrl_*/*/*/figures/`

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
  --episodes 5 \
  --episode-time-steps 8760 \
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

## 15. Problemas frecuentes

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
