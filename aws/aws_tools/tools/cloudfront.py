from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

cloudfront_list_distributions = AWSCliTool(
    name="cloudfront_list_distributions",
    description="List CloudFront distributions",
    content="aws cloudfront list-distributions",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List distributions| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves distribution list 🌐]
        D --> E[User receives distribution details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudfront_get_distribution = AWSCliTool(
    name="cloudfront_get_distribution",
    description="Get details of a CloudFront distribution",
    content="aws cloudfront get-distribution --id $distribution_id",
    args=[
        Arg(name="distribution_id", type="str", description="ID of the CloudFront distribution", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get distribution details| B[🤖 TeamMate]
        B --> C{{"Distribution ID?" 🔢}}
        C --> D[User provides ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves distribution details 📊]
        F --> G[User receives distribution information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudfront_create_invalidation = AWSCliTool(
    name="cloudfront_create_invalidation",
    description="Create a CloudFront invalidation",
    content="aws cloudfront create-invalidation --distribution-id $distribution_id --paths $paths",
    args=[
        Arg(name="distribution_id", type="str", description="ID of the CloudFront distribution", required=True),
        Arg(name="paths", type="str", description="Space-separated list of paths to invalidate (e.g., '/images/* /css/*')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create invalidation| B[🤖 TeamMate]
        B --> C{{"Distribution ID and paths?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates invalidation 🔄]
        F --> G[User receives invalidation ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudfront_get_invalidation = AWSCliTool(
    name="cloudfront_get_invalidation",
    description="Get details of a CloudFront invalidation",
    content="aws cloudfront get-invalidation --distribution-id $distribution_id --id $invalidation_id",
    args=[
        Arg(name="distribution_id", type="str", description="ID of the CloudFront distribution", required=True),
        Arg(name="invalidation_id", type="str", description="ID of the invalidation", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get invalidation details| B[🤖 TeamMate]
        B --> C{{"Distribution and invalidation IDs?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves invalidation details 📊]
        F --> G[User receives invalidation information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", cloudfront_list_distributions)
tool_registry.register("aws", cloudfront_get_distribution)
tool_registry.register("aws", cloudfront_create_invalidation)
tool_registry.register("aws", cloudfront_get_invalidation) 