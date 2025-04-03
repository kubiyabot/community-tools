from kubiya_sdk.tools.models import Tool

HONEYCOMB_ICON = "https://www.honeycomb.io/wp-content/themes/honeycomb/assets/images/logo-honeycomb-color.svg"

class HoneycombTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: list = None,
        env: list = None,
        long_running: bool = False,
        mermaid_diagram: str = None
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=HONEYCOMB_ICON,
            type="python",
            content=content,
            args=args or [],
            env=env or ["HONEYCOMB_API_KEY"],
            requirements=["requests>=2.25.0"],
            long_running=long_running,
            mermaid=mermaid_diagram
        ) 