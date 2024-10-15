from .base import DockerTool, register_docker_tool, emoji_status
from kubiya_sdk.tools import Arg

modify_dockerfile_tool = DockerTool(
    name="modify_dockerfile",
    description="Modifies a Dockerfile in a Git repository or local directory",
    content=f"""
    #!/bin/bash
    set -e

    echo "{emoji_status('info')} Starting Dockerfile modification process..."

    if [[ "$source" == http* ]]; then
        echo "{emoji_status('cloning')} Cloning repository..."
        if [[ "$source" == *github.com* ]]; then
            gh repo clone "$source" repo
        elif [ "$BITBUCKET_ENABLED" = "true" ] && [[ "$source" == *bitbucket.org* ]]; then
            git clone "$source" repo
        else
            echo "{emoji_status('warning')} Unsupported Git provider. Falling back to public clone."
            git clone "$source" repo
        fi
        cd repo
    else
        cd "$source"
    fi

    dockerfile_path="${{dockerfile_path:-Dockerfile}}"

    if [ ! -f "$dockerfile_path" ]; then
        echo "{emoji_status('failure')} Dockerfile not found at specified path."
        exit 1
    fi

    echo "{emoji_status('modifying')} Modifying Dockerfile..."
    sed -i "$sed_command" "$dockerfile_path"

    if [ "$commit" = "true" ]; then
        git config user.email "kubiya-bot@example.com"
        git config user.name "Kubiya Bot"
        git add "$dockerfile_path"
        git commit -m "Modified Dockerfile: $commit_message"
        git push
    fi

    echo "{emoji_status('success')} Dockerfile modification completed successfully!"
    """,
    args=[
        Arg(name="source", type="str", description="Git repository URL or local directory path", required=True),
        Arg(name="dockerfile_path", type="str", description="Path to the Dockerfile", required=False, default="Dockerfile"),
        Arg(name="sed_command", type="str", description="sed command to modify the Dockerfile", required=True),
        Arg(name="commit", type="bool", description="Commit and push changes", required=False, default=False),
        Arg(name="commit_message", type="str", description="Commit message", required=False),
    ]
)

register_docker_tool(modify_dockerfile_tool)
