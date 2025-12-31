import boto3
import torch
import json
import os
from datetime import datetime

# Get bucket name from environment or Terraform
bucket_name = os.environ.get('MODEL_BUCKET')
if not bucket_name:
    print("Getting bucket name from Terraform...")
    import subprocess
    result = subprocess.run(['terraform', 'output', '-raw', 'model_bucket'], 
                          capture_output=True, text=True, cwd='infrastructure')
    bucket_name = result.stdout.strip()

print(f"Using bucket: {bucket_name}")
s3 = boto3.client('s3')

# Test 1: Upload a test file
test_data = {
    "test": "Federated Learning Platform",
    "timestamp": datetime.now().isoformat(),
    "phase": "2"
}
s3.put_object(
    Bucket=bucket_name, 
    Key='test/config.json', 
    Body=json.dumps(test_data)
)
print("Uploaded test config")

# Test 2: Upload a model checkpoint
model = torch.nn.Linear(10, 10)
model_state = model.state_dict()
torch.save(model_state, '/tmp/test_model.pt')
s3.upload_file('/tmp/test_model.pt', bucket_name, 'models/test_model.pt')
print("Uploaded test model")

# Test 3: List objects
response = s3.list_objects_v2(Bucket=bucket_name)
print("\nBucket contents:")
if 'Contents' in response:
    for obj in response['Contents']:
        print(f"  - {obj['Key']} ({obj['Size']} bytes)")

# Test 4: Generate presigned URL (for federated learning)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': bucket_name, 'Key': 'models/test_model.pt'},
    ExpiresIn=3600
)
print(f"\nPresigned URL (valid for 1 hour):\n{url[:100]}...")
