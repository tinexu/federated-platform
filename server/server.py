import torch
import copy
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models import SimpleNet
from collections import OrderedDict

class FederatedServer:
    def __init__(self):
        self.global_model = SimpleNet()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.global_model.to(self.device)
        self.round = 0
        
    def get_global_weights(self):
        """Get current global model weights"""
        return copy.deepcopy(self.global_model.get_weights())
    
    def federated_averaging(self, client_weights_list, client_sizes):
        """
        Perform Federated Averaging (FedAvg)
        client_weights_list: List of model weights from each client
        client_sizes: List of number of samples for each client
        """
        # Calculate total number of samples
        total_size = sum(client_sizes)
        
        # Initialize aggregated weights
        aggregated_weights = OrderedDict()
        
        # Weight each client's contribution by their data size
        for key in client_weights_list[0].keys():
            aggregated_weights[key] = torch.zeros_like(client_weights_list[0][key])
            
            for client_idx, client_weights in enumerate(client_weights_list):
                weight = client_sizes[client_idx] / total_size
                aggregated_weights[key] += weight * client_weights[key]
        
        return aggregated_weights
    
    def update_global_model(self, aggregated_weights):
        """Update the global model with aggregated weights"""
        self.global_model.set_weights(aggregated_weights)
        self.round += 1
    
    def evaluate_global_model(self, test_loader):
        """Evaluate the global model"""
        self.global_model.eval()
        test_loss = 0
        correct = 0
        
        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.global_model(data)
                test_loss += torch.nn.functional.cross_entropy(output, target, reduction='sum').item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
        
        test_loss /= len(test_loader.dataset)
        accuracy = 100. * correct / len(test_loader.dataset)
        
        return {'loss': test_loss, 'accuracy': accuracy, 'round': self.round}