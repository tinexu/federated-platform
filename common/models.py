import torch
import torch.nn as nn
import torch.nn.functional as F

class SimpleNet(nn.Module):
    """Simple neural network for MNIST classification."""

    def __init__(self):
        super(SimpleNet, self).__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 10)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = x.view(-1, 784)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return F.log_softmax(x, dim=1)

    def get_weights(self):
        """Extract model weights as a dictionary."""
        return {k: v.cpu().clone() for k, v in self.state_dict().items()} # prevents two things accidentally sharing the same tensor memory; clone() makes a new tensor.

    def set_weights(self, weights):
        """Load weights from dictionary."""
        self.load_state_dict(weights)