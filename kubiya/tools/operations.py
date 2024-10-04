from kubiya_sdk.tools import Arg
from .base import KubiyaTool
from kubiya_sdk.tools.registry import tool_registry

# Kubiya Schedule Task Tool
kubiya_schedule_task = KubiyaTool(
    name="kubiya_schedule_task",
    description="Schedule a task using Kubiya API",
    action="schedule_task",
    args=[
        Arg(name="name", type="str", description="The name of the scheduled task", required=True),
        Arg(name="cron", type="str", description="The cron expression for the schedule", required=True),
        Arg(name="ai_instructions", type="str", description="The AI instructions for the task", required=True),
        Arg(name="source", type="str", description="The source of the task - simple text description of why the task is in the queue", required=True),
    ],
)

# Add more Kubiya tools here as needed

# Update the all_tools list
all_tools = [
    kubiya_schedule_task,
    # Add more tools here as they are created
]

# Register all Kubiya tools
for tool in all_tools:
    tool_registry.register("kubiya", tool)