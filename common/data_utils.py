import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import numpy as np

def get_mnist_data():
    """Download and prepare MNIST dataset"""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST('./data', train=False, transform=transform)
    
    return train_dataset, test_dataset

def split_data_for_clients(dataset, num_clients, non_iid=True):
    """
    Split dataset among clients
    non_iid=True creates heterogeneous data distribution
    """
    total_size = len(dataset)
    indices = list(range(total_size))
    
    if non_iid:
        # Sort by labels to create non-IID partitions
        labels = np.array([dataset[i][1] for i in range(total_size)])
        sorted_indices = np.argsort(labels)
        
        # Create shards (2 shards per client)
        shards_per_client = 2
        shard_size = total_size // (num_clients * shards_per_client)
        
        client_indices = []
        available_shards = list(range(num_clients * shards_per_client))
        
        for i in range(num_clients):
            # Randomly assign shards to clients
            selected_shards = np.random.choice(available_shards, shards_per_client, replace=False)
            available_shards = [s for s in available_shards if s not in selected_shards]
            
            client_idx = []
            for shard in selected_shards:
                start = shard * shard_size
                end = start + shard_size
                client_idx.extend(sorted_indices[start:end])
            
            client_indices.append(client_idx)
    else:
        # IID: Random equal splits
        np.random.shuffle(indices)
        split_size = total_size // num_clients
        client_indices = [indices[i*split_size:(i+1)*split_size] for i in range(num_clients)]
    
    return client_indices

def get_client_dataloader(dataset, indices, batch_size=32):
    """Create DataLoader for a client's subset of data"""
    subset = Subset(dataset, indices)
    return DataLoader(subset, batch_size=batch_size, shuffle=True)