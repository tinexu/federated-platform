import torch
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset

# dirichlet based partitioning is better than shard based partitioning because it's more balanced and less likely to have outliers
# each digit class is split randomly according to a proportion vector from a dirichlet distribution with alpha parameter controlling the skew
# alpha=0.1 means most of one digit goes to one client (realistic bc its more common that one hospital sees mostly pneumonia, another sees mostly fractures); alpha=100 means basically uniform
# partition functions so partitions can be saved to disk and mounted into containers

def get_mnist_data(data_dir="./data"):
    """Download and prepare MNIST dataset."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])
    train_dataset = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(data_dir, train=False, download=True, transform=transform)
    return train_dataset, test_dataset


def split_data_for_clients(dataset, num_clients, non_iid=True, alpha=0.5):
    """
    Split dataset among clients.

    Args:
        dataset: PyTorch dataset.
        num_clients: Number of federated clients.
        non_iid: If True, use Dirichlet-based heterogeneous split.
        alpha: Dirichlet concentration parameter.
                alpha=100  -> nearly uniform (easy)
                alpha=0.5  -> moderate skew
                alpha=0.1  -> extreme skew (realistic)
    """
    total_size = len(dataset)
    labels = np.array([dataset[i][1] for i in range(total_size)])
    num_classes = len(np.unique(labels))

    if non_iid:
        # Dirichlet-based partitioning (better than shard-based)
        client_indices = [[] for _ in range(num_clients)]
        for c in range(num_classes):
            class_idx = np.where(labels == c)[0]
            np.random.shuffle(class_idx)
            proportions = np.random.dirichlet([alpha] * num_clients)
            # Convert proportions to actual counts
            counts = (proportions * len(class_idx)).astype(int)
            # Fix rounding: give remainder to the first client
            counts[0] += len(class_idx) - counts.sum()
            start = 0
            for i in range(num_clients):
                client_indices[i].extend(class_idx[start : start + counts[i]])
                start += counts[i]
    else:
        indices = list(range(total_size))
        np.random.shuffle(indices)
        split_size = total_size // num_clients
        client_indices = [
            indices[i * split_size : (i + 1) * split_size]
            for i in range(num_clients)
        ]

    return client_indices


def get_client_dataloader(dataset, indices, batch_size=32):
    """Create DataLoader for a client's subset of data."""
    subset = Subset(dataset, indices)
    return DataLoader(subset, batch_size=batch_size, shuffle=True)


def save_partition(indices, path):
    """Save a client's data partition indices to disk."""
    np.save(path, np.array(indices))


def load_partition(path):
    """Load a client's data partition indices from disk."""
    return np.load(path).tolist()