from flask import Flask, render_template, jsonify
import boto3
import json
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

# AWS clients
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')
BUCKET_NAME = 'fed-learn-models-1w4zzxzc'

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """Get real-time training metrics"""
    try:
        # Get recent model metadata from S3
        response = s3.list_objects_v2(
            Bucket='fed-learn-models-1w4zzxzc',
            Prefix='model-versions/'
        )
        
        rounds = []
        for obj in response.get('Contents', []):
            if 'metadata.json' in obj['Key']:
                # Download metadata
                metadata_obj = s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                metadata = json.loads(metadata_obj['Body'].read())
                rounds.append(metadata)
        
        # Get system metrics
        system_metrics = {
            'active_clients': get_active_clients(),
            'total_rounds': len(rounds),
            'average_accuracy': calculate_average_accuracy(rounds),
            'privacy_budget_remaining': calculate_remaining_privacy_budget(rounds)
        }
        
        return jsonify({
            'rounds': rounds[-10:],  # Last 10 rounds
            'system': system_metrics,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/privacy_metrics')
def get_privacy_metrics():
    """Get privacy budget consumption over time"""
    # This would aggregate privacy spending from all clients
    privacy_data = []
    
    # Get privacy metadata from S3
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix='privacy/',
        MaxKeys=100
    )
    
    for obj in response.get('Contents', []):
        try:
            privacy_obj = s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
            data = json.loads(privacy_obj['Body'].read())
            privacy_data.append({
                'timestamp': data['timestamp'],
                'client_id': data['client_id'],
                'epsilon_spent': data['epsilon_spent'],
                'rounds_participated': data['rounds']
            })
        except:
            continue
    
    return jsonify(privacy_data)

@app.route('/api/model_performance')
def get_model_performance():
    """Get model performance metrics over time"""
    # This would track accuracy, loss, and other metrics
    performance_data = []
    
    # Simulated data - in production, read from S3/CloudWatch
    for i in range(20):
        performance_data.append({
            'round': i + 1,
            'accuracy': 0.85 + (i * 0.005) + (0.01 * (i % 3)),
            'loss': 0.5 - (i * 0.02),
            'clients': 5 + (i % 3)
        })
    
    return jsonify(performance_data)

def get_active_clients():
    """Count currently active clients"""
    # In production, query from database or ECS
    return 5

def calculate_average_accuracy(rounds):
    """Calculate average accuracy across rounds"""
    if not rounds:
        return 0
    accuracies = [r.get('accuracy', 0) for r in rounds]
    return sum(accuracies) / len(accuracies)

def calculate_remaining_privacy_budget(rounds):
    """Calculate remaining privacy budget"""
    total_budget = 10.0  # Total epsilon budget
    spent = sum(r.get('epsilon_spent', 0) for r in rounds)
    return max(0, total_budget - spent)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)