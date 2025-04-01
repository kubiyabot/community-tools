from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

lambda_list_functions = AWSCliTool(
    name="lambda_list_functions",
    description="List Lambda functions",
    content="aws lambda list-functions",
    args=[],
)

lambda_create_function = AWSCliTool(
    name="lambda_create_function",
    description="Create a Lambda function",
    content="""
    aws lambda create-function \
        --function-name $function_name \
        --runtime $runtime \
        --role $role_arn \
        --handler $handler \
        --zip-file fileb://$zip_file
    """,
    args=[
        Arg(name="function_name", type="str", description="Name of the Lambda function", required=True),
        Arg(name="runtime", type="str", description="Runtime for the Lambda function", required=True),
        Arg(name="role_arn", type="str", description="ARN of the IAM role for the function", required=True),
        Arg(name="handler", type="str", description="Handler for the Lambda function", required=True),
        Arg(name="zip_file", type="str", description="Path to the ZIP file containing the function code", required=True),
    ],
)

lambda_update_function = AWSCliTool(
    name="lambda_update_function",
    description="Update a Lambda function",
    content="aws lambda update-function-code --function-name $function_name --zip-file fileb://$zip_file",
    args=[
        Arg(name="function_name", type="str", description="Name of the Lambda function to update", required=True),
        Arg(name="zip_file", type="str", description="Path to the ZIP file containing the updated function code", required=True),
    ],
)

lambda_delete_function = AWSCliTool(
    name="lambda_delete_function",
    description="Delete a Lambda function",
    content="aws lambda delete-function --function-name $function_name",
    args=[
        Arg(name="function_name", type="str", description="Name of the Lambda function to delete", required=True),
    ],
)

lambda_invoke_function = AWSCliTool(
    name="lambda_invoke_function",
    description="Invoke a Lambda function",
    content="aws lambda invoke --function-name $function_name --payload '$payload' $output_file",
    args=[
        Arg(name="function_name", type="str", description="Name of the Lambda function to invoke", required=True),
        Arg(name="payload", type="str", description="JSON payload for the Lambda function", required=True),
        Arg(name="output_file", type="str", description="File to save the function output", required=True),
    ],
)

lambda_get_function_config = AWSCliTool(
    name="lambda_get_function_config",
    description="Get Lambda function configuration",
    content="aws lambda get-function-configuration --function-name $function_name",
    args=[
        Arg(name="function_name", type="str", description="Name of the Lambda function", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get function config| B[🤖 TeamMate]
        B --> C{{"Function name?" 📝}}
        C --> D[User provides function name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves configuration ⚙️]
        F --> G[User receives function config 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

lambda_list_versions = AWSCliTool(
    name="lambda_list_versions",
    description="List versions of a Lambda function",
    content="aws lambda list-versions-by-function --function-name $function_name",
    args=[
        Arg(name="function_name", type="str", description="Name of the Lambda function", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List versions| B[🤖 TeamMate]
        B --> C{{"Function name?" 📝}}
        C --> D[User provides function name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves versions 🔢]
        F --> G[User receives version list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", lambda_list_functions)
tool_registry.register("aws", lambda_create_function)
tool_registry.register("aws", lambda_update_function)
tool_registry.register("aws", lambda_delete_function)
tool_registry.register("aws", lambda_invoke_function)
tool_registry.register("aws", lambda_get_function_config)
tool_registry.register("aws", lambda_list_versions)