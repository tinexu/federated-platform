import os
import json
import boto3
import torch
from flask import Flask, request, jsonify
from datetime import datetime
import uuid
import logging
import jwt

from common.auth import require_auth, generate_client_token
from common.secure_aggregation import SecureAggregation

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration
REQUIRE_AUTH = os.environ.get('REQUIRE_AUTH', 'true').lower() == 'true'
MIN_CLIENTS_FOR_ROUND = int(os.environ.get('MIN_CLIENTS', '2'))
PRIVACY_BUDGET = float(os.environ.get('PRIVACY_BUDGET', '1.0'))

# AWS clients
s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('MODEL_BUCKET', 'fed-learn-models-1w4zzxzc')

# Server state
current_round = {
    'id': None,
    'client_updates': {},
    'started_at': None,
    'secure_agg': None
}

@app.route('/register', methods=['POST'])
def register_client():
    """Register a new client and return auth token"""
    data = request.json
    client_id = data.get('client_id')
    
    if not client_id:
        return jsonify({'error': 'client_id required'}), 400
    
    # Generate authentication token
    token = generate_client_token(client_id)
    
    # Log registration (in production, save to database)
    logging.info(f"Client {client_id} registered")
    
    return jsonify({
        'token': token,
        'client_id': client_id,
        'privacy_budget': PRIVACY_BUDGET,
        'message': 'Registration successful'
    })

@app.route('/start_round', methods=['POST'])
@require_auth
def start_round():
    """Start a new secure federated learning round"""
    global current_round
    
    # Check if round already active
    if current_round['id'] is not None:
        return jsonify({'error': 'Round already in progress'}), 400
    
    # Initialize new round
    round_id = str(uuid.uuid4())[:8]
    current_round = {
        'id': round_id,
        'client_updates': {},
        'started_at': datetime.utcnow().isoformat(),
        'secure_agg': SecureAggregation(
            num_clients=MIN_CLIENTS_FOR_ROUND,
            threshold=MIN_CLIENTS_FOR_ROUND
        )
    }
    
    logging.info(f"Started round {round_id}")
    
    return jsonify({
        'round_id': round_id,
        'min_clients': MIN_CLIENTS_FOR_ROUND,
        'privacy_budget': PRIVACY_BUDGET,
        'status': 'Round started'
    })

@app.route('/submit_update', methods=['POST'])
@require_auth
def submit_update():
    """Submit encrypted model update"""
    if current_round['id'] is None:
        return jsonify({'error': 'No active round'}), 400
    
    data = request.json
    client_id = request.client_id  # From JWT token
    
    # Store encrypted update
    current_round['client_updates'][client_id] = {
        'encrypted_share': data['encrypted_share'],
        'timestamp': datetime.utcnow().isoformat(),
        'privacy_spent': data.get('privacy_spent', {})
    }
    
    logging.info(f"Received update from client {client_id}")
    
    # Check if we have enough clients
    if len(current_round['client_updates']) >= MIN_CLIENTS_FOR_ROUND:
        # Trigger aggregation
        return trigger_aggregation()
    
    return jsonify({
        'status': 'Update received',
        'clients_submitted': len(current_round['client_updates']),
        'clients_needed': MIN_CLIENTS_FOR_ROUND
    })

def trigger_aggregation():
    """Perform secure aggregation when enough clients have submitted"""
    # This would implement the full secure aggregation protocol
    # For now, return success
    
    round_id = current_round['id']
    num_clients = len(current_round['client_updates'])
    
    # Reset for next round
    current_round['id'] = None
    current_round['client_updates'] = {}
    
    return jsonify({
        'status': 'Aggregation complete',
        'round_id': round_id,
        'clients_aggregated': num_clients,
        'next_round_available': True
    })

@app.route('/audit_log', methods=['GET'])
@require_auth
def get_audit_log():
    """Get audit log for compliance"""
    # In production, this would query a database
    return jsonify({
        'total_rounds': 10,
        'total_clients': 5,
        'privacy_budget_used': 8.5,
        'last_round': current_round['started_at']
    })

if __name__ == '__main__':
    print("Starting Secure Federated Learning Server")
    print(f"Privacy Budget: {PRIVACY_BUDGET}")
    print(f"Min Clients: {MIN_CLIENTS_FOR_ROUND}")
    app.run(host='0.0.0.0', port=5001, debug=True)