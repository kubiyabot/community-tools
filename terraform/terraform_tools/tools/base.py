from kubiya_sdk.tools import Tool, FileSpec

TERRAFORM_ICON_URL = "https://www.terraform.io/assets/images/logo-terraform-main.svg"

class TerraformTool(Tool):
    def __init__(self, name, description, content, args=[], files=[], env=[], secrets=[], long_running=True):
        super().__init__(
            name=name,
            description=description,
            icon_url=TERRAFORM_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            args=args,
            long_running=long_running,
            env=[
                "AWS_PROFILE", # AWS Profile - used to get AWS credentials (integration)
            ],
            secrets=[
                "GITHUB_TOKEN", # Github Token (integration)
            ],
            files=[
                # AWS Credentials (integration) - https://docs.kubiya.ai
                FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
                FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
            ]
        )
