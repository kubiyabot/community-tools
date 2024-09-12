from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

s3_list_buckets = AWSCliTool(
    name="s3_list_buckets",
    description="List S3 buckets",
    content="aws s3 ls",
    args=[],
)

s3_create_bucket = AWSCliTool(
    name="s3_create_bucket",
    description="Create an S3 bucket",
    content="aws s3 mb s3://$bucket_name --region $region",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to create (e.g., 'my-unique-bucket')", required=True),
        Arg(name="region", type="str", description="AWS region for the bucket (e.g., 'us-west-2')", required=True),
    ],
)

s3_delete_bucket = AWSCliTool(
    name="s3_delete_bucket",
    description="Delete an S3 bucket",
    content="aws s3 rb s3://$bucket_name --force",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to delete (e.g., 'my-unique-bucket')", required=True),
    ],
)

s3_list_objects = AWSCliTool(
    name="s3_list_objects",
    description="List objects in an S3 bucket",
    content="aws s3 ls s3://$bucket_name $([[ -n \"$prefix\" ]] && echo \"$prefix\")",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to list objects from (e.g., 'my-bucket')", required=True),
        Arg(name="prefix", type="str", description="Prefix to filter objects (e.g., 'folder/')", required=False),
    ],
)

s3_bulk_delete = AWSSdkTool(
    name="s3_bulk_delete",
    description="Delete multiple objects from an S3 bucket",
    content="""
import boto3

def bulk_delete(bucket_name, prefix):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    
    objects_to_delete = [{'Key': obj.key} for obj in bucket.objects.filter(Prefix=prefix)]
    
    if objects_to_delete:
        bucket.delete_objects(Delete={'Objects': objects_to_delete})
        print(f"Deleted {len(objects_to_delete)} objects from {bucket_name} with prefix {prefix}")
    else:
        print(f"No objects found in {bucket_name} with prefix {prefix}")

bulk_delete(bucket_name, prefix)
    """,
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to delete objects from (e.g., 'my-bucket')", required=True),
        Arg(name="prefix", type="str", description="Prefix of objects to delete (e.g., 'logs/')", required=True),
    ],
    long_running=True,
)

s3_bucket_size_analyzer = AWSSdkTool(
    name="s3_bucket_size_analyzer",
    description="Analyze the size of objects in an S3 bucket",
    content="""
import boto3
from collections import defaultdict

def analyze_bucket_size(bucket_name, prefix=''):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    
    total_size = 0
    size_distribution = defaultdict(int)
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            size = obj['Size']
            total_size += size
            
            if size < 1024:
                size_distribution['< 1 KB'] += 1
            elif size < 1024 * 1024:
                size_distribution['1 KB - 1 MB'] += 1
            elif size < 1024 * 1024 * 10:
                size_distribution['1 MB - 10 MB'] += 1
            elif size < 1024 * 1024 * 100:
                size_distribution['10 MB - 100 MB'] += 1
            else:
                size_distribution['> 100 MB'] += 1
    
    print(f"Total size of objects: {total_size / (1024 * 1024 * 1024):.2f} GB")
    print("Size distribution:")
    for category, count in size_distribution.items():
        print(f"{category}: {count} objects")

analyze_bucket_size(bucket_name, prefix)
    """,
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket to analyze (e.g., 'my-data-bucket')", required=True),
        Arg(name="prefix", type="str", description="Prefix to filter objects (e.g., 'data/2023/')", required=False),
    ],
    long_running=True,
)

s3_upload_file = AWSCliTool(
    name="s3_upload_file",
    description="Upload a file to an S3 bucket",
    content="aws s3 cp $local_file_path s3://$bucket_name/$s3_file_path",
    args=[
        Arg(name="local_file_path", type="str", description="Path to the local file to upload", required=True),
        Arg(name="bucket_name", type="str", description="Name of the S3 bucket to upload to", required=True),
        Arg(name="s3_file_path", type="str", description="Destination path in the S3 bucket", required=True),
    ],
)

s3_download_file = AWSCliTool(
    name="s3_download_file",
    description="Download a file from an S3 bucket",
    content="aws s3 cp s3://$bucket_name/$s3_file_path $local_file_path",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the S3 bucket to download from", required=True),
        Arg(name="s3_file_path", type="str", description="Path of the file in the S3 bucket", required=True),
        Arg(name="local_file_path", type="str", description="Local path to save the downloaded file", required=True),
    ],
)

tool_registry.register("aws", s3_list_buckets)
tool_registry.register("aws", s3_create_bucket)
tool_registry.register("aws", s3_delete_bucket)
tool_registry.register("aws", s3_list_objects)
tool_registry.register("aws", s3_bulk_delete)
tool_registry.register("aws", s3_bucket_size_analyzer)
tool_registry.register("aws", s3_upload_file)
tool_registry.register("aws", s3_download_file)