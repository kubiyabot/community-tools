from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool

REPO_BUILD_SCRIPT = """
import dagger
import sys
import json
import asyncio
import os

async def build_from_repo(
    client,
    repo_url: str,
    branch: str,
    dockerfile_path: str,
    build_args: dict = None,
    secrets: dict = None
) -> dict:
    try:
        # Clone repository
        source = client.git(repo_url, branch=branch).tree()
        
        # Prepare secrets
        secret_mounts = []
        if secrets:
            for name, value in secrets.items():
                secret = client.set_secret(name, value)
                secret_mounts.append(dagger.Secret(name=name, secret=secret))
        
        # Build image
        container = source.docker_build(
            dockerfile=dockerfile_path,
            build_args=[dagger.BuildArg(name=k, value=v) for k, v in (build_args or {}).items()],
            secrets=secret_mounts
        )
        
        # Get image ID
        image_id = await container.id()
        
        return {
            "status": "success",
            "image_id": image_id,
            "repository": repo_url,
            "branch": branch
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

async def main():
    args = json.loads(sys.argv[1])
    async with dagger.Connection() as client:
        result = await build_from_repo(
            client,
            args["repo_url"],
            args["branch"],
            args["dockerfile_path"],
            args.get("build_args"),
            args.get("secrets")
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
"""

repo_build_tool = DockerTool(
    name="build-from-repository",
    description="Clones a Git repository and builds a Docker image from it using Dagger",
    content="""
#!/bin/bash
set -e

# Install dependencies
pip install dagger-io > /dev/null 2>&1

# Prepare build arguments
BUILD_ARGS='{
    "repo_url": "'$repo_url'",
    "branch": "'$branch'",
    "dockerfile_path": "'$dockerfile_path'",
    "build_args": '$build_args',
    "secrets": {
        "github_token": "'$GITHUB_TOKEN'"
    }
}'

# Run build script
python /tmp/repo_build.py "$BUILD_ARGS"
    """,
    args=[
        Arg(
            name="repo_url",
            type="str",
            description="URL of the Git repository",
            required=True
        ),
        Arg(
            name="branch",
            type="str",
            description="Branch to build from",
            required=True
        ),
        Arg(
            name="dockerfile_path",
            type="str",
            description="Path to the Dockerfile in the repository",
            required=True
        ),
        Arg(
            name="build_args",
            type="str",
            description="JSON string of build arguments",
            required=False,
            default='{}'
        )
    ],
    with_files=[
        FileSpec(
            destination="/tmp/repo_build.py",
            content=REPO_BUILD_SCRIPT
        )
    ],
    mermaid="""
    flowchart TD
        A[Git Repository] -->|Clone| B[Source Code]
        B -->|Build Context| C{Dagger Build}
        C -->|Dockerfile| D[Build Process]
        D -->|Layers| E[Image]
        
        F[Build Args] -->|Configure| C
        G[Secrets] -->|Secure| C
        
        style A fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
        style E fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
    """
)

tool_registry.register("docker", repo_build_tool) 