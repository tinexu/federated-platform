# infrastructure/outputs.tf
output "ecr_registry" {
  value = split("/", aws_ecr_repository.server.repository_url)[0]
}

output "quick_start_commands" {
  value = <<EOF

=== Quick Start Commands ===

1. Login to ECR:
   aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${split("/", aws_ecr_repository.server.repository_url)[0]}

2. Build and push server:
   docker build -f Dockerfile.server -t ${aws_ecr_repository.server.repository_url}:latest .
   docker push ${aws_ecr_repository.server.repository_url}:latest

3. Build and push client:
   docker build -f Dockerfile.client -t ${aws_ecr_repository.client.repository_url}:latest .
   docker push ${aws_ecr_repository.client.repository_url}:latest

4. S3 Bucket: ${aws_s3_bucket.model_bucket.id}

EOF
}