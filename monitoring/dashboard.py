import boto3
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/status')
def status():
    # Get metrics from CloudWatch
    cloudwatch = boto3.client('cloudwatch')
    
    # Get current round from server
    server_response = requests.get(f"{SERVER_URL}/get_metrics")
    
    return jsonify({
        'round': server_response.json()['round'],
        'active_clients': len(server_response.json()['clients_in_round']),
        'metrics': server_response.json()['client_metrics']
    })

if __name__ == '__main__':
    app.run(port=8080)