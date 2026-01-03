#!/bin/bash
# scripts/deploy_simple.sh

echo "=== Deploying Federated Learning Infrastructure ==="

# Just deploy to current region first
REGION=$(aws configure get region)
STACK_NAME="federated-learning-simple"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PATH="$SCRIPT_DIR/../infrastructure/federated_learning_stack.yaml"

if [[ ! -f "$TEMPLATE_PATH" ]]; then
  echo "ERROR: Template not found at: $TEMPLATE_PATH"
  echo "Fix TEMPLATE_PATH or move the yaml file."
  exit 1
fi

echo "Deploying to $REGION..."

# Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file infrastructure/simple_federated_learning_stack.yaml \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION

echo "Deployment complete!"

# Get outputs
echo "Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs' \
    --output table