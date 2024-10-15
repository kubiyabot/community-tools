from .base import DockerTool, register_docker_tool, emoji_status
from kubiya_sdk.tools import Arg

docker_build_tool = DockerTool(
    name="docker_build",
    description="Builds a Docker image from a Git repository or local directory",
    content=f"""
    #!/bin/bash
    set -e

    echo "{emoji_status('info')} Starting Docker build process..."

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

    if [ -n "$dockerfile_path" ]; then
        if [ ! -f "$dockerfile_path" ]; then
            echo "{emoji_status('failure')} Dockerfile not found at specified path."
            exit 1
        fi
    else
        dockerfile_path="Dockerfile"
    fi

    echo "{emoji_status('building')} Building Docker image..."
    docker build -t "$image_name:$image_tag" -f "$dockerfile_path" .

    if [ "$push" = "true" ]; then
        echo "{emoji_status('pushing')} Pushing Docker image..."
        if [[ "$image_name" == *ghcr.io* ]]; then
            echo "$GH_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin
        elif [[ "$image_name" == *.dkr.ecr.*.amazonaws.com* ]]; then
            aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $image_name
        fi
        docker push "$image_name:$image_tag"
    fi

    echo "{emoji_status('success')} Docker build process completed successfully!"
    """,
    args=[
        Arg(name="source", type="str", description="Git repository URL or local directory path", required=True),
        Arg(name="image_name", type="str", description="Name for the built image", required=True),
        Arg(name="image_tag", type="str", description="Tag for the built image", required=True),
        Arg(name="dockerfile_path", type="str", description="Path to the Dockerfile", required=False),
        Arg(name="push", type="bool", description="Push the image after building", required=False, default=False),
    ],
    long_running=True
)

register_docker_tool(docker_build_tool)
