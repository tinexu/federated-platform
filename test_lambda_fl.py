import boto3
import json
import time

def run_federated_round_on_lambda(num_clients=3):
    """Run a federated learning round using Lambda"""
    
    lambda_client = boto3.client('lambda')
    s3 = boto3.client('s3')
    
    round_id = f"lambda-round-{int(time.time())}"
    print(f"Starting federated learning round: {round_id}")
    
    # Invoke Lambda for each client
    invocations = []
    for i in range(num_clients):
        print(f"\nInvoking Lambda for client {i}...")
        
        response = lambda_client.invoke(
            FunctionName='federated-learning-container',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'round_id': round_id,
                'client_id': f'lambda-client-{i}',
                'epochs': 3
            })
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Client {i} response: {result}")
        invocations.append(result)
    
    # Check results in S3
    print("\nRound complete! Check S3 for results:")
    print(f"aws s3 ls s3://fed-learn-models-1w4zzxzc/lambda-rounds/{round_id}/ --recursive")
    
    return round_id, invocations

def aggregate_lambda_results(round_id):
    """Aggregate results from Lambda clients"""
    
    s3 = boto3.client('s3')
    
    # List all client results
    response = s3.list_objects_v2(
        Bucket='fed-learn-models-1w4zzxzc',
        Prefix=f'lambda-rounds/{round_id}/clients/'
    )
    
    metrics = []
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('_metrics.json'):
            # Download metrics
            result = s3.get_object(Bucket='fed-learn-models-1w4zzxzc', Key=obj['Key'])
            metric = json.loads(result['Body'].read())
            metrics.append(metric)
            print(f"Client {metric['client_id']}: Accuracy={metric['accuracy']:.2%}, Loss={metric['loss']:.4f}")
    
    # Calculate average metrics
    avg_accuracy = sum(m['accuracy'] for m in metrics) / len(metrics)
    avg_loss = sum(m['loss'] for m in metrics) / len(metrics)
    total_epsilon = sum(m['privacy_epsilon'] for m in metrics)
    
    print(f"\nAggregated Results:")
    print(f"Average Accuracy: {avg_accuracy:.2%}")
    print(f"Average Loss: {avg_loss:.4f}")
    print(f"Total Privacy Budget Used: ε={total_epsilon:.1f}")

if __name__ == "__main__":
    # Run federated learning on Lambda
    round_id, results = run_federated_round_on_lambda(num_clients=3)
    
    # Wait a moment for S3 writes to complete
    time.sleep(2)
    
    # Aggregate results
    aggregate_lambda_results(round_id)