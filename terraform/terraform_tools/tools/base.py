from kubiya_sdk.tools import Tool

TERRAFORM_ICON_URL = "https://www.terraform.io/assets/images/logo-terraform-main.svg"

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        super().__init__(
            name=name,
            description=description,
            icon_url=TERRAFORM_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            args=args,
            long_running=long_running
        )
