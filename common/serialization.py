"""
Utilities for serializing/deserializing model weights over HTTP.
Uses torch save/load with in-memory BytesIO buffers.
"""
# converts weights to base64 strings, which are JSON-safe, and back

# process:
# 1. client calls model.get_weights() which returns a dict of tensors
# 2. weights_to_base64() packs that into a string
# 3. string goes into a JSON POST body
# 4. base64_to_weights() unpacks it back into tensors

import io
import base64
import torch


def weights_to_base64(weights: dict) -> str:
    """Serialize model weights dict to a base64 string."""
    buffer = io.BytesIO()
    torch.save(weights, buffer)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def base64_to_weights(b64_str: str) -> dict:
    """Deserialize a base64 string back to model weights dict."""
    raw = base64.b64decode(b64_str)
    buffer = io.BytesIO(raw)
    return torch.load(buffer, map_location="cpu", weights_only=True)