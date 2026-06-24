# Variables de entrada para el IaC de demo (Fase 8).
# Esto es un ESQUELETO no desplegado: ningún `terraform apply` se ha
# ejecutado. Revisar y ajustar valores antes de usar en una cuenta real.

variable "aws_region" {
  description = "Región AWS donde se despliega la demo"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefijo para nombrar recursos (ECR, logs, EC2, etc.)"
  type        = string
  default     = "madrl-iquitos"
}

variable "instance_type" {
  description = "Tipo de instancia EC2 para la demo (inference + adapter + dashboard)"
  type        = string
  default     = "t3.medium"
}

variable "key_pair_name" {
  description = "Nombre del key pair EC2 existente para acceso SSH"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr" {
  description = "CIDR permitido para SSH (22) — restringir a la IP del usuario"
  type        = string
  default     = "0.0.0.0/0"
}

variable "allowed_http_cidr" {
  description = "CIDR permitido para acceso al dashboard (8501) e inference (8000)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "s3_bucket_models" {
  description = "Nombre del bucket S3 para almacenar el modelo ONNX ganador y metadatos"
  type        = string
  default     = "madrl-iquitos-models"
}

variable "s3_bucket_dataset" {
  description = "Nombre del bucket S3 para el dataset CityLearn Iquitos"
  type        = string
  default     = "madrl-iquitos-dataset"
}
