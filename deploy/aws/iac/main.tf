# IaC de demo (Fase 8) — ESQUELETO, no aplicado.
#
# Provisiona el mínimo para correr el stack docker-compose.aws.yml en una
# sola instancia EC2:
#   - 3 repos ECR (inference, plant-adapter, dashboard)
#   - 2 buckets S3 (modelos, dataset)
#   - Security group (SSH + dashboard 8501 + inference 8000)
#   - Instancia EC2 con Docker + Docker Compose vía user_data
#   - Log groups de CloudWatch referenciados por docker-compose.aws.yml
#
# Antes de `terraform apply`:
#   - Revisar variables.tf (región, CIDRs, key pair)
#   - Confirmar que la cuenta AWS tiene permisos para ECR/EC2/S3/CloudWatch
#   - Este esqueleto NO crea roles IAM con permisos mínimos detallados;
#     usar un rol existente o completar `aws_iam_role`/`aws_iam_instance_profile`.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- ECR ---------------------------------------------------------------

resource "aws_ecr_repository" "inference" {
  name                 = "${var.project_name}/inference"
  image_tag_mutability = "MUTABLE"
}

resource "aws_ecr_repository" "plant_adapter" {
  name                 = "${var.project_name}/plant-adapter"
  image_tag_mutability = "MUTABLE"
}

resource "aws_ecr_repository" "dashboard" {
  name                 = "${var.project_name}/dashboard"
  image_tag_mutability = "MUTABLE"
}

# --- S3 ------------------------------------------------------------------

resource "aws_s3_bucket" "models" {
  bucket = var.s3_bucket_models
}

resource "aws_s3_bucket" "dataset" {
  bucket = var.s3_bucket_dataset
}

# --- CloudWatch Log Groups -------------------------------------------------

resource "aws_cloudwatch_log_group" "inference" {
  name              = "/${var.project_name}/inference"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "plant_adapter" {
  name              = "/${var.project_name}/plant-adapter"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "dashboard" {
  name              = "/${var.project_name}/dashboard"
  retention_in_days = 14
}

# --- Networking / Security group -------------------------------------------

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "demo" {
  name        = "${var.project_name}-demo-sg"
  description = "Acceso SSH + dashboard + inference para la demo MADRL Iquitos"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "Dashboard Streamlit"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [var.allowed_http_cidr]
  }

  ingress {
    description = "Inference service"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_http_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- EC2 instance ------------------------------------------------------------

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "demo" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name != "" ? var.key_pair_name : null
  vpc_security_group_ids = [aws_security_group.demo.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf install -y docker
    systemctl enable --now docker
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    # NOTA: el resto del bootstrap (clonar repo, aws s3 sync modelos/dataset,
    # docker login a ECR, docker-compose up) se documenta en
    # ../README_DEPLOY_AWS.md y se deja como pasos manuales/post-provisioning
    # para esta demo.
  EOF

  tags = {
    Name    = "${var.project_name}-demo"
    Project = var.project_name
  }
}
