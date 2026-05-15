"""
Protocol definitions for coordinator-client communication.
All messages are serialized as JSON with model weights sent as binary tensors.
"""

# round status values
ROUND_WAITING = "waiting"
ROUND_TRAINING = "training"
ROUND_AGGREGATING = "aggregating"
ROUND_COMPLETE = "complete"

# client status values
CLIENT_REGISTERED = "registered"
CLIENT_TRAINING = "training"
CLIENT_DONE = "done"
CLIENT_DEAD = "dead"

# heartbeat/liveness
HEARTBEAT_INTERVAL = 3      # seconds between client heartbeats
SUSPECT_TIMEOUT = 10         # seconds with no heartbeat: suspected
DEAD_TIMEOUT = 30            # seconds with no heartbeat: confirmed dead

CLIENT_ALIVE = "alive"
CLIENT_SUSPECTED = "suspected"