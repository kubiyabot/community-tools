from .base import DockerTool, register_docker_tool, emoji_status
from kubiya_sdk.tools import Arg

docker_push_tool = DockerTool(
    name="docker_push",
    description="Pushes a Docker image to a registry",
    content=f"""
    #!/bin/bash
    set -e

    echo "{emoji_status('info')} Starting Docker push process..."

    if [[ "$image_name" == *ghcr.io* ]]; then
        echo "{emoji_status('info')} Logging in to GitHub Container Registry..."
        echo "$GH_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin
    elif [[ "$image_name" == *.dkr.ecr.*.amazonaws.com* ]]; then
        echo "{emoji_status('info')} Logging in to Amazon ECR..."
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $image_name
    else
        echo "{emoji_status('info')} Using default Docker registry..."
    fi

    echo "{emoji_status('pushing')} Pushing Docker image..."
    docker push "$image_name:$image_tag"

    echo "{emoji_status('success')} Docker push completed successfully!"
    """,
    args=[
        Arg(name="image_name", type="str", description="Name of the image to push", required=True),
        Arg(name="image_tag", type="str", description="Tag of the image to push", required=True),
    ],
    long_running=True
)

register_docker_tool(docker_push_tool)
