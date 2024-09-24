from kubiya_sdk.tools import Tool, FileSpec

TERRAFORM_ICON_URL = "https://www.terraform.io/assets/images/logo-terraform-main.svg"

class TerraformTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        env = [
            "TF_VAR_file",
            "TF_CLI_CONFIG_FILE",
            "TF_LOG",
            "TF_INPUT",
            "TF_IN_AUTOMATION",
            "TF_REGISTRY_DISCOVERY_RETRY",
            "TF_REGISTRY_CLIENT_TIMEOUT",
        ]

        files = [
            FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
            FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
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
            env=env,
            files=files,
        )

    def with_github_token(self):
        self.env.append("GH_TOKEN")
        return self

    def with_aws_credentials(self):
        self.env.extend(["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"])
        return self
