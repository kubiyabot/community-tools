from .tools..operations import get_slack_send_message, get_slack_list_channels
from kubiya_sdk.tools.registry import tool_registry

slack_send_message = get_slack_send_message()
slack_list_channels = get_slack_list_channels()

# Register all Slack tools
for tool in [slack_send_message, slack_list_channels]:
    tool_registry.register("slack", tool)

__all__ = [
    'slack_send_message',
    'slack_list_channels',
]
