from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

vpc_list_vpcs = AWSCliTool(
    name="vpc_list_vpcs",
    description="List VPCs in the current region",
    content="aws ec2 describe-vpcs",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List VPCs| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves VPC list 🌐]
        D --> E[User receives VPC details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_create_vpc = AWSCliTool(
    name="vpc_create_vpc",
    description="Create a new VPC",
    content="aws ec2 create-vpc --cidr-block $cidr_block $([[ -n \"$tag_specifications\" ]] && echo \"--tag-specifications $tag_specifications\")",
    args=[
        Arg(name="cidr_block", type="str", description="CIDR block for the VPC (e.g., '10.0.0.0/16')", required=True),
        Arg(name="tag_specifications", type="str", description="Tags in JSON format (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create VPC| B[🤖 TeamMate]
        B --> C{{"CIDR block?" 🔢}}
        C --> D[User provides CIDR block ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates VPC 🚀]
        F --> G[User receives VPC ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_delete_vpc = AWSCliTool(
    name="vpc_delete_vpc",
    description="Delete a VPC",
    content="aws ec2 delete-vpc --vpc-id $vpc_id",
    args=[
        Arg(name="vpc_id", type="str", description="ID of the VPC to delete", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete VPC| B[🤖 TeamMate]
        B --> C{{"VPC ID?" 🔢}}
        C --> D[User provides VPC ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes VPC 🗑️]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_list_subnets = AWSCliTool(
    name="vpc_list_subnets",
    description="List subnets in a VPC",
    content="aws ec2 describe-subnets $([[ -n \"$vpc_id\" ]] && echo \"--filters Name=vpc-id,Values=$vpc_id\")",
    args=[
        Arg(name="vpc_id", type="str", description="ID of the VPC to list subnets for (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List subnets| B[🤖 TeamMate]
        B --> C{{"VPC ID (optional)?" 🔢}}
        C --> D[User provides VPC ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves subnet list 🌐]
        F --> G[User receives subnet details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_create_subnet = AWSCliTool(
    name="vpc_create_subnet",
    description="Create a subnet in a VPC",
    content="aws ec2 create-subnet --vpc-id $vpc_id --cidr-block $cidr_block --availability-zone $availability_zone $([[ -n \"$tag_specifications\" ]] && echo \"--tag-specifications $tag_specifications\")",
    args=[
        Arg(name="vpc_id", type="str", description="ID of the VPC", required=True),
        Arg(name="cidr_block", type="str", description="CIDR block for the subnet (e.g., '10.0.1.0/24')", required=True),
        Arg(name="availability_zone", type="str", description="Availability Zone for the subnet", required=True),
        Arg(name="tag_specifications", type="str", description="Tags in JSON format (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create subnet| B[🤖 TeamMate]
        B --> C{{"Subnet details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates subnet 🚀]
        F --> G[User receives subnet ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_delete_subnet = AWSCliTool(
    name="vpc_delete_subnet",
    description="Delete a subnet",
    content="aws ec2 delete-subnet --subnet-id $subnet_id",
    args=[
        Arg(name="subnet_id", type="str", description="ID of the subnet to delete", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete subnet| B[🤖 TeamMate]
        B --> C{{"Subnet ID?" 🔢}}
        C --> D[User provides subnet ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes subnet 🗑️]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_list_route_tables = AWSCliTool(
    name="vpc_list_route_tables",
    description="List route tables in a VPC",
    content="aws ec2 describe-route-tables $([[ -n \"$vpc_id\" ]] && echo \"--filters Name=vpc-id,Values=$vpc_id\")",
    args=[
        Arg(name="vpc_id", type="str", description="ID of the VPC to list route tables for (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List route tables| B[🤖 TeamMate]
        B --> C{{"VPC ID (optional)?" 🔢}}
        C --> D[User provides VPC ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves route table list 🌐]
        F --> G[User receives route table details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_create_route = AWSCliTool(
    name="vpc_create_route",
    description="Create a route in a route table",
    content="aws ec2 create-route --route-table-id $route_table_id --destination-cidr-block $destination_cidr_block --gateway-id $gateway_id",
    args=[
        Arg(name="route_table_id", type="str", description="ID of the route table", required=True),
        Arg(name="destination_cidr_block", type="str", description="Destination CIDR block (e.g., '0.0.0.0/0')", required=True),
        Arg(name="gateway_id", type="str", description="ID of the gateway (e.g., Internet Gateway)", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create route| B[🤖 TeamMate]
        B --> C{{"Route details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates route 🚀]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

vpc_delete_route = AWSCliTool(
    name="vpc_delete_route",
    description="Delete a route from a route table",
    content="aws ec2 delete-route --route-table-id $route_table_id --destination-cidr-block $destination_cidr_block",
    args=[
        Arg(name="route_table_id", type="str", description="ID of the route table", required=True),
        Arg(name="destination_cidr_block", type="str", description="Destination CIDR block (e.g., '0.0.0.0/0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete route| B[🤖 TeamMate]
        B --> C{{"Route details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes route 🗑️]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", vpc_list_vpcs)
tool_registry.register("aws", vpc_create_vpc)
tool_registry.register("aws", vpc_delete_vpc)
tool_registry.register("aws", vpc_list_subnets)
tool_registry.register("aws", vpc_create_subnet)
tool_registry.register("aws", vpc_delete_subnet)
tool_registry.register("aws", vpc_list_route_tables)
tool_registry.register("aws", vpc_create_route)
tool_registry.register("aws", vpc_delete_route) 