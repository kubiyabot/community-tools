from kubiya_workflow_sdk.tools import Arg
from .base import create_tool

# Schedule Task Tool
schedule_task = create_tool(
    name="schedule_task",
    description="Schedule a task to be executed by a Kubiya teammate",
    cli_command='''
echo "📅 Scheduling task..."

kubiya schedule task \\
    --time "${schedule_time}" \\
    $([ -n "${teammate_id}" ] && echo "--teammate-id ${teammate_id}") \\
    $([ -n "${teammate_name}" ] && echo "--teammate-name ${teammate_name}") \\
    --instructions "${instructions}" \\
    $([ -n "${slack_channel}" ] && echo "--slack-channel ${slack_channel}") \\
    --output json
''',
    args=[
        Arg(name="schedule_time", type="str", description="When to execute the task (e.g., '30m', '2h', '1d')", required=True),
        Arg(name="teammate_id", type="str", description="Teammate ID to assign the task to", required=False),
        Arg(name="teammate_name", type="str", description="Teammate name to assign the task to", required=False),
        Arg(name="instructions", type="str", description="Instructions for the teammate to execute", required=True),
        Arg(name="slack_channel", type="str", description="Slack channel for notifications", required=False),
    ],
)

__all__ = ['schedule_task']
