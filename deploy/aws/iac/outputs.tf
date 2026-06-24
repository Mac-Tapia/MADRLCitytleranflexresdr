output "ecr_repository_urls" {
  description = "URLs de los repositorios ECR creados"
  value = {
    inference      = aws_ecr_repository.inference.repository_url
    plant_adapter  = aws_ecr_repository.plant_adapter.repository_url
    dashboard      = aws_ecr_repository.dashboard.repository_url
  }
}

output "s3_buckets" {
  description = "Buckets S3 creados para modelos y dataset"
  value = {
    models  = aws_s3_bucket.models.bucket
    dataset = aws_s3_bucket.dataset.bucket
  }
}

output "instance_public_ip" {
  description = "IP pública de la instancia de demo"
  value       = aws_instance.demo.public_ip
}

output "instance_id" {
  value = aws_instance.demo.id
}
