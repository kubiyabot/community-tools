from kubiya_sdk.tools import Arg
from .base import SlackTool
from kubiya_sdk.tools.registry import tool_registry
import json

# Define templates in the global scope
simple_text_with_header_template = [
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "{header}"
        }
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "{body}"
        }
    }
]

info_message_template = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":information_source: *{title}*\n\n{message}"
        }
    }
]

warning_message_template = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":warning: *Warning: {title}*\n\n{message}"
        }
    }
]

success_message_template = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": ":white_check_mark: *Success: {title}*\n\n{message}"
        }
    }
]

two_column_message_template = [
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": "*Left column:*\n{left_column}"
            },
            {
                "type": "mrkdwn",
                "text": "*Right column:*\n{right_column}"
            }
        ]
    }
]

image_message_template = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "{text}"
        }
    },
    {
        "type": "image",
        "title": {
            "type": "plain_text",
            "text": "{image_title}"
        },
        "image_url": "{image_url}",
        "alt_text": "{alt_text}"
    }
]

# Slack Send Message Tool (without blocks)
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
        Arg(name="blocks", type="str", description="JSON string of Block Kit blocks", required=False),
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
        Arg(name="blocks", type="str", description="JSON string of Block Kit blocks", required=False),
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

# New Block Kit template tools

def create_block_kit_message(template, **kwargs):
    blocks = json.dumps(template.format(**kwargs))
    text = kwargs.get('text', 'Message sent using Block Kit')  # Fallback text
    return {'blocks': blocks, 'text': text}

# Simple text message with header
slack_send_simple_text_with_header = SlackTool(
    name="slack_send_simple_text_with_header",
    description="Send a message with a header and body text. Options: header, body",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="header", type="str", description="The header text", required=True),
        Arg(name="body", type="str", description="The body text (supports Markdown)", required=True),
    ],
)

# Information message with icon
slack_send_info_message = SlackTool(
    name="slack_send_info_message",
    description="Send an information message with an icon. Options: title, message",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="title", type="str", description="The title of the information message", required=True),
        Arg(name="message", type="str", description="The message body (supports Markdown)", required=True),
    ],
)

# Warning message with icon
slack_send_warning_message = SlackTool(
    name="slack_send_warning_message",
    description="Send a warning message with an icon. Options: title, message",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="title", type="str", description="The title of the warning message", required=True),
        Arg(name="message", type="str", description="The warning message body (supports Markdown)", required=True),
    ],
)

# Success message with icon
slack_send_success_message = SlackTool(
    name="slack_send_success_message",
    description="Send a success message with an icon. Options: title, message",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="title", type="str", description="The title of the success message", required=True),
        Arg(name="message", type="str", description="The success message body (supports Markdown)", required=True),
    ],
)

# Two-column layout message
slack_send_two_column_message = SlackTool(
    name="slack_send_two_column_message",
    description="Send a message with two columns. Options: left_column, right_column",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="left_column", type="str", description="Content for the left column (supports Markdown)", required=True),
        Arg(name="right_column", type="str", description="Content for the right column (supports Markdown)", required=True),
    ],
)

# Message with image
slack_send_image_message = SlackTool(
    name="slack_send_image_message",
    description="Send a message with an image. Options: text, image_title, image_url, alt_text",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel or user ID to send the message to", required=True),
        Arg(name="text", type="str", description="The message text (supports Markdown)", required=True),
        Arg(name="image_title", type="str", description="The title of the image", required=True),
        Arg(name="image_url", type="str", description="The URL of the image", required=True),
        Arg(name="alt_text", type="str", description="Alternative text for the image", required=True),
    ],
)

# Slack Get User's Presence
slack_get_user_presence = SlackTool(
    name="slack_get_user_presence",
    description="Get a user's presence status",
    action="users_getPresence",
    args=[
        Arg(name="user", type="str", description="User ID to get presence for", required=True),
    ],
)

# Slack Set User's Status
slack_set_user_status = SlackTool(
    name="slack_set_user_status",
    description="Set a user's status",
    action="users_profile_set",
    args=[
        Arg(name="status_text", type="str", description="Status text to set", required=True),
        Arg(name="status_emoji", type="str", description="Status emoji to set", required=True),
        Arg(name="status_expiration", type="int", description="Status expiration time in minutes", required=False),
    ],
)

# Slack Get Channel Info
slack_get_channel_info = SlackTool(
    name="slack_get_channel_info",
    description="Get information about a channel",
    action="conversations_info",
    args=[
        Arg(name="channel", type="str", description="Channel ID to get info for", required=True),
    ],
)

# Slack Archive Channel
slack_archive_channel = SlackTool(
    name="slack_archive_channel",
    description="Archive a channel",
    action="conversations_archive",
    args=[
        Arg(name="channel", type="str", description="Channel ID to archive", required=True),
    ],
)

# Slack Unarchive Channel
slack_unarchive_channel = SlackTool(
    name="slack_unarchive_channel",
    description="Unarchive a channel",
    action="conversations_unarchive",
    args=[
        Arg(name="channel", type="str", description="Channel ID to unarchive", required=True),
    ],
)

# Slack Get User's DM Channel
slack_get_user_dm_channel = SlackTool(
    name="slack_get_user_dm_channel",
    description="Get or create a DM channel with a user",
    action="conversations_open",
    args=[
        Arg(name="users", type="str", description="Comma-separated list of user IDs to open a DM with", required=True),
    ],
)

# Slack Get Workspace Usage
slack_get_workspace_usage = SlackTool(
    name="slack_get_workspace_usage",
    description="Get usage information for the workspace",
    action="team_info",
    args=[],
)

# Slack Get File Info
slack_get_file_info = SlackTool(
    name="slack_get_file_info",
    description="Get information about a file",
    action="files_info",
    args=[
        Arg(name="file", type="str", description="File ID to get info for", required=True),
    ],
)

# Slack Remind User
slack_remind_user = SlackTool(
    name="slack_remind_user",
    description="Create a reminder for a user",
    action="reminders_add",
    args=[
        Arg(name="text", type="str", description="The content of the reminder", required=True),
        Arg(name="time", type="str", description="When this reminder should happen: the Unix timestamp (up to 5 years from now), the number of seconds until the reminder (if within 24 hours), or a natural language description (Ex. 'in 15 minutes', or 'every Thursday')", required=True),
        Arg(name="user", type="str", description="The user who will receive the reminder. If no user is specified, the reminder will go to the user who created it.", required=False),
    ],
)

# Slack Get Team Members
slack_get_team_members = SlackTool(
    name="slack_get_team_members",
    description="Get a list of all users in the Slack workspace",
    action="users_list",
    args=[
        Arg(name="limit", type="int", description="Number of users to return per page", required=False),
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
    slack_send_simple_text_with_header,
    slack_send_info_message,
    slack_send_warning_message,
    slack_send_success_message,
    slack_send_two_column_message,
    slack_send_image_message,
    slack_get_user_presence,
    slack_set_user_status,
    slack_get_channel_info,
    slack_archive_channel,
    slack_unarchive_channel,
    slack_get_user_dm_channel,
    slack_get_workspace_usage,
    slack_get_file_info,
    slack_remind_user,
    slack_get_team_members,
]

# Register all Slack tools
for tool in all_tools:
    tool_registry.register("slack", tool)