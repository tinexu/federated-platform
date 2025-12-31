import os
import sys
import torch
import requests
import boto3
import time
import logging
from flask import Flask, jsonify
import threading
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clients.client import FederatedClient
from common.data_utils import get_mnist_data, split_data_for_clients, get_client_dataloader

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
CLIENT_ID = os.environ.get('CLIENT_ID', str(uuid.uuid4()))
SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:5000')
BUCKET_NAME = os.environ.get('MODEL_BUCKET', 'federated-learning-models')

s3 = boto3.client('s3')
client_instance = None
is_training = False

def initialize_client():
    """Initialize the federated client with data"""
    global client_instance
    
    # For demo, using MNIST with predetermined split
    train_dataset, test_dataset = get_mnist_data()
    
    # Simulate different clients getting different data
    num_clients = int(os.environ.get('TOTAL_CLIENTS', 5))
    client_idx = hash(CLIENT_ID) % num_clients
    
    client_indices = split_data_for_clients(train_dataset, num_clients, non_iid=True)
    train_loader = get_client_dataloader(train_dataset, client_indices[client_idx])
    
    client_instance = FederatedClient(
        client_id=CLIENT_ID,
        train_loader=train_loader,
        test_loader=None
    )
    
    logging.info(f"Client {CLIENT_ID} initialized with {len(train_loader.dataset)} samples")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'client_id': CLIENT_ID,
        'is_training': is_training
    })

@app.route('/participate', methods=['POST'])
def participate():
    """Participate in a federated learning round"""
    global is_training
    
    if is_training:
        return jsonify({'error': 'Already training'}), 400
    
    # Start training in background
    thread = threading.Thread(target=train_and_submit)
    thread.start()
    
    return jsonify({
        'status': 'training_started',
        'client_id': CLIENT_ID
    })

def train_and_submit():
    """Main training loop for the client"""
    global is_training
    is_training = True
    
    try:
        # Get current round info from server
        response = requests.post(f"{SERVER_URL}/start_round")
        round_info = response.json()
        
        round_id = round_info['round_id']
        model_url = round_info['model_url']
        
        logging.info(f"Participating in round {round_info['round_number']}")
        
        # Download global model
        response = requests.get(model_url)
        with open('/tmp/global_model.pt', 'wb') as f:
            f.write(response.content)
        
        global_weights = torch.load('/tmp/global_model.pt')
        client_instance.set_model_weights(global_weights)
        
        # Train on local data
        logging.info("Starting local training...")
        train_losses = client_instance.train(epochs=5)
        
        # Get evaluation metrics if test data available
        metrics = {
            'train_loss': train_losses[-1],
            'samples_trained': client_instance.get_data_size()
        }
        
        # Save updated model
        updated_weights = client_instance.get_model_weights()
        model_filename = f"client_{CLIENT_ID}_round_{round_id}.pt"
        torch.save(updated_weights, f'/tmp/{model_filename}')
        
        # Upload to S3
        s3_key = f"client_updates/{round_id}/{model_filename}"
        s3.upload_file(f'/tmp/{model_filename}', BUCKET_NAME, s3_key)
        
        # Submit update to server
        update_data = {
            'client_id': CLIENT_ID,
            'round_id': round_id,
            'model_url': f"s3://{BUCKET_NAME}/{s3_key}",
            'data_size': client_instance.get_data_size(),
            'metrics': metrics
        }
        
        response = requests.post(f"{SERVER_URL}/submit_update", json=update_data)
        logging.info(f"Submitted update: {response.json()}")
        
    except Exception as e:
        logging.error(f"Error during training: {e}")
    finally:
        is_training = False

@app.route('/trigger_round', methods=['POST'])
def trigger_round():
    """Manually trigger participation in a round (for testing)"""
    threading.Thread(target=participate_in_round).start()
    return jsonify({'status': 'round_triggered'})

def participate_in_round():
    """Automated participation in rounds"""
    while True:
        try:
            # Check if server has active round
            response = requests.get(f"{SERVER_URL}/health")
            if response.status_code == 200:
                train_and_submit()
        except Exception as e:
            logging.error(f"Error checking server: {e}")
        
        # Wait before next round
        time.sleep(30)

if __name__ == '__main__':
    initialize_client()
    
    # Start background thread for automated participation
    if os.environ.get('AUTO_PARTICIPATE', 'true').lower() == 'true':
        thread = threading.Thread(target=participate_in_round)
        thread.daemon = True
        thread.start()
    
    app.run(host='0.0.0.0', port=5001)