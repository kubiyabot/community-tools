from kubiya_sdk.tools import Arg
from .base import SlackTool
from kubiya_sdk.tools.registry import tool_registry

# Slack Send Message Tool
slack_send_message = SlackTool(
    name="slack_send_message",
    description="Send a message to a Slack channel or user",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel name (with # prefix) or ID, or user ID to send the message to", required=True),
        Arg(name="text", type="str", description="The message text", required=True),
    ],
)

# Slack Upload File Tool
slack_upload_file = SlackTool(
    name="slack_upload_file",
    description="Upload a file to Slack",
    action="files_upload",
    args=[
        Arg(name="channels", type="str", description="Comma-separated list of channel IDs to share the file to", required=True),
        Arg(name="content", type="str", description="File content", required=True),
        Arg(name="filename", type="str", description="Name of the file", required=True),
        Arg(name="initial_comment", type="str", description="Initial comment for the file", required=False),
    ],
)

# Slack List Channels Tool
slack_list_channels = SlackTool(
    name="slack_list_channels",
    description="List all channels in the Slack workspace",
    action="conversations_list",
    args=[
        Arg(name="types", type="str", description="Comma-separated list of channel types to include", required=False),
    ],
)

# Slack Create Channel Tool
slack_create_channel = SlackTool(
    name="slack_create_channel",
    description="Create a new Slack channel",
    action="conversations_create",
    args=[
        Arg(name="name", type="str", description="Name of the channel to create", required=True),
        Arg(name="is_private", type="bool", description="Whether the channel should be private", required=False),
    ],
)

# Slack Invite User Tool
slack_invite_user = SlackTool(
    name="slack_invite_user",
    description="Invite a user to a Slack channel",
    action="conversations_invite",
    args=[
        Arg(name="channel", type="str", description="The ID of the channel to invite user to", required=True),
        Arg(name="users", type="str", description="Comma-separated list of user IDs to invite", required=True),
    ],
)

# Update the all_tools list
all_tools = [
    slack_send_message,
    slack_upload_file,
    slack_list_channels,
    slack_create_channel,
    slack_invite_user,
]

# Register all Slack tools
for tool in all_tools:
    tool_registry.register("slack", tool)