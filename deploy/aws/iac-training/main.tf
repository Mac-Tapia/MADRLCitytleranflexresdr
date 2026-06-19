# IaC para entrenamiento MADRL CityLearn v3 en AWS.
#
# Crea una instancia EC2 GPU con rol IAM para S3/CloudWatch y un bucket de
# resultados. Esta IaC esta separada de deploy/aws/iac, que es para inferencia.

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

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

resource "aws_s3_bucket" "training_results" {
  bucket = var.s3_bucket_results

  tags = {
    Project = var.project_name
    Purpose = "madrl-training-results"
  }
}

resource "aws_s3_bucket_public_access_block" "training_results" {
  bucket                  = aws_s3_bucket.training_results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudwatch_log_group" "training" {
  name              = "/${var.project_name}/training"
  retention_in_days = var.cloudwatch_retention_days
}

resource "aws_security_group" "training" {
  name        = "${var.project_name}-training-sg"
  description = "Acceso SSH para entrenamiento MADRL en EC2 GPU"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH desde IP autorizada"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  dynamic "ingress" {
    for_each = var.enable_tensorboard_ingress ? [1] : []

    content {
      description = "TensorBoard opcional"
      from_port   = 6006
      to_port     = 6006
      protocol    = "tcp"
      cidr_blocks = [var.allowed_tensorboard_cidr]
    }
  }

  egress {
    description = "Salida a Internet para paquetes, GitHub, PyPI y S3"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project_name
    Purpose = "madrl-training"
  }
}

resource "aws_iam_role" "training" {
  name = "${var.project_name}-training-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "training" {
  name        = "${var.project_name}-training-policy"
  description = "Permisos minimos para guardar resultados MADRL en S3 y logs en CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TrainingResultsS3"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.training_results.arn,
          "${aws_s3_bucket.training_results.arn}/*"
        ]
      },
      {
        Sid    = "CloudWatchTrainingLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.training.arn}:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "training" {
  role       = aws_iam_role.training.name
  policy_arn = aws_iam_policy.training.arn
}

resource "aws_iam_instance_profile" "training" {
  name = "${var.project_name}-training-instance-profile"
  role = aws_iam_role.training.name
}

resource "aws_instance" "training" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  iam_instance_profile   = aws_iam_instance_profile.training.name
  vpc_security_group_ids = [aws_security_group.training.id]

  root_block_device {
    volume_size           = var.root_volume_size_gib
    volume_type           = "gp3"
    delete_on_termination = true
  }

  user_data = <<-EOF
#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y git git-lfs curl unzip jq tmux htop awscli
  git lfs install --system || true
fi
mkdir -p /opt/madrl
cat >/opt/madrl/README_AWS_TRAINING.txt <<'NOTE'
Instancia lista para clonar:
  git clone --recurse-submodules https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
  cd MADRLCitytleranflexresdr
  bash deploy/aws/training/bootstrap_ubuntu_gpu.sh
  bash deploy/aws/training/check_aws_training_ready.sh
  tmux new -s madrl
  # Dataset canonico: CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json
  bash deploy/aws/training/run_aws_training.sh --scenario ALL --algorithms happo,masac,matd3,maac --episodes 75 --episode-time-steps 8760 --max-parallel-jobs 1 --cuda
NOTE
EOF

  tags = {
    Name    = "${var.project_name}-training"
    Project = var.project_name
    Purpose = "madrl-training"
  }
}
