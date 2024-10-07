from kubiya_sdk.tools import Tool, FileSpec

TERRAFORM_ICON_URL = "https://www.terraform.io/assets/images/logo-terraform-main.svg"

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, long_running=True):
        file_specs = [
            FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
            FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config")
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
            env=["AWS_PROFILE", "GH_TOKEN"],
            secrets=["GITHUB_TOKEN"],
            with_files=file_specs,
        )
