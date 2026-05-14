"""
Protocol definitions for coordinator-client communication.
All messages are serialized as JSON with model weights sent as binary tensors.
"""

# Round status values
ROUND_WAITING = "waiting"
ROUND_TRAINING = "training"
ROUND_AGGREGATING = "aggregating"
ROUND_COMPLETE = "complete"

# Client status values
CLIENT_REGISTERED = "registered"
CLIENT_TRAINING = "training"
CLIENT_DONE = "done"
CLIENT_DEAD = "dead"