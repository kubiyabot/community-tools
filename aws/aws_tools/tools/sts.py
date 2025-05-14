from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

sts_get_caller_identity = AWSCliTool(
    name="sts_get_caller_identity",
    description="Get information about the AWS identity used to make API calls",
    content="aws sts get-caller-identity",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get caller identity| B[🤖 TeamMate]
        B --> C[API request to AWS STS ☁️]
        C --> D[AWS retrieves identity information 🔍]
        D --> E[Format identity information 📝]
        E --> F[User receives identity details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style F fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)


tool_registry.register("aws", sts_get_caller_identity)