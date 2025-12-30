import torch
import torch.nn as nn
import torch.optim as optim
from common.models import SimpleNet
import copy

class FederatedClient:
    def __init__(self, client_id, train_loader, test_loader=None):
        self.client_id = client_id
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.model = SimpleNet()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        
    def train(self, epochs=5, lr=0.01):
        """Train the model on local data"""
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
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(self.train_loader)
            train_losses.append(avg_loss)
            print(f"Client {self.client_id} - Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        return train_losses
    
    def evaluate(self):
        """Evaluate model on test data"""
        if self.test_loader is None:
            return None
            
        self.model.eval()
        test_loss = 0
        correct = 0
        
        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                test_loss += nn.functional.cross_entropy(output, target, reduction='sum').item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
        
        test_loss /= len(self.test_loader.dataset)
        accuracy = 100. * correct / len(self.test_loader.dataset)
        
        return {'loss': test_loss, 'accuracy': accuracy}
    
    def get_model_weights(self):
        """Return model weights for aggregation"""
        return copy.deepcopy(self.model.get_weights())
    
    def set_model_weights(self, weights):
        """Update model with new weights"""
        self.model.set_weights(weights)
    
    def get_data_size(self):
        """Return the number of training samples"""
        return len(self.train_loader.dataset)