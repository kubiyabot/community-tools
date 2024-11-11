from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool
import os
from pathlib import Path

# Get the script content
scripts_dir = Path(__file__).parent.parent / "scripts"
with open(scripts_dir / "network.py", "r") as f:
    NETWORK_SCRIPT = f.read()

network_manager_tool = DockerTool(
    name="manage-network",
    description="Manage Docker networks - create and connect",
    content="""
#!/bin/sh
set -e

echo "🌐 Initializing network management..."

ARGS='{
    "action": "'$action'",
    "network_name": "'$network_name'",
    "driver": "'$driver'",
    "subnet": "'$subnet'"
}'

echo "🚀 Executing network operation: $action"
python /tmp/scripts/network.py "$ARGS"
    """,
    args=[
        Arg(
            name="action",
            type="str",
            description="Action to perform (create/connect)",
            required=True
        ),
        Arg(
            name="network_name",
            type="str",
            description="Name of the network",
            required=True
        ),
        Arg(
            name="driver",
            type="str",
            description="Network driver (bridge/overlay/host)",
            required=False,
            default="bridge"
        ),
        Arg(
            name="subnet",
            type="str",
            description="Subnet CIDR for the network",
            required=False
        )
    ],
    with_files=[
        FileSpec(
            destination="/tmp/scripts/network.py",
            content=NETWORK_SCRIPT
        )
    ],
    mermaid="""
    flowchart LR
        A[Network Management] --> B{Action}
        B -->|Create| C[New Network]
        B -->|Connect| D[Connect Container]
        C --> E[Configure Driver]
        C --> F[Set Subnet]
        
        style A fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
        style C fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
        style D fill:#2496ED,stroke:#fff,stroke-width:2px,color:#fff
    """
)

tool_registry.register("docker", network_manager_tool) 