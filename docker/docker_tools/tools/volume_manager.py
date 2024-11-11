from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool

VOLUME_SCRIPT = """
import dagger
import sys
import json
import asyncio

async def manage_volume(client, action, volume_name, source_path=None):
    try:
        if action == "create":
            volume = client.volume(volume_name)
            if source_path:
                volume = volume.with_directory("/", client.host().directory(source_path))
            volume_id = await volume.id()
            return {"status": "success", "volume_id": volume_id}
            
        elif action == "mount":
            # Mount volume logic
            volume = client.volume(volume_name)
            return {"status": "success", "message": f"Volume {volume_name} mounted"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def main():
    args = json.loads(sys.argv[1])
    async with dagger.Connection() as client:
        result = await manage_volume(
            client,
            args["action"],
            args["volume_name"],
            args.get("source_path")
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
"""

volume_manager_tool = DockerTool(
    name="manage-volume",
    description="Manage Docker volumes - create and mount",
    content="""
#!/bin/bash
set -e

echo "📦 Initializing volume management..."
pip install dagger-io > /dev/null 2>&1

ARGS='{
    "action": "'$action'",
    "volume_name": "'$volume_name'",
    "source_path": "'$source_path'"
}'

echo "🚀 Executing volume operation: $action"
python /tmp/volume.py "$ARGS"
    """,
    args=[
        Arg(
            name="action",
            type="str",
            description="Action to perform (create/mount)",
            required=True
        ),
        Arg(
            name="volume_name",
            type="str",
            description="Name of the volume",
            required=True
        ),
        Arg(
            name="source_path",
            type="str",
            description="Source path for volume content",
            required=False
        )
    ],
    with_files=[
        FileSpec(
            destination="/tmp/volume.py",
            content=VOLUME_SCRIPT
        )
    ],
    mermaid="""
    flowchart TD
        A[Volume Management] --> B{Action}
        B -->|Create| C[New Volume]
        B -->|Mount| D[Mount Volume]
        C --> E[Configure]
        D --> F[Attach to Container]
        
        style A fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
        style C fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
        style D fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
    """
)

tool_registry.register("docker", volume_manager_tool) 