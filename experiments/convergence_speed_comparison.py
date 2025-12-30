# experiments/convergence_comparison.py
import matplotlib.pyplot as plt
from experiments.basic import run_federated_learning

def compare_convergence():
    """Compare how different parameters affect convergence"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Experiment 1: Number of clients
    for num_clients in [3, 5, 10]:
        _, _, history = run_federated_learning(
            num_clients=num_clients, num_rounds=15, local_epochs=5
        )
        ax1.plot(history, label=f'{num_clients} clients')
    ax1.set_title('Impact of Number of Clients')
    ax1.set_xlabel('Round')
    ax1.set_ylabel('Accuracy (%)')
    ax1.legend()
    ax1.grid(True)
    
    # Experiment 2: Local epochs
    for local_epochs in [1, 5, 10]:
        _, _, history = run_federated_learning(
            num_clients=5, num_rounds=15, local_epochs=local_epochs
        )
        ax2.plot(history, label=f'{local_epochs} local epochs')
    ax2.set_title('Impact of Local Training Epochs')
    ax2.set_xlabel('Round')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True)
    
    # Experiment 3: IID vs Non-IID
    for non_iid in [True, False]:
        _, _, history = run_federated_learning(
            num_clients=5, num_rounds=15, local_epochs=5
        )
        label = 'Non-IID' if non_iid else 'IID'
        ax3.plot(history, label=label)
    ax3.set_title('IID vs Non-IID Data Distribution')
    ax3.set_xlabel('Round')
    ax3.set_ylabel('Accuracy (%)')
    ax3.legend()
    ax3.grid(True)
    
    # Experiment 4: Batch size effect
    for batch_size in [16, 32, 64]:
        _, _, history = run_federated_learning(
            num_clients=5, num_rounds=15, local_epochs=5, batch_size=batch_size
        )
        ax4.plot(history, label=f'Batch size {batch_size}')
    ax4.set_title('Impact of Batch Size')
    ax4.set_xlabel('Round')
    ax4.set_ylabel('Accuracy (%)')
    ax4.legend()
    ax4.grid(True)
    
    plt.tight_layout()
    plt.savefig('convergence_comparison.png')
    plt.show()

if __name__ == "__main__":
    compare_convergence()