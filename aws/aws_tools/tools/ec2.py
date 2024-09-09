from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

ec2_describe_instances = AWSCliTool(
    name="ec2_describe_instances",
    description="Describe EC2 instances",
    content="aws ec2 describe-instances $([[ -n \"$instance_ids\" ]] && echo \"--instance-ids $instance_ids\")",
    args=[
        Arg(name="instance_ids", type="str", description="Comma-separated list of instance IDs (e.g., 'i-1234567890abcdef0,i-0987654321fedcba0')", required=False),
    ],
)

ec2_start_instance = AWSCliTool(
    name="ec2_start_instance",
    description="Start an EC2 instance",
    content="aws ec2 start-instances --instance-ids $instance_id",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to start (e.g., 'i-1234567890abcdef0')", required=True),
    ],
)

ec2_stop_instance = AWSCliTool(
    name="ec2_stop_instance",
    description="Stop an EC2 instance",
    content="aws ec2 stop-instances --instance-ids $instance_id",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to stop (e.g., 'i-1234567890abcdef0')", required=True),
    ],
)

ec2_get_console_output = AWSCliTool(
    name="ec2_get_console_output",
    description="Get console output of an EC2 instance",
    content="aws ec2 get-console-output --instance-id $instance_id",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to get console output from (e.g., 'i-1234567890abcdef0')", required=True),
    ],
)

ec2_describe_instance_status = AWSCliTool(
    name="ec2_describe_instance_status",
    description="Get status of EC2 instances",
    content="aws ec2 describe-instance-status $([[ -n \"$instance_ids\" ]] && echo \"--instance-ids $instance_ids\")",
    args=[
        Arg(name="instance_ids", type="str", description="Comma-separated list of instance IDs (e.g., 'i-1234567890abcdef0,i-0987654321fedcba0')", required=False),
    ],
)

ec2_get_instance_metrics = AWSSdkTool(
    name="ec2_get_instance_metrics",
    description="Get CloudWatch metrics for an EC2 instance",
    content="""
import boto3
from datetime import datetime, timedelta

def get_instance_metrics(instance_id, metric_name, period):
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName=metric_name,
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        Statistics=['Average']
    )

    return response['Datapoints']

result = get_instance_metrics(instance_id, metric_name, period)
print(result)
    """,
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to get metrics for (e.g., 'i-1234567890abcdef0')", required=True),
        Arg(name="metric_name", type="str", description="Metric name (e.g., 'CPUUtilization', 'NetworkIn', 'DiskReadOps')", required=True),
        Arg(name="period", type="int", description="Period in seconds (e.g., 300 for 5-minute intervals)", required=True),
    ],
)

ec2_describe_instance_types = AWSCliTool(
    name="ec2_describe_instance_types",
    description="Describe EC2 instance types",
    content="aws ec2 describe-instance-types --instance-types $instance_type",
    args=[
        Arg(name="instance_type", type="str", description="Instance type to describe (e.g., 't2.micro', 'm5.large')", required=True),
    ],
)

ec2_get_instance_tags = AWSCliTool(
    name="ec2_get_instance_tags",
    description="Get tags for an EC2 instance",
    content="aws ec2 describe-tags --filters \"Name=resource-id,Values=$instance_id\"",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to get tags for (e.g., 'i-1234567890abcdef0')", required=True),
    ],
)

tool_registry.register("aws", ec2_describe_instances)
tool_registry.register("aws", ec2_start_instance)
tool_registry.register("aws", ec2_stop_instance)
tool_registry.register("aws", ec2_get_console_output)
tool_registry.register("aws", ec2_describe_instance_status)
tool_registry.register("aws", ec2_get_instance_metrics)
tool_registry.register("aws", ec2_describe_instance_types)
tool_registry.register("aws", ec2_get_instance_tags)