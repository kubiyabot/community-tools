from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

ec2_tool = AWSCliTool(
    name="ec2",
    description="Comprehensive EC2 instance management",
    content="""
    #!/bin/bash
    set -e
    case "$action" in
        describe)
            aws ec2 describe-instances $([[ -n "$instance_id" ]] && echo "--instance-ids $instance_id")
            ;;
        start)
            aws ec2 start-instances --instance-ids $instance_id
            ;;
        stop)
            aws ec2 stop-instances --instance-ids $instance_id
            ;;
        terminate)
            aws ec2 terminate-instances --instance-ids $instance_id
            ;;
        create)
            aws ec2 run-instances --image-id $image_id --instance-type $instance_type --key-name $key_name $([[ -n "$security_group" ]] && echo "--security-group-ids $security_group")
            ;;
        list-types)
            aws ec2 describe-instance-types
            ;;
        create-image)
            aws ec2 create-image --instance-id $instance_id --name $image_name
            ;;
        list-images)
            aws ec2 describe-images --owners self
            ;;
        modify-instance)
            aws ec2 modify-instance-attribute --instance-id $instance_id $attribute $value
            ;;
        *)
            echo "Invalid action"
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform", required=True),
        Arg(name="instance_id", type="str", description="EC2 instance ID", required=False),
        Arg(name="image_id", type="str", description="AMI ID for new instance", required=False),
        Arg(name="instance_type", type="str", description="Instance type", required=False),
        Arg(name="key_name", type="str", description="Key pair name", required=False),
        Arg(name="security_group", type="str", description="Security group ID", required=False),
        Arg(name="image_name", type="str", description="Name for new AMI", required=False),
        Arg(name="attribute", type="str", description="Instance attribute to modify", required=False),
        Arg(name="value", type="str", description="New value for instance attribute", required=False),
    ],
)

tool_registry.register("aws", ec2_tool)