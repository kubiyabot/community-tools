from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

ec2_cli_tool = AWSCliTool(
    name="ec2_cli",
    description="Manages EC2 instances using AWS CLI",
    content="""
    #!/bin/bash
    set -e
    aws ec2 $action $([[ -n "$instance_id" ]] && echo "--instance-ids $instance_id")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (describe-instances, start-instances, stop-instances)", required=True),
        Arg(name="instance_id", type="str", description="EC2 instance ID", required=False),
    ],
)

ec2_sdk_tool = AWSSdkTool(
    name="ec2_sdk",
    description="Manages EC2 instances using AWS SDK",
    content="""
import boto3

def run(action, instance_id=None):
    ec2 = boto3.client('ec2')
    if action == 'describe-instances':
        return ec2.describe_instances(InstanceIds=[instance_id] if instance_id else [])
    elif action in ['start-instances', 'stop-instances']:
        method = getattr(ec2, action.replace('-', '_'))
        return method(InstanceIds=[instance_id])
    else:
        raise ValueError(f"Unsupported action: {action}")

result = run(action, instance_id)
print(result)
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (describe-instances, start-instances, stop-instances)", required=True),
        Arg(name="instance_id", type="str", description="EC2 instance ID", required=False),
    ],
)

tool_registry.register("aws", ec2_cli_tool)
tool_registry.register("aws", ec2_sdk_tool)