import os
import json
import boto3
import torch
from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# For now, let's create a simple mock server to test
class SimpleFederatedServer:
    def __init__(self):
        self.round = 0
        self.model_weights = {}
        
    def get_global_weights(self):
        # Return a simple model state for testing
        if not self.model_weights:
            # Create a simple linear model
            model = torch.nn.Linear(10, 10)
            self.model_weights = model.state_dict()
        return self.model_weights

# Initialize AWS clients
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('MODEL_BUCKET', 'fed-learn-models-1w4zzxzc')

# Global server instance
fed_server = SimpleFederatedServer()
current_round_id = None
client_updates = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'round': fed_server.round})

@app.route('/start_round', methods=['POST'])
def start_round():
    """Initialize a new training round"""
    global current_round_id, client_updates
    
    current_round_id = str(uuid.uuid4())[:8]  # Shorter ID for readability
    client_updates = {}
    
    # Get current global model
    model_weights = fed_server.get_global_weights()
    
    # Save to S3
    model_path = f"rounds/{current_round_id}/global_model.pt"
    
    # Save model to temporary file
    temp_path = f'/tmp/model_{current_round_id}.pt'
    torch.save(model_weights, temp_path)
    
    # Upload to S3
    try:
        s3.upload_file(temp_path, BUCKET_NAME, model_path)
        
        # Generate presigned URL for clients to download
        model_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': model_path},
            ExpiresIn=3600
        )
        
        fed_server.round += 1
        
        return jsonify({
            'round_id': current_round_id,
            'round_number': fed_server.round,
            'model_url': model_url,
            'status': 'Round started successfully'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'Failed to start round'
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    # List bucket contents
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        objects = [obj['Key'] for obj in response.get('Contents', [])]
    except:
        objects = []
    
    return jsonify({
        'message': 'Federated Learning Server is running',
        'bucket': BUCKET_NAME,
        'round': fed_server.round,
        'bucket_objects': objects
    })

if __name__ == '__main__':
    PORT = 5001  # Changed from 5000
    print(f"Starting Federated Learning Server on port {PORT}")
    print(f"Using S3 bucket: {BUCKET_NAME}")
    app.run(host='0.0.0.0', port=PORT, debug=True)