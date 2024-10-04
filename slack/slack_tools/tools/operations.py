from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.models import Tool
from kubiya_sdk.tools.registry import tool_registry

# Define SlackTool class here to avoid circular import
class SlackTool(Tool):
    def __init__(self, name, description, action, args, long_running=False, mermaid_diagram=None):
        super().__init__(
            name=name,
            description=description,
            icon_url="https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png",
            type="docker",
            image="python:3.11",
            content="python /tmp/script.py",
            args=args,
            env=["KUBIYA_USER_EMAIL"],
            secrets=["SLACK_API_TOKEN"],
            long_running=long_running,
            mermaid=mermaid_diagram,
        )

# Slack Send Message Tool
slack_send_message = SlackTool(
    name="slack_send_message",
    description="Send a simple text message to a Slack channel or user",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="text", type="str", description="The message text", required=True),
        Arg(name="thread_ts", type="str", description="Timestamp of the parent message to reply in a thread", required=False),
    ],
)

# Slack Pin Message Tool
slack_pin_message = SlackTool(
    name="slack_pin_message",
    description="Pin a message to a channel",
    action="pins_add",
    args=[
        Arg(name="channel", type="str", description="The channel where the message is located", required=True),
        Arg(name="timestamp", type="str", description="Timestamp of the message to pin", required=True),
    ],
)

# Slack Unpin Message Tool
slack_unpin_message = SlackTool(
    name="slack_unpin_message",
    description="Unpin a message from a channel",
    action="pins_remove",
    args=[
        Arg(name="channel", type="str", description="The channel where the message is located", required=True),
        Arg(name="timestamp", type="str", description="Timestamp of the message to unpin", required=True),
    ],
)

# Slack Send and Pin Message Tool
slack_send_and_pin_message = SlackTool(
    name="slack_send_and_pin_message",
    description="Send a message and pin it to the channel",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="text", type="str", description="The message text", required=True),
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

# Slack Get Channel History Tool
slack_get_channel_history = SlackTool(
    name="slack_get_channel_history",
    description="Get the message history of a Slack channel",
    action="conversations_history",
    args=[
        Arg(name="channel", type="str", description="The ID of the channel to fetch history from", required=True),
        Arg(name="limit", type="int", description="Number of messages to return (default 100)", required=False),
    ],
)

# Slack Add Reaction Tool
slack_add_reaction = SlackTool(
    name="slack_add_reaction",
    description="Add a reaction to a message",
    action="reactions_add",
    args=[
        Arg(name="channel", type="str", description="Channel containing the message", required=True),
        Arg(name="timestamp", type="str", description="Timestamp of the message", required=True),
        Arg(name="name", type="str", description="Name of the emoji to react with", required=True),
    ],
)

# Slack Remove Reaction Tool
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

# Slack Search Messages Tool
slack_search_messages = SlackTool(
    name="slack_search_messages",
    description="Search for messages in a Slack workspace",
    action="search_messages",
    args=[
        Arg(name="query", type="str", description="Search query string", required=True),
        Arg(name="sort", type="str", description="Sort messages by score or timestamp", required=False),
        Arg(name="sort_dir", type="str", description="Sort direction (asc or desc)", required=False),
        Arg(name="count", type="int", description="Number of results to return", required=False),
    ],
)

# Slack Delete Message Tool
slack_delete_message = SlackTool(
    name="slack_delete_message",
    description="Delete a message from a Slack channel",
    action="chat_delete",
    args=[
        Arg(name="channel", type="str", description="Channel containing the message to be deleted", required=True),
        Arg(name="ts", type="str", description="Timestamp of the message to be deleted", required=True),
    ],
)

# Slack Update Message Tool
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

# Slack Upload File Tool
slack_upload_file = SlackTool(
    name="slack_upload_file",
    description="Upload a file to Slack",
    action="files_upload",
    args=[
        Arg(name="channels", type="str", description="Comma-separated list of channel IDs to share the file to", required=True),
        Arg(name="file", type="str", description="File content (use 'base64:' prefix for base64-encoded data)", required=True),
        Arg(name="filename", type="str", description="Name of the file", required=True),
        Arg(name="initial_comment", type="str", description="Initial comment for the file", required=False),
    ],
)

# Slack Schedule Message Tool
slack_schedule_message = SlackTool(
    name="slack_schedule_message",
    description="Schedule a message to be sent later",
    action="chat_scheduleMessage",
    args=[
        Arg(name="channel", type="str", description="The channel to send the message to", required=True),
        Arg(name="text", type="str", description="The message text", required=True),
        Arg(name="post_at", type="int", description="Unix timestamp for when to send the message", required=True),
    ],
)

# Slack Get User Info Tool
slack_get_user_info = SlackTool(
    name="slack_get_user_info",
    description="Get information about a Slack user",
    action="users_info",
    args=[
        Arg(name="user", type="str", description="User ID to get information for", required=True),
    ],
)

# Slack Get Channel Members Tool
slack_get_channel_members = SlackTool(
    name="slack_get_channel_members",
    description="Get the list of members in a Slack channel",
    action="conversations_members",
    args=[
        Arg(name="channel", type="str", description="Channel ID to get members for", required=True),
        Arg(name="limit", type="int", description="Number of members to return per page", required=False),
    ],
)

# Update the all_tools list
all_tools = [
    slack_send_message,
    slack_pin_message,
    slack_unpin_message,
    slack_send_and_pin_message,
    slack_list_channels,
    slack_create_channel,
    slack_invite_user,
    slack_get_channel_history,
    slack_add_reaction,
    slack_remove_reaction,
    slack_search_messages,
    slack_delete_message,
    slack_update_message,
    slack_upload_file,
    slack_schedule_message,
    slack_get_user_info,
    slack_get_channel_members,
]

# Register all Slack tools
for tool in all_tools:
    tool_registry.register("slack", tool)