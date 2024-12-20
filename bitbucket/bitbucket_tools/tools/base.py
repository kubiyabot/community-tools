from kubiya_sdk.tools import Tool, FileSpec
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
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

check_workspace() {{
    if [ -n "$workspace" ]; then
        echo "Using workspace: $workspace"
    else
        # Get user's workspaces
        workspaces=$(curl -s -u $BITBUCKET_AUTH \
            "https://api.bitbucket.org/2.0/workspaces" | \
            jq -r '.values[].slug')
        
        workspace_count=$(echo "$workspaces" | wc -l)
        if [ "$workspace_count" -eq 0 ]; then
            echo "You don't have access to any workspaces."
            exit 1
        elif [ "$workspace_count" -eq 1 ]; then
            workspace=$workspaces
            echo "Using workspace: $workspace"
        else
            echo "Multiple workspaces found. Please specify one:"
            echo "$workspaces"
            exit 1
        fi
    fi
}}

get_repo_context() {{
    if [ -z "$repo" ]; then
        if [ -n "$workspace" ]; then
            echo "No repository specified. Here are your repositories in workspace $workspace:"
            curl -s -u $BITBUCKET_AUTH \
                "https://api.bitbucket.org/2.0/repositories/$workspace" | \
                jq -r '.values[].name'
        fi
        exit 1
    else
        echo "Using repository: $repo"
    fi
}}

setup_auth
check_workspace
get_repo_context

{content}
"""

        updated_args = [arg for arg in args if arg.name not in ["workspace", "repo"]]
        updated_args.extend([
            Arg(name="workspace", type="str", description="Bitbucket workspace slug. If you have access to only one workspace, it will be used automatically.", required=False),
            Arg(name="repo", type="str", description="Repository name in the workspace", required=False)
        ])

        super().__init__(
            name=name,
            description=description,
            icon_url=BITBUCKET_ICON_URL,
            type="docker",
            image=BITBUCKET_CLI_DOCKER_IMAGE,
            content=enhanced_content,
            args=updated_args,
            env=COMMON_ENV,
            files=COMMON_FILES,
            secrets=COMMON_SECRETS,
            long_running=long_running
        )

def register_bitbucket_tool(tool):
    tool_registry.register("bitbucket", tool)