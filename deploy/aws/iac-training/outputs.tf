output "training_public_ip" {
  description = "IP publica de la instancia de entrenamiento"
  value       = aws_instance.training.public_ip
}

output "training_public_dns" {
  description = "DNS publico de la instancia de entrenamiento"
  value       = aws_instance.training.public_dns
}

output "training_ssh_user" {
  description = "Usuario SSH recomendado para AMI Ubuntu/DLAMI"
  value       = var.ssh_user
}

output "putty_host_name" {
  description = "Valor para Host Name en PuTTY"
  value       = "${var.ssh_user}@${aws_instance.training.public_ip}"
}

output "ssh_command" {
  description = "Comando SSH equivalente si usa OpenSSH"
  value       = "ssh -i <key.pem> ${var.ssh_user}@${aws_instance.training.public_ip}"
}

output "s3_bucket_results" {
  description = "Bucket S3 para sincronizar resultados de entrenamiento"
  value       = aws_s3_bucket.training_results.bucket
}

output "cloudwatch_log_group" {
  description = "Grupo CloudWatch para logs de entrenamiento"
  value       = aws_cloudwatch_log_group.training.name
}
