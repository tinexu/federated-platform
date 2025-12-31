import os
import json
import boto3
import torch
from flask import Flask, request, jsonify
from datetime import datetime
from server import FederatedServer
import uuid
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('MODEL_BUCKET', 'federated-learning-models')

# Global server instance
fed_server = FederatedServer()
current_round_id = None
client_updates = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'round': fed_server.round})

@app.route('/start_round', methods=['POST'])
def start_round():
    """Initialize a new training round"""
    global current_round_id, client_updates
    
    current_round_id = str(uuid.uuid4())
    client_updates = {}
    
    # Get current global model
    model_weights = fed_server.get_global_weights()
    
    # Save to S3
    model_path = f"rounds/{current_round_id}/global_model.pt"
    torch.save(model_weights, '/tmp/model.pt')
    s3.upload_file('/tmp/model.pt', BUCKET_NAME, model_path)
    
    # Generate presigned URL for clients to download
    model_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': model_path},
        ExpiresIn=3600
    )
    
    return jsonify({
        'round_id': current_round_id,
        'round_number': fed_server.round,
        'model_url': model_url
    })

@app.route('/submit_update', methods=['POST'])
def submit_update():
    """Receive model updates from clients"""
    data = request.json
    client_id = data['client_id']
    round_id = data['round_id']
    model_url = data['model_url']
    data_size = data['data_size']
    metrics = data.get('metrics', {})
    
    if round_id != current_round_id:
        return jsonify({'error': 'Invalid round ID'}), 400
    
    # Store client update info
    client_updates[client_id] = {
        'model_url': model_url,
        'data_size': data_size,
        'metrics': metrics,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logging.info(f"Received update from client {client_id} for round {round_id}")
    
    return jsonify({
        'status': 'accepted',
        'clients_submitted': len(client_updates)
    })

@app.route('/aggregate', methods=['POST'])
def aggregate():
    """Perform federated averaging"""
    data = request.json
    min_clients = data.get('min_clients', 1)
    
    if len(client_updates) < min_clients:
        return jsonify({
            'error': f'Need at least {min_clients} clients, got {len(client_updates)}'
        }), 400
    
    # Download client models from S3
    client_weights_list = []
    client_sizes = []
    
    for client_id, update_info in client_updates.items():
        # Download model from S3 URL
        model_key = update_info['model_url'].split(f'{BUCKET_NAME}/')[-1].split('?')[0]
        s3.download_file(BUCKET_NAME, model_key, f'/tmp/client_{client_id}.pt')
        
        weights = torch.load(f'/tmp/client_{client_id}.pt')
        client_weights_list.append(weights)
        client_sizes.append(update_info['data_size'])
    
    # Perform aggregation
    aggregated_weights = fed_server.federated_averaging(client_weights_list, client_sizes)
    fed_server.update_global_model(aggregated_weights)
    
    # Save new global model
    new_model_path = f"rounds/{fed_server.round}/aggregated_model.pt"
    torch.save(aggregated_weights, '/tmp/aggregated.pt')
    s3.upload_file('/tmp/aggregated.pt', BUCKET_NAME, new_model_path)
    
    return jsonify({
        'status': 'aggregated',
        'round': fed_server.round,
        'clients_aggregated': len(client_updates),
        'model_path': new_model_path
    })

@app.route('/get_metrics', methods=['GET'])
def get_metrics():
    """Return current training metrics"""
    return jsonify({
        'round': fed_server.round,
        'clients_in_round': len(client_updates),
        'client_metrics': {
            client_id: info['metrics'] 
            for client_id, info in client_updates.items()
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)