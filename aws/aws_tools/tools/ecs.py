from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

ecs_list_clusters = AWSCliTool(
    name="ecs_list_clusters",
    description="List ECS clusters",
    content="aws ecs list-clusters",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List ECS clusters| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves cluster list 🔄]
        D --> E[User receives cluster ARNs 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ecs_describe_clusters = AWSCliTool(
    name="ecs_describe_clusters",
    description="Describe ECS clusters",
    content="aws ecs describe-clusters --clusters $cluster_names",
    args=[
        Arg(name="cluster_names", type="str", description="Comma-separated list of cluster names or ARNs", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Describe ECS clusters| B[🤖 TeamMate]
        B --> C{{"Cluster names?" 🔢}}
        C --> D[User provides cluster names ✍️]
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

ecs_create_cluster = AWSCliTool(
    name="ecs_create_cluster",
    description="Create an ECS cluster",
    content="aws ecs create-cluster --cluster-name $cluster_name $([[ -n \"$tags\" ]] && echo \"--tags $tags\")",
    args=[
        Arg(name="cluster_name", type="str", description="Name for the ECS cluster", required=True),
        Arg(name="tags", type="str", description="Tags in key=value format (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create ECS cluster| B[🤖 TeamMate]
        B --> C{{"Cluster name?" 🔢}}
        C --> D[User provides cluster name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates cluster 🚀]
        F --> G[User receives cluster ARN 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ecs_delete_cluster = AWSCliTool(
    name="ecs_delete_cluster",
    description="Delete an ECS cluster",
    content="aws ecs delete-cluster --cluster $cluster_name",
    args=[
        Arg(name="cluster_name", type="str", description="Name or ARN of the ECS cluster to delete", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete ECS cluster| B[🤖 TeamMate]
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

ecs_list_services = AWSCliTool(
    name="ecs_list_services",
    description="List ECS services in a cluster",
    content="aws ecs list-services --cluster $cluster_name",
    args=[
        Arg(name="cluster_name", type="str", description="Name or ARN of the ECS cluster", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List ECS services| B[🤖 TeamMate]
        B --> C{{"Cluster name?" 🔢}}
        C --> D[User provides cluster name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves service list 🔄]
        F --> G[User receives service ARNs 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ecs_describe_services = AWSCliTool(
    name="ecs_describe_services",
    description="Describe ECS services in a cluster",
    content="aws ecs describe-services --cluster $cluster_name --services $service_names",
    args=[
        Arg(name="cluster_name", type="str", description="Name or ARN of the ECS cluster", required=True),
        Arg(name="service_names", type="str", description="Comma-separated list of service names or ARNs", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Describe ECS services| B[🤖 TeamMate]
        B --> C{{"Cluster and service names?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves service details 📊]
        F --> G[User receives service information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", ecs_list_clusters)
tool_registry.register("aws", ecs_describe_clusters)
tool_registry.register("aws", ecs_create_cluster)
tool_registry.register("aws", ecs_delete_cluster)
tool_registry.register("aws", ecs_list_services)
tool_registry.register("aws", ecs_describe_services) 