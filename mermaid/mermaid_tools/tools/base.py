from kubiya_sdk.tools import Tool, Arg,ServiceSpec

MERMAID_ICON_URL = "https://seeklogo.com/images/M/mermaid-logo-31DD0B8905-seeklogo.com.png"

class MermaidTool(Tool):
    def __init__(self, name, description, content, args, secrets=None, env=None, with_files=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        # Add SLACK_API_TOKEN as a secret
        secrets.extend(["SLACK_API_TOKEN"])


        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="alpine:3.14",
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        )