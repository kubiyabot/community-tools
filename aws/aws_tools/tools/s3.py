from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

s3_cli_tool = AWSCliTool(
    name="s3_cli",
    description="Manages S3 buckets and objects using AWS CLI",
    content="""
    #!/bin/bash
    set -e
    aws s3 $action $source $destination $([[ -n "$options" ]] && echo "$options")
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (ls, cp, mv, rm)", required=True),
        Arg(name="source", type="str", description="Source path", required=True),
        Arg(name="destination", type="str", description="Destination path", required=False),
        Arg(name="options", type="str", description="Additional options", required=False),
    ],
)

s3_sdk_tool = AWSSdkTool(
    name="s3_sdk",
    description="Manages S3 buckets and objects using AWS SDK",
    content="""
import boto3

def run(action, source, destination=None, options=None):
    s3 = boto3.client('s3')
    if action == 'ls':
        return s3.list_objects_v2(Bucket=source)
    elif action == 'cp':
        return s3.copy_object(CopySource=source, Bucket=destination.split('/')[0], Key='/'.join(destination.split('/')[1:]))
    elif action == 'rm':
        return s3.delete_object(Bucket=source.split('/')[0], Key='/'.join(source.split('/')[1:]))
    else:
        raise ValueError(f"Unsupported action: {action}")

result = run(action, source, destination, options)
print(result)
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform (ls, cp, rm)", required=True),
        Arg(name="source", type="str", description="Source path", required=True),
        Arg(name="destination", type="str", description="Destination path", required=False),
        Arg(name="options", type="str", description="Additional options", required=False),
    ],
)

tool_registry.register("aws", s3_cli_tool)
tool_registry.register("aws", s3_sdk_tool)