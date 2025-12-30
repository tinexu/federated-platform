import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
from experiments.basic import run_federated_learning

def compare_iid_vs_noniid():
    """Show how Non-IID data affects training"""
    
    # Run with IID data
    print("Running IID experiment...")
    _, _, iid_history = run_federated_learning(
        num_clients=5,
        num_rounds=10,
        local_epochs=5,
        non_iid=False  # IID data
    )
    
    # Run with Non-IID data  
    print("\nRunning Non-IID experiment...")
    _, _, noniid_history = run_federated_learning(
        num_clients=5,
        num_rounds=10,
        local_epochs=5,
        non_iid=True  # Non-IID data
    )
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.plot(iid_history, 'g-', label='IID Data', linewidth=2)
    plt.plot(noniid_history, 'r-', label='Non-IID Data', linewidth=2)
    plt.xlabel('Round')
    plt.ylabel('Global Model Accuracy (%)')
    plt.title('Impact of Data Distribution on Federated Learning')
    plt.legend()
    plt.grid(True)
    
    # Add annotations
    final_iid = iid_history[-1]
    final_noniid = noniid_history[-1]
    plt.text(15, final_iid + 1, f'IID: {final_iid:.1f}%', fontsize=10)
    plt.text(15, final_noniid - 2, f'Non-IID: {final_noniid:.1f}%', fontsize=10)
    
    plt.savefig('experiments/iid_vs_noniid_impact.png')
    plt.show()
    
    print("\nResults:")
    print(f"IID Final Accuracy: {final_iid:.2f}%")
    print(f"Non-IID Final Accuracy: {final_noniid:.2f}%")
    print(f"Accuracy Gap: {final_iid - final_noniid:.2f}%")

if __name__ == "__main__":
    compare_iid_vs_noniid()