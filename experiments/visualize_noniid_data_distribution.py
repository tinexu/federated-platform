import matplotlib.pyplot as plt
import numpy as np
from common.data_utils import get_mnist_data, split_data_for_clients

def visualize_client_data_distribution(num_clients=5):
    """Visualize what digits each client has"""
    train_dataset, _ = get_mnist_data()
    
    # Get both IID and non-IID distributions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    for idx, (ax, non_iid, title) in enumerate([(ax1, False, "IID Distribution"), 
                                                  (ax2, True, "Non-IID Distribution")]):
        client_indices = split_data_for_clients(train_dataset, num_clients, non_iid=non_iid)
        
        # Count digits for each client
        client_digit_counts = []
        for client_idx in range(num_clients):
            digit_count = np.zeros(10)
            for idx in client_indices[client_idx]:
                label = train_dataset[idx][1]
                digit_count[label] += 1
            client_digit_counts.append(digit_count)
        
        # Create stacked bar chart
        bottom = np.zeros(10)
        colors = plt.cm.tab10(np.linspace(0, 1, num_clients))
        
        for client_id, counts in enumerate(client_digit_counts):
            ax.bar(range(10), counts, bottom=bottom, 
                   label=f'Client {client_id}', color=colors[client_id])
            bottom += counts
        
        ax.set_xlabel('Digit Class')
        ax.set_ylabel('Number of Samples')
        ax.set_title(title)
        ax.legend()
        ax.set_xticks(range(10))
    
    plt.tight_layout()
    plt.savefig('data_distribution.png')
    plt.show()

if __name__ == "__main__":
    visualize_client_data_distribution()