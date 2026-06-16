# Despliegue en AWS (demo Fase 8) — guía de referencia

> **Estado**: esqueleto/plan, NO ejecutado. Ningún recurso AWS ha sido
> creado por este asistente (sin credenciales AWS en esta sesión). Esta guía
> documenta los pasos que el usuario debe ejecutar manualmente cuando decida
> desplegar la demo.

> Para entrenamiento GPU desde cero en AWS use
> `deploy/aws/README_TRAINING_AWS.md`. Esta guia es solo para inferencia/demo
> con Docker Compose despues de tener un modelo ganador exportado.

## 0. Prerrequisitos

- Cuenta AWS con permisos para EC2, ECR, S3, CloudWatch Logs, IAM (rol de
  instancia con acceso a ECR/S3/CloudWatch).
- AWS CLI configurado (`aws configure`) con credenciales válidas.
- Terraform >= 1.5 instalado localmente.
- Un modelo ganador exportado a ONNX + metadata JSON (ver
  `deploy/inference/model_loader.py` para el contrato esperado). Si todavía
  no existe, el stack puede desplegarse igualmente en modo "stub".

## 1. Provisionar infraestructura base (Terraform)

```bash
cd deploy/aws/iac
terraform init
terraform plan   # revisar recursos antes de aplicar
terraform apply  # crea ECR repos, buckets S3, security group, instancia EC2
```

Ajustar `variables.tf` antes de aplicar (región, `key_pair_name`,
`allowed_ssh_cidr`/`allowed_http_cidr` — NO dejar `0.0.0.0/0` en producción).

## 2. Construir y publicar imágenes en ECR

Desde la raíz del proyecto, para cada servicio (`inference`,
`plant-adapter`, `dashboard`):

```bash
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com

docker build -t <ecr_url_inference>:latest deploy/inference
docker push <ecr_url_inference>:latest

docker build -t <ecr_url_plant_adapter>:latest deploy/plant-adapter
docker push <ecr_url_plant_adapter>:latest

docker build -t <ecr_url_dashboard>:latest deploy/dashboard
docker push <ecr_url_dashboard>:latest
```

Las URLs de ECR se obtienen de `terraform output ecr_repository_urls`.

## 3. Subir modelo y dataset a S3

```bash
aws s3 cp models/winning_agent.onnx s3://<s3_bucket_models>/
aws s3 cp models/winning_agent.metadata.json s3://<s3_bucket_models>/
aws s3 sync data/citylearn_iquitos_2023_2025 s3://<s3_bucket_dataset>/citylearn_iquitos_2023_2025/
```

## 4. Configurar y arrancar la instancia EC2

Conectarse por SSH a `terraform output instance_public_ip` y:

```bash
mkdir -p /opt/madrl/models /opt/madrl/data/citylearn_iquitos_2023_2025
aws s3 cp s3://<s3_bucket_models>/winning_agent.onnx /opt/madrl/models/
aws s3 cp s3://<s3_bucket_models>/winning_agent.metadata.json /opt/madrl/models/
aws s3 sync s3://<s3_bucket_dataset>/citylearn_iquitos_2023_2025/ /opt/madrl/data/citylearn_iquitos_2023_2025/

# Clonar (o copiar) el repo para obtener deploy/docker-compose.aws.yml, deploy/.env y deploy/mosquitto.conf
cd /opt/madrl/deploy
cp .env.example .env   # completar ECR_REGISTRY, ECR_REPO_*, AWS_REGION, etc.

aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com

docker-compose -f docker-compose.aws.yml up -d
```

## 5. Verificación

- `curl http://<ip_publica>:8000/health` → `{"status": "ok", ...}`
- Dashboard: `http://<ip_publica>:8501`
- Logs en CloudWatch: grupos `/madrl-iquitos/inference`,
  `/madrl-iquitos/plant-adapter`, `/madrl-iquitos/dashboard`.

## 6. Limpieza

```bash
cd deploy/aws/iac
terraform destroy
```

Y eliminar manualmente las imágenes en ECR y objetos en S3 si
`terraform destroy` no los borra (los buckets/repos con contenido pueden
requerir vaciarse primero).

## Notas de seguridad

- Restringir `allowed_ssh_cidr` y `allowed_http_cidr` a IPs conocidas antes
  de cualquier despliegue real.
- No commitear `deploy/.env` con credenciales reales (ya cubierto por
  `.gitignore` si se añade `deploy/.env`).
- Este esqueleto usa una sola instancia EC2 por simplicidad de demo; para un
  despliegue productivo considerar ECS/Fargate, ALB, TLS y rotación de
  credenciales ECR vía rol IAM de instancia.
