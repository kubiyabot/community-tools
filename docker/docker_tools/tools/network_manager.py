from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool
import os
import inspect

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(os.path.dirname(current_dir), 'scripts')

# Read the network script
with open(os.path.join(scripts_dir, 'network.py'), 'r') as f:
    NETWORK_SCRIPT = f.read()

network_manager_tool = DockerTool(
    name="manage-network",
    description="Manage Docker networks - create and connect",
    content="""
#!/bin/bash
set -e

echo "🌐 Initializing network management..."
pip install dagger-io > /dev/null 2>&1

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