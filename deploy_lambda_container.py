import boto3
import time

account_id = boto3.client("sts").get_caller_identity()["Account"]
region = boto3.Session().region_name
ECR_REGISTRY = f"{account_id}.dkr.ecr.{region}.amazonaws.com"

def deploy_container_lambda():
    lambda_client = boto3.client("lambda")

    function_name = "federated-learning-container"
    image_uri = f"{ECR_REGISTRY}/fed-learn-lambda:latest"

    try:
        resp = lambda_client.create_function(
            FunctionName=function_name,
            Role="arn:aws:iam::932459504153:role/FederatedLearningLambdaRole",
            Code={"ImageUri": image_uri},
            PackageType="Image",
            Timeout=300,
            MemorySize=3008,
            Environment={"Variables": {"MODEL_BUCKET": "fed-learn-models-1w4zzxzc"}},
        )
        arn = resp["FunctionArn"]
        print(f"Created Lambda function: {arn}")

    except lambda_client.exceptions.ResourceConflictException:
        lambda_client.update_function_code(
            FunctionName=function_name,
            ImageUri=image_uri,
            Publish=True,
        )
        arn = lambda_client.get_function(FunctionName=function_name)["Configuration"]["FunctionArn"]
        print("Updated Lambda function with new container")

    print("Waiting for function to be ready...")
    time.sleep(10)

    # Optional: wait until update completes
    waiter = lambda_client.get_waiter("function_updated")
    waiter.wait(FunctionName=function_name)

    return arn

if __name__ == "__main__":
    deploy_container_lambda()