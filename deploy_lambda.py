import boto3
import json
import zipfile
import os

def create_lambda_function():
    """Deploy federated learning to AWS Lambda"""
    
    lambda_client = boto3.client('lambda')
    iam = boto3.client('iam')
    
    # Create IAM role for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        role = iam.create_role(
            RoleName='FederatedLearningLambdaRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = role['Role']['Arn']
        
        # Attach policies
        iam.attach_role_policy(
            RoleName='FederatedLearningLambdaRole',
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create policy for S3 access
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:PutObject"],
                "Resource": "arn:aws:s3:::fed-learn-models-*/*"
            }]
        }
        
        iam.put_role_policy(
            RoleName='FederatedLearningLambdaRole',
            PolicyName='S3Access',
            PolicyDocument=json.dumps(s3_policy)
        )
        
        print(f"Created IAM role: {role_arn}")
        
    except iam.exceptions.EntityAlreadyExistsException:
        # Role already exists
        role_arn = iam.get_role(RoleName='FederatedLearningLambdaRole')['Role']['Arn']
        print(f"Using existing role: {role_arn}")
    
    # Wait for role
    import time
    time.sleep(10)
    
    # Create Lambda function
    with open('lambda-fl-package.zip', 'rb') as f:
        zip_content = f.read()
    
    try:
        response = lambda_client.create_function(
            FunctionName='federated-learning-client',
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.handler',
            Code={'ZipFile': zip_content},
            Description='Federated Learning Client',
            Timeout=300,
            MemorySize=3008,  # Maximum memory
            Environment={
                'Variables': {
                    'MODEL_BUCKET': 'fed-learn-models-1w4zzxzc'
                }
            }
        )
        print(f"Created Lambda function: {response['FunctionArn']}")
        
    except lambda_client.exceptions.ResourceConflictException:
        # Update existing function
        response = lambda_client.update_function_code(
            FunctionName='federated-learning-client',
            ZipFile=zip_content
        )
        print("Updated existing Lambda function")
    
    return response['FunctionArn']

if __name__ == "__main__":
    function_arn = create_lambda_function()
    print(f"\nLambda function deployed: {function_arn}")
    print("You can now invoke federated learning in the cloud!")