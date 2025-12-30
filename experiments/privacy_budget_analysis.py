import numpy as np
import matplotlib.pyplot as plt

def simulate_privacy_leakage():
    """
    Simulate how model updates could leak information
    This shows why we need differential privacy in Phase 3
    """
    rounds = 20
    clients = 5
    
    # Simulate "information leakage" over rounds
    # Without privacy: leakage accumulates
    # With privacy: leakage is bounded
    
    no_privacy_leakage = np.cumsum(np.random.exponential(0.1, rounds))
    with_privacy_leakage = np.array([min(1.0, sum(np.random.exponential(0.01, i+1))) 
                                     for i in range(rounds)])
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(rounds), no_privacy_leakage, 'r-', 
             label='Without Differential Privacy', linewidth=2)
    plt.plot(range(rounds), with_privacy_leakage, 'g-', 
             label='With Differential Privacy (ε=1.0)', linewidth=2)
    plt.xlabel('Federated Learning Rounds')
    plt.ylabel('Potential Information Leakage')
    plt.title('Privacy Preservation in Federated Learning')
    plt.legend()
    plt.grid(True)
    plt.savefig('privacy_analysis.png')
    plt.show()

if __name__ == "__main__":
    simulate_privacy_leakage()