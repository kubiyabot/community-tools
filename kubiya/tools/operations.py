from kubiya_sdk.tools import Arg
from .base import KubiyaTool
from kubiya_sdk.tools.registry import tool_registry

# Kubiya Schedule Task Tool
kubiya_schedule_task = KubiyaTool(
    name="kubiya_schedule_task",
    description="Schedule a task to be executed by a Kubiya AI teammate at a specified time",
    action="schedule_task",
    args=[
        Arg(
            name="schedule_time",
            type="str",
            description="When to execute the task (e.g., '30m' for 30 minutes from now, '2h' for 2 hours, '1d' for 1 day)",
            required=True
        ),
        Arg(
            name="slack_channel",
            type="str",
            description="The Slack channel name or ID to send the task notification (e.g., 'general', 'C01234ABCDE'). If not provided, falls back to the default channel.",
            required=False
        ),
        Arg(
            name="ai_instructions",
            type="str",
            description="Instructions for the AI teammate to execute (e.g., 'Generate a weekly report on sales performance')",
            required=True
        ),
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
