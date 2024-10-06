from kubiya_sdk.tools import Tool, FileSpec

TERRAFORM_ICON_URL = "https://www.terraform.io/assets/images/logo-terraform-main.svg"

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, long_running=True):
        files = []

        super().__init__(
            name=name,
            description=description,
            icon_url=TERRAFORM_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            args=args,
            long_running=long_running,
            env=[],
            files=files,
        )

        # add env vars for github token and aws credentials
        self = self.with_github_token()
        self = self.with_aws_credentials()
        return self

    def with_github_token(self):
        self.env.append("GH_TOKEN")
        return self

    def with_aws_credentials(self):
        self.env.extend(["AWS_PROFILE"])
        self.files.extend([
            FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
            FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config")
        ])
        return self
