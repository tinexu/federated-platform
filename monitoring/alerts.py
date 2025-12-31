import boto3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class AlertManager:
    """Manages alerts and notifications for the federated learning system"""
    
    def __init__(self):
        self.sns_client = boto3.client('sns')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # In production, this would be an SNS topic ARN
        self.sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', None)
        
        # Alert thresholds
        self.thresholds = {
            'min_accuracy': 0.80,
            'max_privacy_budget': 10.0,
            'min_active_clients': 2,
            'max_training_time': 300  # seconds
        }
        
        # Alert history (in production, use DynamoDB)
        self.alert_history = []
    
    def send_notification(self, message: str, severity: str = 'info', 
                         metadata: Dict = None):
        """Send notification via configured channels"""
        
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'message': message,
            'metadata': metadata or {}
        }
        
        # Log to console
        print(f"[{severity.upper()}] {message}")
        
        # Add to history
        self.alert_history.append(alert)
        
        # Send to SNS if configured
        if self.sns_topic_arn and severity in ['warning', 'critical']:
            try:
                self.sns_client.publish(
                    TopicArn=self.sns_topic_arn,
                    Subject=f"FL Alert: {severity.upper()}",
                    Message=json.dumps(alert, indent=2)
                )
            except Exception as e:
                print(f"Failed to send SNS notification: {e}")
        
        # Send CloudWatch alarm for critical alerts
        if severity == 'critical':
            self._create_cloudwatch_alarm(message, metadata)
        
        return alert
    
    def check_model_metrics(self, metrics: Dict) -> List[Dict]:
        """Check if model metrics meet thresholds"""
        alerts = []
        
        # Check accuracy
        if metrics.get('accuracy', 1.0) < self.thresholds['min_accuracy']:
            alerts.append(self.send_notification(
                f"Model accuracy {metrics['accuracy']:.2%} below threshold "
                f"{self.thresholds['min_accuracy']:.2%}",
                severity='warning',
                metadata=metrics
            ))
        
        # Check privacy budget
        if metrics.get('privacy_budget_used', 0) > self.thresholds['max_privacy_budget']:
            alerts.append(self.send_notification(
                f"Privacy budget exhausted: {metrics['privacy_budget_used']:.2f} > "
                f"{self.thresholds['max_privacy_budget']}",
                severity='critical',
                metadata=metrics
            ))
        
        return alerts
    
    def check_system_health(self, system_metrics: Dict) -> List[Dict]:
        """Check overall system health"""
        alerts = []
        
        # Check active clients
        active_clients = system_metrics.get('active_clients', 0)
        if active_clients < self.thresholds['min_active_clients']:
            alerts.append(self.send_notification(
                f"Low client participation: {active_clients} clients active",
                severity='warning',
                metadata=system_metrics
            ))
        
        # Check training time
        training_time = system_metrics.get('avg_training_time', 0)
        if training_time > self.thresholds['max_training_time']:
            alerts.append(self.send_notification(
                f"Training taking too long: {training_time:.1f}s average",
                severity='warning',
                metadata=system_metrics
            ))
        
        return alerts
    
    def _create_cloudwatch_alarm(self, message: str, metadata: Dict):
        """Create CloudWatch alarm for critical issues"""
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=f"FL-Critical-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='CriticalAlerts',
                Namespace='FederatedLearning',
                Period=60,
                Statistic='Sum',
                Threshold=0,
                ActionsEnabled=True,
                AlarmDescription=message,
                Tags=[
                    {'Key': 'System', 'Value': 'FederatedLearning'},
                    {'Key': 'Severity', 'Value': 'Critical'}
                ]
            )
        except Exception as e:
            print(f"Failed to create CloudWatch alarm: {e}")
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        """Get summary of recent alerts"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        recent_alerts = [
            a for a in self.alert_history 
            if datetime.fromisoformat(a['timestamp']).timestamp() > cutoff
        ]
        
        summary = {
            'total_alerts': len(recent_alerts),
            'by_severity': {},
            'recent_critical': []
        }
        
        for alert in recent_alerts:
            severity = alert['severity']
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            if severity == 'critical':
                summary['recent_critical'].append(alert)
        
        return summary
    
    def configure_thresholds(self, new_thresholds: Dict):
        """Update alert thresholds"""
        self.thresholds.update(new_thresholds)
        
        self.send_notification(
            f"Alert thresholds updated: {new_thresholds}",
            severity='info'
        )
    
    def test_alerts(self):
        """Test alert system with sample alerts"""
        print("=== Testing Alert System ===")
        
        # Test different severity levels
        self.send_notification("System started", severity='info')
        self.send_notification("Low client participation", severity='warning')
        self.send_notification("Privacy budget exceeded", severity='critical')
        
        # Test metric checks
        test_metrics = {
            'accuracy': 0.75,  # Below threshold
            'privacy_budget_used': 12.0,  # Above threshold
            'round': 50
        }
        
        alerts = self.check_model_metrics(test_metrics)
        print(f"\nGenerated {len(alerts)} alerts from metric check")
        
        # Get summary
        summary = self.get_alert_summary(hours=1)
        print(f"\nAlert Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    # Test the alert system
    manager = AlertManager()
    manager.test_alerts()