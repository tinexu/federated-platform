import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server import FederatedServer
from clients.client import FederatedClient
from common.data_utils import get_mnist_data, split_data_for_clients, get_client_dataloader
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

def run_federated_learning(num_clients=5, num_rounds=10, local_epochs=5, batch_size=32, non_iid=True):
    """Run a complete federated learning simulation"""
    
    print("=== Federated Learning Experiment ===")
    print(f"Clients: {num_clients}, Rounds: {num_rounds}, Local Epochs: {local_epochs}, Non-IID: {non_iid}")
    
    # Step 1: Prepare data
    print("\n1. Loading MNIST dataset...")
    train_dataset, test_dataset = get_mnist_data()
    
    # Create test loader for global evaluation
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Split training data among clients
    distribution_type = "non-IID" if non_iid else "IID"
    print(f"2. Splitting data among clients ({distribution_type})...")
    client_indices = split_data_for_clients(train_dataset, num_clients, non_iid=non_iid)
    
    # Step 2: Initialize server and clients
    print("3. Initializing server and clients...")
    server = FederatedServer()
    clients = []
    
    for i in range(num_clients):
        train_loader = get_client_dataloader(train_dataset, client_indices[i], batch_size)
        client = FederatedClient(client_id=i, train_loader=train_loader, test_loader=test_loader)
        clients.append(client)
    
    # Step 3: Run federated learning rounds
    print("\n4. Starting federated learning...")
    global_accuracy_history = []
    
    for round_num in range(num_rounds):
        print(f"\n--- Round {round_num + 1}/{num_rounds} ---")
        
        # Get current global model
        global_weights = server.get_global_weights()
        
        # Train clients
        client_weights_list = []
        client_sizes = []
        
        for client in clients:
            # Send global model to client
            client.set_model_weights(global_weights)
            
            # Train on local data
            print(f"\nTraining client {client.client_id}...")
            client.train(epochs=local_epochs)
            
            # Get updated weights
            client_weights = client.get_model_weights()
            client_weights_list.append(client_weights)
            client_sizes.append(client.get_data_size())
        
        # Aggregate weights
        print("\nAggregating client updates...")
        aggregated_weights = server.federated_averaging(client_weights_list, client_sizes)
        
        # Update global model
        server.update_global_model(aggregated_weights)
        
        # Evaluate global model
        global_metrics = server.evaluate_global_model(test_loader)
        global_accuracy_history.append(global_metrics['accuracy'])
        
        print(f"\nGlobal Model - Accuracy: {global_metrics['accuracy']:.2f}%, Loss: {global_metrics['loss']:.4f}")
    
    # Don't show plot when called from other experiments
    if __name__ == "__main__":
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, num_rounds + 1), global_accuracy_history, 'b-', linewidth=2)
        plt.xlabel('Round')
        plt.ylabel('Global Model Accuracy (%)')
        plt.title('Federated Learning Progress')
        plt.grid(True)
        plt.savefig('federated_learning_results.png')
        plt.show()
    
    print("\n=== Experiment Complete ===")
    print(f"Final Global Accuracy: {global_accuracy_history[-1]:.2f}%")
    
    return server, clients, global_accuracy_history

if __name__ == "__main__":
    # Run the experiment
    server, clients, history = run_federated_learning(
        num_clients=5,
        num_rounds=10,
        local_epochs=5,
        batch_size=32,
        non_iid=True
    )