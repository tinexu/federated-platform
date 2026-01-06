import boto3
import json
from datetime import datetime

class FLConnector:
    """Connects the platform to your existing FL infrastructure"""
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.s3 = boto3.client('s3')
        
    def start_training_round(self, job_id, config):
        """Trigger your existing Lambda functions"""
        
        # existing federated-learning-container function
        invocations = []
        
        for i in range(config['num_clients']):
            response = self.lambda_client.invoke(
                FunctionName='federated-learning-container',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'round_id': f'platform-job-{job_id}',
                    'client_id': f'client-{i}',
                    'epochs': config.get('client_epochs', 3),
                    'privacy_epsilon': config['privacy_budget'] / config['rounds']
                })
            )
            invocations.append(response)
            
        return invocations