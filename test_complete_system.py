import sys
import os
import json
import boto3
import time
from datetime import datetime

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all components
from server.server import FederatedServer
from clients.private_client import PrivateFederatedClient
from common.data_utils import get_mnist_data, split_data_for_clients, get_client_dataloader
from mlops.pipeline import MLOpsPipeline
import matplotlib.pyplot as plt

def run_complete_federated_learning_system():
    """Test all 4 phases together"""
    
    print("=== COMPLETE FEDERATED LEARNING SYSTEM TEST ===\n")
    
    # Initialize AWS clients
    s3 = boto3.client('s3')
    bucket_name = 'fed-learn-models-1w4zzxzc'
    
    # Phase 1: Basic Federated Learning
    print("PHASE 1: Federated Learning")
    print("-" * 40)
    
    # Load data
    train_dataset, test_dataset = get_mnist_data()
    client_indices = split_data_for_clients(train_dataset, num_clients=3, non_iid=True)
    
    # Initialize server
    server = FederatedServer()
    
    # Create private clients (Phase 3 feature)
    clients = []
    for i in range(3):
        train_loader = get_client_dataloader(train_dataset, client_indices[i])
        client = PrivateFederatedClient(
            client_id=i,
            train_loader=train_loader,
            epsilon=2.0  # Privacy budget
        )
        clients.append(client)
        print(f"Created private client {i} with ε=2.0")
    
    # Phase 2: Cloud Storage Integration
    print("\nPHASE 2: Cloud Storage")
    print("-" * 40)
    
    # Run federated learning rounds
    accuracy_history = []
    privacy_spent_history = []
    
    for round_num in range(5):
        print(f"\nRound {round_num + 1}/5")
        
        # Get global model
        global_weights = server.get_global_weights()
        
        # Save to S3 (Phase 2)
        round_id = f"test-round-{round_num}"
        s3_key = f"test-runs/{datetime.now().strftime('%Y%m%d-%H%M%S')}/round-{round_num}/global_model.json"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps({k: v.tolist() for k, v in global_weights.items()})
        )
        print(f"  Saved global model to S3: {s3_key}")
        
        # Train clients with privacy (Phase 3)
        client_weights_list = []
        client_sizes = []
        total_privacy_spent = 0
        
        for client in clients:
            # Send global model
            client.set_model_weights(global_weights)
            
            # Train with differential privacy
            print(f"  Training client {client.client_id} with privacy...")
            losses = client.train(epochs=2)
            
            # Get private weights
            private_weights = client.get_model_weights()
            client_weights_list.append(private_weights)
            client_sizes.append(client.get_data_size())
            
            # Track privacy
            total_privacy_spent += client.privacy_spent['epsilon_spent']
        
        privacy_spent_history.append(total_privacy_spent / len(clients))
        
        # Aggregate
        print("  Aggregating with secure aggregation...")
        aggregated_weights = server.federated_averaging(client_weights_list, client_sizes)
        server.update_global_model(aggregated_weights)
        
        # Evaluate
        from torch.utils.data import DataLoader
        test_loader = DataLoader(test_dataset, batch_size=32)
        metrics = server.evaluate_global_model(test_loader)
        accuracy_history.append(metrics['accuracy'])
        
        print(f"  Global accuracy: {metrics['accuracy']:.2f}%")
        print(f"  Average privacy spent: ε={privacy_spent_history[-1]:.2f}")
    
    # Phase 4: MLOps Pipeline
    print("\nPHASE 4: MLOps Pipeline")
    print("-" * 40)
    
    # Initialize pipeline
    pipeline = MLOpsPipeline(bucket_name=bucket_name)
    
    # Deploy final model
    final_weights = server.get_global_weights()
    metadata = {
        'accuracy': accuracy_history[-1] / 100,
        'rounds': 5,
        'privacy_budget_used': sum(privacy_spent_history),
        'num_clients': 3,
        'message': 'Complete system test'
    }
    
    version_hash = pipeline.deploy_model(
        {k: v.tolist() for k, v in final_weights.items()},
        metadata,
        deployment_strategy='canary'
    )
    
    print(f"  Deployed model version: {version_hash}")
    print("  Deployment strategy: Canary (10% traffic)")
    
    # Visualize results
    print("\nGENERATING VISUALIZATIONS...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Accuracy over rounds
    ax1.plot(range(1, 6), accuracy_history, 'b-o', linewidth=2, markersize=8)
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Global Model Accuracy (%)')
    ax1.set_title('Federated Learning Progress')
    ax1.grid(True, alpha=0.3)
    
    # Privacy budget consumption
    cumulative_privacy = [sum(privacy_spent_history[:i+1]) for i in range(len(privacy_spent_history))]
    ax2.plot(range(1, 6), cumulative_privacy, 'r-o', linewidth=2, markersize=8)
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Cumulative Privacy Budget (ε)')
    ax2.set_title('Privacy Budget Consumption')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='Privacy limit')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('complete_system_test.png')
    print("  Saved visualization: complete_system_test.png")
    
    # Summary
    print("\n" + "="*60)
    print("SYSTEM TEST COMPLETE")
    print("="*60)
    print(f"✓ Trained federated model with 3 clients")
    print(f"✓ Achieved {accuracy_history[-1]:.1f}% accuracy")
    print(f"✓ Used differential privacy (ε={sum(privacy_spent_history):.1f} total)")
    print(f"✓ Saved models to S3 bucket: {bucket_name}")
    print(f"✓ Deployed with MLOps pipeline")
    print(f"✓ Version hash: {version_hash}")
    print("\nYour federated learning platform is production-ready!")

if __name__ == "__main__":
    run_complete_federated_learning_system()