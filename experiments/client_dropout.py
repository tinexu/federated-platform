import random
from server.server import FederatedServer
from clients.client import FederatedClient
from common.data_utils import get_mnist_data, split_data_for_clients, get_client_dataloader
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import numpy as np

def run_with_client_dropout(num_clients=10, num_rounds=20, dropout_rate=0.3):
    """
    Simulate unreliable clients (like phones going offline)
    dropout_rate: Probability a client doesn't participate in a round
    """
    train_dataset, test_dataset = get_mnist_data()
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    client_indices = split_data_for_clients(train_dataset, num_clients, non_iid=True)
    
    server = FederatedServer()
    clients = []
    
    for i in range(num_clients):
        train_loader = get_client_dataloader(train_dataset, client_indices[i])
        client = FederatedClient(client_id=i, train_loader=train_loader)
        clients.append(client)
    
    accuracy_history = []
    participation_history = []
    
    for round_num in range(num_rounds):
        # Randomly select participating clients
        available_clients = [c for c in clients if random.random() > dropout_rate]
        
        if len(available_clients) == 0:
            print(f"Round {round_num + 1}: No clients available!")
            continue
        
        print(f"\nRound {round_num + 1}: {len(available_clients)}/{num_clients} clients participating")
        participation_history.append(len(available_clients))
        
        global_weights = server.get_global_weights()
        client_weights_list = []
        client_sizes = []
        
        for client in available_clients:
            client.set_model_weights(global_weights)
            client.train(epochs=5)
            client_weights_list.append(client.get_model_weights())
            client_sizes.append(client.get_data_size())
        
        aggregated_weights = server.federated_averaging(client_weights_list, client_sizes)
        server.update_global_model(aggregated_weights)
        
        metrics = server.evaluate_global_model(test_loader)
        accuracy_history.append(metrics['accuracy'])
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    ax1.plot(accuracy_history, 'b-', linewidth=2)
    ax1.set_ylabel('Global Model Accuracy (%)')
    ax1.set_title(f'Federated Learning with {dropout_rate*100}% Client Dropout')
    ax1.grid(True)
    
    ax2.bar(range(len(participation_history)), participation_history)
    ax2.axhline(y=num_clients, color='r', linestyle='--', label='Total Clients')
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Participating Clients')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig(f'dropout_{dropout_rate}.png')
    plt.show()

if __name__ == "__main__":
    run_with_client_dropout(num_clients=10, dropout_rate=0.3)