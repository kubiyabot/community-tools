from kubiya_workflow_sdk.tools import Tool, FileSpec, Arg
from kubiya_workflow_sdk.tools.registry import tool_registry
from .common import COMMON_ENV, COMMON_FILES, COMMON_SECRETS

BITBUCKET_ICON_URL = "https://cdn-icons-png.flaticon.com/512/6125/6125001.png"
BITBUCKET_CLI_DOCKER_IMAGE = "atlassian/bitbucket-pipelines-runner:latest"

class BitbucketCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False):
        enhanced_content = f"""
#!/bin/sh
set -e

if ! command -v jq >/dev/null 2>&1; then
    apk add --quiet jq curl >/dev/null 2>&1
fi

# Setup Bitbucket authentication
setup_auth() {{
    if [ -z "$BITBUCKET_USERNAME" ] || [ -z "$BITBUCKET_APP_PASSWORD" ]; then
        echo "Error: Bitbucket credentials not set"
        exit 1
    fi
    export BITBUCKET_AUTH="$BITBUCKET_USERNAME:$BITBUCKET_APP_PASSWORD"
}}

setup_auth

{content}
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=BITBUCKET_ICON_URL,
            type="docker",
            image=BITBUCKET_CLI_DOCKER_IMAGE,
            content=enhanced_content,
            args=args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running
        )

def register_bitbucket_tool(tool):
    tool_registry.register("bitbucket", tool)