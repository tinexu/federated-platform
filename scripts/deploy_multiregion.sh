#!/usr/bin/env bash
set -euo pipefail

echo "=== Deploying Multi-Region Federated Learning ==="

REGIONS=("us-east-1" "us-west-2" "eu-west-1")
STACK_NAME="federated-learning-stack"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$SCRIPT_DIR/../infrastructure/federated_learning_stack.yaml"

if [[ ! -f "$TEMPLATE_PATH" ]]; then
  echo "ERROR: Template not found at: $TEMPLATE_PATH"
  echo "Fix TEMPLATE_PATH or move the yaml file."
  exit 1
fi

for REGION in "${REGIONS[@]}"; do
  echo "Deploying to $REGION..."

  aws cloudformation deploy \
    --stack-name "$STACK_NAME-$REGION" \
    --template-file "$TEMPLATE_PATH" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --parameter-overrides ModelBucketName="fed-learn-models-$REGION"

  aws ecs create-cluster \
    --cluster-name "fl-cluster-$REGION" \
    --region "$REGION" \
    --capacity-providers FARGATE_SPOT FARGATE \
    --default-capacity-provider-strategy \
      capacityProvider=FARGATE_SPOT,weight=80 \
      capacityProvider=FARGATE,weight=20 \
    || echo "Cluster fl-cluster-$REGION already exists, skipping."
done

echo "=== Multi-Region Deployment Complete ==="
