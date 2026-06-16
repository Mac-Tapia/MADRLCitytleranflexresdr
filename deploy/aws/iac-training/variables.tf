variable "aws_region" {
  description = "Region AWS donde se crea la instancia GPU"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefijo para recursos AWS"
  type        = string
  default     = "madrl-iquitos"
}

variable "ami_id" {
  description = "AMI GPU actual en la region elegida. Use Deep Learning OSS Nvidia Driver AMI GPU PyTorch o equivalente."
  type        = string

  validation {
    condition     = trimspace(var.ami_id) != ""
    error_message = "Debe indicar ami_id de una AMI GPU/DLAMI en la region seleccionada."
  }
}

variable "instance_type" {
  description = "Tipo de instancia GPU. g5.xlarge es base; use g5.2xlarge o mayor para paralelo."
  type        = string
  default     = "g5.xlarge"
}

variable "root_volume_size_gib" {
  description = "Tamano del disco raiz para codigo, entorno y outputs"
  type        = number
  default     = 300
}

variable "key_pair_name" {
  description = "Nombre del key pair EC2 existente"
  type        = string

  validation {
    condition     = trimspace(var.key_pair_name) != ""
    error_message = "Debe indicar key_pair_name para poder entrar por PuTTY/SSH."
  }
}

variable "ssh_user" {
  description = "Usuario SSH de la AMI. Ubuntu/DLAMI suele usar ubuntu."
  type        = string
  default     = "ubuntu"
}

variable "allowed_ssh_cidr" {
  description = "CIDR autorizado para SSH. Use SU_IP_PUBLICA/32."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_tensorboard_ingress" {
  description = "Abrir puerto 6006 para TensorBoard. Mantener false salvo necesidad puntual."
  type        = bool
  default     = false
}

variable "allowed_tensorboard_cidr" {
  description = "CIDR autorizado para TensorBoard si se habilita."
  type        = string
  default     = "0.0.0.0/0"
}

variable "s3_bucket_results" {
  description = "Bucket S3 globalmente unico para resultados de entrenamiento"
  type        = string
  default     = "madrl-iquitos-training-results"
}

variable "cloudwatch_retention_days" {
  description = "Dias de retencion para logs de entrenamiento"
  type        = number
  default     = 14
}
