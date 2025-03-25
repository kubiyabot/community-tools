from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

vpc_create = AWSCliTool(
    name="vpc_create",
    description="Create a new VPC with specified CIDR block",
    content="aws ec2 create-vpc --cidr-block $cidr_block $([[ -n \"$tag_name\" ]] && echo \"--tag-specifications ResourceType=vpc,Tags=[{Key=Name,Value=$tag_name}]\")",
    args=[
        Arg(name="cidr_block", type="str", description="CIDR block for the VPC (e.g., '10.0.0.0/16')", required=True),
        Arg(name="tag_name", type="str", description="Name tag for the VPC", required=False),
    ],
)

vpc_create_subnet = AWSCliTool(
    name="vpc_create_subnet",
    description="Create a new subnet in a VPC",
    content="aws ec2 create-subnet --vpc-id $vpc_id --cidr-block $cidr_block --availability-zone $availability_zone $([[ -n \"$tag_name\" ]] && echo \"--tag-specifications ResourceType=subnet,Tags=[{Key=Name,Value=$tag_name}]\")",
    args=[
        Arg(name="vpc_id", type="str", description="ID of the VPC", required=True),
        Arg(name="cidr_block", type="str", description="CIDR block for the subnet", required=True),
        Arg(name="availability_zone", type="str", description="Availability Zone for the subnet", required=True),
        Arg(name="tag_name", type="str", description="Name tag for the subnet", required=False),
    ],
)

vpc_create_internet_gateway = AWSCliTool(
    name="vpc_create_internet_gateway",
    description="Create and attach an Internet Gateway to a VPC",
    content="""
    GATEWAY_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
    aws ec2 attach-internet-gateway --vpc-id $vpc_id --internet-gateway-id $GATEWAY_ID
    echo "Created and attached Internet Gateway $GATEWAY_ID to VPC $vpc_id"
    """,
    args=[
        Arg(name="vpc_id", type="str", description="ID of the VPC", required=True),
    ],
)

tool_registry.register("aws", vpc_create)
tool_registry.register("aws", vpc_create_subnet)
tool_registry.register("aws", vpc_create_internet_gateway) 