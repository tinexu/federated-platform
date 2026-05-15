# transition to making https requests instead of straight calling method on objects
# main polls /round_info every few seconds and checks if a new round is active and then pulls model, trains, submits, and waits for the next one
# wait for coordinator handles startup race condition (clients boot before coordinator ready)
# configuration from env vars lets docker set different values per container

"""
Federated Learning Client Service.

Each client runs as an independent process (one per Docker container).
On startup it:
  1. Downloads MNIST and loads its pre-assigned data partition.
  2. Registers with the coordinator.
  3. Starts a heartbeat background thread.
  4. Enters a loop: pull global model -> train locally -> submit update.
"""

import os
import sys
import time
import threading
import logging

import numpy as np
import requests
import torch
import torch.nn as nn
import torch.optim as optim

from common.models import SimpleNet
from common.data_utils import get_mnist_data, get_client_dataloader, load_partition
from common.serialization import weights_to_base64, base64_to_weights
from common import protocol

CLIENT_ID = os.environ.get("CLIENT_ID", "client-0")

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s [CLIENT {CLIENT_ID}] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# configuration from environment variables
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "http://coordinator:5000")
LOCAL_EPOCHS = int(os.environ.get("LOCAL_EPOCHS", 5))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 32))
LEARNING_RATE = float(os.environ.get("LEARNING_RATE", 0.01))
DATA_DIR = os.environ.get("DATA_DIR", "/data")
PARTITION_FILE = os.environ.get("PARTITION_FILE", f"/partitions/{CLIENT_ID}.npy")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 5))
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", protocol.HEARTBEAT_INTERVAL))


# heartbeat background thread
def heartbeat_loop():
    """Send periodic heartbeats to the coordinator."""
    while True:
        try:
            requests.post(
                f"{COORDINATOR_URL}/heartbeat",
                json={"client_id": CLIENT_ID},
                timeout=5,
            )
        except Exception:
            log.warning("Failed to send heartbeat.")
        time.sleep(HEARTBEAT_INTERVAL)


# coordinator communication
def wait_for_coordinator(max_retries=60):
    """Block until the coordinator is reachable."""
    for i in range(max_retries):
        try:
            r = requests.get(f"{COORDINATOR_URL}/health", timeout=3)
            if r.status_code == 200:
                log.info("Coordinator is up.")
                return
        except requests.ConnectionError:
            pass
        log.info("Waiting for coordinator... (%d/%d)", i + 1, max_retries)
        time.sleep(2)
    log.error("Coordinator not reachable after %d retries. Exiting.", max_retries)
    sys.exit(1)


def register():
    r = requests.post(f"{COORDINATOR_URL}/register", json={"client_id": CLIENT_ID}, timeout=10)
    r.raise_for_status()
    log.info("Registered with coordinator.")


def pull_global_model():
    r = requests.get(f"{COORDINATOR_URL}/global_model", timeout=30)
    r.raise_for_status()
    data = r.json()
    weights = base64_to_weights(data["weights_b64"])
    return weights, data["round"]


def get_round_info():
    r = requests.get(f"{COORDINATOR_URL}/round_info", timeout=10)
    r.raise_for_status()
    return r.json()


def submit_update(weights, data_size, round_num):
    payload = {
        "client_id": CLIENT_ID,
        "round": round_num,
        "weights_b64": weights_to_base64(weights),
        "data_size": data_size,
    }
    r = requests.post(f"{COORDINATOR_URL}/submit_update", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def submit_eval(round_num, accuracy, loss):
    payload = {
        "client_id": CLIENT_ID,
        "round": round_num,
        "accuracy": accuracy,
        "loss": loss,
    }
    requests.post(f"{COORDINATOR_URL}/submit_eval", json=payload, timeout=10)


# training
def train_local(model, train_loader, epochs, lr):
    """Train model on local data and return updated weights."""
    device = torch.device("cpu")
    model.to(device)
    model.train()
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        epoch_loss = 0.0
        for data, target in train_loader:
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        avg = epoch_loss / len(train_loader)
        log.info("Epoch %d/%d  loss=%.4f", epoch + 1, epochs, avg)

    return model.get_weights()


def evaluate(model, test_loader):
    device = torch.device("cpu")
    model.to(device)
    model.eval()
    total_loss = 0.0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            total_loss += nn.functional.cross_entropy(output, target, reduction="sum").item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
    n = len(test_loader.dataset)
    return {"loss": total_loss / n, "accuracy": 100.0 * correct / n}


# main loop
def main():
    log.info("Starting client '%s'.", CLIENT_ID)

    # load data
    log.info("Downloading / loading MNIST...")
    train_dataset, test_dataset = get_mnist_data(data_dir=DATA_DIR)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    log.info("Loading partition from %s", PARTITION_FILE)
    indices = load_partition(PARTITION_FILE)
    train_loader = get_client_dataloader(train_dataset, indices, batch_size=BATCH_SIZE)
    log.info("Partition loaded: %d training samples.", len(indices))

    # wait for coordinator and register
    wait_for_coordinator()
    register()

    # start heartbeat thread
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()
    log.info("Heartbeat thread started (interval=%ds).", HEARTBEAT_INTERVAL)

    # training loop
    model = SimpleNet()
    last_completed_round = -1

    while True:
        info = get_round_info()

        # check if finished
        if info["round"] >= info["total_rounds"] and info["status"] == "complete":
            log.info("All rounds complete. Shutting down.")
            break

        # check if any round to participate in
        if info["status"] == "training" and info["round"] > last_completed_round:
            round_num = info["round"]
            log.info("--- Round %d starting ---", round_num)

            # pull global model
            weights, _ = pull_global_model()
            model.set_weights(weights)

            # train locally
            updated_weights = train_local(model, train_loader, LOCAL_EPOCHS, LEARNING_RATE)

            # submit update
            resp = submit_update(updated_weights, len(indices), round_num)
            log.info("Submitted update for round %d: %s", round_num, resp.get("status"))

            # evaluate global model
            model.set_weights(weights)
            eval_result = evaluate(model, test_loader)
            submit_eval(round_num, eval_result["accuracy"], eval_result["loss"])
            log.info("Round %d eval: accuracy=%.2f%%", round_num, eval_result["accuracy"])

            last_completed_round = round_num
        else:
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()