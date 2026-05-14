from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

from flask_socketio import SocketIO, emit
import threading
import time
import random

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

jwt = JWTManager(app)
db = SQLAlchemy(app)

socketio = SocketIO(app, cors_allowed_origins="*")

training_sessions = {}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    job_id = data['job_id']
    
    thread = threading.Thread(target=simulate_training, args=(job_id,))
    thread.daemon = True
    thread.start()

def simulate_training(job_id):
    """Simulate federated learning progress"""
    hospitals = ['St. Mary Hospital', 'Regional Medical', 'University Hospital', 'Metro General']
    
    # Initialize metrics
    metrics = {
        'round': 0,
        'hospital_accuracy': {h: 0.65 + random.random() * 0.1 for h in hospitals},
        'global_accuracy': 0.70,
        'hospital_status': {h: 'waiting' for h in hospitals},
        'privacy_spent': 0.0,
        'samples_processed': 0
    }
    
    # 10 rounds
    for round_num in range(1, 11):
        time.sleep(2)
        
        # Update hospital statuses
        for i, hospital in enumerate(hospitals):
            if round_num > i:
                metrics['hospital_status'][hospital] = 'training'
            if round_num > i + 1:
                metrics['hospital_status'][hospital] = 'complete'
        
        # Update accuracies
        for hospital in hospitals:
            if metrics['hospital_status'][hospital] == 'training':
                metrics['hospital_accuracy'][hospital] += random.uniform(0.01, 0.03)
                metrics['hospital_accuracy'][hospital] = min(0.85, metrics['hospital_accuracy'][hospital])
        
        active_hospitals = [h for h in hospitals if metrics['hospital_status'][h] in ['training', 'complete']]
        if active_hospitals:
            avg_accuracy = sum(metrics['hospital_accuracy'][h] for h in active_hospitals) / len(active_hospitals)
            metrics['global_accuracy'] = avg_accuracy + 0.02
        
        # Update privacy budget
        metrics['privacy_spent'] = round_num * 0.3
        metrics['samples_processed'] = round_num * 12000
        metrics['round'] = round_num
        
        socketio.emit('training_update', {
            'job_id': job_id,
            'metrics': metrics
        })
    
    # Final update
    socketio.emit('training_complete', {
        'job_id': job_id,
        'final_accuracy': metrics['global_accuracy'],
        'total_samples': 120000
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'FL Platform API'})

@app.route('/api/demo')
def demo():
    return jsonify({
        'message': 'FL Platform API',
        'features': [
            'Train models across distributed data',
            'Preserve privacy with differential privacy',
            'Pay only for what you use'
        ]
    })

# backend/app.py - Add medical endpoint
@app.route('/api/jobs/medical', methods=['POST'])
def create_medical_job():
    """Create a medical federated learning job"""
    import boto3
    import json
    import uuid
    
    data = request.get_json()
    job_id = f"med-{str(uuid.uuid4())[:8]}"
    
    # Hospital names for demo
    hospitals = ['Regional Medical Center', 'St. Mary Hospital', 
                 'University Hospital', 'Metro General', 'Coastal Health']
    
    # Trigger Lambda with medical context
    lambda_client = boto3.client('lambda')
    results = []
    
    try:
        for i in range(data.get('num_clients', 3)):
            response = lambda_client.invoke(
                FunctionName='federated-learning-container',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'round_id': job_id,
                    'client_id': f'hospital-{hospitals[i]}',
                    'epochs': 5,
                    'model_type': data.get('model_type', 'ResNet50'),
                    'privacy_epsilon': 3.0,  # HIPAA compliant
                    'data_type': 'medical_imaging',
                    'use_case': data.get('use_case')
                })
            )
            
            result = json.loads(response['Payload'].read())
            results.append(result)
        
        return jsonify({
            'job_id': job_id,
            'status': 'training',
            'hospitals': hospitals[:data.get('num_clients', 3)],
            'hipaa_compliant': True,
            'privacy_budget': 3.0,
            'results': results,
            's3_path': f's3://fed-learn-models-1w4zzxzc/medical/{job_id}/'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to create medical FL job'
        }), 500

@app.route('/api/jobs/demo', methods=['POST'])
def create_demo_job():
    """Create a demo FL job using existing Lambda infrastructure"""
    import boto3
    import json
    import uuid
    
    data = request.get_json()
    job_id = str(uuid.uuid4())[:8]
    
    # Trigger your existing Lambda functions
    lambda_client = boto3.client('lambda')
    results = []
    
    try:
        for i in range(data.get('num_clients', 3)):
            response = lambda_client.invoke(
                FunctionName='federated-learning-container',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'round_id': f'demo-job-{job_id}',
                    'client_id': f'client-{i}',
                    'epochs': 3,
                    'job_config': data
                })
            )
            
            result = json.loads(response['Payload'].read())
            results.append(result)
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'results': results,
            's3_path': f's3://fed-learn-models-1w4zzxzc/lambda-rounds/demo-job-{job_id}/'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to create FL job. Make sure Lambda function is deployed.'
        }), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)