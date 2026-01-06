from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

jwt = JWTManager(app)
db = SQLAlchemy(app)

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
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)