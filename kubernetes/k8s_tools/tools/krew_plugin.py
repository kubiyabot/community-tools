from kubiya_sdk.tools import Arg
from .base import KubernetesTool
from kubiya_sdk.tools.registry import tool_registry

krew_plugin_tool = KubernetesTool(
    name="krew_plugin",
    description="Executes kubectl commands using Krew plugins.",
    content="""
#!/bin/bash
set -e

# Ensure the Krew plugins are accessible
export KREW_ROOT="/root/.krew"
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"

# Execute the kubectl plugin command
kubectl $plugin_command
""",
    args=[
        Arg(name="plugin_command", type="str", description="The kubectl plugin command to execute.", required=True),
    ],
)

tool_registry.register("kubernetes", krew_plugin_tool) 