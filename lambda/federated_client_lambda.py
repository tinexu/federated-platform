import json
import boto3
import torch
import torch.nn as nn
import numpy as np
from datetime import datetime
import base64
import os

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('MODEL_BUCKET', 'fed-learn-models-1w4zzxzc')

def handler(event, context):
    """Lambda handler for federated learning client"""
    
    # Extract parameters
    round_id = event.get('round_id', 'test-round')
    client_id = event.get('client_id', 'lambda-client-1')
    epochs = event.get('epochs', 3)
    
    print(f"Starting training - Round: {round_id}, Client: {client_id}")
    
    try:
        # Define model architecture
        class SimpleNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(784, 128)
                self.fc2 = nn.Linear(128, 64)
                self.fc3 = nn.Linear(64, 10)
                
            def forward(self, x):
                x = x.view(-1, 784)
                x = torch.relu(self.fc1(x))
                x = torch.relu(self.fc2(x))
                return self.fc3(x)
        
        # Download global model from S3
        model = SimpleNet()
        try:
            s3.download_file(BUCKET_NAME, f'lambda-rounds/{round_id}/global_model.pt', '/tmp/global_model.pt')
            model.load_state_dict(torch.load('/tmp/global_model.pt'))
            print("Loaded global model from S3")
        except:
            print("No global model found, starting fresh")
        
        # Generate synthetic data for client
        np.random.seed(hash(client_id) % 1000)
        num_samples = 500
        
        # Simulate non-IID data
        primary_digits = np.random.choice(10, size=2, replace=False)
        print(f"Client {client_id} specializes in digits: {primary_digits}")
        
        X = []
        y = []
        for _ in range(num_samples):
            if np.random.rand() < 0.8:
                label = np.random.choice(primary_digits)
            else:
                label = np.random.randint(0, 10)
            
            # Simple synthetic image
            image = np.random.randn(784) * 0.1
            image[label*78:(label+1)*78] += 0.5
            
            X.append(image)
            y.append(label)
        
        X = torch.FloatTensor(X)
        y = torch.LongTensor(y)
        
        # Train model
        model.train()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
        criterion = nn.CrossEntropyLoss()
        
        total_loss = 0
        for epoch in range(epochs):
            # Mini-batch training
            indices = torch.randperm(num_samples)
            epoch_loss = 0
            
            for i in range(0, num_samples, 32):
                batch_indices = indices[i:i+32]
                batch_X = X[batch_indices]
                batch_y = y[batch_indices]
                
                optimizer.zero_grad()
                output = model(batch_X)
                loss = criterion(output, batch_y)
                loss.backward()
                
                # Add noise for differential privacy
                with torch.no_grad():
                    for param in model.parameters():
                        param.grad += torch.randn_like(param.grad) * 0.1
                
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / (num_samples // 32)
            total_loss += avg_loss
            print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}")
        
        # Calculate accuracy
        model.eval()
        with torch.no_grad():
            outputs = model(X)
            _, predicted = torch.max(outputs.data, 1)
            accuracy = (predicted == y).sum().item() / num_samples
        
        # Save updated model to S3
        model_path = f'lambda-rounds/{round_id}/clients/{client_id}_model.pt'
        torch.save(model.state_dict(), '/tmp/client_model.pt')
        s3.upload_file('/tmp/client_model.pt', BUCKET_NAME, model_path)
        
        # Save metrics
        metrics = {
            'client_id': client_id,
            'round_id': round_id,
            'accuracy': float(accuracy),
            'loss': float(total_loss / epochs),
            'samples': num_samples,
            'timestamp': datetime.utcnow().isoformat(),
            'privacy_epsilon': epochs * 0.5  # Simplified
        }
        
        metrics_path = f'lambda-rounds/{round_id}/clients/{client_id}_metrics.json'
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=metrics_path,
            Body=json.dumps(metrics)
        )
        
        print(f"Training complete - Accuracy: {accuracy:.2%}, Loss: {total_loss/epochs:.4f}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'metrics': metrics
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e)
            })
        }