#!/usr/bin/env python3
"""
Benchmark: Impact of non-IID data on federated learning convergence.

Sweeps across Dirichlet alpha values and plots accuracy curves.
Run from project root:
    python experiments/benchmark_noniid.py
"""

# benchmarked FedAvg across Dirichlet-parameterized non-IID distributions and measured a 7% accuracy gap at alpha=0.1
# this motivated my switch to FedProx

import sys
import os
import copy
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import matplotlib
matplotlib.use("Agg")  # non-interactive backend so it works headless
import matplotlib.pyplot as plt

from common.models import SimpleNet
from common.data_utils import get_mnist_data, split_data_for_clients, get_client_dataloader


# config
NUM_CLIENTS = 5
NUM_ROUNDS = 15
LOCAL_EPOCHS = 5
BATCH_SIZE = 32
LEARNING_RATE = 0.01
SEED = 42

# alpha values to sweep
ALPHA_VALUES = [100.0, 1.0, 0.5, 0.1]
ALPHA_LABELS = {
    100.0: "alpha=100 (near-IID)",
    1.0: "alpha=1.0 (mild skew)",
    0.5: "alpha=0.5 (moderate skew)",
    0.1: "alpha=0.1 (extreme skew)",
}


# training helpers
def train_local(model, train_loader, epochs, lr):
    model.train()
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    criterion = nn.CrossEntropyLoss()
    for _ in range(epochs):
        for data, target in train_loader:
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
    return model.get_weights()


def evaluate(model, test_loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data, target in test_loader:
            output = model(data)
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
            total += target.size(0)
    return 100.0 * correct / total


def federated_averaging(weight_list, sizes):
    total = sum(sizes)
    aggregated = {}
    for key in weight_list[0].keys():
        aggregated[key] = torch.zeros_like(weight_list[0][key])
        for i, w in enumerate(weight_list):
            aggregated[key] += (sizes[i] / total) * w[key]
    return aggregated


# with alpha run a whole experiment
def run_experiment(train_dataset, test_loader, alpha, non_iid=True):
    label = ALPHA_LABELS.get(alpha, f"alpha={alpha}")
    print(f"\n{'='*60}")
    print(f"  Experiment: {label}")
    print(f"{'='*60}")

    np.random.seed(SEED)
    torch.manual_seed(SEED)

    # partition data
    client_indices = split_data_for_clients(
        train_dataset, NUM_CLIENTS, non_iid=non_iid, alpha=alpha
    )

    # log distribution per client
    for i, indices in enumerate(client_indices):
        labels = [train_dataset[idx][1] for idx in indices]
        unique, counts = np.unique(labels, return_counts=True)
        dist = dict(zip(unique.tolist(), counts.tolist()))
        print(f"  client-{i}: {len(indices)} samples, top classes: {dict(sorted(dist.items(), key=lambda x: -x[1])[:3])}")

    # create client data loaders
    client_loaders = [
        get_client_dataloader(train_dataset, idx, BATCH_SIZE)
        for idx in client_indices
    ]
    client_sizes = [len(idx) for idx in client_indices]

    # global model
    global_model = SimpleNet()
    accuracy_history = []

    for round_num in range(NUM_ROUNDS):
        global_weights = global_model.get_weights()

        # each client trains
        updated_weights = []
        for c in range(NUM_CLIENTS):
            local_model = SimpleNet()
            local_model.set_weights(copy.deepcopy(global_weights))
            w = train_local(local_model, client_loaders[c], LOCAL_EPOCHS, LEARNING_RATE)
            updated_weights.append(w)

        # aggregate
        agg = federated_averaging(updated_weights, client_sizes)
        global_model.set_weights(agg)

        # evaluate
        acc = evaluate(global_model, test_loader)
        accuracy_history.append(acc)
        print(f"  Round {round_num+1:2d}/{NUM_ROUNDS}  accuracy={acc:.2f}%")

    return accuracy_history


# main function logic
def main():
    print("Loading MNIST...")
    train_dataset, test_dataset = get_mnist_data(data_dir="data/mnist")
    test_loader = DataLoader(test_dataset, batch_size=256, shuffle=False)

    results = {}

    for alpha in ALPHA_VALUES:
        history = run_experiment(train_dataset, test_loader, alpha)
        results[str(alpha)] = history

    # run a true IID baseline
    print(f"\n{'='*60}")
    print(f"  Experiment: IID (uniform random split)")
    print(f"{'='*60}")
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    client_indices = split_data_for_clients(train_dataset, NUM_CLIENTS, non_iid=False)
    client_loaders = [get_client_dataloader(train_dataset, idx, BATCH_SIZE) for idx in client_indices]
    client_sizes = [len(idx) for idx in client_indices]
    global_model = SimpleNet()
    iid_history = []
    for round_num in range(NUM_ROUNDS):
        global_weights = global_model.get_weights()
        updated_weights = []
        for c in range(NUM_CLIENTS):
            local_model = SimpleNet()
            local_model.set_weights(copy.deepcopy(global_weights))
            w = train_local(local_model, client_loaders[c], LOCAL_EPOCHS, LEARNING_RATE)
            updated_weights.append(w)
        agg = federated_averaging(updated_weights, client_sizes)
        global_model.set_weights(agg)
        acc = evaluate(global_model, test_loader)
        iid_history.append(acc)
        print(f"  Round {round_num+1:2d}/{NUM_ROUNDS}  accuracy={acc:.2f}%")
    results["iid"] = iid_history

    # results saved as JSON
    os.makedirs("experiments/results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = f"experiments/results/noniid_benchmark_{timestamp}.json"
    with open(results_path, "w") as f:
        json.dump({
            "config": {
                "num_clients": NUM_CLIENTS,
                "num_rounds": NUM_ROUNDS,
                "local_epochs": LOCAL_EPOCHS,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "seed": SEED,
            },
            "results": results,
        }, f, indent=2)
    print(f"\nResults saved to {results_path}")

    # plot
    plt.figure(figsize=(12, 7))
    rounds = list(range(1, NUM_ROUNDS + 1))

    # plot IID baseline
    plt.plot(rounds, results["iid"], "k--", linewidth=2, label="IID (uniform)")

    # plot each alpha
    colors = ["#2ecc71", "#3498db", "#e67e22", "#e74c3c"]
    for i, alpha in enumerate(ALPHA_VALUES):
        label = ALPHA_LABELS[alpha]
        plt.plot(rounds, results[str(alpha)], linewidth=2, color=colors[i], label=label)

    plt.xlabel("Communication Round", fontsize=13)
    plt.ylabel("Global Model Accuracy (%)", fontsize=13)
    plt.title("Impact of Data Heterogeneity on Federated Learning Convergence", fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plot_path = f"experiments/results/noniid_benchmark_{timestamp}.png"
    plt.savefig(plot_path, dpi=150)
    print(f"Plot saved to {plot_path}")
    plt.close()

    # print summary table
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Setting':<30} {'Final Acc':>10} {'Round 5 Acc':>12}")
    print(f"  {'-'*52}")
    for key, label in [("iid", "IID (uniform)")] + [(str(a), ALPHA_LABELS[a]) for a in ALPHA_VALUES]:
        final = results[key][-1]
        mid = results[key][4] if len(results[key]) > 4 else results[key][-1]
        print(f"  {label:<30} {final:>9.2f}% {mid:>11.2f}%")


if __name__ == "__main__":
    main()