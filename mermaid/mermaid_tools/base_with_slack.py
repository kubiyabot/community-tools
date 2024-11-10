from kubiya_sdk.tools import Tool, Arg

# Custom Docker image that includes mermaid-cli and slack-cli
MERMAID_SLACK_DOCKER_IMAGE = "your_docker_registry/mermaid-slack-cli:latest"
MERMAID_ICON_URL = "https://raw.githubusercontent.com/mermaid-js/mermaid/develop/img/header.png"

class MermaidSlackTool(Tool):
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
            image=MERMAID_SLACK_DOCKER_IMAGE,
            content=content,
            args=args,
            icon_url=MERMAID_ICON_URL,
            secrets=secrets,
            env=env,
        ) 