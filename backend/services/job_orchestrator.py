import boto3
import json

class JobOrchestrator:
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.ecs_client = boto3.client('ecs')
        self.cloudformation = boto3.client('cloudformation')
        
    def deploy_job(self, job):
        """Deploy FL infrastructure for a job"""
        
        # Create CloudFormation stack for this job
        stack_name = f"fl-job-{job.id}"
        
        template = self._generate_cf_template(job.config)
        
        self.cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=json.dumps(template),
            Parameters=[
                {
                    'ParameterKey': 'JobId',
                    'ParameterValue': job.id
                },
                {
                    'ParameterKey': 'NumClients',
                    'ParameterValue': str(job.config['num_clients'])
                }
            ]
        )
        
        # Create Lambda functions for coordination
        coordinator_arn = self._deploy_coordinator(job)
        
        # Schedule training rounds
        self._schedule_rounds(job)
        
        return {
            'stack_name': stack_name,
            'endpoint': f"https://api.fl-platform.com/v1/jobs/{job.id}",
            'coordinator_arn': coordinator_arn
        }
    
    def _generate_cf_template(self, config):
        """Generate CloudFormation template for FL job"""
        
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "JobQueue": {
                    "Type": "AWS::SQS::Queue",
                    "Properties": {
                        "QueueName": f"fl-job-{config['name']}-queue"
                    }
                },
                "ResultsBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": f"fl-results-{config['name']}"
                    }
                },
            }
        }