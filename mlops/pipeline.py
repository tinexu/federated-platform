import os
import sys
import json
# import boto3
from datetime import datetime

import typing as Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.model_versioning import ModelVersionManager
from common.ab_testing import ABTestManager
from monitoring.alerts import AlertManager

class MLOpsPipeline:
    """Complete MLOps pipeline for federated learning"""
    
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.version_manager = ModelVersionManager(bucket_name)
        self.ab_manager = ABTestManager(self.version_manager)
        self.alert_manager = AlertManager()
        
    def deploy_model(self, model_state: Dict, metadata: Dict,
                    deployment_strategy: str = 'canary') -> str:
        """Deploy a new model version with specified strategy"""
        
        # Save model version
        version_hash = self.version_manager.save_model_version(
            model_state, metadata
        )
        
        print(f"Saved model version: {version_hash}")
        
        if deployment_strategy == 'direct':
            # Direct deployment to production
            self.version_manager.tag_version(version_hash, 'production')
            self.alert_manager.send_notification(
                f"Model {version_hash} deployed to production"
            )
            
        elif deployment_strategy == 'canary':
            # Canary deployment (10% traffic initially)
            current_prod = self.version_manager.get_version_by_tag('production')
            
            if current_prod:
                # Create A/B test with 10% traffic to new model
                test = self.ab_manager.create_test(
                    test_name=f"Canary deployment {version_hash}",
                    variant_a=current_prod['metadata']['version_hash'],
                    variant_b=version_hash,
                    traffic_split=0.9  # 90% to current, 10% to new
                )
                
                print(f"Started canary deployment: {test['test_id']}")
                
                # Tag as canary
                self.version_manager.tag_version(version_hash, 'canary')
            else:
                # No current production, deploy directly
                self.version_manager.tag_version(version_hash, 'production')
        
        elif deployment_strategy == 'blue_green':
            # Blue-green deployment
            self.version_manager.tag_version(version_hash, 'staging')
            
            print(f"Model {version_hash} deployed to staging")
            print("Run 'promote_to_production' when ready")
        
        return version_hash
    
    def promote_to_production(self, version_hash: str):
        """Promote a model version to production"""
        
        # Get model metadata
        model_data = self.version_manager.get_model_version(version_hash)
        
        # Check model meets production criteria
        if not self._validate_production_ready(model_data['metadata']):
            raise ValueError("Model does not meet production criteria")
        
        # Perform rollback-safe promotion
        self.version_manager.rollback(version_hash)
        
        self.alert_manager.send_notification(
            f"Model {version_hash} promoted to production"
        )
        
        return version_hash
    
    def monitor_deployment(self, test_id: str = None):
        """Monitor active deployments"""
        
        if test_id:
            # Monitor specific A/B test
            results = self.ab_manager.get_test_results(test_id)
            
            print(f"Test: {results['test_name']}")
            print(f"Duration: {results['duration']}")
            
            for variant, data in results['variants'].items():
                print(f"\n{variant}:")
                print(f"  Requests: {data['requests']}")
                print(f"  Accuracy: {data['avg_accuracy']:.4f}")
                print(f"  Latency: {data['avg_latency']:.2f}ms")
                print(f"  Confidence: {data['confidence']:.2%}")
            
            if results['winner']:
                print(f"\nWinner: {results['winner']} (statistically significant)")
                
                # Auto-promote winner if configured
                if os.environ.get('AUTO_PROMOTE_WINNER', 'false') == 'true':
                    winner_hash = results['variants'][results['winner']]['version_hash']
                    self.promote_to_production(winner_hash)
        else:
            # General monitoring
            versions = self.version_manager.list_versions(limit=5)
            
            print("Recent model versions:")
            for v in versions:
                print(f"  {v['version_hash']}: {v.get('tags', [])} "
                      f"(accuracy: {v.get('accuracy', 'N/A')})")
    
    def rollback_production(self):
        """Rollback to previous production version"""
        
        previous = self.version_manager.get_version_by_tag('previous-production')
        
        if not previous:
            raise ValueError("No previous production version found")
        
        version_hash = previous['metadata']['version_hash']
        self.version_manager.rollback(version_hash)
        
        self.alert_manager.send_notification(
            f"ROLLBACK: Reverted to model {version_hash}",
            severity='high'
        )
        
        return version_hash
    
    def _validate_production_ready(self, metadata: Dict) -> bool:
        """Validate model meets production criteria"""
        
        # Check accuracy threshold
        min_accuracy = float(os.environ.get('MIN_PROD_ACCURACY', '0.85'))
        if metadata.get('accuracy', 0) < min_accuracy:
            print(f"Accuracy {metadata.get('accuracy')} below threshold {min_accuracy}")
            return False
        
        # Check privacy budget
        max_epsilon = float(os.environ.get('MAX_PROD_EPSILON', '5.0'))
        if metadata.get('privacy_budget_used', 0) > max_epsilon:
            print(f"Privacy budget {metadata.get('privacy_budget_used')} exceeds {max_epsilon}")
            return False
        
        # Check minimum clients participated
        min_clients = int(os.environ.get('MIN_PROD_CLIENTS', '3'))
        if metadata.get('num_clients', 0) < min_clients:
            print(f"Only {metadata.get('num_clients')} clients, need {min_clients}")
            return False
        
        return True

# Alert manager (simplified)
class AlertManager:
    def send_notification(self, message: str, severity: str = 'info'):
        # In production, integrate with PagerDuty, Slack, etc.
        print(f"[{severity.upper()}] {message}")