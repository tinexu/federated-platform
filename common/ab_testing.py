import random
import json
from typing import Dict, List, Optional
from datetime import datetime

class ABTestManager:
    """Manages A/B testing for model deployments"""
    
    def __init__(self, version_manager):
        self.version_manager = version_manager
        self.active_tests = {}
    
    def create_test(self, test_name: str, variant_a: str, variant_b: str,
                    traffic_split: float = 0.5) -> Dict:
        """Create a new A/B test between two model versions"""
        
        test_config = {
            'test_id': f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'test_name': test_name,
            'variant_a': {
                'version_hash': variant_a,
                'traffic_percentage': traffic_split
            },
            'variant_b': {
                'version_hash': variant_b,
                'traffic_percentage': 1 - traffic_split
            },
            'metrics': {
                'variant_a': {'requests': 0, 'accuracy': [], 'latency': []},
                'variant_b': {'requests': 0, 'accuracy': [], 'latency': []}
            },
            'started_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        self.active_tests[test_config['test_id']] = test_config
        return test_config
    
    def get_model_for_request(self, test_id: str, user_id: str = None) -> str:
        """Determine which model variant to use for a request"""
        
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.active_tests[test_id]
        
        # Use consistent hashing for user stickiness
        if user_id:
            hash_value = hash(user_id) % 100
            threshold = test['variant_a']['traffic_percentage'] * 100
            
            if hash_value < threshold:
                return test['variant_a']['version_hash']
            else:
                return test['variant_b']['version_hash']
        else:
            # Random assignment
            if random.random() < test['variant_a']['traffic_percentage']:
                return test['variant_a']['version_hash']
            else:
                return test['variant_b']['version_hash']
    
    def record_result(self, test_id: str, variant: str, accuracy: float,
                     latency: float):
        """Record results from an A/B test"""
        
        if test_id not in self.active_tests:
            return
        
        variant_key = 'variant_a' if variant == self.active_tests[test_id]['variant_a']['version_hash'] else 'variant_b'
        
        metrics = self.active_tests[test_id]['metrics'][variant_key]
        metrics['requests'] += 1
        metrics['accuracy'].append(accuracy)
        metrics['latency'].append(latency)
    
    def get_test_results(self, test_id: str) -> Dict:
        """Get current results of an A/B test"""
        
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.active_tests[test_id]
        results = {
            'test_id': test_id,
            'test_name': test['test_name'],
            'duration': self._calculate_duration(test['started_at']),
            'variants': {}
        }
        
        for variant in ['variant_a', 'variant_b']:
            metrics = test['metrics'][variant]
            
            results['variants'][variant] = {
                'version_hash': test[variant]['version_hash'],
                'traffic_percentage': test[variant]['traffic_percentage'],
                'requests': metrics['requests'],
                'avg_accuracy': sum(metrics['accuracy']) / len(metrics['accuracy']) if metrics['accuracy'] else 0,
                'avg_latency': sum(metrics['latency']) / len(metrics['latency']) if metrics['latency'] else 0,
                'confidence': self._calculate_confidence(metrics)
            }
        
        # Determine winner if enough data
        results['winner'] = self._determine_winner(results['variants'])
        
        return results
    
    def _calculate_duration(self, started_at: str) -> str:
        """Calculate test duration"""
        start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        duration = datetime.utcnow() - start.replace(tzinfo=None)
        return str(duration)
    
    def _calculate_confidence(self, metrics: Dict) -> float:
        """Calculate statistical confidence (simplified)"""
        if metrics['requests'] < 100:
            return 0.0
        
        # Simplified confidence calculation
        # In production, use proper statistical tests
        return min(0.95, metrics['requests'] / 1000)
    
    def _determine_winner(self, variants: Dict) -> Optional[str]:
        """Determine winning variant if statistically significant"""
        
        a_acc = variants['variant_a']['avg_accuracy']
        b_acc = variants['variant_b']['avg_accuracy']
        a_conf = variants['variant_a']['confidence']
        b_conf = variants['variant_b']['confidence']
        
        # Need high confidence for both
        if a_conf < 0.95 or b_conf < 0.95:
            return None
        
        # Require 2% improvement
        if abs(a_acc - b_acc) < 0.02:
            return None
        
        return 'variant_a' if a_acc > b_acc else 'variant_b'