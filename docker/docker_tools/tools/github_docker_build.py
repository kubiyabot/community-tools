from .base import DockerTool, register_docker_tool
from kubiya_sdk.tools import Arg

github_docker_build_tool = DockerTool(
    name="github_docker_build",
    description="Builds a Docker image from a GitHub repository",
    content="""
    #!/bin/bash
    set -e

    # Clone the GitHub repository
    gh repo clone $repo_url -- -b $branch
    repo_name=$(basename $repo_url .git)
    cd $repo_name

    # Run the Dagger script to build and push the Docker image
    python3 /tmp/dagger_script.py <<EOF
import asyncio
from dagger_script import build_docker_image, clone_github_repo

async def main():
    await clone_github_repo("$repo_url", "$branch")
    await build_docker_image(".", "$dockerfile_path", "$image_name", "$image_tag")

asyncio.run(main())
EOF
    """,
    args=[
        Arg(name="repo_url", type="str", description="GitHub repository URL", required=True),
        Arg(name="branch", type="str", description="Git branch to use", required=False, default="main"),
        Arg(name="dockerfile_path", type="str", description="Path to the Dockerfile in the repository", required=True),
        Arg(name="image_name", type="str", description="Name for the built image", required=True),
        Arg(name="image_tag", type="str", description="Tag for the built image", required=True),
    ],
)

register_docker_tool(github_docker_build_tool)
