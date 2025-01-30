from kubiya_sdk.tools import Tool, Arg,ServiceSpec
from kubiya_sdk.tools.models import ImageProvider, Auth

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, content, args, secrets=None, env=None, with_files=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        # Add SLACK_API_TOKEN as a secret
        secrets.extend(["SLACK_API_TOKEN","JF_SECRET_PASS"])

        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="trialc5eche.jfrog.io/test-docker/mermaid-server",
            image_provider=ImageProvider(
                kind="jfrog",
                auth=[
                    Auth(
                        name="username",
                        value="avi.rosenberg@kubiya.ai",
                    ),
                    Auth(
                        name="password",
                        value_from={
                            "secret": "JF_SECRET_PASS"
                        }
                    )
                ]
            ),
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        )