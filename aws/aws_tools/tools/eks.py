from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

eks_list_clusters = AWSCliTool(
    name="eks_list_clusters",
    description="List EKS clusters",
    content="aws eks list-clusters",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List EKS clusters| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves cluster list 🔄]
        D --> E[User receives cluster names 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

eks_describe_cluster = AWSCliTool(
    name="eks_describe_cluster",
    description="Describe an EKS cluster",
    content="aws eks describe-cluster --name $cluster_name",
    args=[
        Arg(name="cluster_name", type="str", description="Name of the EKS cluster", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Describe EKS cluster| B[🤖 TeamMate]
        B --> C{{"Cluster name?" 🔢}}
        C --> D[User provides cluster name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves cluster details 📊]
        F --> G[User receives cluster information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

eks_create_cluster = AWSCliTool(
    name="eks_create_cluster",
    description="Create an EKS cluster",
    content="aws eks create-cluster --name $cluster_name --role-arn $role_arn --resources-vpc-config subnetIds=$subnet_ids,securityGroupIds=$security_group_ids",
    args=[
        Arg(name="cluster_name", type="str", description="Name for the EKS cluster", required=True),
        Arg(name="role_arn", type="str", description="ARN of the IAM role for EKS", required=True),
        Arg(name="subnet_ids", type="str", description="Comma-separated list of subnet IDs", required=True),
        Arg(name="security_group_ids", type="str", description="Comma-separated list of security group IDs", required=True),
    ],
    long_running=True,
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create EKS cluster| B[🤖 TeamMate]
        B --> C{{"Cluster details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates cluster 🚀]
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

eks_delete_cluster = AWSCliTool(
    name="eks_delete_cluster",
    description="Delete an EKS cluster",
    content="aws eks delete-cluster --name $cluster_name",
    args=[
        Arg(name="cluster_name", type="str", description="Name of the EKS cluster to delete", required=True),
    ],
    long_running=True,
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete EKS cluster| B[🤖 TeamMate]
        B --> C{{"Cluster name?" 🔢}}
        C --> D[User provides cluster name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes cluster 🗑️]
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

eks_list_nodegroups = AWSCliTool(
    name="eks_list_nodegroups",
    description="List node groups in an EKS cluster",
    content="aws eks list-nodegroups --cluster-name $cluster_name",
    args=[
        Arg(name="cluster_name", type="str", description="Name of the EKS cluster", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List node groups| B[🤖 TeamMate]
        B --> C{{"Cluster name?" 🔢}}
        C --> D[User provides cluster name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves node groups 🖥️]
        F --> G[User receives node group list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

eks_create_nodegroup = AWSCliTool(
    name="eks_create_nodegroup",
    description="Create a node group in an EKS cluster",
    content="aws eks create-nodegroup --cluster-name $cluster_name --nodegroup-name $nodegroup_name --subnets $subnet_ids --node-role $node_role_arn --scaling-config minSize=$min_size,maxSize=$max_size,desiredSize=$desired_size --instance-types $instance_types",
    args=[
        Arg(name="cluster_name", type="str", description="Name of the EKS cluster", required=True),
        Arg(name="nodegroup_name", type="str", description="Name for the node group", required=True),
        Arg(name="subnet_ids", type="str", description="Comma-separated list of subnet IDs", required=True),
        Arg(name="node_role_arn", type="str", description="ARN of the IAM role for nodes", required=True),
        Arg(name="min_size", type="int", description="Minimum size of the node group", required=True),
        Arg(name="max_size", type="int", description="Maximum size of the node group", required=True),
        Arg(name="desired_size", type="int", description="Desired size of the node group", required=True),
        Arg(name="instance_types", type="str", description="Comma-separated list of instance types", required=True),
    ],
    long_running=True,
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create node group| B[🤖 TeamMate]
        B --> C{{"Node group details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates node group 🚀]
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

tool_registry.register("aws", eks_list_clusters)
tool_registry.register("aws", eks_describe_cluster)
tool_registry.register("aws", eks_create_cluster)
tool_registry.register("aws", eks_delete_cluster)
tool_registry.register("aws", eks_list_nodegroups)
tool_registry.register("aws", eks_create_nodegroup) 