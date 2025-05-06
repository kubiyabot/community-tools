from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

iam_list_roles = AWSCliTool(
    name="iam_list_roles",
    description="List IAM roles",
    content="aws iam list-roles",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List IAM roles| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves role list 🔄]
        D --> E[User receives role details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

iam_get_role = AWSCliTool(
    name="iam_get_role",
    description="Get details of an IAM role",
    content="aws iam get-role --role-name $role_name",
    args=[
        Arg(name="role_name", type="str", description="Name of the IAM role", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get IAM role details| B[🤖 TeamMate]
        B --> C{{"Role name?" 🔢}}
        C --> D[User provides role name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves role details 📊]
        F --> G[User receives role information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

iam_create_role = AWSCliTool(
    name="iam_create_role",
    description="Create an IAM role",
    content="aws iam create-role --role-name $role_name --assume-role-policy-document '$assume_role_policy'",
    args=[
        Arg(name="role_name", type="str", description="Name for the IAM role", required=True),
        Arg(name="assume_role_policy", type="str", description="JSON policy document for the role trust relationship", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create IAM role| B[🤖 TeamMate]
        B --> C{{"Role details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates role 🚀]
        F --> G[User receives role ARN 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

iam_delete_role = AWSCliTool(
    name="iam_delete_role",
    description="Delete an IAM role",
    content="aws iam delete-role --role-name $role_name",
    args=[
        Arg(name="role_name", type="str", description="Name of the IAM role to delete", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete IAM role| B[🤖 TeamMate]
        B --> C{{"Role name?" 🔢}}
        C --> D[User provides role name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes role 🗑️]
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

iam_list_policies = AWSCliTool(
    name="iam_list_policies",
    description="List IAM policies",
    content="aws iam list-policies $([[ -n \"$scope\" ]] && echo \"--scope $scope\")",
    args=[
        Arg(name="scope", type="str", description="Scope of policies to list (e.g., 'AWS', 'Local')", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List IAM policies| B[🤖 TeamMate]
        B --> C{{"Scope (optional)?" 🔢}}
        C --> D[User provides scope ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves policy list 🔄]
        F --> G[User receives policy details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

iam_create_policy = AWSCliTool(
    name="iam_create_policy",
    description="Create an IAM policy",
    content="aws iam create-policy --policy-name $policy_name --policy-document '$policy_document'",
    args=[
        Arg(name="policy_name", type="str", description="Name for the IAM policy", required=True),
        Arg(name="policy_document", type="str", description="JSON policy document", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create IAM policy| B[🤖 TeamMate]
        B --> C{{"Policy details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates policy 🚀]
        F --> G[User receives policy ARN 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

iam_attach_role_policy = AWSCliTool(
    name="iam_attach_role_policy",
    description="Attach an IAM policy to a role",
    content="aws iam attach-role-policy --role-name $role_name --policy-arn $policy_arn",
    args=[
        Arg(name="role_name", type="str", description="Name of the IAM role", required=True),
        Arg(name="policy_arn", type="str", description="ARN of the policy to attach", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Attach policy to role| B[🤖 TeamMate]
        B --> C{{"Role and policy details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS attaches policy 🔗]
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

tool_registry.register("aws", iam_list_roles)
tool_registry.register("aws", iam_get_role)
tool_registry.register("aws", iam_create_role)
tool_registry.register("aws", iam_delete_role)
tool_registry.register("aws", iam_list_policies)
tool_registry.register("aws", iam_create_policy)
tool_registry.register("aws", iam_attach_role_policy) 