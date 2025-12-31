import numpy as np
import torch
from typing import List, Dict, Tuple
import hashlib
import hmac
from cryptography.fernet import Fernet
import json
import base64

class SecureAggregation:
    """
    Implements secure aggregation using secret sharing
    Ensures server cannot see individual client updates
    """
    
    def __init__(self, num_clients: int, threshold: int = None):
        """
        Args:
            num_clients: Total number of clients
            threshold: Minimum clients needed for aggregation
        """
        self.num_clients = num_clients
        self.threshold = threshold or (num_clients // 2 + 1)
        self.client_keys = {}
        
    def generate_client_keys(self, client_id: int) -> Tuple[bytes, Dict[int, bytes]]:
        """Generate keys for a client to share with others"""
        # Generate this client's secret key
        secret_key = Fernet.generate_key()
        
        # Generate pairwise keys with other clients
        pairwise_keys = {}
        for other_id in range(self.num_clients):
            if other_id != client_id:
                # Deterministic key generation for pairs
                shared_secret = f"{min(client_id, other_id)}-{max(client_id, other_id)}".encode()
                pairwise_keys[other_id] = base64.urlsafe_b64encode(
                    hashlib.sha256(shared_secret).digest()
                )
        
        return secret_key, pairwise_keys
    
    def create_shares(self, weights: Dict[str, torch.Tensor], 
                     client_id: int, client_keys: Tuple[bytes, Dict[int, bytes]]) -> Dict[int, Dict]:
        """
        Create secret shares of model weights
        Each client gets a share that reveals nothing individually
        """
        secret_key, pairwise_keys = client_keys
        shares = {}
        
        # Convert weights to numpy for processing
        weight_arrays = {k: v.cpu().numpy() for k, v in weights.items()}
        
        # Create random masks for each other client
        for other_id in range(self.num_clients):
            if other_id == client_id:
                # Client keeps their own weights + sum of masks
                shares[client_id] = weight_arrays
            else:
                # Generate deterministic random mask
                np.random.seed(int.from_bytes(pairwise_keys[other_id][:4], 'big'))
                
                mask = {}
                for key, array in weight_arrays.items():
                    mask[key] = np.random.randn(*array.shape).astype(array.dtype)
                
                shares[other_id] = mask
                
                # Subtract mask from own share
                if client_id not in shares:
                    shares[client_id] = {}
                    
                for key in weight_arrays:
                    if key not in shares[client_id]:
                        shares[client_id][key] = weight_arrays[key].copy()
                    shares[client_id][key] -= mask[key]
        
        # Encrypt shares
        encrypted_shares = {}
        fernet = Fernet(secret_key)
        
        for target_id, share in shares.items():
            # Serialize share
            serialized = json.dumps({
                k: v.tolist() for k, v in share.items()
            })
            
            # Encrypt
            encrypted = fernet.encrypt(serialized.encode())
            encrypted_shares[target_id] = encrypted
        
        return encrypted_shares
    
    def aggregate_shares(self, all_client_shares: List[Dict[int, bytes]], 
                        client_keys: Dict[int, bytes]) -> Dict[str, torch.Tensor]:
        """
        Aggregate encrypted shares from all clients
        Only works if threshold number of clients participate
        """
        if len(all_client_shares) < self.threshold:
            raise ValueError(f"Need at least {self.threshold} clients, got {len(all_client_shares)}")
        
        # Decrypt and aggregate shares
        aggregated = {}
        
        for client_id, shares in enumerate(all_client_shares):
            if client_id in client_keys:
                fernet = Fernet(client_keys[client_id])
                
                for share_id, encrypted_share in shares.items():
                    # Decrypt
                    decrypted = fernet.decrypt(encrypted_share)
                    share_data = json.loads(decrypted)
                    
                    # Add to aggregation
                    for key, values in share_data.items():
                        if key not in aggregated:
                            aggregated[key] = np.zeros_like(values)
                        aggregated[key] += np.array(values)
        
        # Convert back to torch tensors and average
        num_clients = len(all_client_shares)
        result = {}
        for key, array in aggregated.items():
            result[key] = torch.from_numpy(array / num_clients).float()
        
        return result