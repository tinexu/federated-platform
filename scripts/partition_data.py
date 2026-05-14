#!/usr/bin/env python3
"""
Partition MNIST across N clients and save index files.

Run this BEFORE docker compose up:
    python scripts/partition_data.py --num_clients 5 --alpha 0.5

Creates:
    data/partitions/client-0.npy
    data/partitions/client-1.npy
    ...
"""

# run on host machine before "docker compose up"
# downloads mnist and splits it across n clients using the dirichlet method
# saves client's indices as a file

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.data_utils import get_mnist_data, split_data_for_clients, save_partition
import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Partition MNIST for federated clients.")
    parser.add_argument("--num_clients", type=int, default=5)
    parser.add_argument("--non_iid", action="store_true", default=True)
    parser.add_argument("--iid", action="store_true")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="Dirichlet alpha (lower = more skew). Ignored if --iid.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out_dir", type=str, default="data/partitions")
    args = parser.parse_args()

    np.random.seed(args.seed)
    non_iid = not args.iid

    print(f"Downloading MNIST to data/mnist ...")
    train_dataset, _ = get_mnist_data(data_dir="data/mnist")

    print(f"Splitting into {args.num_clients} clients (non_iid={non_iid}, alpha={args.alpha}) ...")
    client_indices = split_data_for_clients(
        train_dataset, args.num_clients, non_iid=non_iid, alpha=args.alpha
    )

    os.makedirs(args.out_dir, exist_ok=True)
    for i, indices in enumerate(client_indices):
        path = os.path.join(args.out_dir, f"client-{i}.npy")
        save_partition(indices, path)
        # Count label distribution for logging
        labels = [train_dataset[idx][1] for idx in indices]
        unique, counts = np.unique(labels, return_counts=True)
        dist = dict(zip(unique.tolist(), counts.tolist()))
        print(f"  client-{i}: {len(indices)} samples, distribution: {dist}")

    print(f"\nPartitions saved to {args.out_dir}/")


if __name__ == "__main__":
    main()