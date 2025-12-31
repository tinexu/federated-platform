import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.private_client import PrivateFederatedClient
from common.secure_aggregation import SecureAggregation
from common.data_utils import get_mnist_data, split_data_for_clients, get_client_dataloader
import matplotlib.pyplot as plt
import numpy as np

def test_differential_privacy():
    """Test differential privacy impact on model accuracy"""
    
    # Load data
    train_dataset, test_dataset = get_mnist_data()
    client_indices = split_data_for_clients(train_dataset, num_clients=3, non_iid=True)
    
    # Test different privacy levels
    epsilon_values = [0.1, 0.5, 1.0, 5.0, float('inf')]  # inf = no privacy
    results = []
    
    for epsilon in epsilon_values:
        print(f"\nTesting with epsilon = {epsilon}")
        
        # Create private client
        train_loader = get_client_dataloader(train_dataset, client_indices[0])
        
        if epsilon == float('inf'):
            # Use regular client (no privacy)
            from clients.client import FederatedClient
            client = FederatedClient(client_id=0, train_loader=train_loader)
        else:
            client = PrivateFederatedClient(
                client_id=0, 
                train_loader=train_loader,
                epsilon=epsilon
            )
        
        # Train
        losses = client.train(epochs=5)
        
        # Get final loss
        results.append({
            'epsilon': epsilon,
            'final_loss': losses[-1],
            'privacy_spent': getattr(client, 'privacy_spent', {}).get('epsilon_spent', 0)
        })
    
    # Plot results
    plt.figure(figsize=(10, 6))
    epsilons = [r['epsilon'] for r in results if r['epsilon'] != float('inf')]
    losses = [r['final_loss'] for r in results if r['epsilon'] != float('inf')]
    
    plt.plot(epsilons, losses, 'b-o', linewidth=2, markersize=8)
    plt.axhline(y=results[-1]['final_loss'], color='r', linestyle='--', 
                label='No Privacy Baseline')
    
    plt.xlabel('Privacy Budget (ε)')
    plt.ylabel('Training Loss')
    plt.title('Privacy-Utility Tradeoff in Federated Learning')
    plt.xscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('experiments/privacy_utility_tradeoff.png')
    plt.show()
    
    print("\nPrivacy-Utility Tradeoff Results:")
    for r in results:
        eps_str = f"{r['epsilon']:.1f}" if r['epsilon'] != float('inf') else "∞"
        print(f"ε = {eps_str}: Loss = {r['final_loss']:.4f}")

def test_secure_aggregation():
    """Test secure aggregation protocol"""
    
    print("\nTesting Secure Aggregation Protocol")
    
    # Simulate 3 clients
    num_clients = 3
    secure_agg = SecureAggregation(num_clients=num_clients, threshold=2)
    
    # Generate keys for each client
    client_keys = {}
    for i in range(num_clients):
        client_keys[i] = secure_agg.generate_client_keys(i)
    
    # Simulate model weights from each client
    import torch
    client_weights = []
    for i in range(num_clients):
        weights = {
            'layer1': torch.randn(10, 10) * (i + 1),  # Different weights per client
            'layer2': torch.randn(5, 5) * (i + 1)
        }
        client_weights.append(weights)
    
    # Create secret shares
    all_shares = []
    for i in range(num_clients):
        shares = secure_agg.create_shares(client_weights[i], i, client_keys[i])
        all_shares.append(shares)
    
    print(f"Created secret shares for {num_clients} clients")
    print(f"Share sizes: {[len(s) for s in all_shares]}")
    
    # Aggregate (simulating some clients dropping out)
    participating_shares = all_shares[:2]  # Only 2 out of 3 clients
    
    try:
        # This should work with threshold=2
        aggregated = secure_agg.aggregate_shares(
            participating_shares, 
            {i: client_keys[i][0] for i in range(2)}
        )
        print(f"Aggregation successful with {len(participating_shares)} clients")
        print(f"Aggregated weight keys: {list(aggregated.keys())}")
    except ValueError as e:
        print(f"Aggregation failed: {e}")

if __name__ == "__main__":
    print("=== Testing Privacy Features ===")
    
    # Test differential privacy
    test_differential_privacy()
    
    # Test secure aggregation
    test_secure_aggregation()
    
    print("\n=== Privacy Tests Complete ===")