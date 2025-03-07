from kubiya_sdk.tools import Arg
from .base import SlackTool
from kubiya_sdk.tools.registry import tool_registry

# Slack Send Message Tool
slack_send_message = SlackTool(
    name="slack_send_message",
    description="Send a message to a given channel name or ID",
    action="chat_postMessage",
    args=[
        Arg(name="text", type="str", description="The message text, markdown is supported", required=True),
        Arg(name="channel", type="str", description="The channel name (with or without # prefix) or ID to send the message to", required=True),
    ],
)

slack_send_message_to_predefined_channel = SlackTool(
    name="slack_send_message_to_predefined_channel",
    description="Send a message to predefined channel",
    action="chat_postMessage",
    args=[
        Arg(name="text", type="str", description="The message text, markdown is supported", required=True),
    ],
    env=["NOTIFICATION_CHANNEL"]
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

#Slack List Channels Tool -  need permissions: channels:read- groups:read- mpim:read- im:read
slack_list_channels = SlackTool(
    name="slack_list_channels",
    description="List all channels in the Slack workspace",
    action="conversations_list",
    args=[
        Arg(name="types", type="str", description="Comma-separated list of channel types to include", required=False),
    ],
)

#Slack Create Channel Tool - need permissions channels:write.invites and channels:manage
slack_create_channel = SlackTool(
    name="slack_create_channel",
    description="Create a new Slack channel",
    action="conversations_create",
    args=[
        Arg(name="name", type="str", description="Name of the channel to create", required=True),
        Arg(name="is_private", type="bool", description="Whether the channel should be private", required=False),
    ],
)

# Slack Invite User Tool - need permissions channels:manage
slack_invite_user = SlackTool(
    name="slack_invite_user",
    description="Invite a user to a Slack channel",
    action="conversations_invite",
    args=[
        Arg(name="channel", type="str", description="The ID of the channel to invite user to", required=True),
        Arg(name="users", type="str", description="Comma-separated list of user IDs to invite", required=True),
    ],
)

# Slack Get Channel Info Tool - Requires permissions (channels:read, groups:read, mpim:read, im:read).
slack_get_channel_info = SlackTool(
    name="slack_get_channel_info",
    description="Get information about a Slack channel",
    action="conversations_info",
    args=[
        Arg(name="channel", type="str", description="The ID of the channel to get info for", required=True),
    ],
)

# Slack Get User Info Tool
slack_get_user_info = SlackTool(
    name="slack_get_user_info",
    description="Get information about a Slack user",
    action="users_info",
    args=[
        Arg(name="user", type="str", description="The ID of the user to get info for", required=True),
    ],
)

# Slack Add Reaction Tool
slack_add_reaction = SlackTool(
    name="slack_add_reaction",
    description="Add a reaction to a message",
    action="reactions_add",
    args=[
        Arg(name="channel", type="str", description="The channel containing the message", required=True),
        Arg(name="timestamp", type="str", description="The timestamp of the message", required=True),
        Arg(name="name", type="str", description="The name of the emoji to react with", required=True),
    ],
)

slack_delete_message = SlackTool(
    name="slack_delete_message",
    description="Delete a message from a Slack channel",
    action="chat_delete",
    args=[
        Arg(name="channel", type="str", description="Channel containing the message to be deleted", required=True),
        Arg(name="ts", type="str", description="Timestamp of the message to be deleted", required=True),
    ],
)

slack_update_message = SlackTool(
    name="slack_update_message",
    description="Update an existing message in a Slack channel",
    action="chat_update",
    args=[
        Arg(name="channel", type="str", description="Channel containing the message to be updated", required=True),
        Arg(name="ts", type="str", description="Timestamp of the message to be updated", required=True),
        Arg(name="text", type="str", description="New text for the message", required=True),
    ],
)

slack_remove_reaction = SlackTool(
    name="slack_remove_reaction",
    description="Remove a reaction from a message",
    action="reactions_remove",
    args=[
        Arg(name="channel", type="str", description="Channel containing the message", required=True),
        Arg(name="timestamp", type="str", description="Timestamp of the message", required=True),
        Arg(name="name", type="str", description="Name of the emoji to remove", required=True),
    ],
)

#Slack Get Channel History Tool
slack_get_channel_history = SlackTool(
    name="slack_get_channel_history",
    description="Get the message history of a Slack channel",
    action="conversations_history",
    args=[
        Arg(name="channel", type="str", description="The ID of the channel to fetch history from", required=True),
        Arg(name="limit", type="int", description="Number of messages to return (default 10)", required=False),
    ],
)

# Update the all_tools list
all_tools = [
    slack_send_message,
    slack_delete_message,
    slack_update_message,
    slack_add_reaction,
    slack_remove_reaction,
    slack_upload_file,
    slack_list_channels,
    slack_create_channel,
    slack_invite_user,
    slack_get_channel_info,
    slack_get_user_info,
    slack_get_channel_history,
    slack_send_message_to_predefined_channel,
]

# Register all Slack tools
for tool in all_tools:
    tool_registry.register("slack", tool)
