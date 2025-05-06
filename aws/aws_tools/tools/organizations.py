from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

organizations_list_accounts = AWSCliTool(
    name="organizations_list_accounts",
    description="List accounts in the organization",
    content="aws organizations list-accounts",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List accounts| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves account list 🏢]
        D --> E[User receives account details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

organizations_describe_account = AWSCliTool(
    name="organizations_describe_account",
    description="Describe an account in the organization",
    content="aws organizations describe-account --account-id $account_id",
    args=[
        Arg(name="account_id", type="str", description="ID of the account", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Describe account| B[🤖 TeamMate]
        B --> C{{"Account ID?" 🔢}}
        C --> D[User provides account ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves account details 📊]
        F --> G[User receives account information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

organizations_create_account = AWSCliTool(
    name="organizations_create_account",
    description="Create a new account in the organization",
    content="aws organizations create-account --email $email --account-name '$account_name'",
    args=[
        Arg(name="email", type="str", description="Email address for the account", required=True),
        Arg(name="account_name", type="str", description="Name for the account", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create account| B[🤖 TeamMate]
        B --> C{{"Account details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates account 🚀]
        F --> G[User receives account ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

organizations_list_users = AWSCliTool(
    name="organizations_list_users",
    description="List IAM users in an account",
    content="aws iam list-users",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List IAM users| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves user list 👥]
        D --> E[User receives user details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

organizations_create_user = AWSCliTool(
    name="organizations_create_user",
    description="Create a new IAM user",
    content="aws iam create-user --user-name $user_name",
    args=[
        Arg(name="user_name", type="str", description="Name for the IAM user", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create IAM user| B[🤖 TeamMate]
        B --> C{{"User name?" 🔢}}
        C --> D[User provides user name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates user 🚀]
        F --> G[User receives user ARN 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", organizations_list_accounts)
tool_registry.register("aws", organizations_describe_account)
tool_registry.register("aws", organizations_create_account)
tool_registry.register("aws", organizations_list_users)
tool_registry.register("aws", organizations_create_user) 