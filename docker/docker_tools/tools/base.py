from kubiya_sdk.tools import Tool, Arg, FileSpec
import os

DOCKER_ICON_URL = "https://www.docker.com/sites/default/files/d8/2019-07/vertical-logo-monochromatic.png"

class DockerTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        setup_script = """
        #!/bin/bash
        set -e

        # Install necessary tools
        apk add --no-cache curl jq kubectl git github-cli aws-cli

        # Your tool's content starts here
        """

        full_content = setup_script + "\n" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=DOCKER_ICON_URL,
            type="docker",
            image="docker:dind",
            content=full_content,
            args=args,
            with_files=[
                FileSpec(
                    source="/var/run/docker.sock",
                    destination="/var/run/docker.sock"
                )
            ],
            long_running=long_running
        )

def register_docker_tool(tool):
    from kubiya_sdk.tools.registry import tool_registry
    tool_registry.register("docker", tool)

# Helper function for emoji indicators
def emoji_status(status):
    emojis = {
        "success": "✅",
        "failure": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "building": "🏗️",
        "pushing": "🚀",
        "cloning": "📥",
        "modifying": "✏️"
    }
    return emojis.get(status, "")