#!/bin/bash

# Build and push Docker images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build server
docker build -f Dockerfile.server -t federated-learning-server .
docker tag federated-learning-server:latest $ECR_REGISTRY/federated-learning-server:latest
docker push $ECR_REGISTRY/federated-learning-server:latest

# Build client  
docker build -f Dockerfile.client -t federated-learning-client .
docker tag federated-learning-client:latest $ECR_REGISTRY/federated-learning-client:latest
docker push $ECR_REGISTRY/federated-learning-client:latest

# Deploy infrastructure
cd infrastructure
terraform init
terraform apply -auto-approve

# Create ECS services
aws ecs create-service \
  --cluster federated-learning-cluster \
  --service-name server \
  --task-definition federated-learning-server:1 \
  --desired-count 1

# Launch multiple clients
for i in {1..5}; do
  aws ecs create-service \
    --cluster federated-learning-cluster \
    --service-name client-$i \
    --task-definition federated-learning-client:1 \
    --desired-count 1 \
    --environment CLIENT_ID=client-$i
done