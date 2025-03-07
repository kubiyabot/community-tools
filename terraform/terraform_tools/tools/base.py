from kubiya_sdk.tools import Tool, FileSpec

TERRAFORM_ICON_URL = "https://www.terraform.io/assets/images/logo-terraform-main.svg"

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, long_running=True):
        file_specs = [
            FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"), # AWS Credentials (integration) - https://docs.kubiya.ai/integrations/aws
            FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config") # AWS Credentials (integration) - https://docs.kubiya.ai/integrations/aws
        ]

        super().__init__(
            name=name,
            description=description,
            icon_url=TERRAFORM_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            args=args,
            long_running=long_running,
            env=["AWS_PROFILE"], # AWS Profile - used to get AWS credentials (integration) - https://docs.kubiya.ai/integrations/aws
            secrets=["GH_TOKEN"], # Github Token (integration) - https://docs.kubiya.ai/integrations/github
            with_files=file_specs,
        )
