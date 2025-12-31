import boto3
from datetime import datetime, timedelta
from tabulate import tabulate

def check_resources():
    # ECS
    ecs = boto3.client('ecs')
    clusters = ecs.list_clusters()
    
    print("ECS Clusters:")
    for cluster_arn in clusters['clusterArns']:
        if 'fed-learn' in cluster_arn:
            services = ecs.list_services(cluster=cluster_arn)
            tasks = ecs.list_tasks(cluster=cluster_arn)
            print(f"  - {cluster_arn.split('/')[-1]}")
            print(f"    Services: {len(services.get('serviceArns', []))}")
            print(f"    Running tasks: {len(tasks.get('taskArns', []))}")
    
    # ECR
    ecr = boto3.client('ecr')
    repos = ecr.describe_repositories()
    
    print("\nECR Repositories:")
    for repo in repos['repositories']:
        if 'fed-learn' in repo['repositoryName']:
            images = ecr.list_images(repositoryName=repo['repositoryName'])
            print(f"  - {repo['repositoryName']}: {len(images['imageIds'])} images")
    
    # S3
    s3 = boto3.client('s3')
    
    print("\nS3 Buckets:")
    for bucket in s3.list_buckets()['Buckets']:
        if 'fed-learn' in bucket['Name']:
            try:
                objects = s3.list_objects_v2(Bucket=bucket['Name'])
                count = objects.get('KeyCount', 0)
                size = sum(obj['Size'] for obj in objects.get('Contents', []))
                print(f"  - {bucket['Name']}: {count} objects, {size/1024:.2f} KB")
            except:
                print(f"  - {bucket['Name']}: Access error")
    
    # Costs
    ce = boto3.client('ce')
    end_date = datetime.now().date()
    start_date = end_date.replace(day=1)
    
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': str(start_date),
            'End': str(end_date)
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )
    
    print("\nCurrent Month Costs:")
    costs = []
    for result in response['ResultsByTime'][-7:]:  # Last 7 days
        costs.append([
            result['TimePeriod']['Start'],
            f"${float(result['Total']['UnblendedCost']['Amount']):.4f}"
        ])
    print(tabulate(costs, headers=['Date', 'Cost'], tablefmt='grid'))
    
    total = sum(float(r['Total']['UnblendedCost']['Amount']) 
                for r in response['ResultsByTime'])
    print(f"\nTotal this month: ${total:.2f}")

if __name__ == "__main__":
    check_resources()
