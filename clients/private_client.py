import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch.nn as nn
import torch.optim as optim
from clients.client import FederatedClient
from common.privacy import DifferentialPrivacy
import copy

class PrivateFederatedClient(FederatedClient):
    """Federated client with differential privacy"""
    
    def __init__(self, client_id, train_loader, test_loader=None, 
                 epsilon=1.0, delta=1e-5, max_grad_norm=1.0):
        super().__init__(client_id, train_loader, test_loader)
        
        # Initialize differential privacy
        self.privacy_engine = DifferentialPrivacy(
            epsilon=epsilon,
            delta=delta,
            max_grad_norm=max_grad_norm
        )
        
        self.privacy_spent = {'epsilon': 0, 'delta': delta}
        
    def train(self, epochs=5, lr=0.01):
        """Train with differential privacy"""
        self.model.train()
        optimizer = optim.SGD(self.model.parameters(), lr=lr, momentum=0.9)
        criterion = nn.CrossEntropyLoss()
        
        train_losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            
            for batch_idx, (data, target) in enumerate(self.train_loader):
                data, target = data.to(self.device), target.to(self.device)
                
                optimizer.zero_grad()
                output = self.model(data)
                loss = criterion(output, target)
                loss.backward()
                
                # Clip gradients for privacy
                total_norm = self.privacy_engine.clip_gradients(self.model)
                
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(self.train_loader)
            train_losses.append(avg_loss)
            
            print(f"Client {self.client_id} - Epoch {epoch+1}/{epochs}, "
                  f"Loss: {avg_loss:.4f}, Gradient Norm: {total_norm:.4f}")
        
        # Update privacy budget spent
        self.privacy_spent = self.privacy_engine.get_privacy_spent(epochs)
        print(f"Client {self.client_id} - Privacy spent: ε={self.privacy_spent['epsilon_spent']:.2f}")
        
        return train_losses
    
    def get_model_weights(self):
        """Return differentially private model weights"""
        weights = super().get_model_weights()
        
        # Add noise to weights before sending to server
        private_weights = self.privacy_engine.add_noise_to_weights(weights)
        
        return private_weights