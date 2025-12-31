import boto3

def check_resources():
    print("=== AWS Resources Status ===\n")
    
    # ECS
    ecs = boto3.client('ecs')
    clusters = ecs.list_clusters()
    
    print("ECS Clusters:")
    for cluster_arn in clusters['clusterArns']:
        if 'fed-learn' in cluster_arn:
            services = ecs.list_services(cluster=cluster_arn)
            tasks = ecs.list_tasks(cluster=cluster_arn)
            cluster_name = cluster_arn.split('/')[-1]
            print(f"  - {cluster_name}")
            print(f"    Services: {len(services.get('serviceArns', []))}")
            print(f"    Running tasks: {len(tasks.get('taskArns', []))}")
            
            if len(tasks.get('taskArns', [])) > 0:
                print("    WARNING: Tasks are running (costing money!)")
    
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
                
                # List objects
                if count > 0 and count < 20:  # Only list if reasonable number
                    print("    Contents:")
                    for obj in objects.get('Contents', []):
                        print(f"      - {obj['Key']}")
            except:
                print(f"  - {bucket['Name']}: Access error")

if __name__ == "__main__":
    check_resources()
