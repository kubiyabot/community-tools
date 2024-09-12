from kubiya_sdk.tools import Arg
from .base import SlackTool
from kubiya_sdk.tools.registry import tool_registry

slack_send_message = SlackTool(
    name="slack_send_message",
    description="Send a message to a Slack channel or thread",
    content="""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.environ['SLACK_API_KEY'])

try:
    response = client.chat_postMessage(
        channel=channel,
        text=message,
        thread_ts=os.environ.get('SLACK_THREAD_TS')
    )
    print(f"Message sent: {response['ts']}")
except SlackApiError as e:
    print(f"Error sending message: {e}")
    """,
    args=[
        Arg(name="channel", type="str", description="Channel to send the message to", required=True),
        Arg(name="message", type="str", description="Message text", required=True),
    ],
    thread_context=True
)

slack_upload_file = SlackTool(
    name="slack_upload_file",
    description="Upload a file to a Slack channel or thread",
    content="""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.environ['SLACK_API_KEY'])

try:
    response = client.files_upload(
        channels=channel,
        file=file_path,
        title=title,
        initial_comment=initial_comment,
        thread_ts=os.environ.get('SLACK_THREAD_TS')
    )
    print(f"File uploaded: {response['file']['id']}")
except SlackApiError as e:
    print(f"Error uploading file: {e}")
    """,
    args=[
        Arg(name="channel", type="str", description="Channel to upload the file to", required=True),
        Arg(name="file_path", type="str", description="Path to the file to upload", required=True),
        Arg(name="title", type="str", description="Title of the file", required=False, default=""),
        Arg(name="initial_comment", type="str", description="Initial comment for the file", required=False, default=""),
    ],
    thread_context=True
)

slack_list_channels = SlackTool(
    name="slack_list_channels",
    description="List all channels in the Slack workspace",
    content="""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.environ['SLACK_API_KEY'])

try:
    response = client.conversations_list(limit=1000)
    channels = response['channels']
    for channel in channels[:10]:  # Limit output to 10 channels
        print(f"#{channel['name']} (ID: {channel['id']})")
    if len(channels) > 10:
        print(f"... and {len(channels) - 10} more channels")
except SlackApiError as e:
    print(f"Error listing channels: {e}")
    """,
    args=[]
)

slack_create_channel = SlackTool(
    name="slack_create_channel",
    description="Create a new Slack channel",
    content="""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.environ['SLACK_API_KEY'])

try:
    response = client.conversations_create(
        name=channel_name,
        is_private=is_private
    )
    print(f"Channel created: #{response['channel']['name']} (ID: {response['channel']['id']})")
except SlackApiError as e:
    print(f"Error creating channel: {e}")
    """,
    args=[
        Arg(name="channel_name", type="str", description="Name of the channel to create", required=True),
        Arg(name="is_private", type="bool", description="Whether the channel should be private", required=False, default=False),
    ]
)

slack_invite_user = SlackTool(
    name="slack_invite_user",
    description="Invite a user to a Slack channel",
    content="""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.environ['SLACK_API_KEY'])

try:
    response = client.conversations_invite(
        channel=channel_id,
        users=user_id
    )
    print(f"User {user_id} invited to channel {channel_id}")
except SlackApiError as e:
    print(f"Error inviting user: {e}")
    """,
    args=[
        Arg(name="channel_id", type="str", description="ID of the channel to invite the user to", required=True),
        Arg(name="user_id", type="str", description="ID of the user to invite", required=True),
    ]
)

slack_get_channel_history = SlackTool(
    name="slack_get_channel_history",
    description="Get the message history of a Slack channel",
    content="""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token=os.environ['SLACK_API_KEY'])

try:
    response = client.conversations_history(
        channel=channel_id,
        limit=limit
    )
    messages = response['messages']
    for msg in messages[:10]:  # Limit output to 10 messages
        print(f"[{msg['ts']}] {msg.get('text', 'No text')[:50]}...")  # Truncate long messages
    if len(messages) > 10:
        print(f"... and {len(messages) - 10} more messages")
except SlackApiError as e:
    print(f"Error getting channel history: {e}")
    """,
    args=[
        Arg(name="channel_id", type="str", description="ID of the channel to get history from", required=True),
        Arg(name="limit", type="int", description="Maximum number of messages to retrieve", required=False, default=100),
    ]
)

# Register all Slack tools
for tool in [slack_send_message, slack_upload_file, slack_list_channels, slack_create_channel, slack_invite_user, slack_get_channel_history]:
    tool_registry.register("slack", tool)