from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

ecr_create_repository = AWSCliTool(
    name="ecr_create_repository",
    description="Create a new ECR repository",
    content="aws ecr create-repository --repository-name $repository_name $([[ -n \"$tags\" ]] && echo \"--tags $tags\")",
    args=[
        Arg(name="repository_name", type="str", description="Name of the repository", required=True),
        Arg(name="tags", type="str", description="Tags in format 'Key=key1,Value=value1 Key=key2,Value=value2'", required=False),
    ],
)

ecr_delete_repository = AWSCliTool(
    name="ecr_delete_repository",
    description="Delete an ECR repository",
    content="aws ecr delete-repository --repository-name $repository_name --force",
    args=[
        Arg(name="repository_name", type="str", description="Name of the repository to delete", required=True),
    ],
)

ecr_list_repositories = AWSCliTool(
    name="ecr_list_repositories",
    description="List ECR repositories",
    content="aws ecr describe-repositories",
    args=[],
)

tool_registry.register("aws", ecr_create_repository)
tool_registry.register("aws", ecr_delete_repository)
tool_registry.register("aws", ecr_list_repositories) 