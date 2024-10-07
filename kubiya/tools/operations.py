from kubiya_sdk.tools import Arg
from .base import KubiyaTool
from kubiya_sdk.tools.registry import tool_registry

# Kubiya Schedule Task Tool
kubiya_schedule_task = KubiyaTool(
    name="kubiya_schedule_task",
    description="Schedule a task with the Kubiya API",
    action="schedule_task",
    args=[
        Arg(name="execution_delay", type="str", description="The delay before the task is executed (e.g., 5h for 5 hours, 30m for 30 minutes)", required=True),
    ],
)

# Add more operation-related tools here as needed

# Update the all_tools list
all_tools = [
    kubiya_schedule_task,
    # Add more tools here as they are created
]

# Register all Kubiya operation tools
for tool in all_tools:
    tool_registry.register("kubiya_operation", tool)
