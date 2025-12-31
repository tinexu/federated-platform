import torch
import numpy as np
from typing import Dict, Any

class DifferentialPrivacy:
    """
    Implements differential privacy for federated learning
    Using the Gaussian mechanism for gradient perturbation
    """
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5, 
                 max_grad_norm: float = 1.0):
        """
        Args:
            epsilon: Privacy budget (smaller = more private)
            delta: Failure probability
            max_grad_norm: Maximum L2 norm for gradient clipping
        """
        self.epsilon = epsilon
        self.delta = delta
        self.max_grad_norm = max_grad_norm
        
        # Calculate noise scale using privacy analysis
        self.noise_scale = self._calculate_noise_scale()
        
    def _calculate_noise_scale(self) -> float:
        """Calculate noise scale to achieve (epsilon, delta)-DP"""
        # Using the analytical gaussian mechanism
        return (2 * self.max_grad_norm * np.sqrt(2 * np.log(1.25 / self.delta))) / self.epsilon
    
    def add_noise_to_weights(self, weights: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Add Gaussian noise to model weights for privacy"""
        noisy_weights = {}
        
        for name, weight in weights.items():
            # Add Gaussian noise scaled by the privacy parameters
            noise = torch.normal(
                mean=0,
                std=self.noise_scale,
                size=weight.shape,
                device=weight.device
            )
            noisy_weights[name] = weight + noise
            
        return noisy_weights
    
    def clip_gradients(self, model: torch.nn.Module) -> float:
        """Clip gradients to bounded L2 norm"""
        total_norm = 0.0
        
        # Calculate total gradient norm
        for param in model.parameters():
            if param.grad is not None:
                param_norm = param.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
        total_norm = np.sqrt(total_norm)
        
        # Clip gradients if needed
        clip_coef = self.max_grad_norm / (total_norm + 1e-6)
        if clip_coef < 1:
            for param in model.parameters():
                if param.grad is not None:
                    param.grad.data.mul_(clip_coef)
        
        return total_norm
    
    def get_privacy_spent(self, num_rounds: int) -> Dict[str, float]:
        """Calculate privacy budget spent after num_rounds"""
        # Using advanced composition theorem
        total_epsilon = np.sqrt(2 * num_rounds * np.log(1/self.delta)) * self.epsilon
        total_epsilon += num_rounds * self.epsilon * (np.exp(self.epsilon) - 1)
        
        return {
            'epsilon_spent': min(total_epsilon, num_rounds * self.epsilon),
            'delta': self.delta,
            'rounds': num_rounds
        }