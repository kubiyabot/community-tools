from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

iam_create_policy = AWSCliTool(
    name="iam_create_policy",
    description="Create a new IAM policy",
    content="aws iam create-policy --policy-name $policy_name --policy-document file://$policy_document",
    args=[
        Arg(name="policy_name", type="str", description="Name of the policy", required=True),
        Arg(name="policy_document", type="str", description="Path to the JSON policy document", required=True),
    ],
)

iam_attach_role_policy = AWSCliTool(
    name="iam_attach_role_policy",
    description="Attach an IAM policy to a role",
    content="aws iam attach-role-policy --role-name $role_name --policy-arn $policy_arn",
    args=[
        Arg(name="role_name", type="str", description="Name of the IAM role", required=True),
        Arg(name="policy_arn", type="str", description="ARN of the policy to attach", required=True),
    ],
)

iam_list_policies = AWSCliTool(
    name="iam_list_policies",
    description="List IAM policies",
    content="aws iam list-policies $([[ \"$scope\" == \"local\" ]] && echo \"--scope Local\" || echo \"--scope AWS\")",
    args=[
        Arg(name="scope", type="str", description="Policy scope ('local' or 'aws')", required=False),
    ],
)

iam_list_roles = AWSCliTool(
    name="iam_list_roles",
    description="List IAM roles",
    content="aws iam list-roles",
    args=[],
)

iam_create_role = AWSCliTool(
    name="iam_create_role",
    description="Create a new IAM role",
    content="""aws iam create-role \
        --role-name $role_name \
        --assume-role-policy-document file://$policy_document \
        $([[ -n "$description" ]] && echo "--description '$description'")""",
    args=[
        Arg(name="role_name", type="str", description="Name of the role to create", required=True),
        Arg(name="policy_document", type="str", description="Path to the trust relationship policy document", required=True),
        Arg(name="description", type="str", description="Description of the role", required=False),
    ],
)

iam_delete_role = AWSCliTool(
    name="iam_delete_role",
    description="Delete an IAM role",
    content="aws iam delete-role --role-name $role_name",
    args=[
        Arg(name="role_name", type="str", description="Name of the role to delete", required=True),
    ],
)

tool_registry.register("aws", iam_create_policy)
tool_registry.register("aws", iam_attach_role_policy)
tool_registry.register("aws", iam_list_policies)
tool_registry.register("aws", iam_list_roles)
tool_registry.register("aws", iam_create_role)
tool_registry.register("aws", iam_delete_role) 