from kubiya_sdk.tools import Tool, Arg

MERMAID_DOCKER_IMAGE = "your_docker_registry/mermaid-tools:latest"
MERMAID_ICON_URL = "https://raw.githubusercontent.com/mermaid-js/mermaid/develop/img/header.png"

class MermaidTool(Tool):
    def __init__(self, name, description, content, args, secrets=None, env=None):
        if secrets is None:
            secrets = []
        if env is None:
            env = []
        # Add SLACK_API_TOKEN as a secret and SLACK_CHANNEL_ID, SLACK_THREAD_TS as environment variables
        secrets.extend(["SLACK_API_TOKEN"])
        env.extend(["SLACK_CHANNEL_ID", "SLACK_THREAD_TS"])
        super().__init__(
            name=name,
            description=description,
            type="docker",
            image=MERMAID_DOCKER_IMAGE,
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        )