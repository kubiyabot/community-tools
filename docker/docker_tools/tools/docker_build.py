from .base import DockerTool, register_docker_tool, emoji_status
from kubiya_sdk.tools import Arg

docker_build_tool = DockerTool(
    name="docker_build",
    description="Builds a Docker image from various sources using Dagger",
    content=f"""
    #!/bin/bash
    set -e

    echo "{emoji_status('info')} Starting Docker build process..."

    # Install Python and pip
    apk add --no-cache python3 py3-pip git

    # Create a temporary Python script with all necessary imports and logic
    cat << EOF > /tmp/docker_build_script.py
import os
import sys
import asyncio
import subprocess

# Install required packages
subprocess.check_call([sys.executable, "-m", "pip", "install", "dagger-io"])

import dagger

async def clone_repo(repo_url, branch="main"):
    if "github.com" in repo_url:
        subprocess.run(["gh", "repo", "clone", repo_url, "--", "-b", branch], check=True)
    elif "bitbucket.org" in repo_url and os.environ.get("BITBUCKET_ENABLED") == "true":
        subprocess.run(["git", "clone", "-b", branch, repo_url], check=True)
    else:
        print("{emoji_status('warning')} Unsupported Git provider. Falling back to public clone.")
        subprocess.run(["git", "clone", "-b", branch, repo_url], check=True)
    
    return os.path.basename(repo_url.rstrip(".git"))

async def build_docker_image(dockerfile_path, context_path, image_name, image_tag):
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        # Create a directory object from the build context
        context_dir = client.host().directory(context_path)

        # Build the Docker image
        image = await context_dir.docker_build(
            dockerfile=dockerfile_path,
            tag=f"{{image_name}}:{{image_tag}}"
        )

        # Push the image to the registry (assuming the registry is already configured)
        await image.publish(f"{{image_name}}:{{image_tag}}")

        return f"Successfully built and pushed Docker image: {{image_name}}:{{image_tag}}"

async def main():
    source = os.environ["SOURCE"]
    image_name = os.environ["IMAGE_NAME"]
    image_tag = os.environ["IMAGE_TAG"]
    dockerfile_path = os.environ.get("DOCKERFILE_PATH", "Dockerfile")
    context_path = "."

    if source.startswith("http"):
        print("{emoji_status('cloning')} Cloning repository...")
        repo_name = await clone_repo(source, os.environ.get("BRANCH", "main"))
        context_path = repo_name
        os.chdir(context_path)
    else:
        os.chdir(source)

    if not os.path.exists(dockerfile_path):
        print("{emoji_status('failure')} Dockerfile not found at specified path.")
        sys.exit(1)

    result = await build_docker_image(dockerfile_path, context_path, image_name, image_tag)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
EOF

    # Run the Python script
    python3 /tmp/docker_build_script.py

    echo "{emoji_status('success')} Docker build process completed successfully!"
    """,
    args=[
        Arg(name="source", type="str", description="Git repository URL or local directory path", required=True),
        Arg(name="image_name", type="str", description="Name for the built image", required=True),
        Arg(name="image_tag", type="str", description="Tag for the built image", required=True),
        Arg(name="dockerfile_path", type="str", description="Path to the Dockerfile", required=False, default="Dockerfile"),
        Arg(name="branch", type="str", description="Git branch to use (for repository sources)", required=False, default="main"),
    ],
    long_running=True
)

register_docker_tool(docker_build_tool)
