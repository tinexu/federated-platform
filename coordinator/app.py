"""
Federated Learning Coordinator Service.

Manages training rounds, accepts client registrations, collects model updates,
performs aggregation, and broadcasts the global model.

Endpoints:
    POST /register          - Client registers with the coordinator
    GET  /global_model      - Client pulls the current global model
    GET  /round_info        - Client checks current round status
    POST /submit_update     - Client submits trained model weights
    GET  /health            - Health check
    GET  /metrics           - Training metrics (for dashboard / debugging)
"""

# real http server using flask
# flow of one round:
# 1. all 5 clients POST to /register on startup and once 5 are registered coordinator sets the round status to training
# 2. each client polls /round_info and sees status is training with round=0 so each GET /global_model to pull current weights
# 3. each client trains locally and then POSTs updated weights to /submit_update
# 4. each time /submit_update called, the aggregation logic checks if all 5 updates are in and once they are the federated averaging function is run, updates global model, increments the current
# round and then status is set back to training for the next round
# 5. repeated until all rounds are completed

# threading.Lock bc flask is concurrent (two clients submit at the same time)so critical section needs to be protected
# federated averaging function adapted to work with base64-encoded weights from http instead of in-memory dicts

import os
import time
import threading
import logging
from collections import OrderedDict

import torch
from flask import Flask, request, jsonify

from common.models import SimpleNet
from common.serialization import weights_to_base64, base64_to_weights
from common import protocol

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [COORDINATOR] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

# coordinator state
NUM_CLIENTS = int(os.environ.get("NUM_CLIENTS", 5))
NUM_ROUNDS = int(os.environ.get("NUM_ROUNDS", 10))
ROUND_TIMEOUT = int(os.environ.get("ROUND_TIMEOUT", 300))  # seconds

global_model = SimpleNet()
current_round = 0
round_status = protocol.ROUND_WAITING  # waiting for clients to register

# registered clients: {client_id: {"registered_at": ts}}
clients = {}

# updates received for the current round: {client_id: {"weights_b64": ..., "data_size": ...}}
round_updates = {}

# history of global accuracy per round (filled by clients reporting eval)
metrics_history = []

lock = threading.Lock()


# aggregation function
def federated_averaging(updates):
    """Weighted FedAvg over submitted client updates."""
    weight_list = []
    sizes = []
    for cid, u in updates.items():
        w = base64_to_weights(u["weights_b64"])
        weight_list.append(w)
        sizes.append(u["data_size"])

    total = sum(sizes)
    aggregated = OrderedDict()
    for key in weight_list[0].keys():
        aggregated[key] = torch.zeros_like(weight_list[0][key])
        for i, w in enumerate(weight_list):
            aggregated[key] += (sizes[i] / total) * w[key]
    return aggregated


def maybe_aggregate():
    """Check if all expected updates arrived; if so, aggregate and advance."""
    global current_round, round_status, round_updates

    expected = len(clients)
    received = len(round_updates)

    if received >= expected and expected > 0:
        log.info(
            "Round %d: received %d/%d updates, aggregating...",
            current_round, received, expected,
        )
        round_status = protocol.ROUND_AGGREGATING
        aggregated = federated_averaging(round_updates)
        global_model.set_weights(aggregated)
        round_status = protocol.ROUND_COMPLETE

        log.info("Round %d complete. Global model updated.", current_round)

        # Advance to next round (or finish)
        current_round += 1
        round_updates = {}
        if current_round < NUM_ROUNDS:
            round_status = protocol.ROUND_TRAINING
            log.info("Starting round %d.", current_round)
        else:
            round_status = protocol.ROUND_COMPLETE
            log.info("All %d rounds finished.", NUM_ROUNDS)


# endpoints
@app.route("/register", methods=["POST"])
def register():
    global round_status, current_round
    data = request.get_json()
    cid = data.get("client_id")
    with lock:
        clients[cid] = {"registered_at": time.time()}
        log.info("Client '%s' registered (%d/%d).", cid, len(clients), NUM_CLIENTS)

        # Once all clients register, start round 0
        if len(clients) >= NUM_CLIENTS and round_status == protocol.ROUND_WAITING:
            current_round = 0
            round_status = protocol.ROUND_TRAINING
            log.info("All clients registered. Starting round 0.")

    return jsonify({"status": "ok", "client_id": cid})


@app.route("/global_model", methods=["GET"])
def get_global_model():
    b64 = weights_to_base64(global_model.get_weights())
    return jsonify({"weights_b64": b64, "round": current_round})


@app.route("/round_info", methods=["GET"])
def round_info():
    return jsonify({
        "round": current_round,
        "status": round_status,
        "total_rounds": NUM_ROUNDS,
        "registered_clients": len(clients),
        "updates_received": len(round_updates),
    })


@app.route("/submit_update", methods=["POST"])
def submit_update():
    data = request.get_json()
    cid = data["client_id"]
    round_num = data["round"]

    with lock:
        if round_num != current_round:
            return jsonify({"status": "stale", "msg": f"Expected round {current_round}, got {round_num}"}), 409

        round_updates[cid] = {
            "weights_b64": data["weights_b64"],
            "data_size": data["data_size"],
        }
        log.info(
            "Round %d: received update from '%s' (%d/%d).",
            current_round, cid, len(round_updates), len(clients),
        )
        maybe_aggregate()

    return jsonify({"status": "ok"})


@app.route("/submit_eval", methods=["POST"])
def submit_eval():
    """Clients can optionally report their local eval of the global model."""
    data = request.get_json()
    with lock:
        metrics_history.append({
            "round": data.get("round"),
            "client_id": data.get("client_id"),
            "accuracy": data.get("accuracy"),
            "loss": data.get("loss"),
            "timestamp": time.time(),
        })
    return jsonify({"status": "ok"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "round": current_round})


@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "current_round": current_round,
        "round_status": round_status,
        "total_rounds": NUM_ROUNDS,
        "registered_clients": list(clients.keys()),
        "history": metrics_history,
    })


# entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("COORDINATOR_PORT", 5000))
    log.info("Coordinator starting on port %d, expecting %d clients, %d rounds.", port, NUM_CLIENTS, NUM_ROUNDS)
    app.run(host="0.0.0.0", port=port)