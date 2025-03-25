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

tool_registry.register("aws", iam_create_policy)
tool_registry.register("aws", iam_attach_role_policy)
tool_registry.register("aws", iam_list_policies) 