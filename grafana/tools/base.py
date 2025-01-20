from kubiya_sdk import Tool

GRAFANA_ICON = "https://img.icons8.com/color/200/grafana.png"

# Common environment variables
COMMON_ENV = [
    "GRAFANA_SVC_URL",
    "SLACK_CHANNEL_ID",
    "SLACK_THREAD_TS",
]

# Common secrets
COMMON_SECRETS = ["GRAFANA_API_TOKEN"]

class GrafanaRenderTool(Tool):
    """Base class for Grafana render tools."""
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        env: list = None,
        # Default to long running to ensure the tool is always available
        # As the tools are waiting for the TTL to expire before revoking access
        # This is to avoid race conditions where the tool is not available when the TTL expires
        long_running: bool = False,
        mermaid: str = None,
        with_files: list = None,
        args: list = None
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=GRAFANA_ICON,
            type="docker",
            image="python:3.12-alpine",
            content=content,
            env=env or COMMON_ENV,
            with_files=(with_files or []) ,
            secrets=COMMON_SECRETS,
            long_running=long_running,
            mermaid=mermaid,
            args=args or []
        )
__all__ = ['GrafanaRenderTool']
