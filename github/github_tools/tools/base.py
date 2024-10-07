from kubiya_sdk.tools import Tool
from .common import COMMON_ENV, COMMON_FILES

GITHUB_ICON_URL = "https://cdn-icons-png.flaticon.com/256/25/25231.png"

class GitHubCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        super().__init__(
            name=name,
            description=description,
            icon_url=GITHUB_ICON_URL,
            type="docker",
            image="maniator/gh:latest",
            content=content,
            args=args,
            env=COMMON_ENV,
            secrets=["GH_TOKEN"],
            files=COMMON_FILES,
            long_running=long_running
        )
