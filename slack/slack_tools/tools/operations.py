from kubiya_sdk.tools import Arg
from .base import SlackTool
from kubiya_sdk.tools.registry import tool_registry

# Slack Send Message Tool
slack_send_message = SlackTool(
    name="slack_send_message",
    description="Send a message to a Slack channel",
    action="chat_postMessage",
    args=[
        Arg(name="channel", type="str", description="The channel to send the message to", required=True),
        Arg(name="text", type="str", description="The message text", required=True),
    ],
)

#need permissions: channels:read- groups:read- mpim:read- im:read
#slack_list_channels = SlackTool(
 #   name="slack_list_channels",
  #  description="List all channels in the Slack workspace",
   # action="conversations_list",
    #args=[]

# Slack Create Channel Tool - need permissions channels:write.invites and channels:manage
#slack_create_channel = SlackTool(
 #   name="slack_create_channel",
  #  description="Create a new Slack channel",
   # action="conversations_create",
    #args=[
     #   Arg(name="name", type="str", description="Name of the channel to create", required=True),
      #Arg(name="is_private", type="bool", description="Whether the channel should be private", required=False),
    #],
#)

# Slack Invite User Tool - need permissions channels:manage
#slack_invite_user = SlackTool(
 #   name="slack_invite_user",
  #  description="Invite a user to a Slack channel",
   # action="conversations_invite",
    #args=[
     #   Arg(name="channel", type="str", description="The ID of the channel to invite user to", required=True),
        #Arg(name="users", type="str", description="Comma-separated list of user IDs to invite", required=True),
    #],
#)

#Slack Get Channel History Tool
slack_get_channel_history = SlackTool(
    name="slack_get_channel_history",
    description="Get the message history of a Slack channel",
    action="conversations_history",
    args=[
        Arg(name="channel", type="str", description="The ID of the channel to fetch history from", required=True),
        Arg(name="limit", type="int", description="Number of messages to return (default 100)", required=False),
    ],
)

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

# - permissions required channels:history, groups:history, search:read
#slack_search_messages = SlackTool(
 #   name="slack_search_messages",
  #  description="Search for messages in a Slack workspace",
   # action="search_messages",
    #args=[
     #   Arg(name="query", type="str", description="Search query string", required=True),
      #  Arg(name="sort", type="str", description="Sort messages by score or timestamp", required=False),
       # Arg(name="sort_dir", type="str", description="Sort direction (asc or desc)", required=False),
        #Arg(name="count", type="int", description="Number of results to return", required=False),
    #],
#)

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

# Register all Slack tools
all_tools = [
    slack_send_message,
    slack_get_channel_history,
    slack_update_message,
    slack_delete_message,
    slack_add_reaction,
    slack_remove_reaction,
]

for tool in all_tools:
    tool_registry.register("slack", tool)