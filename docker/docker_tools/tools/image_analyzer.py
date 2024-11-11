from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool
import inspect

ANALYZE_SCRIPT = """
import dagger
import sys
import json
import asyncio

async def analyze_image(client, image_ref):
    try:
        # Pull the image
        container = client.container().from_(image_ref)
        
        # Get image details
        config = await container.config()
        
        # Get image size
        size = await container.rootfs().size()
        
        # List installed packages (basic approach)
        try:
            pkg_list = await container.with_exec(["dpkg-query", "-l"]).stdout()
        except:
            try:
                pkg_list = await container.with_exec(["rpm", "-qa"]).stdout()
            except:
                pkg_list = "Package list unavailable"

        # Get environment variables
        env = await container.env()
        
        # Get exposed ports
        ports = await container.ports()
        
        return {
            "config": config,
            "size_bytes": size,
            "packages": pkg_list,
            "environment": env,
            "exposed_ports": ports
        }
    except Exception as e:
        return {"error": str(e)}

async def main():
    async with dagger.Connection() as client:
        result = await analyze_image(client, sys.argv[1])
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
"""

analyze_image_tool = DockerTool(
    name="analyze-docker-image",
    description="Analyzes a Docker image and provides detailed information about its configuration, size, and contents",
    content="""
#!/bin/bash
set -e

# Install dependencies
pip install dagger-io > /dev/null 2>&1

# Run analysis script
python /tmp/analyze.py "$image_ref"
    """,
    args=[
        Arg(
            name="image_ref",
            type="str",
            description="Docker image reference to analyze (e.g., 'nginx:latest')",
            required=True
        )
    ],
    with_files=[
        FileSpec(
            destination="/tmp/analyze.py",
            content=ANALYZE_SCRIPT
        )
    ],
    mermaid="""
    flowchart TD
        A[Docker Image] --> B{Analysis}
        B --> C[Configuration]
        B --> D[Size]
        B --> E[Packages]
        B --> F[Environment]
        B --> G[Ports]
        
        C --> H[Final Report]
        D --> H
        E --> H
        F --> H
        G --> H
        
        style A fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
        style H fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
    """
)

tool_registry.register("docker", analyze_image_tool) 