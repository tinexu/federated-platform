import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mlops.pipeline import MLOpsPipeline
import torch

def test_mlops_pipeline():
    """Test the complete MLOps pipeline"""
    
    print("=== Testing MLOps Pipeline ===\n")
    
    # Initialize pipeline
    pipeline = MLOpsPipeline(bucket_name='fed-learn-models-1w4zzxzc')
    
    # Simulate model training results
    model_v1 = {
        'layer1.weight': torch.randn(10, 10).tolist(),
        'layer1.bias': torch.randn(10).tolist()
    }
    
    metadata_v1 = {
        'round': 10,
        'accuracy': 0.87,
        'loss': 0.23,
        'epsilon_spent': 2.5,
        'num_clients': 5,
        'message': 'Initial production model'
    }
    
    # Deploy first model
    print("1. Deploying initial model to production...")
    v1_hash = pipeline.deploy_model(model_v1, metadata_v1, 'direct')
    print(f"   Deployed: {v1_hash}\n")
    
    # Simulate improved model
    model_v2 = {
        'layer1.weight': torch.randn(10, 10).tolist(),
        'layer1.bias': torch.randn(10).tolist()
    }
    
    metadata_v2 = {
        'round': 20,
        'accuracy': 0.91,
        'loss': 0.18,
        'epsilon_spent': 3.8,
        'num_clients': 7,
        'parent_version': v1_hash,
        'message': 'Improved model with more clients'
    }
    
    # Deploy with canary strategy
    print("2. Deploying improved model as canary...")
    v2_hash = pipeline.deploy_model(model_v2, metadata_v2, 'canary')
    print(f"   Deployed: {v2_hash}\n")
    
    # Monitor deployment
    print("3. Monitoring deployments...")
    pipeline.monitor_deployment()
    
    # List versions
    print("\n4. Model version history:")
    versions = pipeline.version_manager.list_versions()
    for v in versions:
        print(f"   {v['version_hash']}: {v.get('tags', [])} "
              f"(accuracy: {v.get('accuracy', 'N/A')})")
    
    print("\n=== MLOps Pipeline Test Complete ===")

if __name__ == "__main__":
    test_mlops_pipeline()
